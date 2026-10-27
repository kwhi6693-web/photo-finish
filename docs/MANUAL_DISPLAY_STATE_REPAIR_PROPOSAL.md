# Manual presentation observation: confirmed expression gap and minimal repair proposal

Status: proposal only. No product code, executable regression tests, installed skill, stable archive or historical task has been changed by this document. Keep this Draft separate from performance PR #16. No merge, tag or release is authorized.

## Confirmed cause

Two naturally authorized non-portrait tasks followed the same path:

1. `photo_edit.submit(..., display_mode="manual")`.
2. Server-side adjustment returns a URL. `photo_edit.returned` / `delivery_adapter.finish` records that editing result with `presented=false`, accurately: no result display had happened at that point.
3. Formal bytes are fetched, reviewed and saved; the final record is saved and the accepted version registered.
4. A separate result-display call succeeds, referring to the same formal output URL.
5. `task_history.delivered(..., presented=True)` validates accepted version bytes, marks SQLite `versions.delivered=1`, and builds its experience response.
6. `experience.describe` reads only `platform_delivery.display.status`. Manual mode has no `platform_delivery`; it therefore returns `display_observed=false` even in the response to this just-confirmed manual presentation.

Source inspected: main 5045c9d and the installed modules used by the two tasks. The actual return path is `task_history.delivered -> experience.describe`; it does not invoke `delivery_adapter.finish` again. That is appropriate because finish describes the earlier editing call, not a later manual display.

Pure in-memory diagnostic executed, without reading private photographs into test fixtures or invoking task mutation: an accepted manual state with a save receipt returns display=false/save=true, whereas platform observed + pending save returns display=true/save=false. These are diagnosis results, not a passing repair regression suite.

## Keep four facts distinct

| Fact | Authority | Meaning / limitation |
| --- | --- | --- |
| Platform automatic presentation | `platform_delivery.display` recorded from the actual platform return | Platform result shown; not persistence |
| Current manual presentation confirmation | Explicit `presented=True` supplied after observing successful display of this exact result | Caller observation, not device-pixel certification or automatic platform presentation |
| Formal persistence | Matched real save receipt, local persistent identity and exact local output association | Independent of presentation and SQLite delivery |
| SQLite `delivered=1` | Conversation version delivery marker | Controls delivery bookkeeping / one-time hints; no raw provider display receipt, timestamp or output-linked presentation evidence is stored in that column |

Never infer presentation from accepted quality, a saved file, a ready editing result, URL existence, or SQLite delivered alone. Do not set `platform_delivery` for a manual result: doing so could route an already saved task into platform-save reconciliation and change unrelated semantics.

`delivery_adapter.status` also reads platform display/save fields. For a manual task its defaults describe lack of platform observations; those fields must not be advertised as an aggregate manual+platform state. No evidence here establishes a failed Adobe widget or failed save.

## Proposed smallest change

Scope the experience result to evidence available in the current call, without changing accepted ledgers or SQLite schema.

- Extend `experience.describe` with an optional explicit current manual-presentation confirmation. Keep its default platform-ledger behavior for existing callers.
- `task_history.delivered` forwards its already-required explicit confirmation only after verifying the exact accepted version and completing normal conversation bookkeeping. The response can then truthfully report `display_observed=true` for that current delivery confirmation.
- Return an explicit observation basis/scope (for example current manual confirmation versus platform-ledger observation). A generic status call without that current confirmation must declare its narrower scope rather than imply it has disproved a separate manual display.
- Keep the raw platform display fact separately identifiable; leave persistence, acceptance, version numbering, one-time hints and adapter STOP/authorization behavior unchanged.
- Do not use `changed`/first-delivery as the presentation boolean: a verified repeated confirmation can still be observed, while the hint remains one-time.
- Do not persist a newly manufactured provider receipt, re-run display, call finish on accepted tasks, backfill old timestamps, change old jobs or reinterpret SQLite delivered as a signed display certificate.

This fixes the contradictory current `delivered` response with a small scoped change. It deliberately does not promise that session-free status calls can retrieve external manual observations they never received. Any future durable manual-observation store or session-aware aggregate status would require a separately reviewed evidence contract and is outside this minimal proposal.

## Targeted regression tests to implement with the repair

These are proposed test cases, not tests already added/run:

1. Synthetic accepted manual task: current explicit confirmation yields display=true with manual-current basis; no `platform_delivery` is created and accepted job bytes remain identical.
2. Manual task with save receipt but no presentation confirmation: cannot become display=true merely because it is saved or accepted.
3. `task_history.delivered(presented=False)` still rejects before registration/mutation; integer/string truthy inputs are not accepted as true.
4. Confirm the same synthetic manual delivery twice: display remains true for each explicit observation, version count stays one, first hint appears once, job bytes unchanged.
5. Platform observed + pending persistence remains display=true/save=false; platform unobserved + saved must not gain display merely from persistence.
6. Platform-only status without manual evidence reports its scope. Legacy SQLite delivered=1 alone never upgrades session-free display state.
7. Wrong output hash / changed historical contract is rejected before an observed experience is returned.
8. No observation operation calls an external image/display/save service; no callback, automatic retry or background reconciliation is introduced.
9. Existing experience, version, adapter and save protocol suites remain green after implementation; distinguish synthetic protocol tests from real-host validation.

Use generated anonymous fixtures only. Do not import either actual photo, filename, private path, task identity, full content hash, tool URL or raw ledger into tests or commits.

## Validation and release boundary

Current evidence confirms a missing manual confirmation input at the experience boundary, not an implemented fix. This document is the only file in this proposal branch. No runtime tests were run against a nonexistent patch and no new photo operations were performed. Product repair should be implemented and tested on this independent Draft before review; the stable v1.5.0 and installed runtime remain unchanged.
