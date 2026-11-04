#!/usr/bin/env python3
"""Enroll or resume an independent Obsidian replica using selected environment inputs."""
import argparse
from dataclasses import dataclass
import getpass
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

DEFAULT_VAULT_ID = '6ced867ab480ebf9acbc2f5f51c74007'


class SetupNeeded(Exception):
    """Actionable failure with no credential values in its message."""


@dataclass
class Settings:
    root: Path
    vault: Path
    vault_id: str
    state: Path
    email: str
    device_name: str
    device_prefix: str
    env: dict

    @property
    def cli(self):
        return self.root / 'dot-box-tools/node_modules/.bin/ob'


def settings_from_env(source=None):
    env = dict(os.environ if source is None else source)
    root = Path(env.get('OB_SK_WORKSPACE_ROOT') or '/workspace').expanduser().resolve()
    vault_id = env.get('OBSIDIAN_VAULT_ID', DEFAULT_VAULT_ID).strip()
    if len(vault_id) != 32 or any(c not in '0123456789abcdef' for c in vault_id):
        raise SetupNeeded('OBSIDIAN_VAULT_ID must be an existing 32-character hexadecimal vault ID.')
    return Settings(root,
                    Path(env.get('OBSIDIAN_VAULT_PATH') or root / 'vaults/DevPod-Vault').expanduser().resolve(),
                    vault_id,
                    Path(env.get('OBSIDIAN_STATE_HOME') or root / '.dot-box-config').expanduser().resolve(),
                    env.get('OBSIDIAN_SYNC_EMAIL') or env.get('OB_SK_OWNER_EMAIL', ''),
                    env.get('OBSIDIAN_DEVICE_NAME', '').strip(),
                    env.get('OBSIDIAN_DEVICE_PREFIX') or 'codex-cloud-box', env)


class Client:
    def __init__(self, settings):
        self.settings = settings

    def run(self, args, *, password=None, capture=True):
        env = self.settings.env.copy()
        env.update(XDG_CONFIG_HOME=str(self.settings.state), NODE_USE_ENV_PROXY='1')
        env.pop('OBSIDIAN_SYNC_PASSWORD', None)
        env.pop('OBSIDIAN_E2EE_PASSWORD', None)
        if password:
            # Put the password in JS argv inside Node, never in the OS command line.
            env['_OB_SK_CLI_PASSWORD'] = password
            shim = ('const p=process.env._OB_SK_CLI_PASSWORD;'
                    'delete process.env._OB_SK_CLI_PASSWORD;'
                    'const cli=process.argv[1];'
                    'process.argv=[process.execPath,cli,...process.argv.slice(2),"--password",p];'
                    'require(cli);')
            cmd = ['node', '-e', shim, str(self.settings.cli.resolve()), *args]
        else:
            cmd = [str(self.settings.cli), *args]
        try:
            return subprocess.run(cmd, env=env, text=True, capture_output=capture,
                                  timeout=60 if capture else None)
        except (OSError, subprocess.TimeoutExpired):
            raise SetupNeeded('Obsidian client unavailable or request timed out; check tools and connectivity.') from None


def decoded(result, operation):
    if result.returncode:
        raise SetupNeeded(f'{operation} failed; check connectivity and the configured credential.')
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError):
        raise SetupNeeded(f'{operation} returned an unexpected response.') from None


def active_writer(settings):
    try:
        # Match the pinned client's native lease; never remove another writer's lock.
        return time.time() - (settings.vault / '.gobsidian/.sync.lock').stat().st_mtime < 5
    except FileNotFoundError:
        return False


def saved_device_name(settings):
    folder = settings.state / 'ob-sk' / settings.vault_id
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = folder / 'device-name'
    if path.exists():
        return path.read_text().strip()
    name = f'{settings.device_prefix}-{secrets.token_hex(6)}'
    try:
        with path.open('x') as out:
            out.write(name + '\n')
    except FileExistsError:
        return path.read_text().strip()
    return name


def bootstrap(settings, client, *, continuous=False, interactive=False):
    result = client.run(['sync-status', '--path', str(settings.vault), '--json'])
    if result.returncode == 0:
        status = decoded(result, 'Local status')
        if status.get('vaultId') != settings.vault_id:
            raise SetupNeeded('Local path is bound to another vault; refusing to rebind.')
    elif result.returncode == 3:
        status = None
    else:
        raise SetupNeeded('Existing Sync configuration is incomplete or unreadable; repair it before enrolling.')
    if active_writer(settings):
        if status is None:
            raise SetupNeeded('A Sync writer owns this path but its binding is unavailable; no changes made.')
        if settings.device_name and settings.device_name != status.get('deviceName'):
            raise SetupNeeded('Stop the existing writer before changing its device name.')
        print('An existing Sync writer owns this replica; leaving its configuration unchanged.')
        return 'already-running'

    remote = client.run(['sync-list-remote', '--json'])
    if remote.returncode:
        if settings.env.get('OBSIDIAN_AUTH_TOKEN'):
            raise SetupNeeded('The supplied OBSIDIAN_AUTH_TOKEN could not list vaults; check the session and network.')
        password = settings.env.get('OBSIDIAN_SYNC_PASSWORD')
        if not password and interactive:
            password = getpass.getpass('Obsidian account password: ')
        if not password or not settings.email:
            raise SetupNeeded('Login required: supply OBSIDIAN_AUTH_TOKEN, or OBSIDIAN_SYNC_EMAIL and OBSIDIAN_SYNC_PASSWORD.')
        if client.run(['login', '--email', settings.email], password=password).returncode:
            raise SetupNeeded('Obsidian account login failed; check credentials or complete MFA interactively.')
        remote = client.run(['sync-list-remote', '--json'])
    remotes = decoded(remote, 'Remote vault listing')
    if not any(v.get('id') == settings.vault_id for group in ('vaults', 'shared')
               for v in remotes.get(group, [])):
        raise SetupNeeded('Requested existing vault unavailable to this account; no remote vault was created.')

    if status is None:
        locals_ = decoded(client.run(['sync-list-local', '--json']), 'Local vault listing')
        if any(v.get('id') == settings.vault_id and Path(v['path']).resolve() != settings.vault
               for v in locals_.get('vaults', [])):
            raise SetupNeeded('This state directory already binds this vault to another path; use an independent OBSIDIAN_STATE_HOME.')
        device = settings.device_name or saved_device_name(settings)
        password = settings.env.get('OBSIDIAN_E2EE_PASSWORD')
        if not password and interactive:
            password = getpass.getpass('Vault encryption password (separate from account password; blank for standard): ')
        setup = client.run(['sync-setup', '--vault', settings.vault_id, '--path', str(settings.vault),
                            '--device-name', device, '--config-dir', '.gobsidian', '--json'], password=password)
        if setup.returncode:
            raise SetupNeeded('Vault enrollment failed; check OBSIDIAN_E2EE_PASSWORD (the vault password), account access and network.')
    else:
        device = settings.device_name or status.get('deviceName') or saved_device_name(settings)
    if active_writer(settings):
        raise SetupNeeded('Another Sync writer started during setup; configuration was not updated.')
    config = client.run(['sync-config', '--path', str(settings.vault), '--device-name', device,
                         '--file-types', 'image,audio,pdf,video,unsupported'])
    if config.returncode:
        raise SetupNeeded('Sync configuration failed; no second writer was started.')
    result = client.run(['sync', '--path', str(settings.vault),
                         *(['--continuous'] if continuous else [])], capture=False)
    if result.returncode:
        raise SetupNeeded('Sync stopped with an error; check connectivity or an existing writer.')
    return 'synced'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--continuous', action='store_true')
    parser.add_argument('--install-only', action='store_true', help='Prepare tooling without account or replica enrollment')
    parser.add_argument('--check', action='store_true', help='Show non-secret settings without writing or connecting')
    args = parser.parse_args()
    try:
        settings = settings_from_env()
        if args.check:
            print(json.dumps(dict(vault_id=settings.vault_id, vault_path=str(settings.vault),
                                  state_home=str(settings.state),
                                  device_name=settings.device_name or '(reuse binding or generate unique name)'), indent=2))
            return 0
        if not settings.cli.exists():
            env = settings.env.copy()
            for key in ['OBSIDIAN_SYNC_PASSWORD', 'OBSIDIAN_E2EE_PASSWORD', 'OBSIDIAN_AUTH_TOKEN']:
                env.pop(key, None)
            install = subprocess.run(['npm', 'install', '--prefix', str(settings.root / 'dot-box-tools'),
                                      '--cache', '/tmp/dot-box-npm-cache', 'obsidian-headless@0.0.14',
                                      '--no-audit', '--no-fund'], env=env)
            if install.returncode:
                raise SetupNeeded('Tool installation failed; check npm and network access.')
        if args.install_only:
            print('Tooling ready; no account login or replica enrollment performed.')
            return 0
        settings.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        bootstrap(settings, Client(settings), continuous=args.continuous, interactive=sys.stdin.isatty())
        return 0
    except (SetupNeeded, OSError) as error:
        print(str(error) if isinstance(error, SetupNeeded) else 'Local setup failed; check paths and permissions.', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == '__main__':
    sys.exit(main())
