# Photo Finish 1.5.0-rc.1 engineering evidence

Date: 2026-10-25. Candidate workflow: 2026-10-25.1. This is an unpublished review candidate; merge, tag and GitHub Release require explicit user approval. Existing stable v1.4.2 remains unchanged.

## Baseline and Windows investigation

Authorized repository: kwhi6693-web/photo-finish, default main, baseline 184a62c7122bd470ae0f2d0bec4838fe3bef0a68. Latest release v1.4.2 targets that same commit; its curated package hash is 23ce92b01a3d4c01fb81203f8d943fbd80a5fe912445e65041cd46b714d0139b.

Local Linux Python 3.12.14: doctor/integrity passed, 209 synthetic tests passed in 6.866s, publication scan found no findings. The four named Windows cases from the handoff all pass here. This does not establish a native Windows result.

The existing [same-commit CI](https://github.com/kwhi6693-web/photo-finish/actions/runs/40105427756) has six successful jobs. The Windows Server 2025 / Python 3.12.10 job log was actually read: 209 tests in 17.359s, OK, no skips reported. It also reproduced the v1.4.2 ZIP hash. The handoff's separate Windows installation lacks exception traces; its four errors cannot responsibly be attributed to a specific OS or product defect. File/directory symlink tests already detect unavailable creation privileges and keep the safety assertions; no tests were removed or disabled. Candidate CI is tracked on the PR, separately from this historical result.

## Implementation and behavior evidence

| Phase | Files / change | Evidence and result | User effect / remaining boundary |
|---|---|---|---|
| P0 presentation | experience.py, photo_edit.py, SKILL and canonical delivery guide | Seven initial behavior tests RED→GREEN; suite 216 passed | Truthful Chinese phase/recovery text; generated/displayed/accepted/saved stay distinct |
| P0 versions / professional layers | task_history.py, workflow_session.py, delivery_automation.py, delivery_adapter.py, conversation-versions.md | Initial nine version tests; suite 225 passed | Indexed V1/V2, cross-turn current cursor, selected-output revisions, inherited local protections, zero-render rollback and unchanged old bytes |
| Metadata performance / style discovery | style_library.py, photo_workflow.py, benchmark_metadata.py | Four new tests; suite 229 passed | Exact serialized-row cache, primary-key ID access, limited synonym matching, recent/frequent use; no vector search |
| Batch / UX metrics | batch_workflow.py, delivery_metrics.py, batch-recovery.md | Seven initial tests; suite 236 passed | Ordered real statuses, independent failure handling, safe replacement preparation, no completed/unknown resubmission, once-per-batch hint |
| Independent review repairs | Retry/profile/protection binding, version contract fingerprint, batch provenance checks, hint retention | Reviewer independently reproduced four substantive defects and an all-failed hint issue; focused RED→GREEN regressions added | Unchanged profiles work on recovery; original task settings/scenes and locked revision protections survive; source/contract changes cannot masquerade as accepted history |
| Release material | canonical runtime policy, mirrors, three READMEs, agents metadata, architecture/runtime/release guides, changelog, candidate manifest | Doctor, full suite, publication history, double build and clean extraction run for the final PR head | Candidate packaging remains separate from stable Release |

The rollback assertions patch submission to fail if called, compare historical ledger bytes and output bytes, and verify hashes again on selection. The production rollback code has no renderer. Save/unknown protections continue to run through the existing real-receipt controller tests. Synthetic fixture receipt IDs, timing and visual judgments are protocol inputs, never represented as real editing, host saving or aesthetic certification.

## Local measured performance

1000 anonymous metadata-only records, Python 3.12.14, 30 warm repetitions: cold read 141.571492 ms; warm median 45.305832 ms; 30000 exact-row cache hits, 1000 misses, bounded capacity 2048. The initial 512-row capacity thrashed at this sample size and was increased before delivery. Script: `python tools/benchmark_metadata.py`.

This measures SQLite metadata reads, normalization and keyword expansion only. It excludes photo decoding, visual selection, network, image service, upload and host delivery; it is not an end-to-end speed improvement claim. New/changed rows invalidate by exact content, deleted records disappear on the next actual SQLite read; selected image bytes are still fully hashed. Policies/theory remain bounded named sources and chapters loaded on demand, with full trust-boundary hashes. No private-library scan or automatic theory ingestion service was introduced.

Metrics separate live/replay/synthetic/unclassified, first output acceptance, per-root observed revision average, duplicate submissions (same input/complete arguments, distinct tokens), accepted-output elapsed and actual persistence receipts. Missing timing is null; incomplete task histories underestimate revision rounds. No current live aesthetic rates are claimed.

## Real host and visual acceptance: open release gates

The actual browser was inspected: a signed-in ChatGPT account and Work mode are accessible. Settings search, plugin settings, personalization and the Work plugin picker were inspected; no verified candidate Skill import/install or automated photo-sequence testing entrypoint was found there. The currently exposed installed Photo Finish skill was read and is still workflow 2026-10-24.2, not this repository candidate. It was not silently replaced.

| Requested real acceptance | Actual result |
|---|---|
| Candidate installation/loading in ChatGPT | Not verified; no supported candidate installer exposed in the inspected UI/tools |
| Photo-only automatic trigger | Not verified for this candidate; requires a newly loaded candidate and actual isolated host turn |
| Actual image editing and full/native-detail review | Not executed; this task supplied a Markdown handoff, no authorized anonymous photo set |
| Live custom rules/style application and continuity | Controller fixtures passed; actual host behavior not verified |
| Version rollback / save | Existing-byte controller regressions passed; live host and authoritative save confirmation not verified |
| Portrait, night, lettering, travel batch, special light aesthetics | All five real-photo regressions remain unverified; no generated/synthetic protocol fixture is described as a photograph test |
| New material and end-to-end host latency | Local metadata measurement only; actual host/service timing remains unverified |

No new paid service, API key, web app, credentials, photographs, private preferences, tasks or receipts are included. Before stable release, load the exact reviewed candidate in an isolated supported host, use authorized anonymous photographs covering the five scenarios, retain actual tool/result evidence and compare original/affected details. Do not infer identity, lettering, print calibration or saving from prompt text or static tests.

## Approval and release traceability

Review the PR source, tests, evidence and candidate ZIP manifest/checksum. After the remaining real acceptance gates are met and approval is given, select an exact verified main commit, update to the approved final version if appropriate, rebuild deterministic bytes, tag that commit, attach matching ZIP/checksum and read back downloaded assets. No tag or Release is created by this optimization branch.

## Final local candidate verification

- Python 3.12.14 / Pillow 12.3.0: 246 tests passed in 8.723s, including all 209 original regressions plus 37 additional cases. No live editor was called by this suite.
- Doctor/integrity: passed, 43 runtime links, 11 policy pointers, 174 repository documentation links, empty distributed reference index.
- Publication scan including 464 reachable historical blobs: passed, no findings. Known-pattern scanner scope is retained; this is not a universal absence guarantee.
- Optional numerical analysis: 5184-pixel synthetic fixture, six palette centers, normalized weights and valid 63-bit perceptual hash passed. `pip check` passed.
- Deterministic double build: identical bytes. Candidate ZIP: 484608 bytes, 113 entries including manifest; version 1.5.0-rc.1; SHA-256 `384c44eff01e0c0d6c75eed8ad1e51076d6f6db2a812bf412484c4ec9c2202b3`.
- Clean temporary extraction: all 112 manifest-listed files verified, bundled doctor and prepare/status CLI passed using an isolated anonymous synthetic image/private root. This is a relocation/controller smoke test, not real-photo or host acceptance.
- `git diff --check`: passed. Windows/macOS/Python 3.10/current-head CI results are available on the draft PR after push; do not substitute the historical baseline result.

The independent reviewer found four substantive bugs and one hint issue; all were reproduced and fixed with regression assertions. Additional review found duplicate status planning and corrupt-index error handling; both now have regression coverage. No known code-review finding is deferred. Real-host/photograph gates above remain open.

## Resume / candidate CI correction

The nine stage trees were recovered and verified exactly, and Draft PR #14 was opened. The first native Windows candidate lane passed all 246 tests (30.587s), then failed only in the newly added standalone four-case diagnostic because the temporary Python script did not include the repository root on sys.path. Three symlink cases passed explicitly. An isolated temporary-script reproduction confirmed the import error; adding the repository root made all four cases pass locally. The workflow-only correction does not alter packaged inputs or the ZIP hash; native current-head CI is checked on PR #14.

## Verified native candidate results after recovery

Candidate/CI-fix commit 7a6fa21c46c23d951ba5d1e18be17a34f8dd6b2f passed all six jobs in push run 40191479841 and all six PR jobs in run 40191482775. Actual Windows logs: 246 tests in 29.269s and all four explicitly named symlink/temporary-alias cases in 0.391s; zero skips, failures or errors. The isolated diagnostic import correction is now verified natively, not inferred from Linux. The candidate archive is unchanged. PR #14 remains draft pending exact-candidate host/real-photo/save acceptance and user approval. Latest progress-only commit identity and live checks resolve through the PR and docs/IMPLEMENTATION_PROGRESS.md.
