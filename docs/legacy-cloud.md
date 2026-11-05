# Legacy cloud deployment compatibility

This is the preserved prior cloud contract, with the project name updated. It is not the dex-box adapter. Commands below mutate tooling/Sync state and require explicit task authorization. Existing account/environment provisioning is an advanced deployment contract; fresh humans should use the supported interactive prompts in the portable guide. Do not acquire secrets from vault notes or chat. No secret copying is a bootstrap step.

The hardcoded vault/path defaults and `.gobsidian` lock assumptions below belong to those legacy deployments. Do not infer that an arbitrary existing replica uses them. File-type flags can replace lists; preserve configured selections instead of using these commands as general repair. No legacy script is invoked by the new snapshot helper or readiness evaluator.

---

# Restore an Obsidian replica

This is the authoritative operational guide for **Obsidian-Boot-Vault**. Start with
[Context Is Key (CIK), the official stage 1 bootloader](https://github.com/globo-gobo-99/context-is-key/blob/main/START.md)
for orientation; CIK hands off here for setup, sync, and recovery.

The commands and tests below belong to a Obsidian-Boot-Vault checkout, not CIK.
The established deployment path is `/workspace/dot-box`; relative commands run
from the Obsidian-Boot-Vault repository root. See the [tooling overview](../README.md) for
deployment guidance.

Prepare tooling once; enroll and validate each independent task replica.

```bash
python3 /workspace/dot-box/bootstrap-vault.py --install-only
python3 /workspace/dot-box/bootstrap-vault.py --check
python3 /workspace/dot-box/bootstrap-vault.py --continuous
```

`--install-only` prepares pinned obsidian-headless 0.0.14 without account login or
replica enrollment. `--check` resolves non-secret settings without connecting or
writing. Omit `--continuous` for a single sync pass.

## Environment inputs
// Supply these through the task's selected personal configuration.

| Variable | Meaning | Default |
| --- | --- | --- |
| `OB_SK_WORKSPACE_ROOT` | Tool and default state/path base | `/workspace` |
| `OB_SK_OWNER_EMAIL` | Dedicated bot-domain owner email; login fallback | None |
| `OBSIDIAN_SYNC_EMAIL` | Obsidian account login email | Owner email |
| `OBSIDIAN_VAULT_ID` | Existing remote vault's 32-hex ID | Existing DevPod-Vault ID for backward compatibility |
| `OBSIDIAN_VAULT_PATH` | Independent local replica | `/workspace/vaults/DevPod-Vault` |
| `OBSIDIAN_STATE_HOME` | Private CLI auth/config state; outside the vault | `/workspace/.dot-box-config` |
| `OBSIDIAN_DEVICE_NAME` | Explicit Sync device identity | Reuse existing binding, otherwise generate and save a unique name |
| `OBSIDIAN_DEVICE_PREFIX` | Prefix for newly generated names | `codex-cloud-box` |
| `OBSIDIAN_AUTH_TOKEN` | Raw Obsidian account session token | Saved local authentication |
| `OBSIDIAN_SYNC_PASSWORD` | Optional account-login fallback | Interactive prompt, otherwise setup-needed error |
| `OBSIDIAN_E2EE_PASSWORD` | Separate vault encryption password on fresh E2EE enrollment | Interactive prompt, otherwise noninteractive enrollment fails clearly |

Secret values needed locally must be direct variables, not network-secret
placeholders. The script does not load `.env` files automatically. `.env.example`
is a placeholder-only inventory; never check in real values. Account MFA may
require interactive login outside the unattended bootstrap.

Node.js 24 and npm must be available. The inherited proxy and CA trust are
preserved; Node's environment proxy support is enabled. Allow the selected npm
and Obsidian HTTPS/WebSocket destinations.

## Replica and recovery rules
// Preserve working bindings and keep new task identities independent.

Existing dot-box keeps its current device name. Separate fresh workspaces get
separate generated names, saved within their local state for resumes. Do not
bake the generated state or authenticated vault into a published environment.
Each local state directory can bind a remote vault ID to one local path; use a
separate `OBSIDIAN_STATE_HOME` for a second local replica of the same remote vault.

The script refuses another vault's binding, does not create remote vaults, and
leaves a replica with a fresh native Sync lock alone. Stop an existing writer
before explicitly renaming it. The pinned CLI owns the final writer lock.
One writer per replica; no configuration or key migration is attempted on an
already-running writer. The encryption password is never reused as the account
password. Password-bearing CLI calls capture their output and pass the password
through the child environment into JS argv, rather than the OS command line.

## Codex Cloud setup
// Published tooling and task-specific enrollment have different lifetimes.

Prepare Node, this Obsidian-Boot-Vault repository and `--install-only` in the reusable setup.
Use CIK's stage 1 entrypoint to find this guide, then use the tested bootstrap
in the Start skill with selected personal inputs.
Publish/republish in the environment UI, then validate a fresh task. Do not
publish a live personal replica, credentials, Sync database or derived keys.
The script does not register an OS boot hook. Repository refresh does not rerun
installation/startup commands. A dot's default computer remains distinct from
a reusable Codex Cloud environment.

## Verification
// Test isolation, failures and secret handling without touching a live vault.

```bash
python3 -m unittest discover -s tests -v
```

[Codex Cloud documentation](https://learn.chatgpt.com/docs/environments/cloud-environments)


## Explicit sync commands
// Choose a one-shot fallback or the live supervisor, keeping one native writer.

- `python3 single-sync.py`: one bootstrap-and-sync pass. If a healthy native writer already owns the replica, it defers; it is not a remote-delivery barrier in that case.
- `python3 continuous-sync.py`: foreground supervisor. It reconnects after recognized transport failures, uses a per-replica supervisor lock, and stops on setup/authentication errors.
- `python3 continuous-sync.py --status`: sanitized state, last observed Fully synced timestamp, process identity, and native writer lease freshness.
- `python3 continuous-sync.py --stop`: stop this matching supervisor and its child group; leave unrelated external writers alone.

The controller writes only sanitized status outside the vault. It runs while the execution session and dot-box stay alive. It is not an OS boot hook. After a resume, inspect status, then restart it or use single-sync. A Fully synced timestamp is an observation, not a guarantee about future edits.

## Optional completion push
// Rootshell must provide a human-created destination pairing before a real push can be sent.

`python3 boop.py --check` reports readiness without sending. After installing and pairing the vendor notifier, `python3 boop.py --device "My iPad"` requests a short generic completion notification. No automatic hook installation or pairing occurs. CLI acceptance is not proof of device delivery; chat is the fallback. Keep notification bodies free of credentials and private content.
