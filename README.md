# Obsidian-Boot-Vault (OBV)

Versioned agent bootstrap procedures and tools for accessing an **existing** Obsidian Sync vault. Vault contents and credentials never belong in this repository.

- [Start](START.md) — Portable stage 1 operational contract.
- [Adapters](adapters/README.md) — Native entry and host mappings.
- [Design and migration](docs/README.md) — Decisions, acceptance and rollback.
- [Examples](examples/README.md) — Human-owned configuration templates.
- [Snapshot helper](agent-bootstrap.py) — Approved committed instruction snapshots.
- [Readiness evaluator](vault-readiness.py) — Conservative evidence-based task gate.

[Context Is Key](https://github.com/globo-gobo-99/context-is-key) (CIK) owns the stage 1 entrypoint and handoff. OBV owns operational requirements, recovery and tools. Runtime handoffs use the **session receipt's pinned OBV snapshot**, never a moving web link or a dirty maintained checkout.

## Delivery status

The existing GitHub repository has been renamed from `dotbox-sync` to `Obsidian-Boot-Vault`. These changes are published on a review branch, not installed or merged into the default branch. Legacy `dot-box` filesystem/state names remain compatibility paths. No service, startup hook or credentials are installed by this repository.

## Verification

Python 3.11+, Git, and Node for the existing bootstrap bridge test:

```bash
python3 -m unittest discover -s tests -v
```

Tests use temporary repositories, synthetic evidence and fake clients; they do not sync a live vault. Native agent instruction loading and live provider delivery are separate, approval-gated acceptance tests.

## Existing cloud tools

`bootstrap-vault.py`, `single-sync.py`, `continuous-sync.py`, and `sync-vault.sh` remain available for previously commissioned cloud deployments. They can install tools, enroll, change settings or transfer files. They are **not** stage 0 and are **not the dex-box adapter**. Their legacy paths, environment contract and behavior are preserved in [the cloud guide](docs/legacy-cloud.md); reading that guide does not authorize execution.

`boop.py` remains an optional explicitly paired notifier, unrelated to bootstrap readiness. No notifications are part of startup.
