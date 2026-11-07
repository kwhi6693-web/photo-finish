# Photo Finish 2.0 — Stage 1 / Stage 5: reference-only tone calibration and non-generative acceptance

**Status:** Draft PR #47 documentation supplement. User clarification: 2026-11-07. No runtime capability claims, photographic GO, formal V1, merge, release or installation.

## Governing decision

**Photo Finish does not perform generative photo editing.** The four source/reference pairs below are `REFERENCE_ONLY_STYLE_CALIBRATION`. Three later stylized images were generated with an image-generation tool; the earlier sky reference's production provenance remains unverified. They are references for *tonality, saturation, warm–cool relationships and shadow hierarchy only*, never content goals, permitted output routes, real edits or accepted V1s. A reference may contain invented information and is not a safe representation of the original photograph.

Never upload private source/reference photos, hashes identifying user files, Library IDs or local paths into the public repository or public release package; the exact private identities belong only in the user's private sample manifest.

## Stage 1 — four style-calibration pairs (not production-success samples)

| Pair | Can be explored with **actually supported bounded, source-preserving** operations | Reference-only alterations **excluded as goals** | Review / classification |
|---|---|---|---|
| **Sky, older source + stylized reference** | Encoded luminance histogram and highlight shoulder; restrained global monotone curve; chroma magnitude; warm/cool balance in source-supported regions; shadow separation and smooth gradients | Added/repainted cloud wisps, recreated sky texture or invented light, unknown resampling and reconstructed geometry | `T1 / T3`; original 960×1280 and reference 1086×1448; reference provenance unknown, even though it has an ICC; distributional description only |
| **Backlit stone street** | Source-supported exposure/brightness distribution, sunlit cobblestones and dark foliage balance, bounded saturation, warm highlights vs cooler shade, existing shadow texture | Added clouds, rewritten or improved-looking street-sign text, fabricated objects, replaced leaves or sun rays | `T2 / T3 / T5`; source and reference differ in dimensions; model-generation reference carries no embedded ICC |
| **Antique-sign alley** | Facade midtones/contrast, shadow layer depth, source-based sign color and restrained saturation, warm wall/cool shade balance, highlight protection | Rewritten Chinese/Portuguese text or glyphs, invented windows/air conditioning/wiring, changed facade geometry or sky | `T2 / T3 / T5`; text and structure are source-anchored mandatory protections; model-generation reference has no embedded ICC |
| **Waterfront city night** | Dark tonal distribution, real-pixel noise reduction if supported, highlight roll-off, warm building lights vs cool sky, actual reflected-light saturation and recoverable shadow hierarchy | Canvas extension/reformatting, shifted or fabricated skyline, invented windows/lamps, hallucinated water reflections | `T3 / T5`; original is **landscape 1448×1086**, reference is **portrait 1086×1448**; no pixel alignment; generated PNG has no embedded ICC |

The first three newly generated references are **confirmed generative** in the conversation, not merely suspected. The sky reference's editor is **unknown**, so it must be treated as untrusted style reference, not labeled with unproved image-creation provenance. A missing embedded ICC does **not** itself prove generation; a constant output dimension is supporting suspicion, not an independent classifier.

### Measurement rules

1. Keep the existing Stage 1 metric definitions: encoded sRGB `L = 0.299R + 0.587G + 0.114B` (a display-encoding proxy, not linear luminance), P01/P50/P99, chroma-radius, highlight headroom, semantic ROI warm/cool, local 8×8 texture/contrast, P05 shadow and near-black counts. Honor actual input ICC through color conversion; references missing ICC are assumed sRGB for **descriptive statistics only** and explicitly flagged.
2. An unregistered crop/scale or changed object means no valid same-pixel difference, SSIM, 1:1 source-reference attribution, content-mask comparison, or reference-driven target numeric threshold. Global distributions may be reported descriptively but can be biased by new/generated content and must not be optimized blindly.
3. Register each pair with two separate lists: `bounded_editing_calibration_dimensions` and `excluded_reference_content`. Plan source-supported adjustments only; if an effect in the reference depends on imagined clouds, lettering, building detail, synthetic sky or reflections, mark it **NOT_REPRODUCIBLE_AS_NON_GENERATIVE_TARGET**, not a shortfall of current bounded-curve strength.
4. The user may choose a style direction without accepting the reference image as an output. Reference-only membership **does not count** toward the eight independent, genuinely edited samples or historical photography GO. Source originals may later join the eight-photo corpus only through a separately authorized, source-bound, non-generative real task.
5. Freeze source/actual-candidate source hashes, original-source ROI and user-protected text/geometry before editing. The reference can influence color/tonal priorities but never define the allowed content changes or masks.

## Stage 5 — acceptance comparison and content-change exclusions

For every true real-photo trial, use **three distinct, non-substitutable identities**:

- **S:** authentic camera-original photograph, source SHA/ICC/orientation and protected semantic content. This is the sole source-of-truth for structure, text, architecture, sky objects and natural texture.
- **R:** reference-only style image, possibly generative. It is never the controller result and contributes no content truth. If an approximate original-scene region can be verified, a qualitative/aggregate tonal comparison may be made after noting crop/color-space differences. Otherwise do not compare it as an exact target.
- **C:** actual output from the verified **non-generative Photo Finish controller**, with source and output receipt, complete SHA, PNG/ICC and same-source ROI evidence. Only C may be submitted for real candidate inspection and user GO/NO-GO.

**Exclude** from S/R style scoring all reference-induced differences in content, such as new clouds, changed lettering, changed street fixtures/building detail, altered perspective/canvas and synthesized water. Incompatible or unpaired pixels are **not scoreable**, not a negative result and not an invitation to reconstruct them. Do not compute content-weighted similarity to R or ask whether C copied its novel objects. Any acceptance statistic must state the exact valid source-based region, any excluded region and the reason; non-overlapping night compositions have no valid 1:1 S–R score at all.

**Do not exclude real C content failures.** Changes to source-sign text, fixed architecture, critical objects, real sky features or substantive reflections **in Photo Finish's own candidate C** remain ordinary **failure/STOP** against S; they are never excused by being present in R. The actual source-to-controller-result technical gates (source SHA, ICC, dimensions under the declared non-generative crop operation, mask bounds, signed-off protected ROIs and visible 1:1) remain fully applicable.

Stage 5's eight authentic photographs, any 2–3 designated difficult scenes and user blind testing retain their existing independent gates. These four **reference pairs contribute zero accepted edits** to the eight; a camera-original that is later separately edited may contribute one genuinely independent trial at most. Historical river/building/Church/Wynn GO and night NO-GO retain their precise prior meaning; generated examples cannot reverse them. No automatic strength threshold or new editing technology is implied by this documentation.

## Evidence and scope

The user's private companion inventory holds the precise four source/reference image SHA-256 identities, dimensions and ICC presence. The current connected repo baseline must be checked before any further change. This supplement only clarifies **what the four references are allowed to teach** and **how they must be excluded from content comparison**. It does not declare any new photo accepted or any controller defect repaired.