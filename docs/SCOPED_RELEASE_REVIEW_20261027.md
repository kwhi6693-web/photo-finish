# Scoped release review — 2026-10-27

Baseline 438c71cfcc1e020c6c8aa6ab22b9bb70ebcb021b; PR #14 remains Draft. This supersedes the release decision in RELEASE_GATE_20261027.md, not its observations.

## Quality decision

Re-inspected the existing actual source/candidate forest comparison. Backlit haze and dark forest are valid photographic atmosphere; insufficient evidence of erroneous exposure or optical defocus. Existing native attempt had insufficient useful improvement and remains rejected. Preserve original; zero new edits, photo saves or version registrations. No newly verified authorized defective sample was established in this run. No claim of passing low-exposure improvement or defocus recovery. Rejection/no-op is a valid professional outcome; guaranteed improvement/defocus restoration is outside the release promise.

## New isolated fault evidence

Added tests/test_fault_injection_release.py. Two new combination tests actually passed on Python 3.12.14 (0.155s), without rerunning prior suite. All image fixtures, provider identities and query receipts are SYNTHETIC; no real Adobe/Library service failures were induced.

- Reserved request followed by injected TimeoutError: plan INVESTIGATE_RENDER, duplicate begin rejected and ledger unchanged. Source-bound synthetic query reconciles the same reservation; repeated reconciliation reuses it without mutation.
- Injected output-fetch timeout leaves ledger unchanged; recovery fetches the existing result, second fetch reuses verified bytes, network fixture called once.
- Failed save receipt blocks completion without ledger mutation; query fixture confirms the same intent, complete is idempotent. Incomplete final-record receipt remains INVESTIGATE_RECORD_SAVE; resolved fixture permits DELIVER.

No production code defect found. No old V1/V2 rollback, batch or checkpoint tests rerun. These tests establish local protocol behavior only: actual external provider timeout, unknown write outcome, auth expiry, outage and remote query capabilities remain uncertified. Recovery requires actual trustworthy tool evidence; no automatic provider query integration is claimed. Never retry an unknown write or rendering submission without investigation.

## Public support boundary

| Class | Scope |
|---|---|
| Core | Non-portrait professional judgement; authorized native full-frame edits; actual visual review and possible rejection/no-op; formal file/hash and real save-receipt distinction; immutable accepted versions and readonly rollback; travel batch under documented host conditions |
| Restricted | Personal rules/references when actually available; automation only under explicit tool-compliant authorization; persistence only with real receipts and accessible persistent session root; local edit only after an effective mask and edge review |
| Uncertified | Reliable sky-only edge protection, optical defocus repair, every low-light image improvement, real external-provider outage recovery, cross-device sync, all hosts, print/RAW certification |

A restricted operation must stop safely rather than silently switch tools, weaken protection or invent a receipt. Existing SKILL/master/native route already specify visual acceptance, STOP/authorization, mask validation and unknown-first-investigation. No architecture or product-instruction changes needed. Anonymous test library was empty, so no new personal-reference effectiveness claim.

## Decision

**Conditional GO recommendation for the explicitly scoped 1.5.0 capabilities above**, subject to new-commit CI success and user release approval. Genuine provider outage certification and optional defocus/sky capabilities are excluded from public guarantees, not represented as passed. Current evidence does not identify an unresolved core data-safety implementation defect. If unconditional automatic provider recovery or guaranteed low-light improvement is required as a core promise, decision remains NO-GO for that broader product.

This is not authorization to merge/tag/publish. Keep rc.1 / Draft until review. Prior original-host history gaps remain irrecoverable and distinct from later recovery chain. New fault tests do not repair those gaps.

Candidate package unchanged: 1.5.0-rc.1 / workflow 2026-10-26.3, 497953 bytes; SHA-256 8cb0e595648f1f23fe5821fc9ebd7b72f461a6916e80fddc45f253cba549da54. New tests/docs are engineering source, not installed runtime changes. No rebuild required for the identical runtime candidate. Scope note must accompany eventual release notes.
