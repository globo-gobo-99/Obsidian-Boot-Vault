"""Real temporary Git repos: never use account credentials or a live vault."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / 'agent-bootstrap.py'


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'maintained'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'fixture@example.test')
        self.git('config', 'user.name', 'Fixture')
        (self.repo / 'START.md').write_text('approved instruction A\n')
        (self.repo / '.gitattributes').write_text('START.md export-ignore\n')
        self.git('add', '.')
        self.git('commit', '-m', 'fixture A')
        self.sha = self.git('rev-parse', 'HEAD')
        self.config = {'schema': 1, 'offline_max_age_seconds': 3600, 'sources': [
            {'name': 'cik', 'repository': str(self.repo), 'ref': 'refs/heads/main',
             'approved_sha': self.sha, 'entry': 'START.md'}]}
        self.config_path = self.root / 'source.json'
        self.state = self.root / 'state'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode().strip()

    def run_cli(self, *args, config=None, env=None):
        self.config_path.write_text(json.dumps(config or self.config))
        return subprocess.run(['python3', str(SCRIPT), '--config', str(self.config_path),
                               '--state', str(self.state), *args], text=True, capture_output=True, env=env)

    def prepared(self, *args, **kwargs):
        result = self.run_cli(*args, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_dirty_checkout_and_export_attributes_cannot_change_snapshot(self):
        (self.repo / 'START.md').write_text('uncommitted human edits\n')
        (self.repo / 'private-untracked.md').write_text('not instructions')
        before = self.git('status', '--porcelain')
        r = self.prepared()
        source = r['sources'][0]
        entry = Path(source['entry_path'])
        self.assertEqual(entry.read_text(), 'approved instruction A\n')
        self.assertFalse((entry.parent / 'private-untracked.md').exists())
        self.assertEqual(source['resolved_sha'], self.sha)
        self.assertEqual(self.git('status', '--porcelain'), before)
        self.assertEqual(entry.stat().st_mode & 0o222, 0)
        self.assertTrue(Path(r['receipt_path']).is_file())

    def test_new_approved_revision_does_not_change_previous_session(self):
        a = self.prepared()
        (self.repo / 'START.md').write_text('approved instruction B\n')
        self.git('add', '.'); self.git('commit', '-m', 'fixture B')
        self.config['sources'][0]['approved_sha'] = self.git('rev-parse', 'HEAD')
        b = self.prepared()
        self.assertNotEqual(a['receipt_path'], b['receipt_path'])
        self.assertEqual(Path(a['sources'][0]['entry_path']).read_text(), 'approved instruction A\n')
        self.assertEqual(Path(b['sources'][0]['entry_path']).read_text(), 'approved instruction B\n')

    def test_unapproved_update_is_rejected_without_receipt(self):
        (self.repo / 'START.md').write_text('unapproved B')
        self.git('add', '.'); self.git('commit', '-m', 'fixture B')
        r = self.run_cli()
        self.assertEqual(r.returncode, 2)
        self.assertIn('approval', r.stderr.lower())
        self.assertFalse(list(self.state.glob('receipts/*.json')))

    def test_offline_requires_explicit_cache_policy_and_existing_snapshot(self):
        self.assertEqual(self.run_cli('--offline', '--allow-cached').returncode, 2)
        a = self.prepared()
        self.assertEqual(self.run_cli('--offline').returncode, 2)
        b = self.prepared('--offline', '--allow-cached')
        self.assertEqual(b['sources'][0]['verification_time'], a['sources'][0]['verification_time'])
        self.assertEqual(b['sources'][0]['retrieval'], 'cache')
        self.assertEqual(b['instruction_freshness'], 'remote-unknown')

    def test_fetch_failure_can_only_use_explicit_verified_cache(self):
        self.prepared()
        self.repo.rename(self.root / 'unavailable')
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(self.prepared('--allow-cached')['sources'][0]['retrieval'], 'cache')

    def test_cache_expiry_and_changed_source_pin_are_rejected(self):
        a = self.prepared()
        record = self.state / 'verified' / (a['sources'][0]['snapshot_identity'] + '.json')
        record.chmod(0o600)
        data = json.loads(record.read_text()); data['verification_time'] = '2000-01-01T00:00:00+00:00'
        record.write_text(json.dumps(data))
        self.assertEqual(self.run_cli('--offline', '--allow-cached').returncode, 2)
        self.config['sources'][0]['approved_sha'] = 'a' * 40
        self.assertEqual(self.run_cli('--offline', '--allow-cached').returncode, 2)

    def test_corrupt_or_extra_files_are_rejected_even_offline(self):
        a = self.prepared()
        path = Path(a['sources'][0]['entry_path'])
        path.chmod(0o600); path.write_text('tampered')
        self.assertEqual(self.run_cli('--offline', '--allow-cached').returncode, 2)

    def test_untracked_snapshot_file_is_rejected(self):
        a = self.prepared()
        folder = Path(a['sources'][0]['entry_path']).parent
        folder.chmod(0o700); (folder / 'injected.md').write_text('injected')
        self.assertEqual(self.run_cli('--offline', '--allow-cached').returncode, 2)

    def test_symlinks_are_rejected(self):
        (self.repo / 'escape').symlink_to('/etc/passwd')
        self.git('add', '.'); self.git('commit', '-m', 'unsafe tree')
        self.config['sources'][0]['approved_sha'] = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.run_cli().returncode, 2)

    def test_missing_entry_and_escaping_entry_are_rejected(self):
        self.config['sources'][0]['entry'] = '../START.md'
        self.assertEqual(self.run_cli().returncode, 2)
        self.config['sources'][0]['entry'] = 'missing.md'
        self.assertEqual(self.run_cli().returncode, 2)

    def test_multi_source_failure_does_not_publish_partial_receipt(self):
        self.config['sources'].append(dict(self.config['sources'][0], name='obv', entry='absent.md'))
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertFalse(list(self.state.glob('receipts/*.json')))

    def test_missing_git_reports_prerequisite_without_traceback(self):
        # Python is absolute; the child has no git executable on PATH.
        self.config_path.write_text(json.dumps(self.config))
        result = subprocess.run([shutil.which('python3'), str(SCRIPT), '--config', str(self.config_path),
                                 '--state', str(self.state)], env=dict(os.environ, PATH='/nonexistent'),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Git', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_secret_bearing_repository_url_is_rejected_and_not_echoed(self):
        self.config['sources'][0]['repository'] = 'https://fake-token@github.com/owner/repo.git'
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('fake-token', result.stderr + result.stdout)


    def test_online_reverification_refreshes_cache_age_without_rewriting_snapshot(self):
        a = self.prepared()
        record = self.state / 'verified' / (a['sources'][0]['snapshot_identity'] + '.json')
        self.assertTrue(record.is_file(), 'online verification attestation missing')
        data = json.loads(record.read_text()); data['verification_time'] = '2000-01-01T00:00:00+00:00'
        record.write_text(json.dumps(data))
        before = Path(a['sources'][0]['entry_path']).stat().st_mtime_ns
        b = self.prepared()
        c = self.prepared('--offline', '--allow-cached')
        self.assertEqual(c['sources'][0]['verification_time'], b['sources'][0]['verification_time'])
        self.assertEqual(before, Path(a['sources'][0]['entry_path']).stat().st_mtime_ns)

    def test_snapshot_root_symlink_is_rejected(self):
        a = self.prepared()
        root = Path(a['sources'][0]['entry_path']).parent
        moved = root.with_name('outside-files')
        root.parent.chmod(0o700)
        root.rename(moved); root.symlink_to(moved, target_is_directory=True)
        self.assertEqual(self.run_cli('--offline', '--allow-cached').returncode, 2)

    def test_simultaneous_sessions_publish_independent_receipts(self):
        self.config_path.write_text(json.dumps(self.config))
        cmd = ['python3', str(SCRIPT), '--config', str(self.config_path), '--state', str(self.state)]
        children = [subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        results = []
        for child in children:
            out, err = child.communicate(timeout=20)
            self.assertEqual(child.returncode, 0, err)
            results.append(json.loads(out))
        self.assertNotEqual(results[0]['receipt_path'], results[1]['receipt_path'])
        self.assertEqual(results[0]['sources'][0]['snapshot_path'], results[1]['sources'][0]['snapshot_path'])


    def test_inherited_git_environment_cannot_redirect_operations(self):
        before = {p.relative_to(self.repo).as_posix(): p.read_bytes()
                  for p in self.repo.rglob('*') if p.is_file()}
        outside_objects = self.root / 'foreign-objects'
        outside_objects.mkdir()
        env = dict(os.environ, GIT_DIR=str(self.repo / '.git'),
                   GIT_WORK_TREE=str(self.repo), GIT_INDEX_FILE=str(self.root / 'foreign-index'),
                   GIT_TRACE=str(self.root / 'foreign-trace'),
                   GIT_OBJECT_DIRECTORY=str(outside_objects),
                   GIT_ALTERNATE_OBJECT_DIRECTORIES=str(self.repo / '.git/objects'))
        result = self.run_cli(env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        after = {p.relative_to(self.repo).as_posix(): p.read_bytes()
                 for p in self.repo.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.root / 'foreign-index').exists())
        self.assertFalse((self.root / 'foreign-trace').exists())
        self.assertEqual(list(outside_objects.iterdir()), [])

    def test_symlinked_state_subdirectories_cannot_redirect_writes(self):
        for name in ['snapshots', 'verified', 'receipts']:
            with self.subTest(directory=name):
                self.state = self.root / ('state-' + name)
                self.state.mkdir(mode=0o700)
                outside = self.root / ('outside-' + name)
                outside.mkdir(mode=0o700)
                (self.state / name).symlink_to(outside, target_is_directory=True)
                result = self.run_cli()
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_state_root_is_rejected(self):
        outside = self.root / 'outside-state'
        outside.mkdir(mode=0o700)
        self.state.symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
