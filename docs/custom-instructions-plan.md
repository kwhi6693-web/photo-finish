# User custom instructions

Historical implementation record for 1.2.0, delivered in [PR #7](https://github.com/kwhi6693-web/photo-finish/pull/7). Current interfaces and later changes are documented in [runtime.md](runtime.md), [architecture.md](architecture.md) and [CHANGELOG](../CHANGELOG.md).

Extend the primary workflow with a private, user-managed layer for durable rules and aesthetic preferences. Keep the current photograph collection, rendering, visual judgment and protection workflow.

## Contract

- Store free-text rules and preferences in the existing private SQLite catalog, outside the installation and Git checkout. Use the same per-user root and standard-library dependencies. Public packages ship no user profile.
- Add profile-show, profile-set and profile-reset to photo_edit.py. Save only on explicit user intent, allow partial replacement and empty-list clearing, and leave photographs untouched. Empty reads do not create files.
- Read the profile before deciding photographic direction. A nonempty profile must have its actual content hash acknowledged by prepare; missing/stale acknowledgment fails before publishing a job.
- Bind the observed profile snapshot and optional task_instructions to the job. Priority: current task instructions, saved rules, saved aesthetic preferences, suitable reference examples, general defaults. Interpret these as photographic context; preserve truthful execution records, tool permissions and locked protection requirements.
- A changed profile affects future tasks. Existing jobs keep their snapshot and can finish without rereading mutable profile state. Do not claim that a hash or validator proves artistic compliance.

## Work

- [x] Add failing tests for persistence, partial updates, clearing, consent, root isolation, corruption, stale/unobserved profiles, per-task context and snapshot stability.
- [x] Implement user_preferences.py and integrate main prepare and management routes; include it in runtime export.
- [x] Update the main skill, user interfaces and three-language documentation, synchronize hashes and rebuild version 1.2.0.
- [x] Run targeted and full synthetic tests, doctor, publication/history scan, deterministic package/extraction checks and independent real-command trials before publishing to GitHub.
