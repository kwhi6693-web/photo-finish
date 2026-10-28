# Delivery recovery credentials: Work host adapter (Draft)

This development protocol does not install a background callback, grant new tool
authority, or change the installed/released version. Use only after authorized
formal delivery. Python has no Library client or account credentials. The Work
assistant must call its authenticated Library tools following the Library skill;
never inject credentials or invent a storage SDK. No extra image edit or rendering.

## Required host operations

1. Complete the existing accepted-photo save, final-record save, actual display
   and version registration. Retain actual save results. DELIVER still describes
   photo/record saving, independently of recovery archiving.
2. Resolve an owner-private Library folder in the current account. No public
   link, sharing change or replacement. Keep each account's session_root separate,
   outside Skill/Git. Require one writer per series; cross-session concurrency is
   not supported by this local lock or by a claimed remote atomic transaction.
3. Materialize the source, original source, outputs and parent outputs needed for
   the selected series prefix through Library. Reuse already materialized bytes
   and actual transfer evidence where valid. Preserve the complete returned
   structuredContent as JSON, including transfer workspace_path and stable
   library_file_id. Missing source identity is a blocker: obtain authorized source
   persistence separately. Never re-upload a generated image to manufacture proof.
4. Call `photo_edit.py delivered` with its usual fields and optional
   `recovery={directory_id,cloud_files:[{path,result_path},...]}`. Or call
   `recovery-prepare` with `path,session_root,directory_id,cloud_files` after the
   existing delivery. It never registers a new version. Hashes must cover every
   required dependency; unrelated inputs and shared receipts containing other
   tasks are rejected. Batch receipts require a separately authorized scoped
   adapter; do not silently sanitize and call it original evidence.
5. Save the returned operation_id, query_name, archive SHA-256 and size with the
   task's handoff. Call `recovery-claim(session_root,series,version)` immediately
   BEFORE the sole real create attempt. Only `write_allowed=true` permits that
   attempt. This durable transition is result_unknown even if the host dies before
   calling Library. Save this ZIP with the existing Library skill/helper, to the
   returned directory_id. Save no photographs again. Persist the helper's complete
   normalized `{results:[{local_path,status,local_metadata_applied,
   library_file_id,...}]}` result, including failures, and pass its path to
   `recovery-observe`. These associations are caller evidence, not server-signed
   content hashes. Direct native tool responses require the Library adapter's
   normalization; never fill successful fields by inference.
6. On result_unknown, search the exact query_name only in that private folder;
   materialize the existing candidate(s). No search hit is NOT proof of no write.
   Do not automatically claim/re-upload or delete failed/ambiguous objects. Multiple
   conflicting identities require investigation. Known successful writes proceed
   to readback even if another batch operation failed.
7. Materialize the ZIP by its stable Library ID into a DIFFERENT path. Pass the
   actual native result JSON and bytes to
   `recovery-confirm(session_root,series,version,result_path,materialized_path)`.
   It checks stable identity, full byte count/SHA-256 and every checkpoint member.
   Only archive_confirmed means this host-observed readback succeeded. On later
   repeated calls, query status, never create again. Hand off the stable Library
   ID, ZIP hash/size and series/version to the user/new session.

The host may co-locate these calls with its normal orchestration, subject to tool
STOP rules. There is no daemon, listener or automatic execution after turn commit.
Until a real new photo exercises this entire host path, report implementation and
synthetic protocol validation only, not production automatic archiving.

## Contents, consistency and interruption

The immutable ZIP contains exact current jobs, final records, original save
results, new recovery.json, and a DERIVED SQLite containing exact selected
version-row values. It excludes photo pixels, unrelated series/session cursors
and style collections. Referenced photo bytes remain in Library and are bound
by actual materialization IDs, sizes and full hashes. The source SQLite is opened
read-only and copied with the online backup API, including committed WAL rows;
its full contents are never uploaded. The scoped SQLite is not the original DB.

Checks before/after capture cover the selected rows and evidence bytes, not a
cross-file atomic transaction. Hosts must quiesce the selected series. Existing
identity/content conflicts, changed history, partial publication or stale lock
stop safely; inspect evidence rather than remove locks blindly. Repeated identical
preparation reuses the same ZIP and cannot increment version numbers. Save and
readback responses remain in a separate private journal: a ZIP cannot contain its
own later save receipt. Its stable Library identity is handed off externally.
The journal is not a replacement historical ledger. It is not remotely durable
merely because it was fsynced locally; the ZIP plus handoff identity supports
independent recovery investigation after journal loss.

Read-only inspection can run `checkpoint-inspect` after independent retrieval,
then fetch and hash/decode referenced photographs. `checkpoint-restore` only
extracts into a new private destination with existing conflict/continuation guards.
It DOES NOT relocate historical job paths or make task_history.restore usable at
new paths. Operational version/cursor restoration and revisions at relocated paths
remain a separate, authorized implementation/acceptance step. Never rebuild old
history from the new descriptor, overwrite originals, or claim that extraction is
a completed version-state restore.

## Review gate: loss of local evidence

A missing state.json in an existing operation slot is a reconciliation blocker,
including interruption before first publication. An immutable claim.json prevents
re-arming a pending state after a failed state flush. delivered reports archival
failure separately; the already completed delivery is retained.

Complete local-directory loss is NOT protected by a local marker. Do not recreate
archival state for a previously delivered task, re-register its version or infer a
new upload authorization from an empty folder/search result. The host must first
retrieve the existing stable handoff or other authoritative persistent operation
evidence, and inspect candidates for the same series/version. If that evidence is
missing, stop for investigation; no fresh claim/create is authorized. Absolute
paths participate in this Draft operation digest, so relocation is NOT portable
idempotency. Durable cross-session operation reconciliation remains a real-host
acceptance blocker. This protocol does not claim complete-directory-loss recovery.
