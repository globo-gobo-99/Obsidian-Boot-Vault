# dex-box: existing DevPod-Vault adapter

Observed 2026-11-04 Boise time; revalidate narrowly, never inherit health claims.

| Setting | Approved target / observed value |
| --- | --- |
| Host/user | dex-box / johnycsh |
| Existing remote | DevPod-Vault |
| Remote ID | 6ced867ab480ebf9acbc2f5f51c74007 |
| Local replica | /workspace/DevPod-Vault |
| Sync owner | systemd user obsidian-sync-devpod-vault.service |
| Owner command | ~/.local/bin/ob sync --path /workspace/DevPod-Vault --continuous |
| CLI/runtime | ob 0.0.14; wrapper uses Node 24.22.1 |
| Shell Node | 18.19.1; do not use it as proof of the wrapper runtime |
| Selective settings | bidirectional; merge; image/audio/pdf/video/unsupported; configs []; excludedFolders [] |

The existing owner uses the local supported CLI state; retain its credential scope. The wrapper currently points into a Codex-managed runtime cache: callable today, not a portable/provisioning guarantee. If missing after a runtime update, the provisioner must repair it under authorization; stage 1 does not install or move state automatically.

Safe targeted checks (inspect help first):

```bash
ob --version
ob sync-status --help
ob sync-status --path /workspace/DevPod-Vault --json
systemctl --user show obsidian-sync-devpod-vault.service --property=ActiveState,SubState,MainPID,FragmentPath
```

Filter remote-list results to the expected ID; do not print account/vault inventories. Inspect the identified PID's executable, selected path/continuous flags and manager ownership without dumping full environments or credential-bearing arguments. Summarize relevant journal completion/transport/conflict evidence without file names or raw messages. Never run a second `ob sync`, a legacy cloud supervisor, or desktop Sync against this replica. Starting/restarting/enabling the existing service needs separate authorization.

At investigation the selected remote was visible and this service emitted repeated Fully synced events, most recently observed at 2026-11-05T03:56:24Z. That is historical evidence, not a readiness claim now. Other existing services own Wreckless Abandon and gobo-vault; they are different replicas and must not be stopped or rebound. Wreckless Abandon had reconnect events and was not listed by the current account's remote read; do not switch credentials to investigate as a bootstrap side effect.

## Narrow context routes

The root README contains credentials and is excluded from automatic loading. The observed root navigation pointed to these candidates; their existence and task relevance must be checked before reading:

- `Projects/Ob-Sk/README.md` — Shared vault system and roles.
- `Projects/Dev-Pod-Dev/README.md` — Terminal, services and recovery.
- Relevant project's nearest AGENTS.md — Project-specific working boundaries.

These are paths into the existing replica, not content to vendor into Git. No universal required-file list is asserted. Before each task, state the selected required context paths, verify availability/selection coverage and load only those. Do not scan private image-run notes, prompts or outputs without explicit authorization.

ai-lab's Mutagen instructions concern `/home/johnycsh/ai-lab`, not this replica. Preserve them until a separate approved migration. Generic old Sessions/Wiki pointers target Wreckless Abandon; do not silently reinterpret them as DevPod-Vault routes. The global skill gate and privacy boundaries remain active until approved replacement and native loading verification.
