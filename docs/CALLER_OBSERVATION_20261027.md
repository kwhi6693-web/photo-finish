# Opt-in caller observation for the next naturally authorized task

Baseline022e4c9 / Draft PR #16. No new live photo task, image-tool call, save, registration or historical reanalysis in this work. v1.5.0 runtime/package stays unchanged.

## Actual available signals (interface inspection, not a live editor probe)

- Current Adobe adjustment/poll schemas expose success, request/origin diagnostic IDs, opaque taskId, working/completed, output and pollInterval. They do not document a uniform server-start/server-end/model/host-compute timing field. An optional metadata object is not proof timing exists. Caller must inspect actual future returns, not invent fields.
- Poll contract requires the latest actual opaque taskId; requestId is not taskId. Follow provider pollInterval and actual STOP/authorization instructions. Observation never starts, polls, retries or resumes tasks.
- Library save response exposes status, identity, size and version, not a documented precise service execution span. Local response arrival is distinct from durable-save proof. Existing workflow receipt validation remains authoritative.
- Python controller already records local monotonic stages and image/tool-observation milestones. Review-receipt time measures recording/validation, not actual model seeing or professional judgement. No model-token or host-scheduler clock is exposed to this observer. exec-command wall_time_seconds concerns that shell command only.

## Minimal implementation and privacy

Added tools/observe_delivery.py, an optional caller-only timing sidecar, not installed by the build allowlist. No runtime imports/hooks, new cache, framework, daemon, telemetry or automatic scheduling. Data: random anonymous task/span IDs, fixed stage/kind/status labels, local wall/monotonic starts and ends. No free-text metadata, paths to photos, tool identifiers, prompts, tool arguments/returns, URLs, receipts or secrets are stored in trace. Actual task mapping stays in the existing private authoritative job, not public timing output.

Specify a new sidecar path outside all Git worktrees using its actual canonical parent (for example resolve the private temporary root before constructing its trace filename); symlink traversal is rejected. macOS /var temporary aliases must not be passed as a symlink path. Exclusive lock prevents concurrent writers; atomic replace plus file fsync checkpoints each event. A stale lock after process loss stops observation; inspect it in private, do not blindly remove it or restart a business task. No cross-device or reboot-safe monotonic clock promise. Use the same host/boot; wall/monotonic disagreement invalidates coverage. File fsync is not a remote persistent-store receipt.

## Use without additional business calls

Import observer in an existing invoking Python harness; create once, mark immediately before/after an ACTUAL operation, retaining its returned anonymous span ID. Example (pseudocode for the operation itself):

```python
from observe_delivery import create, mark, summary
create(private_trace_path)
span = mark(private_trace_path, 'formal_download', 'local_controller')
try:
    result = existing_fetch_operation()  # existing authorized operation, not another download
except Exception:
    mark(private_trace_path, 'formal_download', 'local_controller', span, 'unknown')
    raise
else:
    mark(private_trace_path, 'formal_download', 'local_controller', span, 'ok')
```

The caller must choose failed/timeout/unknown from actual evidence; exceptions do not automatically establish external failure. No automatic retry is attached. Never put free-form exception messages in the timing file. CLI create/start/end/summary supports an existing local harness; end requires --call with the original anonymous span. Do not add model turns or separate frontend/tool interactions just to log. If the actual host cannot co-locate observation with its existing calls, leave those stages unmeasured instead of expanding latency for coverage. CLI process/roundtrip overhead is NOT certified by the in-process benchmark below.

`task_received` and `delivery_observed` are boundary markers: record at actual caller receipt / actual presentation, finish immediately. Their spans are excluded from coverage so an all-task root span cannot fabricate100% attribution. The denominator is caller-received→observed-delivery, NOT upload-start→delivery; upload network/automatic trigger remain unknown unless a real host event is available. Never mark presentation on save acknowledgement or registration alone.

Do not perform an after-call logging step when a tool requires STOP. An open span remains unknown; only later actual authorized evidence can close it, and its elapsed period then includes the interruption, not pure service time. No background callback is installed. End twice is rejected rather than misreported as retry safety. This sidecar neither certifies quality/saving nor controls duplicate business submissions.

## Stage map and attribution

| Stage | Classification / evidence boundary |
|---|---|
| task_received | caller boundary, actual received task; not original upload/trigger |
| context_read | local controller read/validation only |
| reference_view | caller activity window with actual tool/view boundary; not model CPU |
| professional_decision | caller activity only if actual window observable; otherwise absent |
| edit_call | caller-observed external tool wrapper interval, includes transport/queue/handling; no pure backend split |
| poll_call / caller_wait | actual poll or explicitly observed caller wait; same live task, no speculation |
| formal_download | actual fetch including network wait, not CPU-only |
| visual_review | actual viewing window only, never infer from review receipt |
| photo_save_call | actual save-call boundary; real receipt validated separately |
| final_record / record_save_call | existing local construction / actual record-save call |
| version_register | actual existing registration operation, no observer-triggered registration |
| delivery_observed | actual presentation boundary; not save or register |

Summary returns completed interval union, open spans, missing stages, caller-envelope and covered fraction. Nested spans do not double-count union; per-stage totals can overlap and must not be summed as total. Coverage is recorded caller-span coverage, not proof of correct causal attribution. Broad human activity windows may contain idle time; use narrower honest spans. model_compute_seconds, pure_host_seconds and pure_service_compute_seconds remain null. An unmeasured stage remains missing, not zero.

## Actual validation and current coverage

Six new synthetic tests passed: bounded field labels/duplicate end rejection, open unknown span, nested union, endpoint non-inflation, exclusive writes/private Git guard and clock disagreement. These are observer correctness tests, not external service/host/quality tests. No official photograph or accepted history changed.

In-process synthetic overhead:30 start/end pairs, median1.789949ms, maximum2.441174ms, includes lock+JSON+fsync with a trace growing to60 events. Raw result: performance/observer-overhead-20261027.json. Not a Windows/macOS latency benchmark or a new performance improvement. Dependency-only/local host conditions vary.

**New real task count0; real stage coverage unmeasured (null).** Existing022e4c9 historical baseline and its gaps are retained by reference, not recomputed. There is no fresh full end-to-end latency or causal attribution result, and no demonstrated repeatable eliminable wait. Therefore no runtime scheduling change is justified yet.

## Next decision / success criteria

On the next naturally occurring user-authorized non-portrait task only, attach this opt-in observer where actual calling surfaces permit; privately retain trace with normal job evidence. No extra paid edit, duplicate save, or weakening of mandatory visual review. Register no subscriptions or listeners. If no natural task is available, stop at this usable observation kit.

Compare at least two equivalent observed executions before proposing a scheduling change. Require honest interval coverage and available host signals; the prior90% coverage target is an observation goal, not permission to classify unknown gaps. A removable gap must recur outside quality judgement, actual service execution, required poll delay and authorization/STOP boundaries. Success: reduced comparable ready→fetch or receipt→next-operation gaps, equal unique edit/save counts, real quality/receipts/version/hash protections unchanged. Reject a speed claim caused by skipped quality, missing save proof, clock issues, workload differences or shifted logging overhead.

Doctor/publication/diff and exact-head platform CI results are recorded in PR #16. No merge, new tag, 1.6.0 Release or stable package change.


Cross-platform fixture correction: first macOS CI on7fbbe2d failed at setup because its temporary /var alias was rejected by the existing symlink guard. Test fixture now resolves the actual private temporary root before creating the trace. The observer guard is unchanged; no runtime or v1.5.0 repair is implied. Latest-head CI results are reported separately in the PR.
