import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bootstrap_vault', Path(__file__).parents[1] / 'bootstrap-vault.py')
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


class FakeClient:
    def __init__(self, settings, *, existing=False):
        self.s = settings
        self.existing = existing
        self.calls = []
        self.remote_failure = False
        self.setup_failure = False
        self.other_path = False
        self.bound_id = settings.vault_id
        self.old_device = 'existing-dot-box'

    def run(self, args, *, password=None, capture=True):
        self.calls.append((args, password, capture))
        command = args[0]
        code, data = 0, {}
        if command == 'sync-status':
            if self.existing:
                data = {'vaultId': self.bound_id, 'deviceName': self.old_device}
            else:
                code = 3
        elif command == 'sync-list-remote':
            code = 2 if self.remote_failure else 0
            data = {'vaults': [{'id': self.s.vault_id}], 'shared': []}
        elif command == 'login':
            self.remote_failure = False
        elif command == 'sync-list-local':
            data = {'vaults': [{'id': self.s.vault_id, 'path': '/other-replica'}] if self.other_path else []}
        elif command == 'sync-setup':
            code = 2 if self.setup_failure or not password else 0
        return subprocess.CompletedProcess(args, code, json.dumps(data), '')


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = {'OB_SK_WORKSPACE_ROOT': self.tmp.name,
                    'OBSIDIAN_VAULT_ID': 'a' * 32,
                    'OBSIDIAN_VAULT_PATH': self.tmp.name + '/vault',
                    'OBSIDIAN_STATE_HOME': self.tmp.name + '/state',
                    'OBSIDIAN_E2EE_PASSWORD': 'fake-vault-secret'}
        self.s = b.settings_from_env(self.env)

    def test_environment_overrides_are_used_for_enrollment(self):
        self.env['OBSIDIAN_DEVICE_NAME'] = 'cloud-task-test'
        s = b.settings_from_env(self.env)
        c = FakeClient(s)
        self.assertEqual(b.bootstrap(s, c, continuous=True), 'synced')
        setup = next(call for call in c.calls if call[0][0] == 'sync-setup')
        self.assertIn(s.vault_id, setup[0])
        self.assertIn(str(s.vault), setup[0])
        self.assertIn('cloud-task-test', setup[0])
        self.assertEqual(setup[1], 'fake-vault-secret')
        self.assertIn('--continuous', c.calls[-1][0])

    def test_existing_identity_survives_resume(self):
        c = FakeClient(self.s, existing=True)
        b.bootstrap(self.s, c)
        self.assertFalse(any(x[0][0] == 'sync-setup' for x in c.calls))
        config = next(x for x in c.calls if x[0][0] == 'sync-config')
        self.assertIn('existing-dot-box', config[0])

    def test_generated_names_are_stable_and_independent(self):
        first = b.saved_device_name(self.s)
        self.assertEqual(first, b.saved_device_name(self.s))
        env = dict(self.env, OBSIDIAN_STATE_HOME=self.tmp.name + '/second-state')
        second = b.saved_device_name(b.settings_from_env(env))
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith('codex-cloud-box-'))

    def test_wrong_binding_refuses_before_network_or_writes(self):
        c = FakeClient(self.s, existing=True)
        c.bound_id = 'b' * 32
        with self.assertRaisesRegex(b.SetupNeeded, 'refusing to rebind'):
            b.bootstrap(self.s, c)
        self.assertEqual(len(c.calls), 1)

    def test_running_writer_is_preserved(self):
        c = FakeClient(self.s, existing=True)
        lock = self.s.vault / '.gobsidian/.sync.lock'
        lock.mkdir(parents=True)
        self.assertEqual(b.bootstrap(self.s, c), 'already-running')
        self.assertEqual(len(c.calls), 1)

    def test_duplicate_state_for_same_remote_is_not_repointed(self):
        c = FakeClient(self.s)
        c.other_path = True
        with self.assertRaisesRegex(b.SetupNeeded, 'independent OBSIDIAN_STATE_HOME'):
            b.bootstrap(self.s, c)
        self.assertFalse(any(x[0][0] == 'sync-setup' for x in c.calls))

    def test_account_and_vault_passwords_are_separate(self):
        self.env.update(OBSIDIAN_SYNC_EMAIL='bot@example.test', OBSIDIAN_SYNC_PASSWORD='fake-account-secret')
        s = b.settings_from_env(self.env)
        c = FakeClient(s)
        c.remote_failure = True
        b.bootstrap(s, c)
        self.assertEqual(next(x for x in c.calls if x[0][0] == 'login')[1], 'fake-account-secret')
        self.assertEqual(next(x for x in c.calls if x[0][0] == 'sync-setup')[1], 'fake-vault-secret')

    def test_failed_e2ee_never_starts_sync_or_prints_secret(self):
        c = FakeClient(self.s)
        c.setup_failure = True
        with self.assertRaises(b.SetupNeeded) as error:
            b.bootstrap(self.s, c)
        self.assertNotIn('fake-vault-secret', str(error.exception))
        self.assertFalse(any(x[0][0] == 'sync' for x in c.calls))

    def test_invalid_explicit_token_does_not_switch_accounts(self):
        s = b.settings_from_env(dict(self.env, OBSIDIAN_AUTH_TOKEN='fake-invalid-token'))
        c = FakeClient(s)
        c.remote_failure = True
        with self.assertRaisesRegex(b.SetupNeeded, 'supplied OBSIDIAN_AUTH_TOKEN'):
            b.bootstrap(s, c)
        self.assertFalse(any(x[0][0] == 'login' for x in c.calls))

    def test_password_is_not_in_os_arguments_or_unrelated_child_environment(self):
        client = b.Client(self.s)
        with patch.object(b.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{}', '')) as run:
            client.run(['sync-setup', '--json'], password='fake-vault-secret')
            args, kwargs = run.call_args
            self.assertNotIn('fake-vault-secret', ' '.join(args[0]))
            self.assertNotIn('OBSIDIAN_E2EE_PASSWORD', kwargs['env'])
            self.assertEqual(kwargs['env']['_OB_SK_CLI_PASSWORD'], 'fake-vault-secret')

    def test_node_password_bridge_works_with_commonjs_client(self):
        cli = self.s.cli
        cli.parent.mkdir(parents=True)
        cli.write_text('const i=process.argv.indexOf("--password"); if(i<0 || process.argv[i+1]!=="fake-vault-secret" || process.env._OB_SK_CLI_PASSWORD) process.exit(4); console.log("bridge-ok");')
        self.s.env['PATH'] = __import__('os').environ['PATH']
        result = b.Client(self.s).run(['sync-setup', '--json'], password='fake-vault-secret')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'bridge-ok')


if __name__ == '__main__':
    unittest.main()
