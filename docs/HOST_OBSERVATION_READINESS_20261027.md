# Real-host observation readiness — 2026-10-27

Baseline: Draft PR #16, 128e2df1466761485efb23a75f04dc59b0a2d8ab. Scope: observation readiness only. No historical-ledger reanalysis, image editing, downloading, saving, version registration, runtime optimization or stable release modification.

## Actual execution evidence

PR metadata read confirmed the requested baseline, Draft/open/unmerged. Existing Validate skill run40446477997 remains completed/success; it was not rerun.

Two readiness checks executed in this ChatGPT Work host:

1. A single Python invocation imported the unchanged observer, created a temporary private sidecar, marked context_read around reading the existing 9264-byte observation protocol, ended the span and read its summary. One completed stage, zero open spans, no clock warnings. This establishes in-process local instrumentation, not a photographic task or speed result.
2. A single functions.exec invocation sequentially awaited: local observer start via exec_command; the actual GitHub get_pr_info read needed to recheck PR #16; local observer end/summary via exec_command. No model turn occurred between these calls. The resulting completed context_read/external_tool span was 0.806455052 seconds, with zero open spans and no clock warnings. This is a GitHub control-plane readiness probe, NOT an Adobe/photo/save timing sample. It includes local process/dispatch and observation persistence around the connector; it is not pure connector or server execution time. There is one span, so no overlapping intervals; recorded union equals that span. No task-received/delivery endpoints were invented; envelope and coverage remain null. Raw readiness sidecar remains outside Git in temporary private storage, not a durable photo-job checkpoint. Only this anonymous result is committed.

Observer SHA-256: fa3308de3365263f270f73833506160ebef047f2525e1f501b092e95994b7693. No observer source changes or new automated tests in this unit. These checks supplement the existing six correctness tests; they do not recertify image tools or rerun CI.

## Feasibility and exact limits

The current orchestration API can await local commands and a connector inside one execution cell. Thus caller-side bracketing need not introduce a model roundtrip. It does add two local command invocations when Python and the connector live in different runtimes. Those overheads must remain in the observed boundary; no zero-overhead claim. Existing in-process Python downloads/controller operations can instead import mark directly around the already-required operation. Neither route is an installed automatic host hook.

This control-plane result does not prove Adobe permits every route, or that its UI can execute a local after-hook. No supported upload-received, widget-rendered, model-compute or host-scheduler hook was exposed by the inspected APIs. Do not infer their existence. A bounded connector call can be bracketed only if its live rules allow continuation. STOP has priority over any finally/after-call observation: do not wrap a STOP tool with an unconditional after-hook. An already-open span remains unknown. Later closure would include the interruption, not pure editing time.

Current Adobe contracts inspected without calling Adobe:

- Single-image tonal work routes to the interactive widget unless a documented exception actually applies. A performance request is not an instruction to perform editing for the user.
- Interactive adjustments require STOP after calling, return no final asset URL, and do not expose a reliable widget-completion timestamp. No automatic after-call marker is permitted here.
- Server adjustment requires a returned preview and actual visual inspection of every input before each call. Preserve PNG unless JPEG explicitly requested. No observer can replace those steps.
- A working response is not an output. Poll with the latest actual opaque taskId; never resubmit the edit. Follow the actual pollInterval (currently documented as milliseconds, normally zero because status call blocks), not an assumed sleep. No taskId exists in this unit and no poll was sent.
- No uniform documented server-start/end or pure compute time is available. Request IDs/status are not clocks. Use actual returned fields if present in a future task, without fabricating missing ones.

## Current measurement coverage

| Boundary | This unit | Next natural authorized task |
|---|---|---|
| Upload/automatic trigger/task receipt | Unmeasured | Only actual exposed receipt event; never backdate |
| Context read | Readiness probes only | Instrument existing local read/validation |
| Reference viewing / professional decision | Unmeasured | Actual observable window only; not model CPU |
| Editing / waiting / poll | Unmeasured | Allowed caller boundaries and provider-required waiting only |
| Formal download | Unmeasured | Bracket existing fetch; no duplicate download |
| Real visual review | Unmeasured | Actual viewing boundary if exposed; receipt time is not review duration |
| Photo/record save and final record | Unmeasured | Bracket existing authorized operations; keep real receipt verification |
| Version registration / final presentation | Unmeasured | Actual controller/presentation events; do not infer from save |
| Pure model / host / service compute | Unmeasured | Leave null absent authoritative signals |

New real photographic tasks: **0**. Real end-to-end coverage: **null**, not 0% or readiness-probe coverage. No new authorized non-portrait editing request or fresh photo was provided in this turn. Prior authorized photos and completed deliveries do not create a reason to edit/save them again. Accordingly, no live photographic trace exists to persist, compare or certify.

## Operational handoff and decision

Use docs/CALLER_OBSERVATION_20261027.md and unchanged tools/observe_delivery.py on the next naturally occurring, appropriately authorized non-portrait task. Resolve a private Git-external root; create one fresh sidecar and retain its anonymous span handles in the existing caller. If a legal pre/post boundary can be co-located, await start, the original operation, then end within the existing orchestration cell; do not add model turns. Never continue past STOP, invent task readiness, or automatically retry on observer failure. The normal authoritative task ledger and receipt still determine completion. Preserve the resulting real trace with the normal private checkpoint; publish only redacted aggregates.

When real endpoints exist, validate same-host/boot clocks, open/unknown spans and union of overlapping completed intervals. Report uncovered envelope as unassigned, never model/host delay. Per-stage totals may overlap and must not be summed as an end-to-end total. A task lacking actual presentation boundary has null end-to-end coverage. Compare editing/download/save/review only on comparable observed tasks; no comparison is supported by this readiness probe.

No repeatable removable wait has been established. No runtime or scheduling optimization is justified. Existing quality, authorization, STOP, hash binding, true saving, immutable version history and unknown-state duplicate protection remain unchanged. Next breakpoint: the next natural authorized photo task, not a performance-generated photo task. PR stays Draft; no merge, tag or 1.6.0 Release.
