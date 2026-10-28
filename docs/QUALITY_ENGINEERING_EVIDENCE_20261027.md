# Quality engineering evidence — 2026-10-27

Base: immutable v1.5.1, commit 1020cc0a2ff7d18e681fb2f201614adcd8f47cb3. Development only; no installation, historical-data recovery, merge, tag or release.

## Completed checks

- Baseline: 284 synthetic tests passed in 11.782s.
- Development gate RED: three new tests failed because the immutable-release/development-install separation was missing.
- GREEN: three new gate tests passed. Full suite 287 tests passed in 18.857s.
- The released gate pins v1.5.1 tag commit and digest, compares canonical/staged attachments against the tagged payload and manifest, and rejects tag movement or changed artifacts. Formal current-source canonical/release gates remain unchanged.
- Current development source is built twice outside the repository as explicitly `0+candidate`, checked against exact current-source payload hashes, and loaded in isolation using existing anonymous installed-protocol tests. No dist file is rebuilt or replaced.

Ruling: retain source runtime version 1.5.1 while building only explicit non-release candidates; a new version number and installed Skill upgrade are not authorized or useful yet.

## Local revision boundary

- RED: six new test methods ran; ten subcase/assertion failures exposed missing/blank/nontext mask submissions, unknown local editors, low-level full-frame begin and unmasked next-step reservation/state mutation. Masked native parameter binding and non-local editing already passed.
- GREEN: all 20 local-route/version tests passed after moving the guard to the shared adapter. The parent/output/job bytes are checked unchanged on rejected calls.
- First full development suite: 293 tests, two errors in the historical finalization fixture, which incorrectly used changed current source as the immutable v1.5.1 fixture. Updated that fixture to read the tagged source; source-mismatch/tamper rejection assertions remain in place. Full suite then passed: 293 tests, 19.361s.
- Doctor passed; immutable v1.5.1 gate passed. Current candidate built identically twice, SHA-256 fcd2cccf0688ec986aed29fd243e50e09aa2969d5c7bd42f8621daa24599283a; all 115 payloads checked. Isolated installation ran 40 tests, zero skips, using only extracted production modules.
- Parameter presence is not actual mask-source/edge verification. No photograph was edited, viewed as a new result, saved or registered. No measured photographic improvement or speedup is claimed.

Ruling: allow only the documented Adobe native adjustment adapter names for local revisions for now; unsupported local tools stop safely until their real capability and parameter contract are reviewed. Non-local native/global workflows remain available.

## Audit and final local verification

- Nine-concern audit, real-tool schema boundaries and five-scene quality matrix: QUALITY_AUDIT_20261027.md. Current three-language stable notices now identify the already-published v1.5.1 and label this branch unshipped; dated historical evidence is unchanged.
- Final local full suite: 293 tests passed, 18.395s. This duration is test runtime, not product latency. Doctor passed. Publication/history scan passed: 198 files and 778 historical blobs, zero findings under the scanner's stated pattern/class scope.
- Frozen v1.5.0 and immutable v1.5.1 source/artifact gates passed. git diff against the baseline shows no dist changes. No installed Skill, old task, private library or PR #16 file was modified.
- Remote checkpoint commits: a1e7bcc1fd84e61f9f393bd6b5d1a0e680b346ee (development gates), 5ec58ccdd0e36cc8f233b0b478f78e49d786c798 (local route guard). Their published Git tree matches the corresponding tested local tree exactly. Review remains Draft in PR #21.

## Pending

Exact-final-head six-matrix CI results are recorded in Draft PR #21 to avoid making a documentation-only commit recursively invalidate its own CI claim. All new real-photo quality/performance measurements remain unmeasured. Historical evidence is cited by public audit document, not copied from private ledgers. No new device display, photo-only trigger, remote-save or provider-outage certification is claimed.

## Independent whole-branch review and correction

A fresh reviewer inspected baseline→development source and the five-scene audit without private data. It independently ran 23 targeted tests and the immutable v1.5.1 gate, all passed. It found one existing P1 reservation inconsistency: known full-frame generation could be labelled native_preserved/local_excluded on a non-local exact_content task. No accepted damaged image was demonstrated.

The fix pass first reproduced four failing subcases across non-local preserved strategies, the low-level exact-content route without a plan and next-step route switching. The shared adapter now rejects those combinations before reservation. Tests preserve semantic-comparison and unprotected creative generation. The review's two coverage gaps were also closed with actual nested-options.maskURI and successful masked next-step/latest-output/parent-provenance cases. No rendering, photo saving or historical mutation occurred.

The first fix-pass run still reported two failures plus one nested installed-suite error: one assertion expected the older local-route message after the stricter fidelity guard rejected correctly; the new non-local next-step fixture had no preservation target/plan and therefore did not exercise its named condition. Established an explicit exact lettering/native-preserved contract in that fixture and accepted either appropriate rejection category in the local test. No guard was relaxed. Final targeted local/fidelity suite: **13 tests passed**. Final full suite: **300 tests passed in 22.052s**. The new 47-test extracted-candidate smoke suite is a subset/overlap, not 47 additional unique product tests.

Final current-source candidate: two identical builds, 115 payload files, manifest `0+candidate`, SHA-256 `ce08cf695121176d71c8201f82a6425e6a36a758ae3fc52be2e41ff113827744`; extracted production modules only, 47 protocol tests passed, zero skips. This archive is neither a release nor a live installation. The earlier candidate digest above belongs to its earlier source checkpoint.

Review disposition: P1 compatibility hole fixed in the single RED→GREEN pass; both reported P3 coverage gaps covered. No unresolved reviewer finding. No new visual or latency pass is implied. The known-mask URL still requires actual source/mask/final-image review. No further architectural work or performance optimization was justified.
