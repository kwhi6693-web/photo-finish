# Photo Finish quality engineering implementation plan

Goal: improve non-portrait editing safety at the actual submission boundary, without changing the released v1.5.1 or the installed Skill.

Authority: the user's seven-stage engineering brief authorizes continuous implementation on an independent branch, tests and cross-platform CI; no merge, tag or release. Private-history recovery has stopped. PR #16 remains independent.

Architecture: retain the existing prepare/submit/returned/review pipeline. Centralize local-revision route validation at the shared tool adapter, before reservation, for both first submission and subsequent steps. This is a missing-argument/route guard, not a mask-quality detector or a new image editor.

Approaches: prompt-only guidance already exists and did not close low-level bypasses. A new renderer or generic capability registry would expand scope without photographic evidence. Chosen engineering approach: one adapter guard for the currently documented masked native adjustment route; unsupported local routes fail safely. Native full-frame edits remain available for non-local jobs.

Global constraints: no new dependencies, services, paid calls, private data, fixed look, version bump, historical mutations, cache or timing framework. Preserve source/reference/output hashes, STOP/authorization, review, save receipts, unknown-state investigation, independent versions and zero-render rollback. Tests are synthetic protocol evidence, never photographic quality evidence.

## Task 1 — development validation without changing released artifacts

- [x] Add adversarial tests: development-source changes may pass candidate checks but cannot replace the pinned v1.5.1; tag moves, canonical/staged mismatch and payload corruption still fail.
- [x] Observe the missing development gate fail, then add a released-source gate and isolated candidate-install verification using existing builders/checkers.
- [x] Keep the existing formal canonical/release checks unchanged for final release preparation. Run CI against current-source candidates and immutable tagged v1.5.1 separately.
- [x] Commit tooling/tests/CI as one reviewable change.

## Task 2 — local revision boundary

- [x] Reproduce missing-mask native local submission, unknown route and low-level/full-frame bypasses in anonymous fixtures. Assert unchanged job/parent/output bytes on rejection.
- [x] Validate local routes in delivery_adapter.begin and next_step before reservation. Recognize documented namespaced Adobe adjustment names; require a nonempty maskURI. Reject unknown local editors and full-frame generators. Preserve every other authorization/quality gate.
- [x] Cover successful masked parameter binding and unchanged non-local behavior; run all tests.
- [x] Commit the guard/tests and mirrored interface guidance.

## Task 3 — evidence and quality acceptance

- [x] Audit nine existing functional concerns without adding layers; distinguish stable protocol implementation, real host evidence, limitations and absent evidence.
- [x] Record five scene classes with naturalness/detail/structure/light-color/user-intent/delivery criteria and exact evidence scope. No new photo is rendered without an authorized new task.
- [x] Reuse PR #16 findings; no performance change without repeatable comparative evidence.
- [x] Run doctor, publication/history scans, deterministic candidate builds/install checks and the existing six-job CI. Review the entire diff; leave a Draft PR.

Review focus: tool-name namespace aliases; top-level versus nested/blank maskURI; next-step bypasses; loss of parent/selected-version identity; developer CI accidentally treating changed runtime as released v1.5.1. A mask URL establishes only a submitted parameter: actual mask/source association, coverage, feathering, edge review and final visual improvement remain caller obligations and unverified here.

Cross-platform exact-head results and final disposition are recorded in Draft PR #21; this document tracks completed implementation and local checks.

Progress and actual failures/results are recorded in QUALITY_ENGINEERING_EVIDENCE_20261027.md. This plan is implementation bookkeeping, not a new product layer.
