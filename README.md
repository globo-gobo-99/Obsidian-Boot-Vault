# dotbox-sync
// Small explicit tools for one Obsidian replica per cloud workspace.

- [Bootstrap and environment contract](START.md).
- `single-sync.py`: a one-pass fallback; defers to an existing healthy writer.
- `continuous-sync.py`: a foreground reconnecting supervisor with status/stop commands.
- `boop.py`: optional manual Rootshell notification adapter, requiring vendor installation and pairing.

Deploy these files together at `/workspace/dot-box`, or run the Python entrypoints from another checkout. The shell helper targets the established `/workspace/dot-box` path. Keep auth state and private inputs outside the repository. No boot hook or notification pairing is installed automatically.

```bash
python3 -m unittest discover -s tests -v
```
