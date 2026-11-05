# Agent bootstrap implementation plan

> **For agentic workers:** Use executing-plans inline. User approved implementation of the reviewed direction; no additional plan approval loop. A fresh final reviewer checks the complete local change.

**Goal:** Prepare portable CIK/OBV repository changes with deterministic acquisition and honest vault readiness, proven by isolated tests.

**Architecture:** Stage 0 calls a locally installed helper with human-owned source pins; it prepares committed snapshots and a per-session receipt. Stage 1 routes to OBV procedures and a machine adapter. A pure readiness evaluator checks explicit evidence without running Sync.

**Tech Stack:** Python standard library, Git, existing unittest workflow. No installations or toolchain migration.

**Spec:** [bootstrap-design.md](bootstrap-design.md)

## Global constraints

- No changes outside isolated checkouts except their scratch artifacts.
- No live Sync, credentials, enrollment or installed startup configuration changes. The initial local phase deferred publication; the human subsequently approved the repository rename, candidate commits and review-branch pushes.
- Preserve maintained-checkout changes and legacy runtime/state paths.
- Read instructions from one verified revision per source; pin all dependencies.
- Never interpret a timestamp/config read as proof of remote freshness.

## Review focus

- Cache corruption, stale cache and changed approval settings must fail closed.
- Git errors must not echo secret-bearing transport output.
- Unexpected symlinks/submodules and export attributes must not alter snapshot content.
- Evidence missing fields or stale completion after newer changes must not enable edits.
- Naming changes must preserve existing deployments and clearly mark unpublished links.

## Task 1: deterministic acquisition

**Files:** agent-bootstrap.py, tests/test_agent_bootstrap.py, examples/source.example.json, adapters/codex-stage0.md.
**Interface:** prepare(config, state, offline=False, allow_cached=False) -> receipt dict; CLI writes receipt and prints JSON. Config sources specify name/repository/ref/approved_sha/entry; offline_max_age_seconds bounds prior online verification.

- [x] Write failing integration tests with temporary Git repositories for committed content vs dirty checkout, pinned revision updates, clean exports, offline/cache/auth failure, corruption, missing prerequisites and atomic multi-source preparation.
- [x] Run unittest and observe intended failures.
- [x] Implement Git-object snapshots, complete validation, bounded cache reuse, sanitized errors, and immutable per-session receipts.
- [x] Run the acquisition suite and complete OBV suite.

## Task 2: readiness contract and evidence gate

**Files:** vault-readiness.py, tests/test_vault_readiness.py, START.md, adapters/dex-box.md, docs/acceptance.md.
**Interface:** assess(evidence, now=None) -> dict with instruction and vault states, read_allowed, write_allowed, reasons. No subprocess/filesystem/network operations in assess.

- [x] Write failing tests for healthy, wrong/missing identity, incomplete/stale sync, required-file/selective exclusion, conflicts, pending edits and independent instruction/vault freshness.
- [x] Observe failures, implement conservative evaluation, run the whole suite.
- [x] Document evidence collection/limits, prerequisite ownership and supported human enrollment/recovery.

## Task 3: CIK/OBV migration package

**Files:** CIK START.md and README.md; OBV README.md, adapters/README.md, docs/README.md, examples/README.md, docs/migration.md.
**Interface:** CIK consumes the same receipt as Task 1; OBV owns operational contract from Task 2.

- [x] Replace mutable runtime handoff with receipt-pinned OBV navigation.
- [x] Prepare OBV branding while preserving legacy runtime paths/variables.
- [x] Document promotion order, remote rename, native pilot and rollback approvals.
- [x] Run full tests, diff checks and fresh-context final review; fix substantive findings with regression tests.

The local-review phase is complete. The human subsequently approved the existing-repository rename, candidate commits and review-branch pushes. The human subsequently approved default-branch promotion, dex-box startup installation and fresh-session verification; live vault bindings/credentials remain unchanged. Fixture commits are temporary isolated test data only.
