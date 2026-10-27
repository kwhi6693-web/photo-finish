# Frozen stable release and development candidate validation

This CI change is independent of the manual-display product repair in PR #17. No stable tag, published asset, tracked ZIP/checksum, installed skill or private task is modified. No photo operations or performance analysis are performed.

## A. Frozen stable protection

Every existing six-matrix validation job runs `python tools/verify_packages.py stable`.

- `refs/tags/v1.5.0` must still resolve to `48b7e2bfcbd8a4b111ec3815186c96ef14c807fe`.
- The working-tree stable ZIP must match the pinned SHA-256 `84fbc42db21d2aa7dc8122152d4390a526761519eb58a212534f4266bd46fb9f`; the checksum file must contain the exact canonical digest and filename. Updating both files cannot legitimize a replacement. Artifact symlinks are rejected.
- ZIP bytes must equal the tagged artifact. Its 115 payload entries, exact source bytes, manifest hashes, package/version identity and archive safety must match source read from that immutable commit, not today's development tree.
- The existing final `git diff --exit-code -- dist` remains in CI. No step writes into dist.

This is stronger than comparing a newly rebuilt development ZIP with a historical stable ZIP: it independently binds the protected artifact to its published source and immutable digest.

## B. Development candidate verification

Every matrix also runs `python tools/verify_packages.py candidate`.

- Scan the current public source tree; build twice in separate temporary directories outside the repository; reject a candidate output destination within the repository before writing.
- Candidate manifest identity is `version=0+candidate`, `distribution_channel=candidate`. It is not an install/release claim for formal 1.5.0.
- Compare complete ZIP entry sets with the allowlisted current source; validate exact payload bytes, all manifest hashes, generated checksums, archive safety/publication checks and identical bytes across the two builds.
- Do not duplicate-count or skip existing product/protocol tests, doctor, public/history scans or Windows-specific regressions. Temporary build outputs are discarded and are not uploaded as Release assets.

The formal builder's default output and stable manifest format remain byte-compatible; candidate mode is explicit. This change does not bump a product version or authorize release.

## Formal release gate is separate and strict

`python tools/verify_packages.py release --tag v1.5.0 --attachments STAGED_ATTACHMENTS` verifies tagged source, runtime version, manifest, tagged installer/checksum and the actual staged attachment files byte-for-byte. A candidate manifest cannot pass this formal gate. Future formal versions require their own explicitly reviewed version/tag/package changes; this PR does not manufacture them.

`python tools/verify_packages.py published --tag v1.5.0` downloads the public Release installer and checksum to a temporary directory and applies that same gate. The separate read-only `Audit published release` workflow invokes it for a published Release, using the checker from main and source/artifacts from the named version tag. It has only contents-read permission, never creates/releases/replaces assets and does not replace the pre-publication gate. Network, missing assets or mismatches fail closed.

## Executed local evidence

- Candidate-mode test first failed on the old builder; seven focused regressions now pass.
- Real source mutation in an anonymous temporary project passes candidate checks while its previously built stable fixture remains byte-identical.
- Illegal ZIP-only, checksum-only and coordinated ZIP+checksum replacements are rejected. Missing/extra/changed payloads, wrong manifest hashes/version/channel, private media, unsafe archives, changed actual attachments and nondeterministic ZIP metadata are rejected.
- The actual stable source/manifest/ZIP check passes with 115 payload files; two independent current-source candidate builds pass.
- The existing public v1.5.0 Release assets were actually downloaded read-only and verified against the pinned tagged source/installer, not just trusted from metadata.
- Full local suite and six remote matrix outcomes are recorded in the PR comments after their actual completion. Formal published-event workflow dispatch is not simulated by creating or re-publishing a Release.

## Merge dependencies

The CI strategy PR targets main and contains only packaging/CI/tests/documentation. PR #17 can temporarily target this CI branch so its diff remains only the product fix/tests/evidence, while remote validation tests the combined tree. After approval: merge the CI strategy first, retarget/update PR #17 onto main, verify its final head again, then consider product merge. No PR is merged, no tag created and no version published by this work.
