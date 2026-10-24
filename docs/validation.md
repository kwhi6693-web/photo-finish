# Validation scope

Feature package: **1.3.0**, derived from workflow revision **2026-10-24.2** with a self-contained runtime and no private reference corpus.

The release gates are a read-only doctor, publication scan, synthetic regression suite, deterministic ZIP comparison and clean extraction. Local command results and GitHub Actions results are distinct evidence. CI configuration alone does not mean another operating system has passed.

The 1.3.0 feature commit `3c4956ba640cf134b42c5ca88e3806a5bcf60207` passed all six [main-branch matrix jobs](https://github.com/kwhi6693-web/photo-finish/actions/runs/40074715368) on Linux/Python 3.10 and 3.12, Windows/Python 3.12 and macOS/Python 3.12, including both optional-analysis jobs. Formal release preparation adds download entrypoints and documentation without changing the packaged runtime. See the [changelog](../CHANGELOG.md) and [release procedure](releasing.md).

## Personal management and portability — 2026-10-24

Version 1.3.0 adds partial style metadata edits, groups, pins, component scopes and paginated retrieval; observed-scene rules, enabled states, explicit setting conflict checks and a twenty-change undo history; and private versioned export/inspect/import. Legacy catalogs remain readable. Private backups are separate from public installation archives, and default imports preserve existing values.

Local Linux / Python 3.12.14 / Pillow 12.3.0: **196 synthetic tests passed**, including seventeen management/backup regressions. These exercise immutable photograph bytes, metadata stale-write rejection, group/purpose selection, scene acknowledgment, conflicts and current-task overrides, undo/reset, complete restoration and safe merge, archive checksum binding, malformed metadata, path traversal/symlinks/duplicates/future versions, export size boundaries, native SQLite failure rollback and canonical temporary-directory aliases. The alias regression reproduces the temporary path issue detected by Windows/macOS CI without weakening archive confinement. The normal release gates also validate source-only packaging and clean extraction. These are protocol/security tests, not proof of photographic aesthetics.

An independent actual-command trial exercised the documented grouping/rules/backup workflow using synthetic fixtures, including fresh-root restoration, conflict-preserving merge, cleared settings, hostile/corrupt archives and database-write rollback. Platform CI is tracked separately from local evidence.

## Custom instructions and preferences — 2026-10-24

Users can explicitly save, inspect, partially replace and clear their own photographic rules/preferences through the main controller. The private profile shares the existing catalog/root; photographs are preserved when the profile is reset. No new dependency, service or user configuration enters the public package.

Local Linux / Python 3.12.14 / Pillow 12.3.0: **179 synthetic tests passed**, including nine profile regressions. They cover fresh-process Unicode persistence, consent and input boundaries, independent roots, partial updates/clearing, photo preservation, unsupported profile rollback, missing/stale read acknowledgment, per-task instructions stable in-flight snapshots, and clearing old text from current SQLite pages. secure_delete does not certify physical erasure or remove separate job snapshots/backups. Current instructions have documented priority; the controller stores context and does not claim to semantically certify compliance with free-text preferences. An independent documented-CLI trial also verified cross-process save/read, a one-time monochrome direction over a saved color preference, missing/stale profile rejection, partial changes, single-rule removal and reset preserving the photo collection and existing job snapshot. No image service was called. Local and CI results remain separate evidence.

## Personal style library — 2026-10-24

The optional private collection is part of `photo_edit.py`: explicit collection, exact-byte SHA256 deduplication, keyword/ID retrieval, removal and automatic prepare candidates. It adds SQLite from the standard library, reuses Pillow and the existing selection/review gates, and includes no image service or private photographs.

Local Linux / Python 3.12.14 / Pillow 12.3.0: **170 synthetic tests passed**, including fourteen private-library regressions and an adopted-reference submit/returned/review protocol. Tests isolate the collection root from developer data. Profiled non-RGB references preserve their source color mode for ICC analysis; invalid profiles fail before collection writes. Conflicting ID/keyword selectors fail explicitly. A native SQLite page-quota failure removes newly created unindexed copies while preserving preexisting files. The doctor, skill frontmatter validation and publication/history scan passed; deterministic package builds and relocated extraction are exercised by package tests.

A separate agent exercised the documented CLI in isolated temporary storage: thirteen management calls and seven prepare calls verified fresh-process persistence, byte identity, duplicate handling, name/label/note search, automatic/query/ID retrieval, empty fallback, root isolation, explicit missing-ID errors and source-preserving deletion. This does not certify real photograph aesthetics, actual cloud rendering, host durability or cross-device synchronization. Platform CI results are reported separately from local checks.

## Public profile scope — 2026-10-24

This public package uses general-purpose photographic direction. Personal aesthetic priorities belong to a private profile and are excluded from the public policy, entrypoints and installation archive. The delivery-safety fixes are retained.

## Targeted fixes — 2026-10-24

Non-overwriting URL acquisition (including races and symlinks), decoded-format/suffix validation, and per-local-reference SHA256/role binding are covered by offline regressions. Reference changes are checked at result handling and final acceptance. Source-material fidelity and localized feedback methods are integrated. No new cloud render, approval, dependency or daily stage is introduced. Local Linux/Python 3.12 verification: 156 public synthetic tests passed. Fifteen targeted safety tests include destination races, mismatched suffixes, symlink retargeting, immutable submission recipes, current-step receipts and local refinement lineage. A deterministic clean extraction is exercised by the package tests. Windows/macOS results are recorded by the new PR CI, not inferred from this local run. The v1.0.0 tag remains historical.

## Historical local release checks — 2026-10-23

Linux, Python 3.12.14 and Pillow 12.3.0: **138 synthetic protocol, security and package tests passed** on the initial publication source revision. Read-only doctor and publication scan passed. Three additional synthetic optional numeric-planning requests (A/H/I, J and L) completed; these are planning checks, not photograph rendering.

An independent fresh-environment check installed Pillow, verified the checkout, and extracted the exact final runtime ZIP into a different temporary directory. All 97 manifest hashes matched; relocated doctor and synthetic prepare passed with zero references and no Library dependency. The initial v1.0.0 runtime archive contains 98 entries and is 403,223 bytes. The current main-branch checksum is published in `dist/photo-finish.zip.sha256`.

The first GitHub Actions run passed Linux/Python 3.10 and 3.12, and identified a Windows default-text-encoding failure plus a macOS temporary-path-alias assertion. The public code now uses explicit UTF-8 file and subprocess text I/O, UTF-8 JSON CLI streams and LF writes; the read-count test compares resolved paths. A regression also starts the JSON CLI with an ASCII stdio default and verifies non-ASCII image/job paths. The corrected matrix results are recorded by the latest linked [Validate skill workflow](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml). Public-history scanning also passed after the initial commit (112 historical blobs); every subsequent CI run scans the actual current history again.

## Contract coverage

- Source/context hashes, stale configuration and policy mirrors.
- Empty-library professional fallback without fabricated references.
- Explicit per-target preservation strategy and protected region scope.
- No weakening of locked exact-content constraints at acceptance.
- Atomic rollback for invalid submissions and incomplete review events.
- Formal-file identity and hash-bound decode reuse.
- Color declarations, bounded screen assumptions and invalid/conflicting metadata.
- Separate presentation, quality acceptance and durable-save evidence.
- Deduplicated measured timing, image revisions and validation failures.
- Private-data/credential/path checks and archive traversal/symlink rejection.
- Restored controller bootstrap without personal media or remote Library access.

## Evidence limits

Tests use locally generated geometric images and synthetic review statements to exercise controller contracts. They are not photographic portfolios and do not demonstrate real-world quality, actual cloud-tool execution, calibrated color, print readiness or full-scene success rates. This publication task does not regenerate or publish private user photographs. Earlier private real-image experiments are not included or claimed as reproducible public evidence.

Quality on a new photograph depends on the host image tool and the agent's actual inspection. Unavailable capabilities stay unavailable; a field validator cannot certify an aesthetic result or recover detail lost in the source.

## Dependency maintenance — 2026-10-23

The main branch permits Pillow `>=12.3,<14`; pip respects package `Requires-Python` metadata instead of forcing Pillow 13 onto Python 3.10. Clean resolution selected Pillow 12.3.0 for Python 3.10 and 13.0.0 for Python 3.12. The existing 138-test suite also passed locally with Pillow 12.3.0 after the dependency change. A new isolated Python 3.12.14 environment installed Pillow 13.0.0, NumPy 2.5.4 and SciPy 1.18.1; `pip check`, doctor, all 138 tests and the numerical smoke check passed.

CI retains the four core platform/interpreter jobs and adds optional-analysis jobs on Linux/Python 3.10 and 3.12. These install `requirements-analysis.txt`, run `pip check`, exercise the actual color measurement, palette and perceptual-hash functions on a synthetic fixture, and run the full suite and archive checks. The linked workflow records the actual outcomes; configuration is not a claim that a pending run has passed.

NumPy and SciPy remain optional with broad compatible ranges. Dependabot uses `increase-if-necessary` to avoid raising a minimum solely because the current range already admits a newer release. Dependency PRs must include rebuilt archives and checksums when packaged inputs change. The tagged v1.0.0 release remains immutable; main-branch maintenance is separate from that published snapshot.
