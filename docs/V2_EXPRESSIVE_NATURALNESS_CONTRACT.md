# Photo Finish 2.0 — expressive naturalness contract (research)

**Status:** working design standard for Draft PR #45. This document does not change the released/installed Skill. It records the user's explicit 2026-11-04 long-term preference and the acceptance logic for implementation.

## Non-negotiable objective

> **Natural coherence is a hard constraint, not a command to weaken photographic expression.** A photo must look like a credible professional post-processing result of the *same real photographed scene*, with meaningful visual direction and a noticeably more mature first delivery wherever source information permits. "Remove AI look" does **not** mean "reduce saturation, contrast and editing to near zero."

Two **independent, equally necessary** decisions are required:
1. **Photographic fidelity and naturalness:** fixed buildings, scene objects, tree/branch geometry, real fountain/reflective patterns, readable text, important people and physical relationships are not reconstructed, erased or replaced. Tonal/color edits, a legitimate crop and controlled editing of the photo's recorded details are permitted. No conspicuous halos, painted textures, plastic smoothness, imaginary lights, impossible water lines or CG-like material.
2. **Editorial expressiveness:** the actual edited result establishes an intentional hierarchy, light direction, color design, spatial depth and story. Where meaningful improvement exists in the source, a minimally different or merely cleaned-up edit is **insufficient**. Aim for restrained but strong, independent-magazine / photographer-portfolio visual impact from the **first output**; do not force a universal blue/gold LUT, night exposure or specific contrast amount.

**Acceptance is a three-axis AND gate:** (1) fixed-scene integrity/natural look PASS, **and** (2) a perceptible and fitting spatial narrative PASS, **and** (3) observable editorial impact PASS. A technical editor/ICC/geometry pass alone does not authorize visual quality claims. Numeric SSIM, changed-pixel count, or model-led image similarity are supporting diagnostics, not photographic proof.

## Universal spatial-storytelling rule (explicit user requirement, 2026-11-04)

> **Every photo must deliberately convey spatial storytelling while retaining meaningful photographic expression, aiming for independent photography-magazine / professional portfolio quality.** This is a required photographic decision and review dimension, not an instruction to impose the same foreground/background formula, crop, lighting preset or high-contrast look on all photos.

**What "spatial storytelling" means:** The image makes the viewer understand *where the subject is*, its relationship to the surroundings, *what to notice first and next*, and how light, shadow, scale, layers and negative space direct attention. A minimalist or close-up scene may achieve this through subject/background distance, texture, shadow, scale or negative space; it does **not** need artificially added physical depth or three mandatory layers.

For every photo, the photographic direction must explicitly document, before any editing:
1. **Spatial premise** — subject + environmental context + the visual relationship or scene being narrated (not merely an object category).
2. **Viewing route** — attention entry, principal point of interest, secondary discovery, and the relevant foreground/middle/background or simpler spatial structure; retain useful negative space.
3. **Narrative leverage** — the real, source-supported light gradients, color separation, framing edges, perspective, scale, reflections, texture or ambient motion that can strengthen that relationship.
4. **Visual intervention** — the specific intended change visible at normal viewing size and its protected structure, e.g., local dodge/burn, restrained highlight emphasis, color distribution or justified crop, with enough strength to be perceptible but without inventing scene features.
5. **Failure criteria** — reject if the result feels flat/undirected, overwhelms its environmental context, relies on generic filters, only looks subtly "cleaned up", or distorts fixed content/creates halos/CG-like lighting.

**Real-photo check, not self-scoring:** Compare the exact source and output at the same viewing crop. Answer: "What is the scene telling? Where does the eye go first and second? Is that route visibly more coherent and expressive? Does the image still look naturally photographed?" Record a reasoned human/user assessment instead of claiming an unsupported objective magazine-quality score. If no credible stronger edit is possible, retain the source and report the limit rather than fake improvement.

**Scene-specific examples from actual tests:**
- Historic stone facade: the shadowed near-side passage becomes a spatial threshold leading to the sunlit stone architecture and the open sky; do not merely saturate the blue sky or distort carvings.
- Macau night street: foreground people/signage supply lived city scale, receding road creates depth, warm hotel lights provide the main visual destination; preserve literal sign text and real people.
- Window courtyard: dark aged window frame is the observer's position, the existing lateral fountain arcs and tree shadows lead into the sunlit courtyard beyond; do **not** invent a tiered fountain or sacrifice the authentic frame simply to enlarge leaves.
- Macau tower night reference: tower–river reflection establishes vertical depth/axis while dark water and opposing riversides give quiet context; reference the *principle*, not universal color values.

**Release gate:** A photo with technical fidelity but without a readable spatial narrative and substantial artistic gain is still NO-GO for *improved editorial output*. Conversely a visually dramatic image that reconstructs buildings, trees, water structures or text is NO-GO for fidelity. Strong is not synonymous with oversaturated, and natural is not synonymous with weak.

## Real operating rules

- **Inspect:** Identify true subject, spatial premise, actual environmental relationships and existing aesthetic potential (light, material, geometry, narrative); confirm the source contains the data needed.
- **Direction before execution:** State an intended *visible* improvement (e.g., "night street: the lit hotel stands out against an appropriately dark road and authentic signage"; "courtyard: existing water arcs and dappled daylight become the story within a dark architectural frame"). Avoid instructions that only say "+5 contrast" or "soften".
- **Implement with justified amplitude:** Use scene-aware local dodge-and-burn, color relationships, tone/contrast distribution and purposeful crop with safe masks/edge transition; choose strength from observed image and quality gate, **not** a blanket "gentle only" constraint. Keep text, fixed scene structures and edges protected.
- **Compare actual images:** Compare the untouched source, previous real candidate, new real candidate at the same matched framing and a normal viewer size. Flag exaggerated/flat/AI-like results and defects. Explicit user preference is evidence but does not override discovered content deformation.
- **Fail constructively:** If a real photo is already excellent or no supported adjustment can deliver *meaningful* natural improvement, return the original/STOP and explain the limitation. Do not claim a conservative cosmetic change met the brief.
- **Delivery:** Show the actual final image inline; preserve the native, directly savable output. A synthetic visualization or generated comparison must never be substituted for the real accepted output.

## Applied evidence and pending work

- **Macau tower:** user-approved *aesthetic reference* for clear subject, dark-negative-space, warm/cool discipline and strong-but-natural atmosphere; never a mandatory color preset, and not equivalent to a fixed-scene fidelity pass.
- **Night street V6:** user said "明显改善". Positive evidence for visually meaningful editing on one photo, not universal validation.
- **Window courtyard V6/V7:** user reported no noticeable improvement in V6; source-locked V7 was also insufficient. More slider movement alone does not solve a weak art direction.
- **Window courtyard V8 exploratory fork:** two different strengths of source-pixel Lab tonal direction were tested on the real V6 in private; an alternative *true* 4:5 crop of that same photo was tested. V8 full-size 1080×1350; crop 900×1125. Original ICC bytes remained attached and original scene object geometry was not generatively altered. Early visual inspection suggests more contrast and subject occupancy, but the actual user/portfolio-quality result is **pending**. This is an experimental trial, not the Photo Finish 2.0 editing engine connected to Adobe or released v1.5.x. Do not upload raw assets or hashes publicly.

**Promotion gates:** For the three independent samples, require at least two with genuinely improved editorial quality and no uncorrected content violation; then continue the nine-photo study. Photo aesthetics and fixed-object fidelity must be evaluated separately. Keep PR #45 Draft until verified editor integration, full CI and appropriate independent review.


## Incremental implementation: editorial direction → source-bound local edit → three-axis review

**This is a Draft-PR-only research bridge; no released Skill runtime has been replaced.** The existing v1.5.7 `photo_edit.prepare/submit/returned/review` flow and `delivery_automation.direction_details` use six input fields. `experiments/v2_local_light/editorial_contract.py` now maps the actual observed spatial premise, viewing path, source light, target gain, fidelity and failure conditions into exactly those six supported fields **without inserting extra model calls**. It binds to the real source SHA-256 and checks reported native-editor, local-mask, ICC and geometry capabilities before suggesting an edit. This is a **preflight**, not a claim that a host tool has run or that its capabilities were independently inspected.

`experiments/v2_local_light/editorial_pipeline.py` takes an explicit local source file and a separately supplied tonal-only candidate and user-inspected target/core/allowed/protected mask. It recomputes the source file SHA before and after decoding/composition, runs the existing `editor_adapter.integrate_verified_tonal_edit`, and returns only a **PENDING_SPATIAL_NATURALNESS_EXPRESSIVE_VISUAL_REVIEW** in-memory result. It does **not** export a photo, handle an external image service, edit the installed Skill, create records, certify a magazine-standard aesthetic or implement direct iPhone save.

The V2 editorial review receives the actual observed source and output SHA-256 plus explicit real-image comparison and separate yes/no judgments for (1) fixed-scene naturalness, (2) spatial narrative gain and (3) visible expressive gain. Negative user feedback blocks acceptance. Passing this review alone never claims independent professional portfolio certification. The caller still has to carry out genuine image viewing and reliable file/host delivery; fabricated flags are not ground truth.

**Test evidence:** 17 synthetic decision/review tests passed in the isolated local Python staging directory. Nine synthetic end-to-end wiring tests were authored and submitted to GitHub for Python 3.11/3.12 / macOS / Windows CI validation. They require the actual repository's existing `editor_adapter.py` and Pillow 13. The three existing private real originals were re-read unchanged: each 1152×1536, Display P3, EXIF orientation 1, with full source-file SHA-256 matching; no new mask was visually certified for this bridge, so all three real-photo preflights intentionally return STOP. Exact filenames/hashes and the private read-only readiness report are **not committed**.

**Promotion remains blocked:** real host-level mask/tool provenance; a real photo using the new integrated bridge (not just a synthetic fixture), normal-size and edge-detail V5/V6-versus-new output comparisons, two out of three genuinely improved photographs, independent engineering review, and current-source CI success. The previous night-street V6 preference is positive one-scene evidence, not a quality pass for the new code. The courtyard has repeatedly failed the expressive-improvement criterion and must not be silently reclassified.
