# Incremental migration and rollback

## Present authority map

| Source | Preserve / proposed disposition |
| --- | --- |
| ~/.codex/AGENTS.md | Preserve current instructions; later add short stage 0 entry. Never mask it with an override. |
| ~/.local/bin/codex-ready and ~/.codex/preflight | Preserve file gate. Plan a supported provisioning/recovery distribution outside the vault before removing vault-dependent directions. |
| ai-lab/AGENTS.md | Preserve project Mutagen scope; correct host metadata only in an independently reviewed change. |
| Wreckless Abandon AGENTS/Sessions/Wiki | Preserve content and existing links. Deduplicate only after the new vault routing is approved and native pilot passes. |
| Local headless skill | Retain version-specific CLI checks/privacy rules. OBV portable contract owns bootstrap requirements; adapter owns host binding. Audit before consolidating. |
| CIK START.md | Owns orientation and receipt-pinned handoff, not duplicated Sync recipes. |
| OBV START.md | Owns portable procedures, prerequisite ownership and evidence requirements. |
| OBV adapters/dex-box.md | Owns this host's selected existing replica; observations require revalidation. |
| OBV docs/legacy-cloud.md | Preserved prior cloud contract; legacy scripts keep their existing behavior and compatibility paths. |
| Other nearby repositories | Infrastructure/template/maintenance sources; do not substitute them as bootstrap authority. |

## Publish and promotion order

1. Review the local CIK and OBV diffs, fixture tests, proposed stage 0 block and scope. No existing instructions are retired.
2. With explicit authorization, rename the existing `globo-gobo-99/dotbox-sync` GitHub repository to `Obsidian-Boot-Vault`. Verify canonical identity/default branch and preserve redirect/old consumers; do not create a replacement repository. The human approved this operation after local review; the canonical name is now Obsidian-Boot-Vault. The repository ID remains 1445100564, and the old URL redirects to that same repository.
3. Commit the reviewed OBV candidate and record its exact SHA. Commit the CIK candidate. Push reviewed branches only with authorization; merge/publish after review. No uncommitted bytes qualify as a release snapshot.
4. Copy `examples/source.example.json` outside Git into the approved local private config location, replace both SHA placeholders with reviewed committed revisions, and confirm actual source URLs/ref policy. The example deliberately fails validation until promotion. Baseline observations were CIK 90325941ea9d735198de5e919b0d738fc59a5222 and OBV 31c111b402ebebd52e3476f2919843307422b99e; they do not include this candidate and must not be labeled its release.
5. With installation approval, distribute the reviewed local helper and retrieval recovery document outside the vault, back up existing native entry/launcher/config with hashes, and add the minimal native block. Preserve all current hooks and permissions.
6. Run the fresh-session native pilot from ai-lab and another project, through both plain Codex and its launcher. Verify exact source SHAs/entry reads, governing/project precedence and no truncation. A printout from the helper alone does not pass this test.
7. Perform read-only live identity/owner/required-file/evidence checks for the selected existing replica. Do not run the legacy cloud scripts on dex-box. Propose narrowly scoped recovery only if needed; seek separate approval for state changes.
8. Only after successful replacement tests, propose each duplicate instruction removal as a reviewable diff. Obtain explicit removal approval, preserve originals and human edits, then retire one source at a time.

## Ref and offline policy

Default proposal: fully qualified main refs with **explicit SHA promotion**, no automatic adoption; a moved ref fails closed. The human may instead pin immutable full SHAs. Approving a ref selector is not approving its future contents. Never advance active sessions: their receipt remains binding. All source/dependency pins are selected together in human-owned configuration; CIK may not introduce an unpinned third source via a link.

The example policy allows an explicitly requested cached start for seven days since the most recent successful online verification. Each source must match its configured identity/pin, pass exact Git/files verification and have a matching local verification attestation. Cache reads do not renew the attestation. No eligible cache means stop. Unapproved ref movement is not a transport error; it never silently falls back. A deliberate offline invocation may use the still-approved old snapshot within policy, with remote freshness unknown and qualified local reads only.

## Rollback

Before installing anything, record exact existing files and hashes; keep backups outside synced vaults. Disable/remove only the newly installed native block/helper invocation and restore the previously approved source config. Select the previous verified committed snapshots for new sessions; preserve active receipts. Do not reset maintained checkouts, delete snapshots used by sessions, rewind the vault, change account state, replace encryption keys or resolve conflicts during rollback.

The first delivery was local uncommitted review material. The human then approved the existing-repository rename, commits and review-branch publication. Before installation, rollback means leaving the published bootstrap unused. The human subsequently approved default-branch promotion and dex-box installation; the machine's private installation receipt records source pins, backups, hashes and verification evidence. Restore those backed-up native instructions/configuration to roll back a machine; never reset a vault. Reverting the remote name requires a separate decision because other consumers may already use the new URL. Preserve the candidate checkouts and receipts as review material.
