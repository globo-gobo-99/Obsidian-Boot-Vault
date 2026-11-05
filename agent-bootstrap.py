#!/usr/bin/env python3
"""Prepare pinned instruction snapshots; never execute repository code or touch a vault.

Python 3.11+, Git. The reviewed local installation of this file is stage 0 tooling;
remote copies are data until separately reviewed and installed by the human.
"""
import argparse
import errno
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import urlsplit


class BootstrapError(Exception):
    """Sanitized bootstrap failure."""


class RetrievalError(BootstrapError):
    """Only transport failures may fall back to explicitly allowed cache."""


def git(*args, cwd=None):
    # Keep supported CA/credential prompting adapters; discard repository/config/trace
    # selectors inherited from whichever checkout launched the coding agent.
    transport_keys = {'GIT_SSL_CAINFO', 'GIT_SSL_CAPATH', 'GIT_ASKPASS'}
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_') or k in transport_keys}
    env['GIT_TERMINAL_PROMPT'] = '0'
    try:
        result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null',
                                 '-c', 'protocol.ext.allow=never', *args], cwd=cwd,
                                env=env,
                                capture_output=True, timeout=60)
    except FileNotFoundError:
        raise BootstrapError('Git is required; provision it before retrieving stage 1.') from None
    except (OSError, subprocess.TimeoutExpired):
        raise RetrievalError('Git operation unavailable or timed out; check access and connectivity.') from None
    if result.returncode:
        # Git stderr can contain credential-helper output; never relay it.
        raise RetrievalError('Git operation failed; check repository access, ref and connectivity.')
    return result.stdout


def utcnow():
    return datetime.now(timezone.utc)


def relative_file(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise BootstrapError('Entry/file path must be a safe relative POSIX path.')
    parts = value.split('/')
    if any(p in ('', '.', '..', '.git') for p in parts) or PurePosixPath(value).is_absolute():
        raise BootstrapError('Entry/file path must stay inside the snapshot.')
    return value


def validate_config(config):
    if not isinstance(config, dict) or config.get('schema') != 1:
        raise BootstrapError('Source configuration schema must be 1.')
    age = config.get('offline_max_age_seconds')
    if type(age) is not int or not 0 < age <= 30 * 86400:
        raise BootstrapError('Set offline_max_age_seconds explicitly between 1 and 2592000.')
    sources = config.get('sources')
    if not isinstance(sources, list) or not sources:
        raise BootstrapError('At least one explicitly approved source is required.')
    names = set()
    for s in sources:
        if not isinstance(s, dict) or set(s) != {'name', 'repository', 'ref', 'approved_sha', 'entry'}:
            raise BootstrapError('Each source requires only name, repository, ref, approved_sha and entry.')
        if not isinstance(s['name'], str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,39}', s['name']) or s['name'] in names:
            raise BootstrapError('Source names must be unique lowercase identifiers.')
        names.add(s['name'])
        repo = s['repository']
        if not isinstance(repo, str) or not repo or '\n' in repo or '\r' in repo:
            raise BootstrapError('Invalid source repository.')
        # Absolute paths support offline mirrors and isolated fixtures; never execute URL helpers.
        if not Path(repo).is_absolute():
            u = urlsplit(repo)
            if (u.scheme != 'https' or u.netloc != 'github.com' or u.query or u.fragment
                    or not re.fullmatch(r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?', u.path)):
                raise BootstrapError('Use a credential-free HTTPS GitHub URL or explicit absolute mirror path.')
        if not isinstance(s['approved_sha'], str) or not re.fullmatch(r'[0-9a-f]{40}', s['approved_sha']):
            raise BootstrapError('An approved full 40-character commit SHA is required.')
        ref = s['ref']
        if not isinstance(ref, str) or not (re.fullmatch(r'[0-9a-f]{40}', ref) or ref.startswith(('refs/heads/', 'refs/tags/'))):
            raise BootstrapError('Requested ref must be a full commit SHA or fully qualified branch/tag.')
        if any(c.isspace() or c in '~^:?*[\\' for c in ref) or '..' in ref or '@{' in ref:
            raise BootstrapError('Requested ref is invalid.')
        relative_file(s['entry'])
    return sources


def source_key(source):
    return hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()


def tree_files(repo, sha):
    # fsck checks object hashes, including the commit and its tree; no hooks or remote reads.
    git('fsck', '--strict', '--no-reflogs', cwd=repo)
    if git('rev-parse', f'{sha}^{{commit}}', cwd=repo).decode().strip() != sha:
        raise BootstrapError('Snapshot commit identity does not match approval.')
    entries = git('ls-tree', '-rz', '--full-tree', sha, cwd=repo).split(b'\0')
    files = {}
    total = 0
    for entry in filter(None, entries):
        meta, raw_path = entry.split(b'\t', 1)
        mode, kind, oid = meta.split()
        if kind != b'blob' or mode not in (b'100644', b'100755'):
            raise BootstrapError('Snapshot symlinks, submodules and special files are not supported.')
        try:
            path = relative_file(raw_path.decode('utf-8'))
        except UnicodeError:
            raise BootstrapError('Instruction filenames must be UTF-8.') from None
        blob = git('cat-file', 'blob', oid.decode(), cwd=repo)
        total += len(blob)
        if len(blob) > 5 * 1024 * 1024 or total > 50 * 1024 * 1024 or len(files) >= 5000:
            raise BootstrapError('Instruction source exceeds snapshot size limits.')
        files[path] = blob
    return files


def readonly(path):
    for child in path.rglob('*'):
        child.chmod(0o555 if child.is_dir() else 0o444)
    path.chmod(0o555)


def verify_snapshot(snapshot, source):
    if snapshot.is_symlink():
        raise BootstrapError('Snapshot path must not be a symlink.')
    try:
        record_path = snapshot / 'verification.json'
        if record_path.is_symlink():
            raise BootstrapError('Snapshot metadata must not be a symlink.')
        record = json.loads(record_path.read_text())
        if record['source'] != source:
            raise BootstrapError('Cached source does not match the approved configuration.')
        files = tree_files(snapshot / 'objects.git', source['approved_sha'])
        root = snapshot / 'files'
        if root.is_symlink() or not root.is_dir() or (snapshot / 'objects.git').is_symlink():
            raise BootstrapError('Snapshot roots must be real directories.')
        actual = set()
        for p in root.rglob('*'):
            if p.is_symlink():
                raise BootstrapError('Snapshot contains a symlink.')
            if p.is_file():
                name = p.relative_to(root).as_posix()
                actual.add(name)
                if name not in files or p.read_bytes() != files[name]:
                    raise BootstrapError('Snapshot content verification failed.')
            elif not p.is_dir():
                raise BootstrapError('Snapshot contains a special file.')
        if actual != set(files) or source['entry'] not in files:
            raise BootstrapError('Snapshot is incomplete or entry file is missing.')
        digest = hashlib.sha256()
        for name, blob in sorted(files.items()):
            digest.update(name.encode() + b'\0' + hashlib.sha256(blob).digest())
        record['content_digest'] = digest.hexdigest()
        return record
    except (OSError, ValueError, KeyError, TypeError, RetrievalError):
        raise BootstrapError('Snapshot verification failed; preserve it and investigate; no fallback to working files.') from None


def acquire(source, state, offline, allow_cached, max_age):
    key = source_key(source)
    snapshot = state / 'snapshots' / key
    retrieval = 'online'
    verification_time = None
    if not offline:
        staging = Path(tempfile.mkdtemp(prefix='.prepare-', dir=state))
        try:
            repo = staging / 'objects.git'
            git('init', '--bare', str(repo))
            git('fetch', '--no-tags', '--depth=1', '--', source['repository'], source['ref'], cwd=repo)
            sha = git('rev-parse', 'FETCH_HEAD^{commit}', cwd=repo).decode().strip()
            if sha != source['approved_sha']:
                raise BootstrapError('Requested ref changed: approval of a new SHA is required; no instructions loaded.')
            files = tree_files(repo, sha)
            if source['entry'] not in files:
                raise BootstrapError('Approved entry file is absent from the committed revision.')
            root = staging / 'files'
            root.mkdir()
            for name, blob in files.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(blob)
            verification_time = utcnow().isoformat()
            (staging / 'verification.json').write_text(json.dumps({
                'source': source, 'verification_time': verification_time}, indent=2) + '\n')
            if snapshot.exists():
                verify_snapshot(snapshot, source)
            else:
                # Publish only a completely built tree. Existing snapshots are never rewritten.
                readonly(staging)
                staging.chmod(0o700)  # rename across parents updates this directory's ..
                try:
                    staging.rename(snapshot)
                    snapshot.chmod(0o555)
                except OSError as error:
                    if error.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                        raise
                    verify_snapshot(snapshot, source)
        except RetrievalError:
            if not allow_cached:
                raise
            retrieval = 'cache'
        finally:
            if staging.exists():
                # Only remove this call's unpublished staging directory.
                for p in staging.rglob('*'):
                    if p.is_dir():
                        p.chmod(0o700)
                staging.chmod(0o700)
                shutil.rmtree(staging)
    else:
        retrieval = 'cache'
        if not allow_cached:
            raise BootstrapError('Offline startup requires explicit --allow-cached and a verified snapshot.')
    record = verify_snapshot(snapshot, source)
    attestations = state / 'verified'
    attestations.mkdir(mode=0o700, exist_ok=True)
    attestation = attestations / f'{key}.json'
    if retrieval == 'online':
        data = {'source': source, 'content_digest': record['content_digest'],
                'verification_time': verification_time}
        fd, temporary = tempfile.mkstemp(prefix='.verified-', dir=attestations)
        try:
            with os.fdopen(fd, 'w') as out:
                json.dump(data, out)
            os.replace(temporary, attestation)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    if retrieval == 'cache':
        try:
            if attestation.is_symlink():
                raise BootstrapError('Cached verification attestation must not be a symlink.')
            data = json.loads(attestation.read_text())
            if data['source'] != source or data['content_digest'] != record['content_digest']:
                raise BootstrapError('Cached verification attestation does not match snapshot.')
            age = (utcnow() - datetime.fromisoformat(data['verification_time'])).total_seconds()
        except (OSError, KeyError, TypeError, ValueError):
            raise BootstrapError('Cached verification attestation is missing or invalid.') from None
        if not 0 <= age <= max_age:
            raise BootstrapError('Previously verified snapshot is expired or has an invalid future time.')
        verification_time = data['verification_time']
    return {
        'name': source['name'], 'repository': source['repository'], 'requested_ref': source['ref'],
        'resolved_sha': source['approved_sha'], 'entry_file': source['entry'],
        'verification_time': verification_time, 'retrieval': retrieval,
        'snapshot_identity': key, 'snapshot_path': str(snapshot),
        'content_digest': record['content_digest'], 'entry_path': str(snapshot / 'files' / source['entry'])}


def private_directory(path):
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise BootstrapError('Bootstrap state directories must be real private directories, not links.')
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.stat().st_mode & 0o077:
        raise BootstrapError('Bootstrap state directories must have owner-only permissions; provision them explicitly.')


def prepare(config, state, offline=False, allow_cached=False):
    sources = validate_config(config)
    if shutil.which('git') is None:
        raise BootstrapError('Git is required, including for cached snapshot validation.')
    state = Path(state).expanduser().absolute()
    private_directory(state)
    state = state.resolve()
    for name in ['snapshots', 'verified', 'receipts']:
        private_directory(state / name)
    prepared = [acquire(s, state, offline, allow_cached, config['offline_max_age_seconds']) for s in sources]
    receipts = state / 'receipts'
    receipts.mkdir(mode=0o700, exist_ok=True)
    identity = str(uuid.uuid4())
    path = receipts / f'{identity}.json'
    receipt = {'schema': 1, 'receipt_identity': identity, 'receipt_path': str(path),
               'prepared_at': utcnow().isoformat(),
               'instruction_freshness': 'remote-unknown' if any(s['retrieval'] == 'cache' for s in prepared) else 'approved-ref-verified',
               'sources': prepared}
    # No credentials or inherited environment are recorded. No global latest pointer.
    with path.open('x') as out:
        json.dump(receipt, out, indent=2)
        out.write('\n')
    path.chmod(0o444)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--allow-cached', action='store_true')
    args = parser.parse_args()
    try:
        receipt = prepare(json.loads(args.config.read_text()), args.state, args.offline, args.allow_cached)
        print(json.dumps(receipt, indent=2))
        return 0
    except (BootstrapError, OSError, ValueError, TypeError):
        error = sys.exc_info()[1]
        print(str(error) if isinstance(error, BootstrapError) else 'Cannot read configuration or prepare private snapshot storage.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
