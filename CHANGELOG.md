# Changelog

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
