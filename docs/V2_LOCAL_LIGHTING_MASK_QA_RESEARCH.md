# Photo Finish 2.0 — local-lighting and mask QA prototype

**Status:** isolated experimental code, NOT installed, merged, released, or part of the current stable Skill. No private images, account URLs, reference assets, or output bytes are committed here.

## Goal and non-negotiable constraints

The user wants a visibly stronger, independent-photography-magazine / photographer-portfolio aesthetic without a generic filter or obvious AI-rendered appearance. The final image must preserve real buildings, natural objects, facilities, signs, people, their spatial relationships and their recognizable details. A reference image with attractive color is not sufficient if it reconstructs these elements.

Photo Finish 2.0 should first inspect the photograph, select one clear creative direction, then execute only *supported* image adjustments. Source alignment, natural visual coherence and major fixed-scene identity are HARD STOP conditions. A stronger contrast slider cannot compensate for inadequate light control.

## Real 3-image exploration (2026-11-03, authorized images retained outside Git)

- **Historic stone facade under blue sky:** The first new semantic mask for the building selected primarily the **sky**, not the facade, despite reporting tool success. Repeated prompt did not correct it. An earlier visually inspected facade mask on unchanged scene geometry was usable; no crop or perspective operation was applied. Changes to sculpture tonality were still modest.
- **Macau street at night:** The illuminated tall hotel was selected credibly. Right-side old buildings were selected too broadly; road selections caught only part of the foreground and were rejected for broad local sculpting. Signs, exact lettering and people are protected. Warm building light separation improved slightly, but a decisive visual hierarchy was still lacking.
- **Courtyard through dark frame:** The dark surrounding frame was selectable with some inclusion of foreground ground; strong changes were inappropriate. A fountain-specific selection failed; another foliage mask included sky/background. The edited result remained aesthetically restrained with no demonstrated portfolio-level improvement.

**Observed failure classes:** selection tool reports success but selects the opposite subject; oversized/spilling selection; incomplete mask; total mask-generation failure. This dataset is deliberately qualitative: no algorithmic accuracy scores, objective photometric measurements, or claims of universal sample coverage.

## Proposed production integration

1. A photo editor returns an actual source image and geometry identity. Geometry is inherited across **light/color only** edits but changes on crop, rotation, perspective or generative reconstruction.
2. Request the positive target region (building, sky, frame, etc). Inspect returned mask pixels against the real photo before any masked change. Do not treat API `success:true` or a bounding box as reliable evidence that the right subject was selected.
3. Record an explicit visual classification **verified / partial / leaking / wrong_target / unverified** with concrete inspection notes. The experimental gate rejects everything except verified. Rejected masks trigger a safer alternative, such as unmasked conservative tone work or a STOP; do not silently loosen the rule.
4. For an approved mask, use the actual host editor on the *unchanged geometry* with limited exposure/tonal controls. Keep the protected subject/text regions safe. Never add invented object geometry for expressiveness.
5. After editing, inspect the exact output at both full-image and relevant local-detail scale. Accept only if the photograph has visibly better composition/subject hierarchy, light, color and atmosphere **AND** fixed content, text and natural look remain intact. A "mask accepted" flag does NOT imply "photographic image accepted".
6. Deliver one actual accepted final image directly; use saved file/version receipts only after genuine host verification. Avoid mandatory extra model calls or mandatory multi-candidate rendering.

## Experiment interface

`experiments/v2_local_light/mask_gate.py` provides an intentionally small, dependency-free **pre-edit safety contract**:
- requires an approved actual mask URL, concrete visual note and positive normalized bbox;
- binds region and source geometry identity; blocks reuse across geometry changes;
- refuses unknown, partial, leaking or misdirected masks;
- **blocks strong localized changes** until the adapter can verify feathering and absence of halos at object edges; the present prototype has no such verified capability;
- requires known edit strength, explicit fixed-object protection and actual image preview;
- independently gates final visual-acceptance claims.

### Pixel-audited feathering spike (separate from the existing gate)

`experiments/v2_local_light/pixel_mask_qa.py` adds an **isolated**, non-network Pillow prototype. It does not automatically run in Photo Finish v1.x or the current V2 editor. It requires four *same-geometry* 8-bit grayscale masks: returned selection, a separately inspected unmistakable target **core**, a separately inspected broader **allowed region**, and a **protected detail** mask. The latter three are supplied by an actual reviewer and **are not machine-inferred from the image**.

- Pixel check rejects empty/full-frame selection, missed target core, out-of-region selection, and any mask overlap with protected content; records mask, core, allowed and protected digests.
- Deterministic bounded Gaussian feathering (radius 1–10 px) contracts the binary edge before blur, checks the dilated blur support fits the allowed region, and excludes protected details with a safety margin.
- Tonal-only compositing supports unchanged image geometry and checks actual protected source pixels remain **bit-exact**. The output cannot silently mix different sizes, color modes or modified alpha receipts. No source/photo material is committed to Git.
- `tests/test_v2_mask_feather.py` has **14 synthetic cases**, including wrong sky-vs-facade, incomplete road mask, protected sign leakage, wrong geometry and single-level color corruption. They were executed locally under Python 3 / Pillow 12.3.0; CI must re-run under this repository's required Pillow 13 before claiming full compatibility.

**Two separate limits:** (1) the existing `mask_gate.py` does not inspect pixels itself, call a pixel-mask adapter, or allow strong edits; (2) the new standalone pixel prototype does not determine semantic subject identities, ensure that source and candidate share real scene geometry, manage Display P3 to sRGB/ICC/metadata, call an image provider, or establish halo-free/portfolio-grade photographic results. A separately observed **real photo and same-source V3/V4/V5 comparison** remains mandatory. Neither test success nor numeric mask overlap authorizes `visual_status="verified"` without actual human/assistant inspection.

**Limitations:** The existing selection gate does not inspect actual mask pixels, compute segmentation IoU, feather boundaries, call Adobe, edit photos, compare photographic aesthetics, store user media, or modify the existing Skill. The calling editor/reviewer must provide real evidence and will still need integration. A dishonest reviewer could still mark a mask verified; this module cannot detect that. No claim of better real photos is justified by passing these protocol tests.

## Promotion gates

- [ ] Implement a real editor adapter supplying reviewed masks and geometry lineage.
- [ ] Add real-photo negative cases (wrong sky/facade inversion, partial street selection, frame leakage) privately, without uploading photos to public Git.
- [ ] Confirm the same-source V3 vs V4 result actually improves at least two of the three authorized scenes; gather user preference and inspect real pixel edges/wording.
- [ ] Integrate with the rewritten Skill directions, preserving STOP and old versions; do not silently enable the experimental contract for installed v1.5.7.
- [ ] Run full existing CI/manifest requirements and independent review on a new version-specific candidate, then broader 9-photo study only after initial quality gates pass.

This is research evidence and an integration starting point, not a release milestone.

## Phase 3: source-bound tonal adapter and real-V5 readiness (2026-11-03)

`experiments/v2_local_light/editor_adapter.py` is an **isolated experimental adapter**, not a current Skill route and not a connected Adobe capability. It consumes externally produced same-source tonal-only images, source-aligned segmentation masks and independently reviewed target/allowed/protected maps. Before compositing, it fails closed when operation provenance is not declared as non-generative tonal work, real mask inspection is missing, geometry/source-pixel hash differs, orientation is not normalized, color profiles differ or are absent, RGB dimensions disagree, tonal delta is above the configured bound, or the pixel-mask QA gate rejects the selection. After bounded feathering it checks that protected source pixels and the area outside the allowed zone remain unchanged. Output is marked `technical_candidate_only_not_visual_acceptance`, never automatically promoted to a V1/V5.

**What is verified:** the 10 synthetic adapter tests passed in the local Pillow 12.3.0 environment, together with the existing 14 synthetic feather tests (24/24 total for these two isolated suites). A CI result using the repository's required Pillow 13 is separately required. These are computational contract tests, **not a real-photograph quality or fidelity certification**. Caller assertions about source lineage and semantic mask correctness are not independently established by this module.

**Real-input readiness:** three authorized originals were read locally without alteration; each has 1152×1536 pixels, EXIF orientation 1, and an embedded Display P3 profile. Individual source SHA-256 hashes and identities are retained in a **private, non-Git report**. The Adobe V4 outputs and segmentation masks were previously visually inspected through the editor, but direct full-resolution byte transfer into the experimental local adapter is unavailable from this host. Therefore none of the three has a completed V5 produced by this integrated route. No V4→V5 superiority claim is supported. Do not stage private originals, outputs, asset URLs, style references or per-photo records in this public repository.

**Next real-photo gate:** use an approved asset bridge that preserves exact bytes and ICC; record actual editor-tonal-only provenance and geometry, inspect source-aligned target/allowed/protected masks, produce V5 for these same three authorized originals and compare real V4/V5 images for stronger composition/light/color, absence of halos, stable architecture/words/people and photo-like naturalness. If the bridge or any fidelity check remains unavailable, STOP rather than substitute a generated look or counterfeit provenance. Keep PR Draft.

## V6 real-scene art direction (two independent same-source photo trials; 2026-11-03)

Following earlier V5 original-based trials, two private same-source **non-generative** editorial variations were produced in the local working container (no Adobe V4 bytes were used and this PR's experimental \`editor_adapter.py\` was **not** called to create V6). These are research results, not a claim that the repository integration is finished.

- **Macau night street:** stronger warm hotel/black street hierarchy through spatially smooth luminance and chromaticity changes; no new or removed objects. The selected V6 full-frame result retains 1152×1536 geometry and sRGB ICC. Relative to same-size V5, SSIM is 0.9296 and 1-pixel-tolerant edge recall is 0.8737. Some sign subregion SSIM values fell to approximately 0.89–0.95; preserved lettering remains a required human QA item.
- **Courtyard through dark wooden frame:** focused daylight/fountain and patio shadow corrections plus a true 4:5 photographic crop of existing pixels to 1080×1350. No replacement or redrawing of branches, jets, window, or background. SSIM 0.9733 and edge recall 0.9368 **against the equivalently cropped V5 region**, not the uncropped frame.

The photo sources, preview thumbnails, output bytes, exact asset hashes, actual crop coordinates and expanded assessment remain **private**, outside this public repository. The numbers above describe signal similarity/structure retention, not aesthetic preference or photo-identity proof; the user's own V5/V6 choice remains pending. The night street appears more intentionally cinematic, while the courtyard's largest gain is compositional and its tonal improvement is limited. This is insufficient for 2/3 strong-quality pass; **still NO-GO for promotion**.

### CI status nuance

At the previous PR head \`5b60007b38b1e686f5bbf7fc729ccd0312b0f675\`, GitHub workflow run \`41665134413\` completed 6/6 successful validation jobs. Concurrent run \`41665141486\` had 5 successful jobs and a **cancelled** macOS job; it is not a second 6/6 success and not established as a source test failure. The source change in this section is documentation only and requires its own current-head CI.

**Next acceptance hinge:** secure an actual full-resolution source/mask bridge for the adapter; enforce mask/source/ICC lineage, compare true locally integrated photo renders, and get an explicit user preference result before broad 9-photo tests. Keep PR Draft and keep the released Skill unchanged.

## Actual user review of V6 (2026-11-04)

The user reviewed the actual two V6 renders against the earlier results:

- **Macau night street:** "明显改善" (clear / noticeable improvement). Mark as a **positive subjective improvement signal** for this *one* scene. Do not extrapolate to all night scenes, do not assert a magazine-level pass, and keep the separately identified protected-sign detail risk open.
- **Courtyard through window:** "并未有显著区别" (no significant difference). Mark as **NO-GO for expressive-improvement criterion**, despite correct protected geometry and a 4:5 crop. The crop alone did not produce the intended step-change in photographic expression.

**Updated experiment decision:** One positive sample and one negative sample; the required 2/3 real-scene improvement criterion has NOT been met. Do not proceed to the nine-photo extension or promote the prototype. Preserve existing V5/V6 source assets for private comparison.

**Next controlled experiment:** Re-examine the courtyard's value proposition before changing parameters. Set a concrete visual hypothesis for the viewer's attention: the dark frame acts as a quiet near-field boundary, while outdoor dappled light, water arcs and sunlit patio carry the narrative. Compare a single constrained intervention with the V5/V6 baseline, without hallucinating fountain jets, moving branches, reconstructing background buildings or destroying natural timber texture. Confirm that the edit route can actually act on those regions; reject failed or leaking masks. Consider the scene **unsuited for forced dramatic editing** if actual source data and masks cannot support a material aesthetic gain. Record the user's comparative preference independently from technical gate checks.

This feedback is about visual preference only. It does not authorize publishing the photo, collecting it in a permanent style library, or merging/releasing the experimental PR.


## Courtyard V7 same-scene corrective trial (2026-11-04)

A previous generative V7/V8 comparison infographic depicted materially different architectural framing, tree layout and an ornate central fountain that **do not exist in the authorized courtyard photo**. That infographic is **invalid test evidence** and its assertions of portfolio-grade success are rejected. It was not an acceptable Photo Finish delivery.

A corrective local experiment used the **actual V6 courtyard file as the immutable scene source**. Three controlled non-generative, source-pixel tonal candidates were tried, affecting only existing outdoor sunlight, foliage shadow and original horizontal fountain water jets; one restrained candidate was selected for direct V6/V7 review. The selected full-frame result is 1080×1350, retains the baseline ICC bytes, and three specified dark-frame reference zones remain bit-exact. Pixel operations only (no generated tree, new building or substituted fountain), with an observed largest RGB channel change of 50 levels and 47.37% of pixels receiving some degree of tonal change. Real source/result bytes and hashes remain private, not published to GitHub.

**Finding:** this V7 is a technically inspectable, same-scene candidate but the composition and subjective editorial impact remain close to V6. Therefore **NO-GO for significant expressive improvement**; numerical pixel change alone is not evidence of editorial quality. The three candidates should not be marketed as V7 quality-accepted outputs. One neighborhood image may have limited potential for dramatic, natural retouching because the real water feature is a distributed series of arcs, not a tiered central sculpture. Do not hallucinate or reconstruct a new fountain to match an aesthetic mockup.

**Next decision:** stop repeating incremental saturation/contrast/exposure on this sample. Require a *new* photographic hypothesis, e.g., whether the actual light-and-shadow framing is worth publishing as-is or whether a legitimate alternative crop changes the storytelling without removing key architectural context. A visually stronger design that changes fixed objects fails regardless of apparent magazine quality. Reuse the authorized original only; do not extend the remaining nine-photo set or merge/install the research Skill until a genuine quality result is obtained.


## V9 three-source real-photo mask retest and discovered highlight risk (2026-11-04)

Three existing, individually authorized user originals (historic church, Macau night street, and framed courtyard) were reused privately without modifying their bytes. Each 1152×1536 Display P3 JPEG was explicitly converted to a separate sRGB working PNG; the full raw-source identities were checked against the earlier private readiness records. **No user image or source filename, private SHA, mask/preview content, Adobe asset, user style, or private reference was committed.**

New independent **hand-scoped** masks were drawn against each original's image coordinates, with a separately identified interior target core, expanded allowed region, and protected content. The first courtyard protection polygon was demonstrably wrong (it covered the entire target interior) and was **rejected and corrected before editing**. The checked masks then had zero known protected overlap and zero outside-allowance coverage. Each mask's 3px soft-edge support was checked against its explicit allowance. These are *bounded human-inspected editing regions, not automated semantic segmentation guarantees or full structure identity certificates*.

A private, independent local Pillow/OpenCV tonal experiment used these current source-aligned masks and the V2 `editorial_contract` preflight. Three true same-pixel V9 candidates were created at full original dimensions, without generative reconstruction or crop. Pixel QA checked no changes outside the soft-support region, exact unchanged protected pixels, original dimensions and real sRGB ICC. This was a **local photo harness, not the published Skill's runtime or a call of the GitHub `editorial_pipeline`**. Its local result does not prove the GitHub runtime can access production Adobe files.

**Discovered real-photo defect:** initial non-generative local contrast adjustments created **over 25,000** additional clipped-highlight pixels on church and **over 29,000** on courtyard; existing structural/crop gates did not flag this. The local harness was corrected to cap positive per-channel highlights before compositing, and rerun. Final V9 newly clipped pixel counts were **zero** on church/night street and non-positive on courtyard; other requested protected-pixel/edge checks passed. The new experimental GitHub `editor_adapter.py` now includes a *research-only*, configurable 0.2%-of-image newly clipped-highlight veto, with synthetic negative tests; this is not an established general professional threshold and it does not automatically approve color/aesthetics.

**Editorial verdict:** V9 church's stone relief is slightly stronger, night street hotel's light differs slightly but does **not** surpass the user-approved V6, and courtyard garden retains the known too-subtle narrative weakness. All three are marked **NO-GO on expressive improvement**; retain V6 street as the positive user-judged baseline. This is precisely why technical masks/ICC/edge tests must remain separate from the three-axis spatial/natural/expressive evaluation. No new official V1, new personal reference, merge or Skill install is authorized by this research.

**Next hinge:** demonstrate the actual checked candidate/mask provenance via the GitHub editor adapter and real host route, then test a higher-level (but source-preserving) photo direction capable of producing visibly better *first output* than these local tonal changes. Do not continue numerical slider retries on the courtyard without an explicit, testable compositional/light-and-shadow hypothesis; only expand to nine photos when genuine 2/3 subjective-quality and content-safety gates pass.


## V10 source-pixel spatial lighting spike (2026-11-04)

**Hypothesis:** V9 was content-safe but artistically weak because it mostly applied a uniform lightness curve inside one semantic mask. A bounded, **spatially positioned** dodge/burn field should have more potential to establish the planned foreground→subject→background viewing path, without moving or synthesizing objects. This is a falsifiable hypothesis, not a claim of success.

**Implementation:** \`experiments/v2_local_light/spatial_light_field.py\` introduces 1–4 explicit \`LightNode\` objects, each with a scene-reviewed selected mask, independently inspected target core, broader allowed/support region, protected objects, normalized image-space center, elliptical light falloff and signed bounded tone strength. Pure-Pillow deterministic ellipsoid gradients, thresholded mask checks, a narrow soft edge and smoothly shouldered per-channel midtone curve preserve original pixels outside verified regions. The engine rechecks the decoded source-pixel fingerprint and caller-supplied file SHA agreement, protects all explicitly flagged detail pixels, refuses masks that miss the actual core, rejects light spill outside allowed regions and refuses newly saturated channel values. Its output status is always **PENDING_USER_VISUAL_REVIEW**. It does **not** perform semantic segmentation, source-to-Adobe file transfer, actual service provenance checks, automatic artistic evaluation, host save or Skill runtime integration.

**Actual three-photo observation:** the same three previously authorized source JPEGs were handled only in the private local working container, using previously visual-checked image-coordinate region/core/protection maps and verified Display P3→sRGB working PNGs. The original bytes were unchanged. A first experimental tone shoulder was correctly **rejected** because a few RGB=254 highlights rounded up to 255; the actual curve was corrected to retain 255 only where the original source already had it. Revised same-geometry source-pixel V10 trials then passed observed protected-content, ICC, allowed-zone, and no-new-clipping checks. Mean absolute per-channel changes compared to each original (not a quality score): **church 4.68**, **night street 1.71**, **courtyard 3.63** in 8-bit RGB levels. Therefore the overall visual impact remained **too weak at ordinary viewing scale** to satisfy the user’s explicit editorial/spatial-storytelling goal. The approved Macau night street V6 still has stronger subjective evidence than the V10 trial. The real photo outputs, user filenames, hashes and masks stay private, not in GitHub.

**Test evidence and limits:** fourteen synthetic local tests passed with Pillow 12.3.0, including source mismatch, independently inspected core coverage, protected pixel fidelity, incorrect masks, bounded light amount, source immutability, directional movement of focal lighting, multiple light nodes and clipping prohibition. The latest GitHub head must run the project-required Pillow 13 and six CI jobs before any compatibility statement. Even 14/14 synthetic success is **not** a claim of portfolio-level quality. Mask geometry, color-space, and “light placement” are reviewed/defined by the caller; the module does not infer spatial storytelling on its own.

**Research decision:** V10 is **engineering-only**, NO-GO for current photographic quality. Do not replace user-approved V6, force further slider revisions of the courtyard, merge Draft PR #45, publish, or install this prototype. A genuinely new multi-region foreground/subject/background art-direction route with independently verified masks and *normal-size* side-by-side creative review must demonstrate a clearly improved first photo before promoting any real image engine. An already strong original may justifiably be retained unchanged if realistic further gains are unavailable.
