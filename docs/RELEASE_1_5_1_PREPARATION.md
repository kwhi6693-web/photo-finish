# v1.5.1 maintenance release preparation

Historical preparation/design record. The current authorized path transition and protection policy are described in [v1.5.1 finalization](RELEASE_1_5_1_FINALIZATION.md); earlier canonical-path statements below refer to the preparation stage.

Status: unpublished, Draft PR review only. Merge, tag creation, Release publication and live installed-skill replacement require separate approval.

## Scope

Base main: `3661f50528c4e7a6595ba907a5d65a48efaaa55c`. Only merged PR #17 manual display response and PR #18 package validation boundaries are included. PR #16 stays Draft and excluded. Non-portrait scope, STOP rules, authorization, real review, source protection and private data isolation remain unchanged.

A current explicit `presented=True` confirmation reaches the experience layer and returns `display_observed=true`, source `current_manual_confirmation`, scope `current_delivery_response`. Automatic platform observation, manual confirmation, actual persistence and SQLite delivered are independent. Saved bytes, a URL or delivered=1 never imply presentation. Confirmation is caller evidence, not a device-render certificate. Historical ledgers are not migrated.

## Package and evidence

The frozen `dist/photo-finish.zip` remains v1.5.0. Staged **unpublished** v1.5.1 bytes are under `dist/v1.5.1/`, with the eventual attachment basenames. Its manifest version identifies intended content, not a published Release. Development CI also retains separate `0+candidate` builds in external temporary directories. The builder obtains the intended manifest version from SESSION_BRIEF rather than an independent stale constant.

`python tools/verify_release_preparation.py` checks all installation version fields, exact allowlist, manifest and payload hashes, safe/public contents, canonical checksum, two independent external builds against staged bytes, and isolated extraction/loading. It runs existing anonymous manual-display, version/restore, save/recovery, fault/permission and experience regressions using only extracted production modules. This is a fresh temporary Python install/load, not ChatGPT UI registration, automatic host invocation, real photograph editing, device rendering or remote-save certification. No active installed skill is replaced.

Executed local evidence on Python 3.12.14: all 281 regressions passed (278 existing + 3 preparation failures/version tests). A newly created virtualenv installed requirements from scratch (Pillow 13.0.0; pip check clean). That environment verified the staged package twice, installed/loaded its exact payload, and passed all 34 selected anonymous regressions with zero skips. `doctor`, public tree/history scan (no findings), frozen-stable guard and isolated development-candidate gate passed. The installed stable baseline contains 116 non-cache files; their exact hash map is unchanged. Runtime product modules `experience.py`, `task_history.py` and `delivery_adapter.py` are byte-identical to base main.

Staged v1.5.1 ZIP: 498139 bytes, 115 payload files plus manifest; SHA-256 `0d929e31f4cf132c9855b933771c0c8fc98ece4702f598aaca759b9444d70608`. Manifest, runtime/distribution metadata and all file hashes agree. Development-only 0+candidate SHA-256: `104e9e9093425bebc05811b749bf06372fa11c93d29310c50b3c57b5e30c6aad`. These identities serve different purposes.

The final Draft PR head requires actual six-job CI results; its PR audit comment will record the run and exact head after completion. Configuration alone is not passing evidence. No performance improvement is claimed; no external image call or historical photo operation is involved.

## Upgrade after formal approval

1. Finish review and require all six current-head CI jobs, including frozen stable protection and staged installation checks, to pass. Merge only with explicit approval.
2. For the separate formal release, authorize moving the approved v1.5.1 artifact into the canonical `dist/photo-finish.zip` location and advancing the stable guard to v1.5.1 in a reviewed transition. Preserve v1.5.0 in its immutable tag/Release and retain its integrity regression. Rerun all gates on the exact final source and bytes before tagging; do not tag this preparation tree as-is because formal `release` validation expects canonical tagged artifacts.
3. Authorize tag and publication separately. The tag must select the exact approved main commit; run strict source/manifest/installer/staged-attachment comparison, attach the verified ZIP/checksum, then read back and verify actual public attachments using `verify_packages.py published --tag v1.5.1`. A publication event audit is post-publication detection, not authorization or a substitute for prepublication verification.
4. User installation is a separate action. Verify the final public checksum and manifest; extract into a new directory, install the complete directory with bundled runtime, and refresh host discovery. Keep private photos, style library and task/session roots outside installation and reuse the same private paths. Do not edit, resave or re-register old tasks during upgrade. Updating GitHub does not update an installed Skill.

## Downgrade

Before replacing an installation, retain its version/checksum and use existing private backup only if the user authorizes that separate operation. For downgrade, obtain the immutable v1.5.0 ZIP and checksum from its version-specific Release, verify SHA-256 `84fbc42db21d2aa7dc8122152d4390a526761519eb58a212534f4266bd46fb9f`, and restore its complete Skill directory. Keep the same external private roots; this maintenance does not change database schema or old task bytes. Do not mix runtime files across versions or regenerate historical photos. The v1.5.0 current manual response retains its known display-reporting limitation. Candidate acceptance does not replace checking host reload after any user-approved upgrade/downgrade.
