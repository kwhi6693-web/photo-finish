# Contributing

Keep the default edit path short and the photographic direction strong. Preserve composition freedom, visible-source lettering consistency, natural photographic detail and final-photo-only delivery.

1. Make focused changes and update the corresponding canonical policy or guide.
2. Run `python tools/sync_public.py` after intentional policy/guide changes. Never rebuild reference data as part of an ordinary edit.
3. Run `python tools/doctor.py`, `python tools/run_tests.py` and `python tools/check_publication.py --history`.
4. Build the release twice and compare SHA-256 checksums. Verify that a clean extraction passes the doctor and tests.
5. Describe actual test scope. Synthetic fixtures do not demonstrate real-photo aesthetics, color calibration, identity preservation or durable host saving.

Use synthetic fixtures created inside temporary directories. Do not commit photographs, names from private datasets, Library identifiers, machine paths, signed URLs, credentials, job files or runtime caches. Keep new dependencies optional unless needed by the daily controller. Do not use generated pass/fail values as substitutes for actual visual inspection.

Dependency updates must retain Python 3.10 support unless a deliberate compatibility change is documented. Do not raise a lower bound only because a release is newer when the current range already admits it. Validate the core and optional analysis profiles, and rebuild `dist/photo-finish.zip` plus its checksum in the same PR when packaged inputs change. Keep the reproducibility check enabled.
