import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('readiness', Path(__file__).parents[1] / 'vault-readiness.py')
r = importlib.util.module_from_spec(spec)
# Missing implementation is an assertion failure rather than a silent skipped suite.
if spec.origin and Path(spec.origin).exists():
    spec.loader.exec_module(r)


class ReadinessTests(unittest.TestCase):
    def evidence(self):
        return {'schema': 1,
                'instructions': {'snapshot_verified': True, 'approved': True, 'remote_verified': True,
                                 'cache_allowed': False, 'cache_within_policy': False},
                'vault': {'expected_id': 'a' * 32, 'bound_id': 'a' * 32,
                          'expected_path': '/replica', 'bound_path': '/replica',
                          'remote_visible': True, 'owner_count': 1, 'owner_running': True,
                          'initial_sync_complete': True, 'required_files_present': True,
                          'selective_sync_covers_required': True, 'conflicts_checked': True,
                          'conflicts': False, 'pending_changes_checked': True, 'pending_changes': False,
                          'last_complete_at': '2026-11-04T20:00:00+00:00',
                          'last_change_at': '2026-11-04T19:59:00+00:00',
                          'last_failure_at': None, 'health_checked_at': '2026-11-04T20:00:00+00:00',
                          'max_evidence_age_seconds': 300}}

    def assess(self, e):
        self.assertTrue(callable(getattr(r, 'assess', None)), 'readiness assess is not implemented')
        return r.assess(e, now='2026-11-04T20:01:00+00:00')

    def test_healthy_existing_vault_allows_task_edits(self):
        result = self.assess(self.evidence())
        self.assertTrue(result['read_allowed'])
        self.assertTrue(result['write_allowed'])
        self.assertEqual(result['vault_state'], 'ready-at-observation')

    def test_wrong_or_missing_vault_identity_blocks_reads_and_edits(self):
        for key, value in [('bound_id', 'b' * 32), ('bound_id', None), ('bound_path', '/other')]:
            with self.subTest(key=key, value=value):
                e = self.evidence(); e['vault'][key] = value
                result = self.assess(e)
                self.assertFalse(result['read_allowed'])
                self.assertFalse(result['write_allowed'])

    def test_incomplete_stale_conflicted_or_pending_vault_blocks_edits(self):
        cases = [('initial_sync_complete', False), ('required_files_present', False),
                 ('selective_sync_covers_required', False), ('conflicts', True),
                 ('conflicts_checked', False), ('pending_changes', True),
                 ('pending_changes_checked', False), ('owner_count', 2), ('owner_running', False),
                 ('remote_visible', False), ('last_complete_at', None),
                 ('last_complete_at', '2026-11-04T19:00:00+00:00'),
                 ('health_checked_at', '2026-11-04T19:00:00+00:00'),
                 ('last_change_at', '2026-11-04T20:00:30+00:00'),
                 ('last_failure_at', '2026-11-04T20:00:30+00:00')]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                e = self.evidence(); e['vault'][key] = value
                self.assertFalse(self.assess(e)['write_allowed'])

    def test_instruction_and_vault_freshness_are_independent(self):
        e = self.evidence(); e['instructions']['remote_verified'] = False
        e['instructions'].update(cache_allowed=True, cache_within_policy=True)
        result = self.assess(e)
        self.assertEqual(result['instruction_state'], 'verified-cache-remote-unknown')
        self.assertEqual(result['vault_state'], 'ready-at-observation')
        self.assertTrue(result['read_allowed']); self.assertFalse(result['write_allowed'])
        e = self.evidence(); e['vault']['remote_visible'] = False
        result = self.assess(e)
        self.assertEqual(result['instruction_state'], 'approved-ref-verified')
        self.assertNotEqual(result['vault_state'], 'ready-at-observation')
        self.assertFalse(result['write_allowed'])

    def test_absent_or_malformed_evidence_fails_closed_without_echoing_input(self):
        for evidence in [{}, {'schema': 1}, {'schema': 1, 'instructions': 'fake-secret'}]:
            result = self.assess(evidence)
            self.assertFalse(result['read_allowed']); self.assertFalse(result['write_allowed'])
            self.assertNotIn('fake-secret', str(result))
        e = self.evidence(); e['vault']['conflicts'] = 'false'
        self.assertFalse(self.assess(e)['write_allowed'])

    def test_expired_or_unapproved_instructions_block_readiness(self):
        for key in ['snapshot_verified', 'approved', 'remote_verified']:
            e = self.evidence(); e['instructions'][key] = False
            self.assertFalse(self.assess(e)['read_allowed'])

    def test_evaluator_never_changes_evidence(self):
        e = self.evidence(); original = copy.deepcopy(e)
        self.assess(e)
        self.assertEqual(e, original)


if __name__ == '__main__':
    unittest.main()
