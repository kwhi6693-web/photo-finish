# Targeted long-latency implementation gate — 2026-10-29

Status: **blocked on causal evidence; no speedup implemented or claimed**.

## Scope and immutable baselines

Implementation authorization covers only proven removable seconds-level latency. Research PR [#16](https://github.com/kwhi6693-web/photo-finish/pull/16) remains open/Draft at `6eca4e4d8bcb0b7ac6bdb87b0fcfbb6ee99b45d7`. This independent work starts from main `194ffd3d4ac64303147e94744b668edd68d06769`. No runtime, installed v1.5.3, photographic-quality policy, release artifact or private history is modified.

Reused the existing historical latency report, caller observation protocol, host readiness report, unchanged observer source and both real-photo audit comments on #16. Did not rerun the historical analysis, benchmark or photo tasks. Public comments are redacted audit evidence; underlying private trace archives were not retrieved in this turn, so no new raw-trace verification is claimed.

## Existing real measurements (not before/after)

Historical same-coverage independent V1/V2 pair: photo+record saves 31.557 s, formal downloads 16.884 s, editor-call union 16.703 s. Unassigned record-response envelope gaps: 76.286 / 91.666 s. The two versions are one scene, not independent matched trials.

Later natural-photo audits:

| Observed boundary | A (s) | B (s) |
| --- | ---: | ---: |
| Formal download outer span | 8.930085262 | 8.478408726 |
| Photo save outer span | 3.558107271 | 5.132234675 |
| Record save outer span | 3.434707703 | 3.298567765 |
| First version registration | 0.010197316 | 0.009665424 |
| Edit API, adjacent await | 5.574 | 4.935 |
| Poll calls | 0 | 0 |

A and B differ in content, dimensions, ICC, recipe and service time. Differences are not optimization gains. A's 79.188426541 s and B's 54.513192264 s uncovered local windows use different boundaries; neither is a measured removable wait. Full upload-to-device coverage remains unknown. The historical 83.657 s editor-call union includes working/poll; it does not isolate idle scheduler time.

## Current source-path inspection

- `delivery_automation.fetch` reuses an acquired output only after path/full-byte identity checks; otherwise downloads the confirmed ready URL. No unconditional duplicate download or fixed sleep was found.
- `workflow_session.download_image` streams one response, validates signature/hash/decoding/color/extension and publishes exclusively. Removing checks or changing codecs would not meet this task.
- `delivery_automation.complete` consumes the photo save acknowledgement before constructing/verifying the final record. `record_intent` binds that exact record; `record_saved` consumes its separate real receipt. These are dependent operations, so parallel speculative saves are inappropriate.
- `delivery_automation.plan` distinguishes working, unknown, transfer recovery and unconfirmed saves. It describes the next action; it does not own external service scheduling. No runtime fixed-delay polling loop was found in the inspected delivery/controller paths.
- Version registration is about 10 ms in A/B; excluded from optimization under the authorized scope.

Confirmed: external call/download/save boundaries account for seconds of elapsed time. **Not confirmed:** which portion is network, service queue/compute, host scheduling or eliminable caller idle time. Source inspection cannot supply missing timing causality.

## Decision

No runtime trial was made: there is no supported removable-delay hypothesis to implement and evaluate. No unsuccessful change is retained. Before/after and savings are **unmeasured**, not zero or an estimated percentage. This Draft is an evidence gate and handoff, not a completed performance fix.

No new image, poll, upload, download, photo/record save, rendering, model-based photo review or version operation was performed. Engineering tool calls in this investigation do not establish the photo workflow's model-round count. Photographic rules, actual visual review, authorization/STOP, hashes, receipts and version safeguards remain unchanged by this diff.

## Minimal next natural-task observation

Reuse `tools/observe_delivery.py` at the exact #16 commit above (SHA-256 `fa3308de3365263f270f73833506160ebef047f2525e1f501b092e95994b7693`); do not copy/fork it into runtime. Use the existing caller protocol from that commit.

Only during a future naturally requested and authorized photo task, bracket the existing operations in the same orchestration cell where allowed:
1. Ready result received → existing formal fetch → verified file ready. Within that existing transfer, capture first-byte/transfer versus decode/hash only if available without an extra download.
2. Existing photo save response → receipt verification → final-record construction/save-intent → existing record save response → verification/registration. Retain both authoritative save receipts.
3. If working actually occurs, record response time, actual provider interval and the existing next poll start. Use the latest opaque task identity; no additional polling or resubmission for measurement.
4. Record observable caller activity between these boundaries. Leave invisible scheduler/model/service components unknown. Exclude actual judgement/review and mandatory authorization/STOP time from any proposed removable idle gap.

Do not add model turns or separate business calls for logging. If co-location is unavailable, leave the boundary missing. STOP forbids after-hooks; unknown outcomes require investigation, not retries. Observer failure must not block normal safe delivery. Persist only through the normal authorized private checkpoint; no extra evidence upload solely for timing.

Compare equivalent observed conditions before implementing one minimal cause-specific change. Report sample count, variation, interval union and instrumentation overhead. Retain a change only with demonstrated user-wait benefit and unchanged business call counts, quality and protections; otherwise revert. No synthetic benchmark substitutes for real user-wait evidence.

## Validation scope

Documentation-only diff: run publication/history scan, doctor and diff checks; normal existing cross-platform CI runs on this Draft. CI success would validate unchanged product behavior and documentation integration, not prove a latency improvement. Exact commit/run results are reported on the PR.
