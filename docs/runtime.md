# Runtime guide

Run the controller from the bundled `runtime/` directory. Keep photographs, jobs and internal records in a separate work directory, outside the Git checkout. Paths in the examples are placeholders chosen by the caller and must refer to actual local files.

The host agent still reads `SKILL.md`, the complete policy and the applicable host image-tool instructions. It must inspect the actual source and actual result. These commands do not render an image and must not be used to manufacture review evidence.

## Read-only capability check

From the repository root:

```bash
python tools/doctor.py
```

Install core dependencies explicitly in your own environment if missing. The skill does not install dependencies during an edit.

## Daily interface

Observe the actual scene, then read `profile-show` with the same `scenes` before choosing final photographic direction. Global instructions are optional: unspecified choices use professional photographic judgment, with suitable references as adaptable evidence. Use active_rules/active_preferences. prepare defaults to tags as its profile scenes; profile_scenes can explicitly supply observed custom labels. A nonempty saved profile requires its actual `sha256` as `observed_profile_sha256` in prepare. Empty profiles preserve the existing interface.

From `runtime/`, call `python 10_SYSTEM_CONFIG/scripts/photo_edit.py ACTION` with one JSON object on stdin. For example, after actually viewing the source:

```json
{
  "project_root": ".",
  "source_path": "../../photo-work/source.jpeg",
  "path": "../../photo-work/job.json",
  "tags": [],
  "evaluation_kind": "live",
  "scenario": "actual-scene-description"
}
```

1. `prepare` binds current context, source identity and candidate retrieval without locking final direction. The public index is empty; the current user’s optional private collection is queried automatically. Choose professional fallback when no applicable reference exists.
2. After viewing suitable candidates, `submit` atomically records protection and reference decisions, then locks final `direction`, observed issues and complete actual image-tool arguments. Supply the direction object documented in the adapter guide at this step. Legacy `prepare.direction` is a provisional draft; it may be reused for professional fallback, while adopted/partial references require explicit final `submit.direction`. Invalid selection or direction leaves the job unchanged.
3. Execute the real host image tool **once**, measuring the actual call boundaries. `returned` registers its real task/output and checks formal file bytes. Resume an existing in-progress task rather than submitting it again.
4. Actually inspect the full result and affected native details. Supply truthful events to `review`; unresolved issues or unmet protection block acceptance. Save internal records only through the supported host route.

The full [adapter field guide](../references/delivery-adapter.md) contains `submit`, `returned`, `review`, correction and save examples. Generic descriptions in examples are not completed observations or permission to fill pass values automatically.

## User rules and preferences

Use `photo_edit.py profile-show`, `profile-set`, and `profile-reset` with JSON stdin. The [custom-instructions guide](../references/custom-instructions.md) documents explicit save intent, partial section updates, individual-rule removal and clearing. Profiles share the private per-user SQLite catalog with photographs, without shipping any user data.

Rules and aesthetic preferences are optional free-text lists. Without active guidance the receipt reports professional_judgment.mode=autonomous; with saved/current guidance it reports guided. Both use professional judgment for unspecified choices and neither modifies saved settings. These labels describe supplied context, not automatic interpretation or quality certification. Read them before forming the actual `direction`, and bind the returned hash through `observed_profile_sha256`; stale/missing acknowledgment fails before publishing the job. Optional `task_instructions` belongs only to that job. Current-task instructions take priority over saved rules, preferences, suitable references and general defaults. The agent implements that priority in actual photographic decisions; the controller does not infer semantic compliance.

`prepare` records the observed profile snapshot under `customization` and `user_customization` in the ledger. Future profile changes do not invalidate in-flight jobs, alter their context or trigger repeated image calls. Existing review and locked protection gates remain. All new commands use existing Python/Pillow and standard-library SQLite only.

## Personal style library

Use the same controller's `style-add`, `style-list`, and `style-remove` commands to maintain an opt-in private collection. See the [field guide](../references/personal-style-library.md) for JSON examples and storage behavior. An explicit collection request authorizes `consent: true`; a plain edit request does not. The host obtains a real local file before collection; there is no hosted upload endpoint.

`prepare` automatically queries that user's collection. Optional `style_query` filters title/labels/note, `style_ids` selects up to three actual IDs (choose one selector, not both), and `style_library_root` overrides the environment/default location. The returned candidate `path` and `sha256` let the agent inspect the exact reference. Existing `selection` decisions still require actual viewing. Missing/changed candidates are reported; explicitly requested missing IDs, unmatched keywords/groups or entirely unavailable explicit results fail rather than silently selecting another style. Adopted bytes are checked before submission and later acceptance. New unrelated entries do not invalidate existing jobs.

Management commands accept `library_root`, or use PHOTO_FINISH_STYLE_LIBRARY, or default to the OS user's application data directory. Never store private data inside the skill or any Git checkout. Multi-user hosts must assign trusted separate roots; ephemeral hosts must supply persistent storage. This is a local collection, with no built-in account service or cross-device sync. Empty lookup does not write files, and a damaged catalog raises an error. The distributed `reference_index.json` stays empty; `doctor` continues to validate the public package.

## Personal management and portable backups

`style-update` partially edits metadata, groups, pins and saved component scopes; `style-list` supports group/pin filters and pagination. Image identity stays immutable. A selected scoped reference must explicitly name allowed `uses`. See the [style guide](../references/personal-style-library.md).

`profile-rule-add/set/remove` manages scene labels and enabled rules. `profile-show` returns applicable active lists. Explicit setting/value conflicts at the same priority must be resolved or covered by a real current task_settings override before prepare. `profile-history/undo` retains up to twenty prior changes. Full profile-reset clears active and undo settings while preserving photographs. See the [rule guide](../references/custom-instructions.md).

`backup-export/inspect/import` provides private, versioned migration outside the skill and Git checkout. Validate before writes; default merges preserve existing values and report conflicts. Restore into a new directory to recover a damaged store. The [backup guide](../references/private-backup.md) documents limits, integrity, merge policies and archive privacy. No new dependency/service is required.

## Recovery and saving

Use the existing job's status to continue a tool task or acquire a formal result. Do not treat a rendered preview as the formal original. Tool presentation, quality acceptance and confirmed durable save are separate states. When a host auto-saves after the turn and no authoritative receipt exists yet, keep internal `pending_confirmation`; do not poll indefinitely, re-upload the image, or claim that saving is confirmed.

## Optional baselines

`runtime/06_SCENE_PRESETS/` and `style_config.json` contain advisory numerical settings and XMP files. Their numeric controls are engine-specific. They do not replace actual rendering, image-tool discovery, RAW interpretation, visual review or per-image exposure/white-balance decisions. Use `requirements-analysis.txt` only for optional numerical/report tools that need those dependencies.

## Conversation and batch UX (1.5.0 candidate)

The normal image pipeline is unchanged. Add private session_root to version/delivery commands, independent from the style-library root. See [versions](../references/conversation-versions.md) and [batch recovery](../references/batch-recovery.md). Index rows locate accepted ledgers; output/source hashes are checked on use. Never use an index or displayed image as visual/save evidence. Natural-language selection is performed by the host assistant, with deterministic source/version/protection gates in Python.

For screen sharing use actual supported color declarations; export-web creates a separate tagged derivative only when needed, without silently relabeling P3/HDR. Printing requires target paper/device ICC, actual soft proof, dimensions and rendering intent; absent those, deliver a bounded screen result and state that printing is unverified. No printing calibration is inferred from an embedded ICC.

## 私有恢复与保存续接

任务源图/成片/账本/日志/索引按需使用[检查点接口](../references/private-checkpoints.md)，不是风格库备份格式。明确私有根必须在所有Git与Skill之外；本地ZIP不等于持久保存。真实存储回执、归档取回和关键文件哈希核验分别留证。已登记的同一保存意图可在回执已到达后只读恢复，仍需独立确认，不能因此重新修图。
