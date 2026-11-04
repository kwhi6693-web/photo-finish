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


## V12 independent real-photo review: a STOP is a valid outcome (2026-11-04)

**Church:** independent inspection of the real revised V11 render at full and detail size still found visible sky/stone edge artifacts (particularly around the upper pinnacles). The V11 engineering mask pass is not a photographic-quality pass. A single controlled V12 trial used only the *original* 1152×1536 sRGB pixels: the sky and stone each had a deliberately retained unchanged narrow boundary corridor and inward-only tonal fade. Despite source identity, ICC, geometry and 0 changed pixels within the designated seven-pixel boundary guard, the **real V12 still visibly produced scalloped tonal contours outside the spires**. The visual sample is rejected: even an unchanged immediate pixel border does not ensure natural optical transition. Do **not** use this V12 as an accepted final image or treat the engineering proof as evidence that halo control has been solved. This shows the current coarse semantic boundary and fade topology are inadequate.

**Courtyard:** a single alternate, source-pixel-only V12 creative hypothesis tested the dark aged wooden frame as a stable vantage point while reducing competing courtyard/patio/background luminance and leaving the original fountain arcs, leaves, stones and structures unchanged. The window-interior mean weighted RGB luminance went from approximately **123.5** to **102.5** within the inspected region; the wood/frame exclusion mask changed **0 pixels**, ICC stayed the same, dimensions remained 1152×1536 and there were **0 newly clipped RGB 255 channel pixels**. However, in the actual normal-size side-by-side image, lowering overall outdoor brightness did **not** create a convincing new first/second viewing path or a material magazine-level photographic improvement. **NO-GO for expression**. Do not reinterpret this 21-level brightness shift as an artistic pass.

**Engineering response:** the experimental `editorial_contract.review_editorial` now requires two separate explicit observations for source-aligned local edits: `edge_detail_reviewed is True` and `halo_or_seam_absent is True`. Synthetic negative tests reject absent/false/truthy-string claims. This is a fail-closed **review contract**, not automated halo detection, and a dishonest reviewer or imprecise segmentation is still possible. Current-head CI and human inspection remain required.

**Decision:** do not run V13 merely by further adjusting gamma or blur radii. Preserve the **user-approved Macau street V6** as a positive reference; mark both church and courtyard *not quality-accepted* under the present local editing capability. Continue only if the editor can demonstrably obtain high-fidelity semantic scene boundaries and a non-haloing natural transition, or if an independently justified change to the photograph's real spatial storytelling becomes possible. No new user photos required until that prerequisite is met. All real media/asset hashes remain private; only qualitative observations and aggregate ROI statistics are documented in Git.

## A/B editing capability comparison (2026-11-04; private same-source trial)

**Decision being tested:** whether a genuinely more scene-aware *non-generative* tonal operation beats a traditional full-frame color grade, before more Skill safety code is written. The same authorized church and Macau night street originals were compared under two actual pixel-edit techniques. Images were decoded from privately verified full-resolution 1152x1536 sRGB working sources, and only real source pixels were processed. No new source, object or geometry was generated, no personal photos or hashes are committed.

**A — global grade:** smooth full-frame film-like tonal curve + restrained color contrast. **B — scene-adaptive:** (church) original-pixel color distinction between stone and blue sky, bounded bilateral texture-local enhancement, and continuous source-color tonal weighting without coarse binary sky/stone masks; (night street) broad position-aware context/road darkening, with original warm-light colors used to retain hotel illumination.

**Night-street descriptive ROI mean weighted brightness, 0–255:** near road **93.1 original / 86.1 A / 71.7 B / 66.9 user-approved V6**; warm hotel region **58.0 / 52.0 / 52.8 / 56.8**, respectively. Side buildings **39.3 / 32.4 / 31.5 / 33.9**, close signs **92.0 / 84.5 / 80.3 / 72.1**. The hotel ROI includes dark architecture; these are not supposed to be absolute spot-luminance readings. B more closely reproduces the *relative context recession* of V6 than A; no user approval of B or causal proof of excellence.

**Church outcome:** B makes some stone relief more distinct and mildly reduces sky competition, but does **not** produce a compelling magazine-level editorial improvement over the source. A is less directional still. The earlier scalloped sky-boundary failure from coarse masking was not seen in the inspected detail crop of B, but this is not a full independent edge acceptance.

**Technical evidence:** output sizes and pixel coordinates match the originals; original sRGB working ICC bytes remain in outputs. An initial sRGB conversion introduced new channel-255 pixels, which were **rejected and subsequently reduced to zero** by a source-conditional highlight guard in all four A/B experimental outputs. This is local trial logic, not a commit to the current production editor. Lighting and color operations were purely source-pixel transformations, so readable signs and building shapes were not text-generated, but detailed final visual identity must still be reviewed independently.

**Actual verdict:** both approaches are **research candidates, not accepted final photos**. B is a more promising tonal *component* than A for establishing scene priority, but B has not surpassed the real user-preferred V6, and the church does not have a verified expressive step-change. These outcomes directly discourage continued small gamma/brightness iteration or adding more acceptance checkboxes without a higher-capability editor. The next meaningful comparison must use a demonstrably different, authentic editing capability with high-quality region/edge awareness, traceable full-resolution output and original-scene identity. Keep PR Draft and don't start the nine-photo extension.

## Promotion decision

- [x] Quantify the specific photo the user preferred, without making that its universal color recipe.
- [x] Build and synthetic-test a source-preserving multi-zone test adapter.
- [x] Compare two additional genuine same-source images locally without publishing personal assets.
- [ ] Latest-commit six-job cross-platform CI and independent engineering review.
- [ ] User/independent visual confirmation of any accepted church candidate, including close-up stone edges.
- [ ] Prove a fully integrated host editor's actual mask provenance and direct-to-ChatGPT native image save.
- [ ] Achieve clear editorial improvement in at least **two of the three** existing photos, with independent fixed-object/naturalness approval, before adding nine new photos.

**Keep PR #45 Draft, NO-GO for installation, merge, release and expanded photo testing.** Do not claim the new courtyard result is a professional portfolio final.
