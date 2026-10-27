# Quality engineering evidence — 2026-10-27

Base: immutable v1.5.1, commit 1020cc0a2ff7d18e681fb2f201614adcd8f47cb3. Development only; no installation, historical-data recovery, merge, tag or release.

## Completed checks

- Baseline: 284 synthetic tests passed in 11.782s.
- Development gate RED: three new tests failed because the immutable-release/development-install separation was missing.
- GREEN: three new gate tests passed. Full suite 287 tests passed in 18.857s.
- The released gate pins v1.5.1 tag commit and digest, compares canonical/staged attachments against the tagged payload and manifest, and rejects tag movement or changed artifacts. Formal current-source canonical/release gates remain unchanged.
- Current development source is built twice outside the repository as explicitly `0+candidate`, checked against exact current-source payload hashes, and loaded in isolation using existing anonymous installed-protocol tests. No dist file is rebuilt or replaced.

Ruling: retain source runtime version 1.5.1 while building only explicit non-release candidates; a new version number and installed Skill upgrade are not authorized or useful yet.

## Pending

Adapter local-route RED/GREEN; final suite, doctor/publication/history/candidate checks; six-matrix CI; whole-branch review; scene audit. All new real-photo quality/performance measurements remain unmeasured. Historical evidence is cited by public audit document, not copied from private ledgers.
