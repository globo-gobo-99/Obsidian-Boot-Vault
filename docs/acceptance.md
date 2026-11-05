# Acceptance and evidence

Fixture tests run with `python3 -m unittest discover -s tests -v`. They use temporary Git repositories, synthetic readiness evidence and fake existing clients. They never authenticate to Obsidian or touch a live replica. A passing fixture suite does not prove native loading, live conflict absence or remote delivery.

| Case | Expected behavior | Evidence / status |
| --- | --- | --- |
| Dirty maintained checkout | Snapshot contains committed files; human edits/untracked files stay untouched. | Real Git fixture, including export-ignore. |
| Revision A then approved B | New receipt reads B; old receipt/snapshot still reads A. | Real Git fixture. |
| Ref moves before approval | Reject new SHA and publish no receipt. | Real Git fixture. |
| Offline first start | Stop; no verified snapshot exists. | CLI fixture. |
| Offline cached start | Explicit permission, unchanged pins, bounded age and complete validation required. | CLI fixture. |
| Authentication/transport failure | Sanitized error; only explicit eligible-cache fallback. | Unavailable local transport fixture; actual auth failure not induced. |
| Missing Git | Explain prerequisite; no traceback or fabricated success. | Restricted-PATH fixture. |
| Cache corruption, injected file, symlink | Reject, preserve for investigation, no working-tree substitution. | Real filesystem fixtures. |
| Inherited Git selectors | Strip repository/index/object/trace selectors; leave unrelated repositories untouched. | Real Git/environment fixture. |
| State-container symlinks | Reject linked root/snapshots/verified/receipts before redirected writes. | Real filesystem fixtures. |
| Concurrent sessions | Independent immutable receipts, shared verified snapshot, no latest-pointer race. | Concurrent CLI fixture. |
| Existing healthy replica | Allow task edits only with complete, fresh identity/owner/file/selection/conflict/pending evidence. | Pure evaluator fixture; live acceptance pending. |
| Missing/wrong vault | Block context selection and edits; do not enroll/rebind. | Evaluator + existing fake-client tests. |
| Incomplete/stale sync | Block edits; incomplete context also blocks reads. | Table-driven evaluator fixtures. |
| Later edit/failure after completion | Block edits until newer supported evidence. | Evaluator fixture. |
| Conflicts/unknown checks | Block edits; preserve both versions for authorized reconciliation. | Evaluator fixture; no live conflict created. |
| Current Git but uncertain vault | Report separate results and block edits. | Evaluator fixture. |
| Cached Git but healthy vault | Qualified local reading only under cache policy; no edits. | Evaluator fixture. |
| Native fresh Codex | Show native sources plus actual tool reads of exact CIK/OBV receipt entries, honor precedence. | PENDING installation/pilot approval. |
| Another agent/host | Its documented native loading adapter works with same portable contract. | PENDING selected agent/host. |
| Live round trip/recovery | Correct existing ID and one owner; approved harmless write visible on another device, with preserved content. | PENDING separate mutation approval. |

## Evidence limitations

The evaluator trusts the collector, so it is a decision aid rather than an independent attestation. Never create evidence by copying the example and treating its true values as observations. Logs need bounded coverage and ordering; an absent conflict line or active PID is not sufficient. Provider state, local pending edits, and semantic conflicts may lack a supported read-only oracle. Record unknown and stop dependent edits rather than inventing a stronger guarantee.

Snapshot identity includes the complete source selection/configuration; content digest covers committed file names and bytes. Git object verification anchors files to the approved commit. Read-only permissions protect against accidental changes only. The same user can change local approval/state; defending against that requires an external trust anchor and is outside this design.

The human approved the existing-repository rename, candidate commits and review-branch pushes after local review. Live mutation tests, account enrollment, service restarts, native startup configuration and merging remain separately approved checkpoints.
