# Changelog


## 1.5.0-rc.1 — 2026-10-25 (unreleased candidate)

- Truthful Chinese stage/recovery/save messages and once-per-conversation-version delivery hints with opt-out.
- Private indexed V1/V2 history, selected-output revisions with inherited protections, verified existing-byte rollback and same-task comparisons.
- Ordered batch status and never-submitted failure recovery; completed/working/unknown tasks are excluded from new rendering.
- Finite keyword synonym expansion, recent/frequent accepted-style use and exact-row metadata cache; no vector-search claim.
- Observed revision/duplicate-render/save/readiness metrics, concise onboarding and explicit screen/print boundaries.
- Existing source bindings, real review, content protection and authoritative save receipts remain mandatory. Host/real-photo acceptance remains a release gate, reported separately.


## 1.4.2 — 2026-10-24

- Add a practical theory reference for tonal organization, color restraint, local separation and visual hierarchy, with approximate tutorial timestamps, official Adobe mechanism references and clearly labeled application reasoning.
- Connect that reference to the skill entrypoint, master standard and synchronized creative/development/professional guides. Decisions use existing direction, reference-scope and actual-review fields; the four daily calls and instruction priority remain.
- Treat low saturation plus high contrast as an optional expression, not a universal preset. Preserve intentional fog, soft light, high/low key and vivid color; do not copy tutorial slider values or judge aesthetics by histogram width.
- Refresh three-language navigation and the deterministic installation package. No new controller behavior, dependency, image service or private media is introduced. Synthetic tests do not certify photographic aesthetics.

## 1.4.1 — 2026-10-24

- Refresh all repository materials: three-language navigation, feature/architecture/operation map, contributor guidance and current security/privacy scope, including the history scanner's file-blob boundary.
- Align optional Lightroom and scene guides, style translation, low-level retrieval descriptions and machine-readable explanatory metadata with the reference-first workflow and current feature method. Numeric presets, XMP compatibility versions and historical release facts remain unchanged.
- Mark earlier design plans as historical, record completed 1.4.0 publication/validation, and rebuild the skill ZIP with synchronized guide/policy hashes.
- No new rendering, management behavior, dependency or service. Existing 209 synthetic regressions remain the verification baseline; each release also verifies its own current-head CI and latest-download artifacts.

## 1.4.0 — 2026-10-24

- **Reference-first direction:** observe the source, read optional global instructions, retrieve and view suitable private references, then lock final direction with submission. The four daily calls remain prepare/submit/returned/review.
- **Optional global guidance:** no instructions means professional photographic autonomy; partial instructions guide the task while unspecified choices remain professional decisions. One-time requests do not rewrite saved rules or preferences.
- **Selection integrity:** direction is bound after actual reference decisions; later query/selection changes are blocked. Invalid direction or unviewed adoption leaves the task unchanged and reserves no tool call.
- **Explicit style requests:** missing keyword/group results and entirely unavailable explicit results report a problem instead of silently using another style or fallback. Automatic empty or unsuitable retrieval still allows professional source-based processing.
- **Compatibility:** prepare.direction becomes a provisional draft. Existing professional-fallback callers can reuse it; adopted/partial reference callers now pass final submit.direction after viewing. Already recorded legacy jobs retain their original interface, subject to the existing current-context checks.
- The first release's creative freedom, content protection, photographic realism, actual visual review and one-final-photo delivery remain. Private library management and backup remain on demand; no new dependency or image service is added.

## 1.3.0 — 2026-10-24

This release includes the 1.1.0 and 1.2.0 features previously available on `main`. Those versions did not have separate GitHub Releases. The original v1.0.0 release remains historical.

- **Personal style management:** edit names, labels and notes; organize groups, pin references, filter and paginate results. Restrict reference use to light, color, material, composition or atmosphere without changing the original image bytes.
- **Scene rules and preferences:** create scoped rules, enable or disable entries, surface explicitly structured setting conflicts, and undo up to twenty changes. Current-task instructions retain priority. Full profile reset clears rule history while preserving style photographs.
- **Private backup and recovery:** export, inspect and import photographs, metadata, settings and history. Imports validate names, formats, sizes and hashes before writing; default merges preserve existing values. Private ZIPs are unencrypted and are separate from public installation packages.
- **Platform reliability:** canonicalize temporary-directory aliases on Windows and macOS during backup staging, with a regression test.
- **Distribution:** English, Simplified Chinese and Traditional Chinese release/download entrypoints, a versioned installable ZIP, SHA-256 checksum and maintainer release instructions.

Validation: 196 local synthetic tests passed; the feature revision also passed the six-job GitHub Actions matrix across Linux, Windows and macOS. Documentation-only release preparation is validated separately by its PR checks. These tests cover workflow, persistence, security boundaries and packaging; they do not demonstrate real-photo aesthetics or actual image-service execution.

### Upgrade from 1.0.0 or an earlier main checkout

Install the new `photo-finish/` directory in your host's skill location, retaining its bundled `runtime/`. Updating GitHub alone does not update an already installed skill. Existing private catalogs remain readable and stay outside the skill installation and Git checkout. Keep the same private storage location; before moving hosts, use the [private backup workflow](references/private-backup.md). Existing jobs retain their recorded snapshots.

## 1.2.0 — 2026-10-24 (main only)

- Save, view, partially replace and clear private editing rules and aesthetic preferences.
- Bind each edit to a current profile acknowledgment and stable task snapshot, while allowing one-time instructions without rewriting the saved profile.
- Nine profile regressions brought the synthetic suite to 179 tests.

## 1.1.0 — 2026-10-24 (main only)

- Explicitly collect favorite photographs with names, labels and notes in a private local style library.
- Preserve exact source bytes, deduplicate by SHA-256, retrieve by keyword or ID, remove saved copies and supply up to three suitable candidates to the main editing workflow.
- Fourteen library regressions brought the synthetic suite to 170 tests. Correct source-mode ICC handling and failed-write cleanup are included.

## 1.0.0 — 2026-10-23

- Initial public Agent Skill: photographic direction, composition, light/color treatment, local retouching, observed review and one-final-photo delivery.
- Bundled controller/runtime, empty public reference index, three-language README, MIT license and deterministic installation package.
- Initial publication validation: 138 synthetic tests and cross-platform CI. Later main-branch maintenance is included in 1.3.0; it does not alter the historical v1.0.0 tag.
