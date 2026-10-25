# Photo Finish UX Engineering Implementation Plan

> Execute inline under the supplied handoff and explicit authorization to implement, test and open a PR. Merge, tags and release publication require user approval.

**Goal:** Preserve the mature editing controller while making delivery, revisions, recovery and style management understandable and durable.
**Architecture:** Add a presentation protocol first, then a private SQLite conversation/task index. The index locates records; accepted ledgers and exact image hashes remain authoritative. New revisions are separate contract-3 tasks; rollback only reads files. Extend the existing style catalog and metrics without a service or vector dependency.
**Tech Stack:** Python 3.10+, standard library, existing Pillow, existing optional analysis profile.
**Spec:** User-supplied Photo Finish UX handoff (2026-10-25) and current repository contracts.

## Constraints and review focus

- Never fabricate tool calls, visual reviews, progress, persistence or host acceptance.
- Never mutate accepted photographic history to implement rollback; verify every historical output on use.
- Unknown/working calls and failed saves must never become render retries.
- Conversation hint settings are private session state, not inferred long-term preferences.
- No private photos, jobs, catalogs, credentials or machine paths in the repository/package.
- Missing/modified files, branching from an old version, repeated delivery, partial batches and stale indexes must fail safely.

## Tasks

- [ ] 0. Baseline: doctor, 209 regressions, publication scan; investigate four Windows cases and collect existing CI evidence. Commit the plan and baseline report.
- [ ] 1a. Presentation: add truthful Chinese phase/save/recovery mapping and one-time delivery hints, short local-edit clarification and comparison routing. Add failing behavior tests, implement, run full suite, commit.
- [ ] 1b. Versions: private indexed V1/V2 history, source-bound revision preparation, locked inherited protections/direction and read-only rollback/comparison. Test hash changes, cross-turn reload, duplicate registration and zero render calls; run suite, commit.
- [ ] 2. Professional layers: document conflict precedence and authorized collection; enforce inherited protection contracts across low-level entry points. Test user/profile/reference separation, run suite, commit.
- [ ] 3. Performance: indexed task lookup, incremental metadata/style cache with content invalidation; retain full hashing at trust boundaries. Benchmark actual local metadata operations, explicitly exclude cloud/host latency. Test add/update/delete invalidation; run suite, commit.
- [ ] 4. P1/P2: batch summaries and safe recovery lists, synonym keyword matching, recent/frequent styles, concise onboarding/export boundaries and observational UX metrics. Test partial failures and no completed resubmission; run suite, commit.
- [ ] 5. Host/visual: inspect available host capabilities; use anonymous authorized fixtures if available. Record installation, photo-only trigger, actual editing/review/save and continuity separately; mark inaccessible capabilities unverified.
- [ ] 6. Delivery: update canonical guides/mirrors, READMEs, changelog and release candidate version; doctor, full tests, history publication scan, deterministic double build and clean extraction. Independent review, focused fixes and current-head CI. Push branch and open draft PR with exact evidence and unresolved release gates.

## Baseline

Repository: kwhi6693-web/photo-finish; main 184a62c7122bd470ae0f2d0bec4838fe3bef0a68.
Latest release: v1.4.2, same target commit; package SHA-256 23ce92b01a3d4c01fb81203f8d943fbd80a5fe912445e65041cd46b714d0139b.
Linux Python 3.12.14: doctor passed (41 runtime links, 11 policy pointers); 209 tests passed in 6.866s.
Existing same-commit CI run 40105427756: six jobs succeeded, including Windows Python 3.12 core. This is historical CI evidence, not a new native Windows run in this workspace. The handoff lacks exception traces; root cause of that specific Windows failure remains unconfirmed.
