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

Read `profile-show` before choosing photographic direction. A nonempty saved profile requires its actual `sha256` as `observed_profile_sha256` in prepare. Empty profiles preserve the existing interface.

From `runtime/`, call `python 10_SYSTEM_CONFIG/scripts/photo_edit.py ACTION` with one JSON object on stdin. For example, after actually viewing the source:

```json
{
  "project_root": ".",
  "source_path": "../../photo-work/source.jpeg",
  "path": "../../photo-work/job.json",
  "direction": {
    "intent": "Replace this with the actual photographic direction",
    "hierarchy": "Describe the actual subject and supporting layers",
    "light_material": "Describe the observed light/material and intended treatment",
    "output_use": "screen",
    "route": "creative",
    "qa_focus": ["Specify the actual affected details"]
  },
  "tags": [],
  "evaluation_kind": "live",
  "scenario": "actual-scene-description"
}
```

1. `prepare` binds current context, source identity, direction and candidate retrieval. The public index is empty; the current user’s optional private collection is queried automatically. Choose professional fallback when no applicable reference exists.
2. `submit` locks explicit protections and fidelity strategy, reference decisions, observed issues and the complete actual image-tool arguments.
3. Execute the real host image tool **once**, measuring the actual call boundaries. `returned` registers its real task/output and checks formal file bytes. Resume an existing in-progress task rather than submitting it again.
4. Actually inspect the full result and affected native details. Supply truthful events to `review`; unresolved issues or unmet protection block acceptance. Save internal records only through the supported host route.

The full [adapter field guide](../references/delivery-adapter.md) contains `submit`, `returned`, `review`, correction and save examples. Generic descriptions in examples are not completed observations or permission to fill pass values automatically.

## User rules and preferences

Use `photo_edit.py profile-show`, `profile-set`, and `profile-reset` with JSON stdin. The [custom-instructions guide](../references/custom-instructions.md) documents explicit save intent, partial section updates, individual-rule removal and clearing. Profiles share the private per-user SQLite catalog with photographs, without shipping any user data.

Rules and aesthetic preferences are free-text lists. Read them before forming the actual `direction`, and bind the returned hash through `observed_profile_sha256`; stale/missing acknowledgment fails before publishing the job. Optional `task_instructions` belongs only to that job. Current-task instructions take priority over saved rules, preferences, suitable references and general defaults. The agent implements that priority in actual photographic decisions; the controller does not infer semantic compliance.

`prepare` records the observed profile snapshot under `customization` and `user_customization` in the ledger. Future profile changes do not invalidate in-flight jobs, alter their context or trigger repeated image calls. Existing review and locked protection gates remain. All new commands use existing Python/Pillow and standard-library SQLite only.

## Personal style library

Use the same controller's `style-add`, `style-list`, and `style-remove` commands to maintain an opt-in private collection. See the [field guide](../references/personal-style-library.md) for JSON examples and storage behavior. An explicit collection request authorizes `consent: true`; a plain edit request does not. The host obtains a real local file before collection; there is no hosted upload endpoint.

`prepare` automatically queries that user's collection. Optional `style_query` filters title/labels/note, `style_ids` selects up to three actual IDs (choose one selector, not both), and `style_library_root` overrides the environment/default location. The returned candidate `path` and `sha256` let the agent inspect the exact reference. Existing `selection` decisions still require actual viewing. Missing/changed candidates are reported; explicitly requested missing IDs fail. Adopted bytes are checked before submission and later acceptance. New unrelated entries do not invalidate existing jobs.

Management commands accept `library_root`, or use PHOTO_FINISH_STYLE_LIBRARY, or default to the OS user's application data directory. Never store private data inside the skill or any Git checkout. Multi-user hosts must assign trusted separate roots; ephemeral hosts must supply persistent storage. This is a local collection, with no built-in account service or cross-device sync. Empty lookup does not write files, and a damaged catalog raises an error. The distributed `reference_index.json` stays empty; `doctor` continues to validate the public package.

## Recovery and saving

Use the existing job's status to continue a tool task or acquire a formal result. Do not treat a rendered preview as the formal original. Tool presentation, quality acceptance and confirmed durable save are separate states. When a host auto-saves after the turn and no authoritative receipt exists yet, keep internal `pending_confirmation`; do not poll indefinitely, re-upload the image, or claim that saving is confirmed.

## Optional baselines

`runtime/06_SCENE_PRESETS/` and `style_config.json` contain advisory numerical settings and XMP files. Their numeric controls are engine-specific. They do not replace actual rendering, image-tool discovery, RAW interpretation, visual review or per-image exposure/white-balance decisions. Use `requirements-analysis.txt` only for optional numerical/report tools that need those dependencies.
