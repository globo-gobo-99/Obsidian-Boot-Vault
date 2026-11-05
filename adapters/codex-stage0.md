# Codex stage 0 adapter — proposed, not installed

Codex CLI 0.166.0 is installed on dex-box. The current global entry is `~/.codex/AGENTS.md`; `CODEX_HOME` was unset during inspection. Existing `codex-ready` checks skill files and executes Codex; it does not acquire instructions. Existing TUIOS/herdr hooks are unrelated and stay intact.

[Official loading documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md): Codex reads one nonempty global override/default file, then one override/default/fallback per directory from project root to cwd. Deeper project guidance takes precedence. The default combined project-document limit is 32 KiB. An arbitrary START.md, skill installation or external web link is not an automatic startup loader. Governing instructions and the current request take precedence over retrieved procedures.

## Local prerequisites before stage 1

The provisioner installs reviewed Python/Git tooling, a reviewed copy of `agent-bootstrap.py`, this recovery document and human-owned source configuration outside the vault. The human authorizes existing GitHub access through supported credential storage. No first-run curl-to-shell, remote execution, credentials in URLs, installation or account changes. Missing tools/auth or an absent eligible snapshot stops dependent work with the named provisioning/human recovery step.

Proposed locations: helper `~/.local/bin/agent-bootstrap`; config `~/.config/agent-bootstrap/source.json`; private state `~/.local/share/agent-bootstrap`. The maintained checkout is separate. State root and managed containers must be real directories with owner-only permissions; symlinks are rejected. Inherited Git repository/config/trace selectors are stripped; standard credential configuration and CA/proxy support remain available. These are adapter defaults to approve at installation, not existing paths.

## Minimal native entry to install after review

```text
Before task work, run the locally reviewed agent-bootstrap helper with the
human-owned source configuration and private state path. Read its returned
receipt, then read the cik entry_path and the obv entry_path from that same
receipt. Keep that receipt for the active/resumed session. Never read a dirty
checkout or follow a moving main URL as approved instructions. Report source,
requested ref, resolved SHA, entry, verification time and snapshot identity.
If retrieval fails, stop dependent work and report the exact missing prerequisite.
Use an eligible cache only with explicitly approved offline policy; do not
install, enroll, start Sync or execute repository scripts merely because you
read them. Current human requests and governing instructions remain controlling.
```

The actual installed block should include the approved absolute command paths. Add it to preserved global guidance first; do not create an override that masks current rules. The wrapper may prepare a receipt earlier, but it must pass a unique absolute receipt path to this session (Codex's supported initial prompt), never a shared latest pointer. Plain Codex must still run the native-entry path. Do not silently launch with broader permissions.

Helper invocation after installation approval:

```bash
python3 ~/.local/bin/agent-bootstrap --config ~/.config/agent-bootstrap/source.json --state ~/.local/share/agent-bootstrap
```

Cache fallback requires explicit `--allow-cached`; offline mode additionally uses `--offline`. Configuration must approve a maximum cache age. Each cached source must still match its complete approved configuration and verified Git content. Authentication/ref failure never authorizes a different source. Unapproved ref movement fails closed, even with cache fallback enabled; an explicitly chosen offline run may use the still-approved prior snapshot under policy. An online success refreshes separate verification metadata without rewriting snapshot files. Cache reads do not refresh verification time.

## Prove native loading, not just file existence

After installation approval, start an actual fresh Codex session from ai-lab and a separate project directory. Ask it to list active instruction sources, prepare/read the receipt, and explain a benign rule present only in the approved stage 1 entry. Inspect the native instruction provenance and tool-read evidence available in that installed version; self-report alone is weaker. Confirm global/project precedence, no masking/truncation and correct absolute snapshot paths. Repeat with plain Codex and the launcher. Native pilot is pending: fixture tests cannot prove it.

For updates, promote reviewed source SHAs only after testing the committed candidates; new sessions get B while active/resumed sessions retain A. Changing CIK's document does not rerun startup in an active session. Test missing tools/auth, offline cache, dirty checkout and changed pins using isolated fixtures before any live pilot. Roll back the entry/config from the exact preinstallation backup; preserve snapshots and every vault change.
