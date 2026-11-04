# Photo Finish 2.0 — relational multi-region editorial lighting experiment

**Research-only, Draft PR #45, not a released Skill or automatic edit route.**

## Why this branch exists

The prior V9/V10 experiments reliably preserved selected content but made weak normal-size visual changes. The user-approved Macau night-street V6 motivated a measurable, non-stylistic hypothesis: meaningful photographic expression often comes from controlling the **relative priority of environmental regions**, not merely lightening the main subject. The implementation must express the scene's viewing path while maintaining genuine architecture, people, vegetation, text, real water arcs and natural materials.

### Privately verified reference comparison (same-size sRGB)

Within independently selected approximate rectangles, the **weighted RGB brightness** changed from original → user-preferred night-street V6 as follows: golden hotel 60→59, receding street 94→70, side buildings 49→42, close signs 92→73. This supports the hypothesis that the hotel stayed relatively luminous while its competing context receded. These are **descriptive ROI means, not objective aesthetic grades, causal proof or a prescription for all photos**. The two source files were visually inspected; they were not published or used as a new universal LUT.

## Prototype implementation

`experiments/v2_local_light/multizone_editor.py` accepts **2–4 separate, human-inspected zones**, each with a source-aligned binary region mask, independently inspected target core, explicit allowed region, fixed-object protection, bounded luma gamma and optional color-saturation factor. It uses the pre-existing `pixel_mask_qa.py` audit and feather support, unions protections across all zones before compositing, keeps original nonselected pixels bit-exact and rejects mismatched source-pixel fingerprints, missing/mismatched ICC bytes, unreviewed masks, new RGB 255 channel clipping and unreviewed output changes. This is a *pure Pillow*, non-generative, same-geometry tonal adapter. It returns **PENDING_REAL_IMAGE_EDITORIAL_REVIEW**, never quality acceptance, host-save certification or an invented V1.

`tests/test_v2_multizone_editor.py` contains 12 synthetic checks: different foreground/subject tonal priorities; original immutability; cross-zone protected overlap; source hash; explicit human preview flag; concrete spatial goal; bad core; whole-frame mask; ICC mismatch; new white clipping; unchanged outside zone; gamma bound; and fail-closed truthy-string review flags. These passed locally with Pillow 12.3.0; Python 3.11/3.12 / Pillow 13 CI on the **latest GitHub commit** is required before compatibility is claimed.

## Real-photo exploration (private assets, not part of code tests)

The existing three authorized sources remain outside Git. The previously approved **night-street V6** is retained as a positive visual comparator; no additional night-street reconstruction or arbitrary color copying is required.

Two independent **same-source, non-generative** daylight candidates were made using the original source pixels:

- **Historic church:** a color-observed blue-sky selection was rendered separately from visually checked stone masonry. By darkening its genuine blue sky while maintaining the sunlit stone and deep recessed carving, subject/background separation became more legible than V10. Inspecting the actual candidate at normal size shows a potentially more editorial architecture hierarchy, but **user preference and exact final aesthetic pass are still unconfirmed**. The darkest framing wall remains unchanged.
- **Courtyard through heavy wooden window:** the original near-dark window frame was preserved as the observer's position. The upper outdoor light and sunlit paving were edited separately to reduce competing brightness, while existing lateral water arcs, real trunks and background building shapes were not redrawn. The resulting impact is still **too subtle** relative to the user goal: **NO-GO** for significant expressive gain.
- An initial automatically color-selected `courtyard hedge` mask leaked onto parts of the background wall. It was **rejected** rather than used for strong local edits. It does not count as evidence of successful segmentation.

Original source bytes were preserved. Both local linked two-zone test outputs have 1152×1536 geometry, matching output ICC bytes and no newly clipped RGB channels or changes outside the inspected region support. Their private source/output hashes, masks, original media and outputs are NOT committed. The locally observed technical checks are not proof that the current GitHub or Adobe host has a working production adapter.

**Known limits:** The algorithm does not autonomously discover accurate zone boundaries, infer professional art direction, authenticate all masks or service operations, calculate scene/texture fidelity in a full semantic sense, certify no perceived halo from a mathematical support test, or decide magazine-grade taste. Gamma-based tonality is only one small tool. Repeated courtyard micro-editing is not warranted merely because the mask checks pass.

## Real-photo negative test: bright architectural-edge halo

The first local two-zone church render visibly showed a **light fringe along stone spires and the sky boundary**: soft blurring of a sky selection made the surrounding pixels appear too bright. The result was **rejected for naturalness** despite passing region-support and protected-pixel checks. This is decisive evidence that numeric feather checks are NOT sufficient to guarantee a natural photo.

A targeted experimental `pixel_locked` edge policy now exists for **independently visually inspected, source-color-derived sharp boundaries**. It restricts sky tonal changes to actually selected sky pixels rather than Gaussian-blending across the stone outline; use it ONLY where the real boundary has been inspected. Strong local edits without a verified boundary must STOP. Other, nonhard masks retain narrow soft feathering.

The same original church was rerendered locally with a blue-sky selection that follows the observed un-eroded sky pixels and the audited pixel-locked policy. The formerly prominent tower fringe was substantially reduced in the real visual inspection, while sky/stone contrast and actual building structure were preserved. **This is not a final user-rated photo and does not prove all halo artifacts are absent.** The courtyard still showed weak overall improvement. The source files, masks, and local output bytes remain private.

The two negative tests (sharp-boundary fidelity and reject unreviewed hard-edge editing) raised local synthetic coverage from **12 to 14 tests**. Only current-head CI using the project's pinned Pillow-13 compatible environment can confirm repository test compatibility.

## Promotion decision

- [x] Quantify the specific photo the user preferred, without making that its universal color recipe.
- [x] Build and synthetic-test a source-preserving multi-zone test adapter.
- [x] Compare two additional genuine same-source images locally without publishing personal assets.
- [ ] Latest-commit six-job cross-platform CI and independent engineering review.
- [ ] User/independent visual confirmation of any accepted church candidate, including close-up stone edges.
- [ ] Prove a fully integrated host editor's actual mask provenance and direct-to-ChatGPT native image save.
- [ ] Achieve clear editorial improvement in at least **two of the three** existing photos, with independent fixed-object/naturalness approval, before adding nine new photos.

**Keep PR #45 Draft, NO-GO for installation, merge, release and expanded photo testing.** Do not claim the new courtyard result is a professional portfolio final.
