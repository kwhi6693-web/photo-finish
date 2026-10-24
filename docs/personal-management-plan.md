# Personal management and portability

Implement the three recommended improvements within the existing private SQLite/Pillow runtime. No hosted service or additional dependency.

## Scope and contracts

1. Style management: partial metadata edits, group, pin and saved reference purposes; group/keyword filtering and paginated listing. Keep exact image bytes/IDs and source-bound candidate selection. Explicit IDs cannot silently disappear behind additional filters.
2. Scene rules: individual rules/preferences with stable IDs, enabled state and scene labels (existing A–L or explicit observed custom labels). Apply only global and matching enabled entries before photographic direction. Structured setting/value conflicts are surfaced; free-text compatibility still requires agent judgment. Keep a bounded change history and support undo. Full profile reset clears active settings and undo history, preserving photos and existing job snapshots.
3. Private backup: versioned ZIP with a portable JSON catalog, settings/history and original image bytes; manifest hashes, bounded entries/sizes, strict member names and no symlinks/extraction traversal. Inspect before import. Default merge preserves existing metadata/settings and reports conflicts; explicit policies allow backup metadata/settings. Validate the entire archive before target writes; rollback newly linked files on transaction failure. Empty-target restore retains source history; merging preserves local history. Never export unindexed files, job records or runtime code.

Public archives remain source-only. Old catalogs remain readable. Daily edits load only relevant settings and a small reference shortlist; maintenance operations own backup/verification work.

## Work

- [x] Test and implement style metadata management and retrieval integration.
- [x] Test and implement scoped rules, conflicts, bounded history and undo.
- [x] Test and implement private export/inspect/import, including corruption, malicious names, merge conflicts and write rollback.
- [x] Update skill, interface guides, UI and three-language READMEs; synchronize hashes and rebuild 1.3.0.
- [x] Run full local verification and independent command trials, publish through GitHub, verify platform CI and merge the reviewed result.
