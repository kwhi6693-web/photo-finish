# v1.5.1 formal release finalization — approval pending

## Authorized base and scope

PR #19 was merged after exact-head revalidation: head `037a58ab03654873b09e114819da4aa74337a517`, actual merge `1b9e2a47e5d2e75c50e7f24e6a901aa2b7e8e739`. The merge tree equals the tested preparation tree. Its six-matrix CI and 281 regressions passed; staged SHA-256 was rechecked and public history scan found no findings. This independent finalization branch starts at that merged main. No PR #16 code, new product behavior, private data or historical task mutation is included.

## Formal path and protection boundaries

- `dist/photo-finish.zip` and its canonical checksum now hold the already verified v1.5.1 bytes, identical to `dist/v1.5.1/`; no payload regeneration/change is involved in path promotion.
- `dist/v1.5.0/` preserves the exact original ZIP/checksum. `verify_packages.py stable` still pins v1.5.0 tag commit and SHA-256, now checking the historical directory against both tagged ZIP and checksum. Historical tag/Release are never moved or overwritten.
- `verify_packages.py canonical` independently pins the intended v1.5.1 archive hash, exact current-source/manifest/payload mapping, source version, canonical checksum and staged attachment bytes. Coordinated replacement of ZIP/checksum/stage still fails the digest pin. Its scope is `canonical_release_ready_not_published`; it does not claim a new stable Release exists.
- All six CI matrices retain historical protection, development-only 0+candidate builds, canonical deterministic rebuild/install tests and final `git diff --exit-code -- dist`, and add the canonical gate. No gate is skipped or weakened. Existing formal `release`/`published` validation still binds tagged source, canonical installer, manifest, checksum and actual attachment bytes.

Version: **1.5.1**, 498139 bytes, **115 payload files + manifest**. Canonical and staged ZIP SHA-256: `0d929e31f4cf132c9855b933771c0c8fc98ece4702f598aaca759b9444d70608`.

Historical v1.5.0 tag target: `48b7e2bfcbd8a4b111ec3815186c96ef14c807fe`; original ZIP SHA-256: `84fbc42db21d2aa7dc8122152d4390a526761519eb58a212534f4266bd46fb9f`. Published stable/downloads and installed stable remain v1.5.0. README stable badges intentionally stay on v1.5.0 until actual publication.

## Validation and limitations

Local execution on Python 3.12.14 passed **284 regressions**, doctor and public tree/history scans (no findings), historical stable protection, canonical pin/source/manifest gate, development candidate builds and strict read-only verification of actual published v1.5.0 attachments. An isolated virtualenv verified/installed the canonical artifact, reproduced it twice and passed all 34 selected installed tests with zero skips. All 116 installed stable non-cache files and all product runtime Python modules remain unchanged.

Exact-head CI results are recorded in the final PR audit, independently of configuration. The finalization adds three adversarial regressions to the existing 281 checks: staged/source mismatch, coordinated canonical replacement, historical-byte and tag tampering. The isolated install reuses 34 selected existing anonymous checks; these overlap the full suite and are not additional unique product tests. Tests use extracted production modules, synthetic inputs and temporary private roots only. They do not edit/display/save real photographs or rewrite old ledgers.

Isolated Python installation/loading and protocol behavior can be verified; ChatGPT UI registration/reload, automatic host invocation, actual device display and a new remote-save roundtrip are not claimed. Current manual confirmation remains caller evidence with `current_manual_confirmation` / `current_delivery_response` scope, independent of automatic platform observation, persistence and SQLite delivered. No performance improvement, aesthetic expansion or portrait handling is introduced. Existing tool authorization and STOP rules remain effective.

## Final release checklist — requires later explicit approval

1. Approve this finalization PR separately, require all six exact-head CI jobs, then merge only with authorization. Verify the resulting main source/tree and all package gates again. No merge of this PR is authorized now.
2. On the exact approved main commit, stage the canonical ZIP/checksum in a separate attachment directory and verify source/manifest/install/attachment bytes. Explicitly authorize creation of `v1.5.1` pointing to that commit; never move v1.5.0. Run `python tools/verify_packages.py release --tag v1.5.1 --attachments APPROVED_ATTACHMENTS` after tag creation and before publication.
3. Publish only with explicit authorization, attach those exact two files using the existing basenames, use [final Release Notes](RELEASE_NOTES_1_5_1.md), and mark latest only as part of the authorized publication. Then run `published --tag v1.5.1`, read back assets/tag/Release, verify latest download bytes, and update public current-stable notices to the actually published version through reviewed documentation changes. The read-only publication audit is detection, not authorization.
4. Any build mismatch, CI failure, protection regression or privacy risk blocks the corresponding operation. Preserve the original evidence; do not bypass a gate.

## Upgrade and downgrade

Installation/replacement of the live stable Skill is a separate authorization. After publication, verify the final public ZIP against its checksum/manifest, extract to a new directory and install the complete `photo-finish/` directory with bundled runtime. Refresh host discovery and verify the loaded version; GitHub publication alone does not update an installed Skill. Keep photos, styles and session/task roots outside the installation, at the same private paths. No schema migration, old task update, photo resave or version re-registration is required.

For downgrade, use the immutable version-specific v1.5.0 Release ZIP/checksum and verify the original hash above. Restore its complete directory rather than mixing runtime files; keep external private roots unchanged. User-authorized private backup is optional and separate; none is performed here. The older manual response reporting limitation returns on v1.5.0. Do not infer actual host reload from file replacement or synthetic checks.

Approval boundary: final Draft PR only. No v1.5.1 tag, Release, latest-download change or live-install replacement is authorized or performed in this finalization.
