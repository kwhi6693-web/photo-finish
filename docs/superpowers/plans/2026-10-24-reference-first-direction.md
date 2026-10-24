# Reference-first photographic direction implementation plan

> Execute inline with test-driven-development and executing-plans. The user approved the consolidated requirements and requested implementation.

**Goal:** Retrieve and visually select personal references before locking final photographic direction, with optional global guidance and professional judgment for unspecified choices.

**Architecture:** Keep prepare/submit/returned/review. Prepare binds the source, observed profile and candidate shortlist; an old prepare.direction is a provisional compatibility draft. Submit atomically records protection/selection, locks the final direction, and reserves the actual tool request. Existing photography, fidelity, review and saving contracts remain.

**Tech stack:** Existing Python 3.10+, Pillow and SQLite; no new service/dependency.

**Spec:** The approved conversation: explicit private collection; observed scene and actual visual suitability; partial use; current instructions first; professional fallback for automatic empty/unsuitable retrieval; explicit unavailable selections reported; management only on demand. Global instructions are optional and persist only on explicit intent; professional choices fill unspecified requirements without resetting saved settings.

## Constraints and review focus

- No private photographs, preferences, task files or paths in the public package.
- Do not bypass profile acknowledgment, protected-content gates, actual tool execution/review or confirmed saving.
- Invalid selection/direction must leave the job unchanged and must not reserve a render.
- Legacy prepare(direction=...) fallback callers remain usable; their direction becomes a draft until submit. Adopted/partial references require explicit final submit.direction to avoid silently reusing a pre-reference draft.
- Explicit missing keyword/group references must not silently switch to another style or fallback; automatic empty lookup remains read-only.
- No claim that metadata scores or protocol tests certify aesthetics.

## Task 1: Runtime order and optional guidance

- [x] Write and run failing real CLI/transaction tests for deferred direction, actual viewed selection, missing/invalid direction rollback, legacy drafts, reference-first low-level gate, explicit selector misses, and professional guidance without unwanted persistence.
- [x] Make prepare.direction optional and provisional; add final submit.direction, selected-reference binding and status hint; enforce order for these new tasks.
- [x] Explain professional judgment in private task context; keep existing global/scoped settings and task priority.
- [x] Run targeted tests and the complete synthetic suite.

## Task 2: Skill contract and distribution

- [x] Update SKILL/UI, canonical runtime guide, style/customization guides and three READMEs for the approved workflow; retain the first release's creative/protection/review/delivery behavior.
- [x] Update release version to 1.4.0, changelog/validation and generated mirrors; build the deterministic installation archive.
- [x] Run doctor, full tests, metadata validation, publication/history scan and clean packaging checks; conduct an independent whole-branch review and address verified issues.

## Task 3: Publish verified source and release

- [x] Commit and publish a review branch/PR, verify remote tree identity and current-head platform CI, then merge.
- [x] Publish v1.4.0 from the exact verified main commit with ZIP/checksum attachments, mark Latest, and verify the latest download bytes/manifest.

Review: independent synthetic CLI/code review completed; explicit group cross-scene behavior and guide ordering corrected. The added group regression failed before the fix and passed afterward. Final local suite: 209/209 passed. Metadata, doctor, publication/history scan and deterministic/relocated package checks passed. Published in [PR #11](https://github.com/kwhi6693-web/photo-finish/pull/11) and [v1.4.0](https://github.com/kwhi6693-web/photo-finish/releases/tag/v1.4.0), targeting commit `9b0402b6951eaa2616cf2c140452fa6bae3de328`. The remote tree matched verified local source, all PR/branch and main/tag checks passed, and latest-download bytes/manifest plus relocated prepare/submit were verified. This completed plan is a historical implementation record; current usage is documented in [runtime.md](../../runtime.md).
