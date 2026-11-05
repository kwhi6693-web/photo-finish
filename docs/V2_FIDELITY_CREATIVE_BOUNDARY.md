# Photo Finish 2.0 — adopted fidelity and creative boundary (2026-11-05)

**Status:** User-adopted policy clarification for future work on Draft PR #47. No change to existing source, historic acceptance evidence, generated photo, installed skill, or current pixel-locked region. This document is not proof of a newly available editor or photographically accepted V1.

## Invariants — do not weaken

Non-portrait scope; incidental person identity and critical appearance; actual readable text/glyphs, structural geometry, product/artwork content and documented facts; honest photographic texture; no fabricated source detail or false tool/visual claims; user authorization and STOP; source/ICC/sha256 audit, privacy, original and historical record immutability, verified native image delivery and version receipts.

## Three different kinds of protection

1. **semantic_identity (ordinary default):** Compare visible source content and identity, not unconditional RGB equality. Real exposure/color/local tonal edits are allowed when the actual content and geometry remain truthful. Text must not be rewritten, completed by guessing, or obscured by styling. The observable original is the source of truth.
2. **exact_content (expressly strict):** Existing exact content/glyph/identity contract applies if the user requests it or the photo serves an appropriately strict archival/evidentiary purpose. It is not an automatic ban on all lighting/color edits unless that is required by the actual strict contract.
3. **pixel_exact_lock (independently explicit):** ROI bytes must be pixel-exact where the current task specifically locks them. In all existing WP4 test cases, `protected` masks remain exact and unchanged. No retroactive unlock; to vary them, create a separately authorized new task and evidence without altering the original acceptance record.

## Allowed photographic expression

Aesthetic judgment may choose PRESERVE, OPTIMIZE, REFRAME; natural or expressive contrast, color, light, texture and composition without a mandatory micro-edit, Gamma-only route, preset strength, crop percentage, candidate count, or new user approval gate. Do not force edits to already successful originals. Actual improvement must be reviewed at delivery scale and affected 1:1 content.

## Tool-route discipline

An operation must be shown to exist and match the task's protection. Current local v2 compositor's `protected` pixel masks remain excluded exactly. Current global LUT cannot honor any pixel-exact lock; fail closed rather than remove a lock or pretend to apply selective exclusion. More capable non-generative operations may be researched in isolation but are not available in production until real implementation and tests. WP4–WP5 project's active trials remain explicitly non-generative. Other permitted creative actions in the broader original skill remain governed by their own current task consent and fidelity rules.

## Distinct judgments

- Engineering/source/ICC/pixel protection GO is **not** photographic GO.
- A concrete legitimate **RETAIN_ORIGINAL** is not a failed edit.
- **NO_GO_QUALITY** is a completed negative photographic review.
- **PENDING_REVIEW** means required visual/independent review evidence is missing.
- **STOP** means a source, consent, tool, or preservation hard gate blocks execution.

These labels are **proposed evaluation vocabulary**, not new programmatic statuses or successful user-facing deliveries. Historical WP4.1–WP4.5 counts, protected ROIs and NO-GO decisions remain unchanged. No change to baseline main, stable v1.5.6 or installed skill.

## Acceptance for future implementation

Test regular semantic-preserving exposure/color edits without implicitly locking all pixels; test explicit pixel locks preserve every protected RGB pixel; test wrong-source, impossible route, invalid or missing consent fail closed; test old WP4 masks still enforce exact exclusion; test photographic outcome independently of engineering. Never translate this policy clarification into unimplemented controller claims.
