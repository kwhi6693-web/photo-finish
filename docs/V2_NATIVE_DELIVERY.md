# V2 explicit acceptance and immutable V1 delivery

The existing `v2_native_entry` has three additional explicit commands:

- `accept-photo ORIGINAL CANDIDATE PROVENANCE.json USER_REVIEW.json ACCEPTED.json`
- `register-v1 ACCEPTED.json SAVE.json READBACK.json READBACK.png LIBRARY_FILE_ID V1.json`
- `restore-v1 V1.json EXPECTED_VERSION_SHA256 READBACK.json READBACK.png`

Run through `scripts/run_photo_finish.py v2_native_entry`. Every JSON output is exclusive; existing histories, source images and installed runtimes are never migrated or overwritten. These are isolated immutable V1 records, not replacements for the mature legacy task-history database or a multi-version cursor implementation.

Acceptance binds the actual source/output hashes to an explicit end-user final GO and its retained decision reference. It records user authority, never independent third-party approval. Provenance must declare `pr47_native_controller` with its exact pending controller receipt, or `external_non_generative`. An external accepted photo remains external: it cannot pass the native renderer E2E gate. Actual fidelity audits remain separate and mandatory; acceptance does not infer scene similarity from a hash or a reviewer flag.

Registration requires the trusted host's real save response and independently materialized same-ID/same-byte PNG. Pass original host JSON unchanged, not a hand-written receipt. Readback transfers must contain `library_file_id`, absolute `workspace_path`, and `workspace_sha256` (or `sha256`). Host JSON is an evidence boundary, not a cryptographic service signature. Record and retain the V1 record hash outside the process before recovery.

Restore only verifies and returns the independently retrieved original PNG. It performs no render, image save, upload, ledger mutation, or legacy cursor update. A new subprocess demonstrates process isolation only; genuine independent cross-conversation retrieval still requires a separate conversation and retained Library identifiers/hash. The controller never changes that gate to passed by itself. iPhone Photos confirmation remains separate and false until actually observed.

These interfaces do not unlock WP5, waive different-category requirements, change old pixel locks, or authorize merge, release or installation. Synthetic regressions verify evidence binding and refusals, not real host delivery or photography.

Signed-URL materializations are also supported without rewriting the original host JSON: the official materializer must preserve local Library identity/version extended attributes, the response must include the same storage version and byte length, and the image must match the accepted/V1 full SHA-256 and complete metadata. Missing or unsupported identity attributes fail closed. This is trusted host/materializer evidence, not a service signature. The workspace-placement route still requires its original host digest. No URL is fetched by the controller.
