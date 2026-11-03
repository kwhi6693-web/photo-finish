# Contributing

Keep the default edit path short and the photographic direction strong. Preserve composition freedom, visible-source lettering consistency, natural photographic detail and final-photo-only delivery.

1. Make focused changes and update the corresponding canonical policy or guide. Keep reference retrieval and actual reference selection before final photographic direction. Optional global instructions guide the task; unspecified choices use professional judgment.
2. Run `python tools/sync_public.py` after intentional policy/guide changes. Never rebuild reference data as part of an ordinary edit.
3. Run `python tools/doctor.py`, `python tools/run_tests.py` and `python tools/check_publication.py --history`.
4. Build the release twice and compare SHA-256 checksums. Run the full suite in the repository checkout; the curated installation ZIP excludes repository tests and the test runner. Verify that a clean extraction passes its bundled doctor and representative synthetic controller calls.
5. Describe actual test scope. Synthetic fixtures do not demonstrate real-photo aesthetics, color calibration, identity preservation or durable host saving.

Use synthetic fixtures created inside temporary directories. Do not commit photographs, names from private datasets, Library identifiers, machine paths, signed URLs, credentials, job files or runtime caches. Keep new dependencies optional unless needed by the daily controller. Do not use generated pass/fail values as substitutes for actual visual inspection.

Current development requires Python 3.11+ and Pillow 13.0.0+ for October 2026 security fixes. Historical release environments retain their documented requirements; do not downgrade the current security floor to retain Python 3.10. Do not raise a lower bound only because a release is newer when the current range already admits it. Validate the core and optional analysis profiles. When packaged inputs change, build and verify candidates in fresh external destinations; stage an approved new version only through the [release procedure](docs/releasing.md). Never overwrite the historical canonical `dist/photo-finish.zip`, its checksum, or any published version directory. Keep the reproducibility check enabled.

For documentation changes, inspect all three READMEs, canonical runtime guides and generated reference mirrors, the [architecture map](docs/architecture.md), [security audit](docs/security-audit.md), [validation evidence](docs/validation.md) and [changelog](CHANGELOG.md). Preserve historical version facts; mark old design records as historical instead of presenting them as current interfaces. Check relative links throughout the tree. Never change a published tag or historical release attachment to disguise a new package; follow the [release procedure](docs/releasing.md).
