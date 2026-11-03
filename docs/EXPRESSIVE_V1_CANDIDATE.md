# Photo Finish — first-output expressive review, development candidate

> Status: **isolated research / not released / not installed**. This is a protocol experiment, not proof of improved photographic aesthetics. Do not merge or ship until the normal source/entrypoint sync, versioned candidate packaging, independent review, CI and real-photo trials pass.

## Failure mode and objective

A successful renderer, identical source/output lineage, correct ICC interpretation and save receipt can coexist with an aesthetically weak V1. A single human-provided `visual_passed=true` is insufficient evidence of improved composition, light hierarchy, color relationships or material rendering. The code cannot independently perceive or certify aesthetics.

The candidate adds a **source-specific, explicit evidence gate** to **new** `photo_edit.prepare(evaluation_kind="live")` jobs only. Older ledgers and `synthetic` protocol tests retain their original rules. Do not label real photos as synthetic or unclassified to bypass the gate.

## Existing first-edit workflow, no extra rendering stage

1. Inspect the actual original, its visual strengths, its deficiencies and protected information. Establish the single most valuable expressive improvement.
2. At `submit.direction`, supply the existing fields plus `expression_plan`, a four-key object with exactly `composition`, `light`, `color` and `material`. Each has:
   - `source_observation`: actual visible baseline;
   - `decision`: `improve` or `preserve`; at least one must improve;
   - `planned_action`: precise and actually supported editing operation or protection;
   - `success_signal`: what a same-source comparison should reveal.
3. Select an authorized real editor, choose the few operations that actually address these goals, and check the tool's output. Never substitute a generic stronger filter for missing targeted capability.
4. In the existing `review` event, include `expression_assessment` with the same four keys. Each records:
   - `outcome`: `improved`, `preserved`, `failed` or `unverified`;
   - `source_comparison`: what was actually observed in the input;
   - `observed_result`: what actually appears in the result;
   - `actual_action`: what the real editor did.
5. The controller rejects missing fields or an improvement reported only as preservation. `accept_job` rejects any failed/unverified goal. These are **structural and provenance checks**; the human/assistant must still genuinely inspect both photos.

Avoid forced dramatic effects, oversaturation, invented textures, blind cropping and generating over exact-content targets. If no meaningful safe improvement is possible, stop without inventing V1.

## Synthetic tests vs visual evidence

`tests/test_expression_gate.py` covers missing plans, absent/malformed observations, non-achievement, all-preserve intents, an accepted structural claim and unchanged legacy behavior using tiny synthetic images. **Passing these tests does not measure photographic quality.**

### Real-photo study required before acceptance

Use **2–3 previously authorized, privately retained originals** spanning architecture / travel / food or landscape. Keep source bytes unchanged, keep results privately outside Git, and compare the released baseline against this candidate with identical photo/output conditions. Do not invent a live test if the candidate cannot actually run in the editing host.

Evaluate for each image:

| Observable measure | Accept criterion | Failure trigger |
|---|---|---|
| Subject and composition | clearer intended focus and purposeful spatial story at delivery scale | meaningless crop or lost context |
| Light hierarchy | more convincing main/secondary light relationship and spatial layering | flat global lift, haloing, crushed important areas |
| Color | coherent white balance, subject/background color hierarchy, preserved relevant hues | arbitrary tinted filter or food/material color shift |
| Material and protection | authentic texture, stable lettering/identity/facts | plasticity, hallucinated details, broken words |
| First V1 success | first accepted version meets the photo-specific goal | needs avoidable V2 for already-known deficiencies |
| Regression | no duplicate render/save, no loss of file/version provenance | stale hashes, changed published packages or extra mandatory model roundtrips |

Store per-image source/output hashes, actual editing route, scoped visual notes, pass/fail and any edits attempted. **GO only if at least two samples show meaningful improvement without critical fidelity regressions**, and the normal six-platform-check matrix and independent review both pass. A failed or untestable live route remains **NO-GO**, with no automatic release or personal-skill replacement.

## Required integration before publication

- Update `SKILL.md` to explicitly request `evaluation_kind="live"` and map the four-field plan and review into the existing direction/review events.
- Regenerate and verify the Skill entrypoint hashes, runtime policy mirrors and `SESSION_BRIEF.json` through the repository's normal `sync_entrypoints.py` procedure; do not relax the freshness checks.
- Rebuild a **new, unpublished version-specific candidate** through normal packaging procedures. Do not replace any existing v1.5.7/earlier release attachment or the historical `dist/photo-finish.zip`.
- Obtain independent review, a clean six-job matrix, and the real sample evidence above before requesting any merge, release or installation.

Current limitation: the isolated tool connection could not publish a synchronized large `SESSION_BRIEF.json` safely, so the speculative Skill-entrypoint and policy edits were reverted. This candidate **only changes the controller and synthetic tests**; it is not enabled as a complete public Skill upgrade.
