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

## P0 host-capability closure (2026-10-29)

The follow-up inspected the currently exposed Work/Library schemas and ran only
new isolated synthetic host probes. It did not repeat photography or recovery
acceptance, modify old Library records, or change runtime code.

| Capability | Exposed contract | Actual observation | Acceptance limit |
| --- | --- | --- | --- |
| Persistent operation data | Files can store caller operation keys; list/search/read expose stable file IDs | Two newly created JSON records with the same synthetic series/version/operation key were both returned by list/search and fully retrieved | Storing operation data is not a server operation registry or unique business key |
| Known write outcomes | Upload results report per-file success or application failure | Create and guarded replacement succeeded; stale replacement returned `conflict`, `version_conflict`, expected version 0/current version 1, `retryable=false` | A transport interruption is still unknown; no exposed lookup resolves a lost create result by caller operation key |
| Existing-file conditional update | `expected_current_version` is exposed on replacements and prepared finalization | Writer A updated version 0 to 1; writer B's stale version-0 write was rejected; full-byte readback still matched A | This protects one known Library file ID, not all files belonging to a series |
| Unique creation or operation idempotency | No caller idempotency key, unique series/version constraint, or create-if-absent business-key field is exposed | Same logical operation persisted as two different Library file IDs; colliding filenames were disambiguated | Names/search hits cannot establish a sole authoritative registry; an empty search never permits retry |
| Independent-session coordination | Stable file IDs enable retrieval; prior independent-session byte retrieval remains accepted | This probe was a same-session stale-writer interleaving, not independent ChatGPT sessions or simultaneous server calls | No new cross-session writer/operation-registry acceptance is claimed |

Correction to an overly broad interpretation: Library is NOT devoid of conditional
writes. Existing-file optimistic version control is exposed and passed this probe.
It cannot by itself establish the initial unique per-series coordinator after both
local state and its binding/handoff are lost. A theoretical pre-provisioned,
authoritatively bound coordinator could use that primitive; its provisioning,
discovery, crash and stale-writer protocol is not implemented or certified here.

The probe retained actual responses and full retrieved bytes privately. No cloud
transport failure was deliberately induced and no unknown upload was replayed.
The duplicate creates were expressly authorized new test objects, not retries of
an uncertain write. No negative search result was used to infer absence.

**P0 decisions:** both remain blocked; overall Phase 5 remains **NO-GO**. Stop this
implementation direction rather than add a local substitute, new service, or
unsupported atomicity claim. A future host contract must provide authoritative
series-to-coordinator binding/create-if-absent, operation-key lookup with durable
states and replay behavior, and conditional transitions/fencing honored by every
series writer. Leases, if used, need stale-holder fencing and failure semantics.
An equivalent atomic host protocol is acceptable; a distributed database product
is not specifically required. Then test actual independent sessions and crashes
using new synthetic targets before expanding support.

**Narrow review recommendation:** PR #24 has independent value as an explicitly
invoked, known-handoff, single-writer credential/readback and recovered-view tool.
It is suitable for code review under that reduced contract, provided these P0
limitations remain release/merge criteria for any broader reliability claim.
Keep Draft in this task; do not silently change Ready status, merge, install,
publish, or migrate historical ledgers. These are documentation-only findings;
the runtime and its existing regression evidence remain unchanged.
