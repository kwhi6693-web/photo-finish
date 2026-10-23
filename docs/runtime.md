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

1. `prepare` binds current context, source identity, direction and candidate retrieval. The public index is empty; choose professional fallback instead of fabricating a match.
2. `submit` locks explicit protections and fidelity strategy, reference decisions, observed issues and the complete actual image-tool arguments.
3. Execute the real host image tool **once**, measuring the actual call boundaries. `returned` registers its real task/output and checks formal file bytes. Resume an existing in-progress task rather than submitting it again.
4. Actually inspect the full result and affected native details. Supply truthful events to `review`; unresolved issues or unmet protection block acceptance. Save internal records only through the supported host route.

The full [adapter field guide](../references/delivery-adapter.md) contains `submit`, `returned`, `review`, correction and save examples. Generic descriptions in examples are not completed observations or permission to fill pass values automatically.

## Reference extension

The shipped `reference_index.json` is an empty list. If you maintain a private local reference set, use only authorized photographs, follow the index contract expected by `photo_workflow.candidates`, and keep the resulting index/photos out of Git. Rebuild the local session brief after intentional configuration changes. Do not promote edit targets or generated outputs into references automatically. The public `doctor` intentionally expects the distributed index to remain empty.

## Recovery and saving

Use the existing job's status to continue a tool task or acquire a formal result. Do not treat a rendered preview as the formal original. Tool presentation, quality acceptance and confirmed durable save are separate states. When a host auto-saves after the turn and no authoritative receipt exists yet, keep internal `pending_confirmation`; do not poll indefinitely, re-upload the image, or claim that saving is confirmed.

## Optional baselines

`runtime/06_SCENE_PRESETS/` and `style_config.json` contain advisory numerical settings and XMP files. Their numeric controls are engine-specific. They do not replace actual rendering, image-tool discovery, RAW interpretation, visual review or per-image exposure/white-balance decisions. Use `requirements-analysis.txt` only for optional numerical/report tools that need those dependencies.
