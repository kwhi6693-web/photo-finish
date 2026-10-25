# Photo Finish implementation progress

Updated: 2026-10-25 (Asia/Shanghai). This file is the restart checkpoint; inspect Git and actual evidence before resuming. Do not recreate completed features or rerun the entire suite without a changed input or unresolved concern.

## Current state

- Repository: kwhi6693-web/photo-finish; default branch: main.
- Stable main and Release: v1.4.2, commit 184a62c7122bd470ae0f2d0bec4838fe3bef0a68, unchanged.
- Development branch: feat/ux-engineering-20261025.
- Candidate: 1.5.0-rc.1, workflow 2026-10-25.1.
- Latest verified local code/package commit before this progress checkpoint: 811c081. Working tree was clean at recovery.
- Eight local stage commits existed at recovery. Command-line push failed because it had no HTTPS credentials. Connector blob upload was interrupted before branch creation; remote branch and PR were actually absent on recovery.
- Resume delivery through the authorized GitHub connector. Uploaded Git object IDs can be reused; create and verify each stage tree before creating commits/branch. Do not force-push or change historical commits.
- The commit containing this document is identified by `git log -1 -- docs/IMPLEMENTATION_PROGRESS.md`; do not guess a self-referential commit hash.

## Task classification

| State | Work | Evidence / next action |
|---|---|---|
| Completed and verified | P0 Chinese truthful status/save view, one-time hints and opt-out, V1/V2 history, selected-version revisions, zero-render rollback/comparison | tests/test_experience.py, tests/test_versions.py; full 246-test log and engineering validation |
| Completed and verified | Custom instructions, authorized style collection, priority and locked protection inheritance | Existing preference/style suites plus revision/recovery regressions; no inferred long-term preferences |
| Completed and verified | Keyword synonym discovery, recent/frequent styles, exact-content row cache and indexed task lookup | tests/test_style_discovery.py; local 1000-row benchmark only, no vector/host speed claim |
| Completed and verified | Ordered batch status, never-submitted failure recovery, completed/working/unknown exclusion, observed UX metrics | tests/test_batches.py, tests/test_ux_metrics.py; four independent reviewer defects and hint issue fixed |
| Completed and verified | Source/docs/runtime/candidate package consistency, publication scan, deterministic build and clean extraction | Exact checks below and docs/ux-engineering-validation.md |
| Modified but untested | None in recovered product code | This progress document is a documentation-only addition; run doctor/link/publication checks |
| In progress | Publish development history and maintain this restart file | Verify remote Git trees against local trees, then create branch and Draft PR |
| Not yet completed | Current-head Windows/macOS/Linux CI and final remote readback | Read actual Actions results and explicit four-case Windows diagnostics; repair only actual failures |
| Environment-dependent / unverified | Candidate installation, photo-only trigger, live rule/style behavior, real editing/visual acceptance, multi-turn continuity and authoritative host save | Installed exposed skill was 2026-10-24.2; inspected signed-in Work UI did not expose a verified candidate installer. Do not call fixtures host acceptance |
| Not yet performed | Portrait, night, lettering, travel batch and special-light real-photo regression | No authorized anonymous photo set was supplied; do not access unrelated personal images |

## Verification already completed

Source/package commit: 811c081 (before progress-only updates). Linux, Python 3.12.14, Pillow 12.3.0.

- 246/246 tests passed in 8.723s; 209 original plus 37 additional tests.
- Doctor/integrity: passed; 43 runtime links, 11 policy pointers, 174 documentation links before this file.
- Publication scan including 464 reachable historical blobs: passed, no findings.
- `pip check` and optional 5184-pixel numerical-analysis fixture: passed.
- Deterministic double build: byte-identical, 484608 bytes, 113 ZIP entries including manifest.
- ZIP SHA-256: 384c44eff01e0c0d6c75eed8ad1e51076d6f6db2a812bf412484c4ec9c2202b3.
- All 112 manifest-listed files verified in a clean extraction; bundled doctor and isolated synthetic prepare/status CLI smoke passed. This did not call an editor.
- `git diff --check`: passed.
- Historical Windows same-baseline CI run 40105427756: 209/209, no skips, Python 3.12.10. This is not candidate CI. The handoff's separate four Windows errors lacked exception traces and were not reproduced locally; no test was deleted or disabled.

## Important code locations

- runtime/10_SYSTEM_CONFIG/scripts/experience.py: Chinese fact and recovery presentation.
- task_history.py: private SQLite version/cursor/hint index, immutable photographic contract, revision provenance/regions and rollback.
- batch_workflow.py: ordered summary and isolated safe failed-task recovery.
- photo_edit.py / delivery_adapter.py / delivery_automation.py / workflow_session.py: existing execution and protection integration.
- style_library.py: finite keyword expansion, exact-row cache and accepted-use records.
- delivery_metrics.py: observed first acceptance/refinement/duplicate render/save/readiness metrics.
- references/conversation-versions.md and references/batch-recovery.md: operator protocols.
- docs/ux-engineering-validation.md: detailed evidence, reviewer fixes, performance scope and open acceptance gates.
- docs/superpowers/plans/2026-10-25-ux-engineering.md: original implementation ledger.

## Known limitations and release gates

No deferred code-review defect is known. External unknown/error submissions remain needs-confirmation until actual investigation; automated replacement is limited to proven never-submitted failures. A save failure must never trigger rendering. Session roots must be private and genuinely persistent for cross-turn recovery; no cloud sync is promised. The keyword matcher is not vector semantic search. Local metadata timing is not end-to-end host latency.

Do not merge main, create a tag or publish a Release without explicit approval. Real-photo and exact-candidate host acceptance are still open. Preserve stable v1.4.2 and its assets. A future stable version bump requires rebuilding and verifying the exact approved source; do not relabel this RC archive.

## Immediate next steps

1. Complete connector-backed branch upload, preserving stage messages and verifying exact tree equality. Record remote commit mapping without rewriting existing history.
2. Open a Draft PR with the test report and unverified host/photo gates. Inspect current-head matrix, including four named Windows symlink/alias tests.
3. Update this file with remote branch/PR/CI evidence; documentation-only updates require doctor/link/publication checks, not another unchanged full local regression.
4. Inspect any newly available supported host/installer interface. If unavailable, document the exact remaining blocker and leave the PR draft; never manufacture installation, photo review or saving evidence.
