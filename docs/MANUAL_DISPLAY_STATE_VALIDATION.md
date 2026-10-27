# Manual display confirmation: implementation validation

This is a correctness fix in Draft #17, independent of performance PR #16. No speed claim, new photo editing, upload, display, save, version registration or historical task repair was performed for validation.

## Implementation

Only two production modules change:

- `experience.describe` accepts a keyword-only `manual_presented` boolean, default false, and rejects non-booleans. A true current confirmation can report `display_observed=true` without manufacturing platform state. It exposes `display_observation_source=current_manual_confirmation` and `display_observation_scope=current_delivery_response`. Without current confirmation, the scope is `platform_ledger`; the source is `platform_delivery` when observed, otherwise `unobserved`.
- `task_history.delivered` passes its already-required explicit `presented=True` only when building the response after accepted-version verification and normal SQLite bookkeeping. It does not derive confirmation from `changed`, version markers, saving, URLs or hint consumption.

The caller still bears responsibility for supplying true only after actually observing that result. The source field identifies a caller confirmation, not a provider-signed receipt or user-device rendering certification. Existing automatic-platform facts remain in their original ledger; quality and persistence checks do not change. No SQLite migration, historical ledger mutation, callback or extra external call is introduced.

## Actual local checks

- Clean baseline: 263 protocol/security tests passed on Python 3.12.
- Red: the new current-manual-confirmation regression failed on the old code with `False is not true`.
- Green: 8 new tests, 30 targeted tests including experience and versions, and 271 full protocol/security tests passed.
- Tests use generated anonymous fixtures, real local controllers/SQLite and no external service. Coverage includes repeated confirmation and one-time hints, strict erroneous-input rejection before mutation, unchanged job/output bytes and version count, independent persistence, platform compatibility, session-free scope, and rejection of changed output/contract before index change.
- Doctor, public-tree scan and whitespace/diff checks passed. No private photo, task identity, local machine path, raw ledger or provider URL is included here.

## Safe actual-host scope

The candidate module was loaded locally without installing it. Two existing authorized records were read only. Their existing successful display results matched each recorded output URL; current version/output bindings were verified. Passing those existing confirmations into the candidate pure experience view returned true with current-manual source and current-response scope. Job, SQLite index and timing-file hashes remained unchanged.

This is read-only replay of existing evidence in the current host, not a new display event or a full new `delivered` invocation. The mutating delivered path is covered by anonymous synthetic regressions. Without explicit confirmation the ordinary status still returns only platform-ledger observations; no durable manual-observation history is promised.

## CI and packaging constraint

The existing workflow runs six Linux/Windows/macOS matrices and then rebuilds `dist/photo-finish.zip` from current sources, requiring no diff. This candidate changes two packaged runtime modules while the tracked v1.5.0 archive is deliberately untouched. A scratch-only candidate build passed, but its bytes differ from the tracked stable archive as expected. This is not a new released package.

Therefore unit/protocol validation can pass while the final archive-equality gate fails. Do not bypass the gate or silently replace/relabel the stable 1.5.0 artifact. Cross-platform outcomes are reported from actual GitHub CI, separately from local Linux verification. The Draft is not merge-ready until this packaging policy conflict is resolved through an approved release/candidate workflow. No workflow, tag, release asset or installed stable file was changed in this patch.
