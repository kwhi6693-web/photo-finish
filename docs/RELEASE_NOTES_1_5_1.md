# Photo Finish v1.5.1

Prepared Release Notes — unpublished, pending explicit merge/tag/publication approval.

This maintenance release fixes the current response after a verified manual presentation and improves release-package verification. It remains a professional non-portrait photography Skill.

- Explicit successful manual presentation now reaches the experience layer and returns `display_observed=true`, source `current_manual_confirmation`, scope `current_delivery_response`.
- Automatic platform display observation, manual confirmation, receipt-confirmed saving and SQLite delivered stay independent. Saved files, URLs and version flags do not imply actual display. Historical ledgers are not modified.
- CI separately protects historical v1.5.0, pins release-ready v1.5.1 canonical/staged bytes, verifies isolated development builds and runs cross-platform installed-protocol checks. Formal source, manifest, installer and actual Release attachments must match.

No new image call, performance optimization, portrait feature, dependency requirement or database migration is included. Existing authorization, content protection, real review, save receipts and STOP rules remain unchanged.

Installer: `photo-finish.zip`, 498139 bytes, 115 payload files plus manifest. SHA-256: `0d929e31f4cf132c9855b933771c0c8fc98ece4702f598aaca759b9444d70608`.

Validation results and host limitations: [finalization audit](RELEASE_1_5_1_FINALIZATION.md). Isolated Python installation/protocol tests do not certify ChatGPT UI registration, device rendering, remote storage or photographic aesthetics. Manual confirmation is explicit caller evidence, not a device certificate. No performance improvement is claimed.

Upgrade: after authorized publication, verify the public checksum, install the complete extracted Skill and verify host reload; retain the same external private roots. Downgrade: reinstall the complete immutable v1.5.0 package, verifying SHA-256 `84fbc42db21d2aa7dc8122152d4390a526761519eb58a212534f4266bd46fb9f`; retain external private roots. No historical photo operation or task migration is required. See the audit for exact steps and approval boundaries.
