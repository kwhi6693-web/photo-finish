# Validation scope

Public release: **1.0.0**, derived from workflow revision **2026-10-23.4** with a self-contained runtime and no private reference corpus.

The release gates are a read-only doctor, publication scan, synthetic regression suite, deterministic ZIP comparison and clean extraction. Local command results and GitHub Actions results are distinct evidence. CI configuration alone does not mean another operating system has passed.

## Local release checks — 2026-10-23

Linux, Python 3.12.14 and Pillow 12.3.0: **138 synthetic protocol, security and package tests passed** on the final source revision. Read-only doctor and publication scan passed. Three additional synthetic optional numeric-planning requests (A/H/I, J and L) completed; these are planning checks, not photograph rendering.

An independent fresh-environment check installed Pillow, verified the checkout, and extracted the exact final runtime ZIP into a different temporary directory. All 97 manifest hashes matched; relocated doctor and synthetic prepare passed with zero references and no Library dependency. The runtime archive contains 98 entries and is 403,223 bytes. Its checksum is published in `dist/photo-finish.zip.sha256`.

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
