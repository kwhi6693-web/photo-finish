# v1.5.4 maintenance candidate — not published

Base: main `7c760d0329817d38ba1d15988356995afaafe996`; normal six-job main CI run 40845466630 succeeded. PR #30 merged as 194ffd3d4ac64303147e94744b668edd68d06769 and PR #32 as this main base.

Only merged native image delivery and photographic decision/review instructions are included. No new photographic algorithm, dependency, performance work or private data. Performance PRs #16/#31 remain separate. Published v1.5.3 and all older ZIPs/checksums remain immutable.

## Candidate verification

Run sync_public, doctor, publication/history scan, the existing regression suite, and build_release with output `dist/v1.5.4/photo-finish.zip`. This is a release-shaped **unpublished candidate**, with manifest version 1.5.4; the separate `--candidate` development mode intentionally uses 0+candidate and is not the formal artifact.

Run verify_release_preparation without --candidate to compare every allowlisted member to current source, verify exact manifest/checksum, rebuild twice deterministically, and load the extracted package with Python -I. The existing 50 isolated protocol tests exercise image delivery, save/resume, V1/V2 and local-route protection. This is not ChatGPT registration, a new phone save test or a new photographic quality certification. Normal six-job CI includes both current-source development checks and this staged maintenance check.

The original assets/icon.svg must match source bytes and the prior v1.5.3 artifact; no redraw or re-encoding. Candidate metrics are recorded below after actual builds.

## Authorization and remaining release gates

Keep this PR Draft. Preparation is not permission to merge, tag, publish a Release or install. Keep existing v1.5.3 primary and v1.5.1 backup untouched; no private collection, historical photograph or version ledger is accessed or migrated.

After later explicit authorization, review current-head CI and exact source, merge normally, verify resulting main and CI, confirm exact candidate bytes and immutable tag target, then publish the ZIP/checksum and verify downloaded assets. Do not point latest-download links at this unpublished candidate.

Risks: native Save-to-Photos depends on the client; isolated loading does not prove byte-preserving live-host installation. Photographic review is an assistant instruction, not an automatic aesthetic classifier; real new-host adherence remains a live-use observation. No speedup claim or broader reliability certification is made.

## Actual candidate bytes

- Version: 1.5.4; 518,503 bytes, 118 payload members + manifest = 119 total members.
- Full SHA-256: `e7a71c1d817b5a7d44bea078093ce4f86f603ed8d23448c12b537a766ff52c42`.
- Two deterministic rebuilds matched. Isolated loader: 50 checks, zero skips, integrity passed.
- Original SVG: 1210 bytes, SHA-256 `49315dda7125ec5fc77ef5f2b96126d8b2121c6e72944b4702972e90f321d3ee`; source, v1.5.3 and candidate bytes identical.
