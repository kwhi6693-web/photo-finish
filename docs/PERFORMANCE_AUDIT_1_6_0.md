# 1.6.0 execution/performance audit — 2026-10-27

Base: main 5045c9d6220cb62dbeb8e90dec64a80a130b7c92. Independent perf/orchestration-1.6.0 branch. v1.5.0 remains the stable implementation; no new package/tag/Release or installed-skill update. This is a measured audit, not a performance release.

## Scope and evidence

Inspected photo_edit, photo_workflow, delivery_automation, workflow_session, style_library, task_history and batch_workflow. Existing anonymous fixture/metadata tools supplied local measurements. Raw evidence is in performance/query-cache-20261027.json, performance/controller-response-20261027.json and performance/metadata-profile-20261027.txt. Generated blank fixtures are protocol data, not real photo quality acceptance. No real editing, saving or external tool submissions.

| Path | Observation | Decision |
|---|---|---|
| photo_edit prepare/submit/returned/review | Unified four calls already merge stages. _response loads ledger and plan loads it twice more; prepare also reads the master hash from ledger. | Do not pass potentially stale caller state across freshness/transaction boundaries without profiling larger actual ledgers and consistency tests. |
| photo_workflow | Image decode inspects real color/clipping; source hashes before/after inspection and matching detect changes. Feature reuse already keyed by method and source hash; no feature extraction when no candidates. | Keep hashes and real review. Do not replace them with mtime assumptions. |
| delivery_automation | plan rechecks context/source/selected inputs and review state. working polls the same task; unknown investigates; confirmed receipts gate delivery. | No blind resubmit or parallel writes to gain throughput. |
| workflow_session | Output inspection already reused by full path/hash/inspection-version, copied to avoid alias mutation. Job reads deserialize JSON; actual stage timers already exist. | No new cross-call rule/image cache. |
| style_library | Exact serialized-row LRU 2048; each retrieval still queries SQLite. Explicit IDs use SQL IN. Free query/group retrieval scans metadata, not all photographs. Entries deep-copied; path containment/symlinks verified. | Largest observed costs are safety checks/copying, not an excuse to drop them. No vector/semantic retrieval claim. |
| task_history | Readonly lookup verifies accepted contract and original/source/output hashes; selected cursor separate; writes use SQLite transactions. | Never cache historical identity without fresh hash proof; no rollback rerun here. |
| batch_workflow | Per-job status checks and isolation; accepted/working/unknown tasks excluded from blind retries. SQLite write ownership and external tool authorization impose real sequencing. | No independent Agent split or speculative external parallel scheduler. |

Rules/theory use existing progressive references and stage/context hashes. This audit cannot count host instruction reads, reasoning tokens, plugin latency or tool-routing choices from Python source. Those are unmeasured; no fabricated redundant-call savings.

## Baselines and rejected prototype

Initial unprofiled existing metadata benchmark: 1000 synthetic rows / 30 warm repetitions, cold 151.906409 ms, warm median 45.8889385 ms. Profiled timing is slower by instrumentation and must not be mixed with unprofiled timing. First profile: 31 metadata retrievals (not a measured SQL statement count), 31000 _asset checks (3.088 cumulative seconds), deep-copy 1.262 cumulative seconds; raw second profile is retained separately with its actual timings. These observations identify cost, not expendable checks.

Six paired alternating-order runs used the same 1000-row fixture/query and 15 warm repetitions per run. Prototype only memoized immutable query parsing (256 entries, key includes vocabulary); catalog, SQL, paths, hashes and output remained fresh. Median of per-run warm medians: before 47.518325 ms, prototype 45.500221 ms, reduction 2.018104 ms / 4.25%. Query parser prototype reported 95999 hits / 1 miss; existing decoded-row cache remains 15000 hits /1000 misses per paired run. SQL reads and asset/path verification counts unchanged; external tool calls remain zero. This is not end-to-end speedup or statistical confidence.

The prototype was **not retained in runtime**: ~2 ms marginal local saving does not establish a worthwhile delivery bottleneck or justify another runtime cache. Two temporary prototype consistency tests passed (bounded immutable cache/vocabulary key; warm-query catalog update/delete/user isolation), then were removed with the discarded runtime experiment. They do not certify deployed behavior. tools/benchmark_query_parsing.py retains a reproducible equivalent prototype and 25 match-equivalence checks; it restores the original matcher in finally and never edits runtime source.

Separate accepted blank-fixture response sample: 3 ledger reads /19530 serialized bytes, 2 explicit identity-hash calls /987 bytes, local median 2.1372745 ms over30 samples. Counters observed separately from timings; bootstrap's lower-level file access is outside these explicit _file counters. No before/after optimization exists for this response path, so no savings claimed.

## Safety / invalidation / deployment boundary

No persistent runtime code, rule, protection, version index, save state, host authorization or routing change remains. Exact-row cache invalidation, readonly hash checks, immutable history, genuine receipts and non-portrait naturalness requirements remain byte-identical to stable main. CI can verify unchanged regressions automatically on this development PR; no new Windows/macOS local execution is claimed. Actual photographic quality, real service/host/end-to-end latency and parallel batch benefit remain unmeasured. No package rebuild or stable artifact modification is necessary because shipped inputs did not change.

Local doctor/publication/diff checks passed. Candidate benchmark runs only anonymous data in temporary private roots; no user photos, preferences or ledgers are committed. Cross-platform CI results belong to the exact PR head and are recorded in its description once observed, not inferred from configuration.

## Next measurements, not implementation promises

- Larger real anonymized ledger-size distributions before considering single-operation state reuse; preserve mutation/freshness boundaries.
- Selective metadata retrieval/index design only with selective-query workload and invalidation/security evidence; do not hide malformed or unsafe entries merely for speed.
- Byte-read and syscall attribution for full prepare/submit/returned/review under isolated authorized workloads; actual host/span measurements separately.
- Batch independent scheduling only after actual tool permission, ordering, fee and unknown-task constraints are established.

No merge/tag/1.6.0 release authorized. Outcome: baseline and reproducible experiment delivered; no worthwhile runtime optimization established in the measured scope. Do not claim that nine layers or complete delivery have become faster.
