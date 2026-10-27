# 📷 Photo Finish

> Give every photograph a clear direction, expressive light and color, and a believable photographic finish.

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[![Agent Skill](https://img.shields.io/badge/Type-Agent%20Skill-3f4856?style=flat-square)](SKILL.md)
[![Version](https://img.shields.io/badge/Stable-1.5.0-2f855a?style=flat-square)](https://github.com/kwhi6693-web/photo-finish/releases/tag/v1.5.0)
[![Validation](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml/badge.svg)](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-2f855a?style=flat-square)](LICENSE)

![Photo Finish — direction, craft, review](docs/assets/photo-finish.svg)

**Jump to:** [Quick Start](#quick-start) · [Capabilities](#capabilities) · [Compatibility](#compatibility) · [Privacy](#privacy) · [Validation](#validation)

<a id="quick-start"></a>

**1.5.0 is the current stable release.** Download from the [v1.5.0 release](https://github.com/kwhi6693-web/photo-finish/releases/tag/v1.5.0). Dated candidate and approval reports remain historical records.

**v1.5.1 maintenance preparation is unpublished and pending approval.** Scope: manual presentation response and CI package boundaries only. Stable downloads remain v1.5.0. See [preparation and upgrade/downgrade steps](docs/RELEASE_1_5_1_PREPARATION.md).

## First use

Photo Finish is a professional non-portrait photography Skill for natural landscapes, city nights, architecture, travel, still life, food and products. It does not develop face beautification, skin smoothing, reshaping, facial-feature changes or portrait optimization. Incidental people retain identity, structure and content protections. Priorities are natural texture, light, color, composition protection, consistent style and real detail. See [product scope](references/product-scope.md).

Send a non-portrait photograph to start editing composition, light, color and detail.

Some single-photo tools require explicit permission to edit for you. Where needed, first say “Please directly edit, check, save and deliver the photo I am about to upload.” Then send the photo. A photo-only upload does not grant blanket tool authority. An interactive preview is not a formal file or save confirmation; tool instructions to stop remain binding.

Local edits require verified tool capabilities. Precise sky selection and protection around complex tree canopies and building edges are not guaranteed. Check actual masks, edge transitions and non-target regions; safely refuse edits that fail quality or protection requirements. Whole-image generation is not a pixel-lock guarantee.

- `Beautify this photo.`
- `Keep the people and lettering; improve only light and color.`
- `Use my saved soft-light wood reference without changing the composition.`

The result carries a compact version and truthful save status. Ask for a local change or “back to V1” to reuse an earlier file.
Actual viewing and editing depend on host tools. Originals are retained; generative editing cannot guarantee pixel-identical people or lettering.
Photos, styles and task records use private storage. Upload behavior depends on the actual host; cloud sync is not promised.

## ⚡ Quick Start

Download the [latest skill ZIP](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip) and [SHA-256 checksum](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip.sha256) from the [latest stable release](https://github.com/kwhi6693-web/photo-finish/releases/latest). These download links always follow the latest stable release. Verify the checksum, then install the extracted `photo-finish/` directory. GitHub's automatically generated source archives contain the whole repository; `photo-finish.zip` is the installable skill package. See the [changelog](CHANGELOG.md) for changes and upgrade notes.

Install this repository as the `photo-finish` skill in your agent's skill directory. Keep `SKILL.md`, `references/`, `scripts/`, `agents/`, `assets/` and **`runtime/` together**; the runtime is included, so no private Library or recovery ZIP is required.

```text
Use $photo-finish to edit this photograph.
```

The agent examines the actual source, develops photographic direction, edits through an available image tool, inspects the result, and makes targeted corrections when needed. **Default delivery: one final photograph at a time, compact version/save status and one optional first-delivery hint.** Originals, comparisons, parameters and reports stay internal unless requested.

For a local checkout:

```bash
git clone https://github.com/kwhi6693-web/photo-finish.git
cd photo-finish
python -m venv .venv
# Activate the environment using your shell's normal command.
python -m pip install -r requirements.txt
python tools/doctor.py
```

Python dependencies do not provide an image generator. The host agent must supply visual understanding, an authorized image-editing tool, and file access. The skill does not collect API keys or silently install tools.

<a id="capabilities"></a>

**Reference-first workflow:** observe the source and read optional global instructions, retrieve and view suitable personal references, then lock the final direction before editing. With no custom instructions, use professional photographic judgment; with partial instructions, decide the remaining choices professionally. The original creative, fidelity, real-review and final-photo delivery requirements remain.

## ✨ Capabilities

| Direction | Craft | Review | Delivery |
|---|---|---|---|
| Source-aware intent and reference decisions | Composition, light, color, local retouching and material treatment | Full-frame expression plus affected native-detail checks | One final photograph; separate quality and save evidence |

- **Expressive by default.** Make the visual intention evident through hierarchy, tonal separation, palette and texture. A tiny exposure adjustment is not the default finish line.
- **Composition freedom.** Preserve, optimize or reframe; crop, aspect ratio and visual center follow the photograph rather than a fixed preset.
- **Believable photography.** Check spatial logic, reflections, perspective, material detail, halos, smearing and repeated synthetic texture. This does not require low contrast or muted color.
- **Protect meaningful content.** Preserve recognizable identity, artwork, inscriptions, stamps and key facts according to the locked task requirements. Ordinary lettering follows the visible source; ambiguous strokes are not invented.
- **Your personal style library.** Explicitly collect favorite photographs with names, labels and notes. Future edits automatically retrieve up to three relevant references; search by keyword or choose saved IDs. Private files live outside the installation and Git checkout.
- **References when useful.** Use authorized references as evidence, not an aesthetic ceiling. An empty or unsuitable reference library goes directly to professional source-based judgment.
- **Real execution records.** Bind source/output hashes, actual tool arguments, protection strategy, observed review, corrections and timing. Do not call a plan a photograph.

## Optional global instructions and professional judgment

Save your own editing rules and aesthetic preferences, then reuse them automatically on future edits. View, replace, remove or clear them through `profile-show / profile-set / profile-reset` in the same controller. Current instructions take priority, so a one-time experiment does not change your long-term profile.

```text
Remember these editing rules and the visual qualities I like for future photographs.
Show my saved editing rules and preferences.
For this photo only, use a different color direction.
```

The agent reads the private profile before retrieving references and choosing final direction; each job binds the actual profile hash and a stable snapshot. User data stays outside the skill/Git checkout. See the [custom-instructions guide](references/custom-instructions.md). These are photographic instructions, not executable scripts or automatic quality certification.

## Manage and move your personal collection

Edit saved names, labels and notes; organize groups, pin useful examples and specify which light/color/material/composition/atmosphere components may be borrowed. Filter and page through collections without changing image bytes.

Add scene-specific rules/preferences, enable or disable them, and undo up to twenty changes. Actual scene labels determine applicable instructions. Structured setting conflicts are surfaced before preparation; free-text interpretation still belongs to the agent.

Export, inspect and merge a private backup of photographs, metadata, settings and undo history. Existing values are preserved by default; empty-target recovery restores the original collection. Backups stay outside the public repository. See the [backup guide](references/private-backup.md).

## Personal style library

```text
Save this photograph to my style library as “Soft wood interiors”; I like its light and texture.
Use $photo-finish to edit this new photo using suitable references from my style library.
Use the “Soft wood interiors” style from my collection for this photograph.
```

The agent uses `photo_edit.py style-add`, `style-list`, and `style-remove`. Collection requires explicit user intent; edit targets and final images are never collected automatically. The same `prepare` call retrieves the current user's collection before the existing visual selection step. The [field guide](references/personal-style-library.md) documents JSON commands, keyword/ID selection and private storage. The collection is local and persistent when the host provides a persistent location; it has no built-in cloud sync or hosted account service.

## 🧭 How It Works

The bundled controller groups routine work into four calls. It records the agent's actual work; it neither renders photographs nor certifies visual judgment automatically.

| Stage | Controller | Required real work |
|---|---|---|
| Understand | `photo_edit.py prepare` | Inspect the source; observe subject, scene, light and material; retrieve references |
| Commit direction | `photo_edit.py submit` | Select viewed references, lock final direction and protected content, record the complete tool request |
| Acquire | `photo_edit.py returned` | Execute the actual editing tool once; inspect formal returned bytes |
| Review | `photo_edit.py review` | Compare source and output, inspect affected details, resolve visible issues |

Read the [runtime guide](docs/runtime.md) for executable examples, [the complete policy](runtime/我的照片美化偏好与修图标准.md) for behavior, and [the adapter contract](references/delivery-adapter.md) only when its fields are needed.

<a id="compatibility"></a>

## 🧩 Compatibility

| Capability | Requirement / boundary |
|---|---|
| Agent | Visual source/output inspection and instruction-following |
| Image editing | A real host-provided editor or reference-aware image-generation tool |
| Controller | Python 3.10+ and Pillow; local Linux/Python 3.12 evidence is reported separately from CI |
| Color | Interpret supported declarations; an explicit bounded screen-sRGB assumption is not calibrated color or print certification |
| Exact text or identity | Use a route that can preserve the protected content; generated reconstruction cannot pass an exact-content requirement |
| Saving | Host-specific; presentation, scoped quality acceptance and confirmed durable saving are different facts |
| Optional tools | Lightroom, RAW decoding, numerical analysis, grids and captions only when applicable and available |

Pillow is bounded to `>=12.3,<14`. pip selects a compatible 12.x release on Python 3.10 and permits 13.x on Python 3.11+. NumPy and SciPy remain optional; their version ranges already permit newer compatible releases.

The public reference index starts empty. The optional numerical baselines and XMP files are designed starting settings, not measured author settings, an obligatory look, or proof of Adobe import/render compatibility. RAW and print results need task-specific verification. Portrait photographs are outside the product scope.

<a id="privacy"></a>

## 🔒 Privacy

The repository contains workflow code, policies, optional presets and synthetic tests. **No private reference photographs, user uploads, generated personal images, Library IDs, session records, credentials or machine-specific paths are distributed.**

Keep images, ledgers, signed result URLs and save receipts outside the installation directory. Image providers receive photographs only through the host tools you authorize; the skill itself installs no daemon, telemetry or upload service. A fresh public Git history prevents accidental publication of the private workspace's earlier commits.

See [SECURITY.md](SECURITY.md) for the disclosure route and [the publication audit](docs/security-audit.md) for check scope and limitations.

<a id="validation"></a>

## ✅ Validation

```bash
python tools/doctor.py
python tools/check_publication.py
python tools/run_tests.py
python tools/build_release.py --output dist/photo-finish.zip
```

The package builder uses an allowlist, rejects unsafe entries, writes deterministic archives and includes MIT license/attribution. Checks cover policy/hash consistency, empty-library fallback, source/output identity, protection contracts, atomic failure behavior, color scope, save-state separation and reproducible extraction. Synthetic tests exercise contracts; they are not real-photo quality evidence. See [validation scope](docs/validation.md).

## 🤝 Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). Keep the ordinary edit path light, preserve actual visual review, and never add private photographs or credentials to tests or examples. A ⭐ helps others discover the project if it is useful to you.

## Documentation

| Need | Guide |
|---|---|
| Main features, architecture and all controller operations | [Architecture and document map](docs/architecture.md) |
| Tone, color and visual hierarchy | [Practical photographic foundations](references/tone-color-foundations.md) |
| Executable workflow and API fields | [Runtime guide](docs/runtime.md) · [Adapter contract](references/delivery-adapter.md) |
| Personal references and optional global instructions | [Style library](references/personal-style-library.md) · [Custom instructions](references/custom-instructions.md) |
| Private migration and recovery | [Backup guide](references/private-backup.md) |
| Updates, evidence and publication | [Changelog](CHANGELOG.md) · [Validation](docs/validation.md) · [Release procedure](docs/releasing.md) |
| Privacy boundaries and contributions | [Security](SECURITY.md) · [Audit](docs/security-audit.md) · [Contributing](CONTRIBUTING.md) |

## License

[MIT](LICENSE), copyright © 2026 kwhi. Method references and dependency boundaries are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). User photographs remain subject to their own rights; this license does not grant rights to third-party images or services.

Instruction priority: safety and content protection, current task instructions, saved rules/preferences, suitable style, professional defaults. A single feedback turn never silently becomes a saved preference.
