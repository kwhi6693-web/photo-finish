# Historical delivery latency: evidence and implementation plan

2026-10-27. Research continuation of d64981b / Draft PR #16. Stable main5045c9d and v1.5.0 artifacts untouched. No new photo, edit, save, rollback or version registration.

## Evidence recovered, scope and missing boundaries

Reused private 61-file travel and 49-file independent-chain checkpoints, retrieved with exact Library identities; full archive hashes matched the original recorded hashes. No restore into old task roots or changes to private source ledgers. Archive hashes and anonymous member hashes are in performance/historical-latency-20261027.json; no photographs, private ledger contents, tool URLs, account IDs or user preferences are published. tools/analyze_historical_latency.py reproduces timing-only extraction from explicitly supplied private archives without extraction or mutation.

Five historical accepted job records: travel1–3, independentV1/V2. V2 is a revision of V1, not another independent scene. Travel tasks share a batch and acknowledgement, so adding task-envelope times would double-count wall time. Historical controlled acceptance includes administrative/inspection delays; it is not representative normal-use latency.

| Requested stage | Actual evidence / limitation |
|---|---|
| Upload / automatic trigger | No reliable upload start or trigger boundary; unmeasured |
| Context load | Controller local monotonic intervals, 5 samples, total0.010136s |
| Style retrieval | Local reference_matching intervals, 5 samples, total0.071501s; includes local matching work; not model reference viewing |
| Professional decision | No isolated model spans; unmeasured |
| Real editor | Actual tool-return objects and ledger intervals; transport+queue+service+host handling, not pure backend compute |
| Formal-file fetch | Local monotonic download span including network wait, not CPU time |
| Visual terminal inspection | Actual quality decisions exist, but start/end absent. review_receipt measures recording/validation, not time spent seeing images |
| Save receipt | Independent chain has photo/record helper-call boundaries; travel receipts exist without equivalent exact call spans |
| Version registration | Rows/returned results exist, but no trustworthy isolated registration duration |
| Full upload-to-user delivery | Not measurable from these checkpoints. Intake→save acknowledgement and intake→record response are narrower envelopes, not full E2E |

Clock durations use original recorded local monotonic seconds where available. Tool/save wall-clock boundaries were observed by the calling harness; no synchronization, backend CPU or fine sub-millisecond accuracy claim. Overlapping/nested intervals are merged; review_receipt sums must not double count nested decorator events. First travel image uses one submission returning working plus one poll returning completion: two waiting intervals are NOT two edits.

## Measured baseline

| Case | Editor-call union s | Fetch s | Photo save s | Record save s | Local controller union s | Intake→photo acknowledgement s |
|---|---:|---:|---:|---:|---:|---:|
| Travel1 |83.657|11.202|unmeasured|unmeasured|0.191|448.518|
| Travel2 |5.690|8.779|unmeasured|unmeasured|0.176|448.496|
| Travel3 |7.235|7.685|unmeasured|unmeasured|0.180|526.727|
| IndependentV1 |7.955|8.373|11.373|7.433|1.049|104.991|
| IndependentV2 |8.748|8.511|7.128|5.623|1.342|117.258|

Five-case accumulated observed editor-call union113.285s, fetch44.551s; two-case photo+record saves31.557s. These unequal-coverage sums do not give an apples-to-apples stage ranking. Across the SAME two independent cases, saves31.557s > fetch16.884s > editor16.703s; local controller union2.391s. This is the supported equal-coverage ranking, not a universal benchmark. Both versions use the same scene; no stable p95/throughput claim.

Independent intake→record-save-response envelopes112.469s and123.018s. Observed stage/tool/save intervals cover36.183s and31.352s; uncovered76.286s and91.666s. These are arithmetically uninstrumented wall intervals, NOT avoidable delay or model/host estimates. Travel uncovered353.468/433.851/511.626s additionally includes uninstrumented batch save/admin/inspection, so it cannot be pooled with the independent cases to rank normal performance.

## Three observed priorities and minimal proposals

No production bottleneck ranking can be definitive until uncovered spans are attributed. The following are research priorities based on the comparable two-case ranking, with the five-case long editor tail noted separately.

1. **Save-call orchestration (31.557s /two cases).** Inspect whether existing mandatory photo and final-record calls cause avoidable scheduling gaps. Keep two distinct authoritative receipts and exact output binding. First add caller-side spans for save-intent, external save response, record construction, record save and register. Only then consider continuation immediately after a confirmed receipt. Do not batch dependent record saving before the photo receipt or retry unknown outcomes. Success criterion: lower paired median/p95 outside-service gap with identical save-call count, verified receipts and zero duplicate writes; no fixed numerical gain is promised.
2. **Formal output acquisition (16.884s /same cases).** Distinguish request-to-first-byte, transfer and decode/hash; instrument the existing fetch once without additional download. If scheduling gaps dominate, fetch the confirmed output immediately where tool rules allow. No new cache, parallel speculative fetch, extra upload or skipped hash/decode. Success: reduced ready→verified-file elapsed under matched output size and conditions, one download attempt unless known bounded failure, byte identity and full checks unchanged.
3. **Editing/poll orchestration (16.703s /same cases, 83.657s travel outlier).** Observe submit/working/poll-ready separately with exact request/task identity and provider poll instructions. Never count polling as rerender. Only optimize a demonstrated caller scheduling gap; cannot claim to speed provider compute. Success: reduced measured working→next-poll gap within provider rules, same unique edit submission count, no extra fee/calls or authorization/STOP bypass.

**Attribution prerequisite has higher confidence than any runtime modification:** add lightweight evidence-only spans in the invoking harness (not a new runtime abstraction) for photo upload accepted, skill intake, reference viewed, decision completed, preview start/end, manual visual inspection start/end, accepted output, each save response, register and actual delivery. Capture actual tool boundaries; do not log private prompts/photos/credentials publicly. Model time is not inferred from lack of Python spans. Host overhead requires a host-provided signal; absent it stays null. No additional editor/save calls required to collect timestamps on the next naturally authorized task.

## Incremental implementation / validation plan

A. Readonly query and attribution design: preserve present evidence; identify available host clock/events. Reject synthetic timings for live quality/host claims. Use anonymous trace IDs and monotonic clocks plus honest wall-clock provenance. No background listener/telemetry service is introduced.

B. One naturally requested authorized non-portrait task, if needed later: timestamp existing operations, preserve normal visual review and receipts, snapshot privately. If host does not expose model/trigger signals, document the remaining gap. This research run did not submit such a task because existing evidence already locates the gap and no blind new edit is necessary.

C. Compare equivalent tasks/data/host/tool conditions; randomize ordering when practical, report sample size and variation. Never compare a batch workload sum with a single-photo elapsed time. Require at least90% interval attribution before claiming an end-to-end dominant cause; attribution coverage target is an instrumentation goal, not authority to classify unknown time as measured.

D. Only implement a change if a measured non-quality, non-safety caller gap exists; retain all stable protections. Acceptance requires source/reference/output/policy hash checks, genuine visual review, legal parent versions, zero-render rollback invariants, individual batch failures, explicit auth/STOP and unknown-first/save idempotency. Check affected modules and corresponding platform CI; do not rerun old photo acceptance just to time it. No duration threshold may force premature quality approval.

Risks: observer timing overhead, human/agent administrative delays, wall-clock discontinuity, photo-size differences, provider variability, shared batch spans and hidden nested decorators. Record them; avoid fabricated speedup. Current report/script introduces no runtime mutation, so no new photographic/authorization non-regression claim is needed beyond unchanged source bytes.

## Result

Historical evidence supports seconds-level external call/fetch/save costs versus milliseconds of context/retrieval. It does NOT establish pure service time, model decision time, actual visual-review duration or full upload-to-delivery latency. No runtime performance optimization, new cache/framework, merge/tag/Release is proposed in this measurement-only commit. Local analysis runs and interval-union self-check pass; cross-platform CI pertains to the exact research head and is reported in PR #16 once observed.
