# Phase 5 scoped recovery engineering

This Draft extends PR #24's private recovery handoff with an explicitly invoked
recovered version view. It leaves the installed skill, released archives, tags,
normal CI and historical ledgers unchanged. No background execution is installed.

## Evidence and boundaries

- Previously completed: authorized non-portrait delivery, V1 registration,
  private Work-host archival and independent-session full-byte read-only recovery.
  Those passed results were retained; no photography experiment was repeated.
- New synthetic fault coverage: old local state loss, exact-byte recovery at new
  paths, unknown create results, confirmation flush loss, partial results,
  duplicate entry, immutable ownership conflicts, changed dependency cloud IDs,
  interrupted copies, relocated readback proofs, tampered recovered output,
  directory symlinks and competing local archive claims.
- New real-file acceptance: authenticated materializations of an existing
  authorized archive/source/output/formal record were copied to a NEW isolated
  private target. Full original PNG hash, V1/series/source/null parent, current
  recovered cursor, unchanged input hashes and identical repeat entry passed.
  A controlled interruption left an unusable incomplete target and resumed.
- A separate process successfully verified that target while an audit hook
  rejected reads from original session paths and host input directories.
  This demonstrates independence from those data paths, not a separate machine
  or a newly independent ChatGPT conversation for the write-style test.
- The restored index is a derived read-only version view, not the original task
  database. It cannot be used to claim operational revision/ledger migration.
  Private image bytes, IDs, names and raw host receipts are intentionally absent
  from this public repository; they remain in the private test evidence.

Independent code review reproduced three defects: rematerialized archive paths
blocked continuation; status did not recheck retained host identity proofs; and
ancestor directory symlinks bypassed asset confinement. All three received
regressions and fixes. Review of the revised code found no additional important
blocker within the explicitly limited recovered-view scope.

## Acceptance decision

The manual, known-handoff, one-writer recovered-view scope passes its evidence
gate. Broad Phase 5 reliability remains **NO-GO**:

| Remaining condition | Risk | Required evidence/capability |
| --- | --- | --- |
| Complete loss of local operation state AND stable handoff | High | Durable host operation registry and authoritative reconciliation; never empty-search retry |
| Same-series writers in different sessions/roots | High | Host/server coordination and conflict detection; local lock is insufficient |
| Portable archival create identity after path relocation | High | Path-independent operation protocol with compatibility and real-host fault tests |
| Process death during a real host create | Medium | Actual host interruption/reconciliation exercise without duplicate or inferred failure |
| Operational task-ledger migration/revision | Medium | Separate destination, transaction/conflict/rollback design and explicit acceptance |
| Unattended background archive and long retention | Medium | Host execution support and repeated elapsed-time observations |

Do not promote this Draft to Ready for Review for a broad reliability claim.
No merge, installation, tag or release is performed by this work. The supported
manual scope can be reviewed separately, with these limitations retained.
