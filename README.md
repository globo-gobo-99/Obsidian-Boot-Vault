# dotbox-sync

Small explicit tools for one Obsidian replica per cloud workspace.

## Relationship to CIK

[Context Is Key (CIK)](https://github.com/globo-gobo-99/context-is-key/blob/main/START.md)
is the official **stage 1 bootloader** and starting point for a fresh task.
It provides orientation and hands off to this repository. dotbox-sync owns the
implementation and the authoritative [bootstrap and environment contract](START.md).
Keep setup, configuration, sync, recovery, and verification instructions here
rather than duplicating them in CIK.

## Tools and deployment

- [Bootstrap and environment contract](START.md): setup, inputs, safety, sync commands, and verification.
- `bootstrap-vault.py`: tooling preparation and replica bootstrap.
- `single-sync.py`: a one-pass fallback; defers to an existing healthy writer.
- `continuous-sync.py`: a foreground reconnecting supervisor with status/stop commands.
- `boop.py`: optional manual Rootshell notification adapter, requiring vendor installation and pairing.

Deploy these files together at `/workspace/dot-box`, or run the Python entrypoints from another checkout. The shell helper targets the established `/workspace/dot-box` path. Keep auth state and private inputs outside the repository. No boot hook or notification pairing is installed automatically.

For the test command, see [Verification](START.md#verification).
