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

## Pending

Final publication/history checks; six-matrix CI; whole-branch review; scene audit. All new real-photo quality/performance measurements remain unmeasured. Historical evidence is cited by public audit document, not copied from private ledgers.
