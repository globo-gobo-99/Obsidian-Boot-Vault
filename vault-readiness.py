#!/usr/bin/env python3
"""Evaluate explicitly collected readiness evidence; never operate on a live vault.

This is a decision aid, not an evidence collector or freshness oracle. The caller
must supply observed facts and mark unsupported/unknown fields unknown. Do not put
credentials, log bodies or private note contents into the evidence document.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return t if t.tzinfo is not None else None
    except ValueError:
        return None


def assess(evidence, now=None):
    reasons = []
    instruction_state = 'blocked'
    vault_state = 'blocked'
    result = {'instruction_state': instruction_state, 'vault_state': vault_state,
              'read_allowed': False, 'write_allowed': False, 'reasons': reasons}
    if not isinstance(evidence, dict) or evidence.get('schema') != 1:
        reasons.append('Missing or unsupported evidence schema.')
        return result
    ins = evidence.get('instructions')
    vault = evidence.get('vault')
    if not isinstance(ins, dict) or not isinstance(vault, dict):
        reasons.append('Both instruction and vault evidence are required.')
        return result
    if ins.get('snapshot_verified') is True and ins.get('approved') is True:
        if ins.get('remote_verified') is True:
            instruction_state = 'approved-ref-verified'
        elif ins.get('cache_allowed') is True and ins.get('cache_within_policy') is True:
            instruction_state = 'verified-cache-remote-unknown'
    result['instruction_state'] = instruction_state
    if instruction_state == 'blocked':
        reasons.append('Instruction approval, snapshot integrity or eligible cache evidence is missing.')
    elif instruction_state != 'approved-ref-verified':
        reasons.append('Instruction remote freshness is unknown; qualified local reading only.')

    expected = vault.get('expected_id')
    identity = (isinstance(expected, str) and re.fullmatch('[0-9a-f]{32}', expected)
                and vault.get('bound_id') == expected
                and isinstance(vault.get('expected_path'), str)
                and vault['expected_path'].startswith('/')
                and vault.get('bound_path') == vault['expected_path'])
    if not identity:
        reasons.append('Vault binding identity/path is missing or wrong; no task context may be selected.')
        return result
    # Exact booleans deliberately reject strings such as "false" or unchecked nulls.
    checks = {
        'remote_visible': 'Remote vault access is not verified.',
        'owner_running': 'The identified Sync owner is not verified running.',
        'initial_sync_complete': 'Initial synchronization completion is not established.',
        'required_files_present': 'Required context files are unavailable.',
        'selective_sync_covers_required': 'Selective sync coverage is not established.',
        'conflicts_checked': 'Conflict evidence is incomplete.',
        'pending_changes_checked': 'Pending-change evidence is incomplete.',
    }
    issues = [message for key, message in checks.items() if vault.get(key) is not True]
    if type(vault.get('owner_count')) is not int or vault['owner_count'] != 1:
        issues.append('Exactly one responsible Sync writer must be established.')
    if vault.get('conflicts') is not False:
        issues.append('Unresolved conflicts are present or unknown.')
    if vault.get('pending_changes') is not False:
        issues.append('Pending transfers/changes are present or unknown.')
    clock = timestamp(now) if now is not None else datetime.now(timezone.utc)
    complete = timestamp(vault.get('last_complete_at'))
    health = timestamp(vault.get('health_checked_at'))
    age = vault.get('max_evidence_age_seconds')
    if clock is None or type(age) is not int or not 0 < age <= 86400:
        issues.append('An explicit evidence-age policy and valid observation time are required.')
    else:
        if complete is None or not 0 <= (clock - complete).total_seconds() <= age:
            issues.append('A recent engine completion observation is missing or expired.')
        if health is None or not 0 <= (clock - health).total_seconds() <= age:
            issues.append('A recent health observation is missing or expired.')
    for key in ['last_change_at', 'last_failure_at']:
        value = vault.get(key)
        parsed = timestamp(value)
        if key not in vault or (value is not None and parsed is None):
            issues.append('Change/failure ordering evidence is incomplete.')
        elif parsed is not None and (complete is None or parsed > complete):
            issues.append('A change or failure followed the last completion observation.')
    reasons.extend(issues)
    vault_state = 'uncertain-local-only' if issues else 'ready-at-observation'
    result['vault_state'] = vault_state
    # Partial initial downloads or excluded required files cannot supply task context.
    result['read_allowed'] = (instruction_state != 'blocked'
                              and vault.get('required_files_present') is True
                              and vault.get('initial_sync_complete') is True
                              and vault.get('selective_sync_covers_required') is True)
    result['write_allowed'] = (instruction_state == 'approved-ref-verified' and not issues)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = assess(json.loads(args.evidence.read_text()))
    except (OSError, ValueError):
        print('Cannot read readiness evidence; no readiness established.', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result['write_allowed'] else 2


if __name__ == '__main__':
    sys.exit(main())
