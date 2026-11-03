# v1.5.6 candidate — historical preparation record

> **Publication update (2026-11-03):** This candidate was later merged through [PR #39](https://github.com/kwhi6693-web/photo-finish/pull/39), with a test-only follow-up [PR #40](https://github.com/kwhi6693-web/photo-finish/pull/40), and [released as v1.5.6](https://github.com/kwhi6693-web/photo-finish/releases/tag/v1.5.6). Final main commit: `565acdcb6be97f999ee02468c06035de992c5489`; [all six main CI jobs passed](https://github.com/kwhi6693-web/photo-finish/actions/runs/41606559987). The pre-release instructions and remaining-gate statements below are preserved as dated evidence, not current publication status. Personal Skill installation and live-provider/photographic acceptance are separate and are not certified by publication.

Base: main `027c8e6d8c25fa117454edd4294b29185f30c707`. This candidate consolidates the four-layer photographic workflow, optional style catalog and photo-only successful delivery, and addresses the prepublication security review. It does not install or publish the candidate.

## Changes and compatibility

- Require Python 3.11+ and Pillow 13.0.0+; Python 3.10 support is intentionally dropped to avoid the vulnerable Pillow 12.x line. Optional analysis retains NumPy/SciPy.
- Provider downloads accept HTTPS/443 without embedded credentials, require every resolved address to be public, pin checked IPs while retaining TLS hostname verification, and recheck at most five redirects. Approved-address fallback shares the original deadline. Ambient proxies are disabled because they bypass checked-IP dialing.
- Reject oversized advertised bodies and enforce a 64 MiB streaming limit. An absolute socket-shutdown watchdog covers TLS, headers, body and chunk framing; temporary files are cleaned and existing destinations remain protected. OS DNS resolution cannot be forcibly interrupted by this watchdog.
- Preserve personal reference-library retrieval, autonomous composition/color choices, content protection, visual review, real save receipts and internal version records. Successful delivery displays the accepted final photo without unsolicited status text.
- Treat the 25-style catalog as project-authored photographic guidance. It is neither Apple presets nor proof of exact iPhone 18 Pro completeness, all-style execution or all-style visual acceptance. Unsupported requested textures remain explicit blockers.
- Read release versions from synchronized runtime metadata, and stage only a new version directory. Historical archives, checksums, tags and the current personal installation remain unchanged.

## Local evidence (2026-11-03)

Linux / Python 3.12.14 / Pillow 13.0.0. Core regression checks passed before installing the optional profile; final full suite with NumPy 2.5.4 and SciPy 1.18.1: **356 tests passed**. `pip check`, doctor and actual color-measurement/palette/perceptual-hash smoke checks passed. No image service was invoked.

Thirteen acquisition-hardening regressions include unsafe URL/DNS rejection, pinned addressing and fallback, redirect cleanup/revalidation/limits, body limits, deadline cleanup and real HTTPResponse parsing of slow headers/chunk trailers over an offline socket pair. TLS is mocked in these drip fixtures; they are not a live TLS/provider compatibility result. Independent read-only engineering review found no remaining actionable issue in the revised download/dependency/release code; that review is not a universal security guarantee.

- New archive: `dist/v1.5.6/photo-finish.zip`, **532,853 bytes**, 119 payload files plus generated manifest = 120 entries.
- SHA-256: `d6737d8634e65c56d476d745e38fd4a2f2f04c4e86c6a9a5efb2919c4f35e6e3`.
- Staged source/member/manifest/checksum verification and two raw-byte-identical rebuilds passed. Relocated isolated installation: 50 checks, zero skips, extracted-package production modules only.
- Separate nonrelease candidate builds passed deterministic mapping checks. Frozen v1.5.0/v1.5.1 guards and v1.5.4 tagged-source installation checks passed. All twelve pre-existing dist files matched the base commit byte for byte.
- Current-tree and reachable-history publication scans passed; the final upload scan records its own actual file/blob counts. Scanning detects known patterns and private-media classes, not every possible secret. Private photographs, signed URLs, collections and ledgers are excluded.

## Remaining gates

The six-job CI matrix covers Linux/Python 3.11 and 3.12, Windows/Python 3.12, macOS/Python 3.12 and the two Linux optional-analysis profiles. Configuration is not evidence of execution: inspect results at the exact final PR head before merge.

Live provider acquisition remains unverified under the new network constraints: the local environment did not provide direct public DNS connectivity, and the downloader deliberately does not fall back to a proxy. Actual ChatGPT materialization, automatic triggering, native final-photo display, saving behavior and visual acceptance of the 25 style definitions need separately scoped host/photo evidence. This candidate does not rerun photographic edits or migrate private data.

Keep the PR Draft. Merge, tagging, publishing release assets and replacing the live installation require the next explicit authorization. The latest-release download links continue to point to the existing stable release.
