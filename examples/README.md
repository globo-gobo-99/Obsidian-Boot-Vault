# Configuration examples

Templates and synthetic evidence; neither is an installed or verified live configuration.

- [Source selection](source.example.json) — Explicit approved revision selection.
- [Readiness evidence](readiness.example.json) — Synthetic gate input for reference.

The source example intentionally contains invalid SHA placeholders: commit/review/publish candidates first, then supply their exact approved revisions outside the repo. The existing GitHub repository is now named Obsidian-Boot-Vault. Review branches remain distinct from an installed/default-branch release. No passwords, tokens or encryption keys belong in either document.

The seven-day cache age is a proposed explicit policy. `--allow-cached` permits eligible fallback; `--offline --allow-cached` deliberately avoids retrieval. Neither permits unapproved revisions or proves vault freshness. A local absolute mirror path is supported when deliberately selected by the human; it does not prove GitHub currency.

The readiness example uses fake IDs/paths and fixed historical times. Replace fields only with actual observed non-secret evidence; missing/unknown checks must block edits. Do not copy true values as claims. Run `python3 vault-readiness.py --evidence /path/to/nonsecret-evidence.json`; exit 2 means edit readiness is not established.
