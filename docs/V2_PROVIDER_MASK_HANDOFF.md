# Photo Finish 2.0 — provider mask handoff (P0 engineering gate)

This is isolated PR #47 research; NOT an installed Skill or an accepted V1.

## Observed real Adobe capability on an authorized private church photo

- An existing Creative Cloud camera JPEG was located without public upload.
- A search rendition supplied to object selection returned only 450 x 600 mask pixels; this is NOT aligned to the camera source.
- The original asset URL from Adobe's asset resolution tool produced mask metadata at 1152 x 1536, matching the camera original geometry.
- An actual selection-masked Adobe tonal edit returned an image/png result URL. An image preview was visually inspected.
- Important unresolved distinction: the preview interface re-encodes output to a JPEG for model inspection. Neither the original remote PNG mask bytes nor the edited PNG bytes were independently materialized or hashed by the native v2 controller.
- Semantic selection quality is NOT certified merely because the reported dimensions match.

## Newly implemented exact-source private handoff

The CLI stage v2_native_entry ingest-mask receives seven positional arguments:

ORIGINAL, LINEAGE.json, PROVIDER_ORIGINAL, RAW_MASK.png, PROVIDER_RESULT.json, CANONICAL_MASK.png, HANDOFF.json

It requires all of the following:
1. Independently checked original-to-working ICC pixel lineage.
2. The independently downloaded provider input original is a separate local file whose SHA-256 equals the camera source file exactly.
3. The provider mask is an actual lossless PNG, not a resized preview JPEG. Pixel geometry equals the working image exactly. L mode is allowed; RGB/RGBA must be achromatic, with opaque alpha.
4. Actual raw and canonical mask bytes are hashed, verified and exclusively published with no overwrite. Small/empty or almost full-frame masks are rejected.
5. Technical success remains pending and explicitly records semantic_mask_accepted false, photographic_quality_accepted false, formal_V1_registered false.
6. If writing a final handoff JSON fails, only its own unreceipted unchanged canonical mask is eligible for rollback, never the photo or any previously owned file.

The private provider response JSON must preserve actual tool success, requestId, image/png output media type and reported source/mask dimensions. The trusted caller explicitly identifies provider Adobe and operation image_select_by_prompt. These metadata claims are not cryptographically signed; the real host must record them from the actual tool, not manufacture a positive response.

A correctly imported raw mask is NOT automatically suitable for photography. Subsequent manual/model inspection against the actual source, per-region core/allowed/protected constraints, edge checks, and independent 1:1 photo review remain mandatory. The native route does not automatically segment scenes, approve photographic quality, register Library V1 or create an iPhone-native deliverable.

## Remaining blocker

The selected real Adobe asset supplies a full-resolution mask URL, but the tool path in this execution did not provide independently materialized original remote mask and provider source **binary bytes** for local exact-source reconciliation. Therefore the real Adobe mask has NOT passed this CLI handoff. It must not be substituted by a model preview or a user-invented file/hash receipt.

Do not weaken the checks to force success. Until exact raw-byte access is proven, retain-original or STOP remains safer. Keep PR #47 Draft; no merge, Release, install, or private photo/URI upload to the public GitHub repository.
