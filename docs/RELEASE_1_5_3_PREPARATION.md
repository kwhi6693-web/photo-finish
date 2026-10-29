# v1.5.3 maintenance candidate — not published

Base: main `b8075fba8b35aa52c603993fa737921a9d7338d0`, the normal merge of PR #24. Its normal six-configuration main CI completed successfully. v1.5.2 remains the published stable release; v1.5.3 has no formal tag or Release. This branch only aligns version metadata, release verification and documentation. It adds no photographic algorithm, dependency or service.

The formal attachment verifier now selects the exact tagged version directory when present, retaining the legacy canonical layout for older tags. Missing/corrupt files in a present version directory fail without falling back to another package. Source/manifest/version/attachment byte checks are unchanged. Isolated anonymous Git fixtures reproduce the old failure, cover both layouts and reject replacement attachments; they create no real repository tag.

## Supported contract

- Known, verifiable credentials from an authorized authenticated host and ONE writer. The host must retain truthful operation/handoff/save receipts.
- Explicit private archival, complete ZIP/member byte and SHA-256 readback, independent-session read-only retrieval, and exact-byte recovered version views in a NEW private target.
- Identical re-entry reuses verified evidence. Unknown outcomes, missing credentials, conflicting identities/content or unowned targets stop safely. Partial successes retain their actual receipts; delivery and archival confirmation remain separate.
- Recovery preserves source, selected parent and series identities, records auditable path mappings, and derives a separate recovered SQLite view/current cursor without editing/rendering, registering an old version, overwriting history or migrating the production task ledger.

Two host-level P0s remain excluded: authoritative reconciliation when all local operation state AND host handoff credentials are lost; cross-session same-series coordination. Existing-file optimistic checks do not provide persistent business-key creation, unique operation registration or series-wide transaction/fencing. No unattended/background archival, indefinite retention or cross-service atomicity is promised. Full Phase 5 long-term reliability remains NO-GO.

The prior real photography, private archival, independent full-byte retrieval and new-target recovery evidence is retained at its original scope. New release checks use synthetic data, never new photography or private historical records.

## Candidate construction and isolation gates

1. Synchronize the runtime, distribution, policy mirror and SESSION_BRIEF to 1.5.3 with `python tools/sync_public.py`. The builder derives the manifest version from this source.
2. Build the release-shaped candidate with `python tools/build_release.py --output dist/v1.5.3/photo-finish.zip`. Do not use `--candidate` for this exact release-shaped artifact: that option deliberately identifies development packages as `0+candidate`. An unpublished 1.5.3 artifact is not proof of publication.
3. Verify `python tools/verify_release_preparation.py`: exact allowlisted payload, complete per-file manifest SHA-256, strict source/version/attachment mapping, two independent reproducible builds, isolated extraction and Python loading. Run the normal cross-platform CI without skips. Keep `dist/photo-finish.zip`, frozen historical archives and published assets unchanged.
4. Check every extracted file including `assets/icon.svg`, with no exclusions, content normalization or hash-rule changes. Exercise the scoped recovery protocols from the extracted runtime, then restore an isolated copy of the full v1.5.1 snapshot and compare every byte. Never replace the active installed Skill or private roots.
5. Record the exact candidate commit, ZIP size/hash, all-member inventory, installation/rollback evidence and actual final CI result in the preparation report. An incomplete CI run is not success.

## Host transfer limitation and upgrade boundary

The earlier real host pipeline changed `assets/icon.svg` between upload commit e72abab (1,210 bytes) and materialization commit e98bf78 (1,619 bytes). A successful local extraction cannot certify that this host transformation has been fixed. The candidate retains the original source icon and strict all-file comparison; accepting the replacement or skipping the icon is forbidden.

This preparation does not push to the active personal-Skill installation. No independently targeted host materialization/registration sandbox has been established. Python loading and isolated filesystem rollback are distinct from real ChatGPT registration, automatic triggering or a verified production upgrade. Until the complete real transfer/materialization chain preserves ALL approved package bytes, formal host upgrade remains NO-GO. Preserve the full v1.5.1 rollback snapshot and leave private data outside this process.

## Separate approval steps

Review and merge this maintenance preparation branch through normal GitHub rules. Before a separately approved v1.5.3 tag/Release, recheck the exact merged source and normal main CI, confirm its package is byte-identical to the approved candidate, and publish only the curated ZIP and checksum. Do not reuse/overwrite v1.5.2 or imply that the current latest-download link already contains this candidate. Public asset/manifest/checksum readback is a publication gate.

Installing/upgrading the live Skill is another authorization and acceptance step. It requires a safe, fully byte-verified host transfer path, preserved rollback copy and real host loading/invocation evidence. Neither source merge nor Release publication upgrades the installation. PR #16, private photographs, style libraries and historical ledgers remain outside this maintenance scope.
