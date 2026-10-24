# Personal style library

Goal: let each user explicitly collect photographs that express their preferred aesthetic, then retrieve applicable examples in the existing main editing flow.

Use the existing Python/Pillow runtime with a small SQLite catalog and private image copies outside the skill and Git checkout. This reuses the current source-bound candidate/selection protocol. A hosted gallery would add accounts, services and dependencies; modifying the shipped reference index would mix user data with releases. Neither is needed for this feature.

## Contract

- Add only on explicit collection intent, preserve exact uploaded bytes and deduplicate by SHA256. Record a title, free-form labels, optional existing scene tags and the user's note about what they like.
- Resolve the persistent root from an explicit argument, PHOTO_FINISH_STYLE_LIBRARY, or the current operating system user's application data directory. Separate roots isolate catalogs; shared hosting must provide trusted per-user roots. Reject roots inside Git or the installed skill. This is local persistence, not a hosted upload or account service.
- Add style-add/list/remove to photo_edit.py. Missing libraries are read-only empty results, without setup or writes. Corruption produces an actionable error rather than a fabricated empty match.
- prepare automatically includes eligible personal references, supports an optional keyword or explicit IDs, returns at most three inspectable candidates and their immutable hashes. Keep the distributed reference index empty.
- Require actual viewing and explicit adopt/partial/reject decisions. Verify selected personal bytes before submission; retain their identities in the job so changes cannot silently replace the selected style. Keep aesthetic judgment and source protections unchanged.
- Never automatically collect edit targets or finished images. No new service, image model, UI or network transfer.

## Implementation and verification

- [x] Write regression tests for collection/restart/deduplication/removal, invalid consent/files/roots, isolation, keyword/ID retrieval, and prepare/submit integration; run against missing feature.
- [x] Implement style_library.py and extend existing candidate retrieval and photo_edit routes. Include the module in runtime exports.
- [x] Update SKILL.md, the three READMEs, UI metadata and runtime guide; synchronize hashes and build the release archive.
- [x] Run the focused tests, full synthetic suite, doctor, history publication scan and deterministic archive check. Independently exercise the documented commands before publishing the reviewed changes through GitHub.
