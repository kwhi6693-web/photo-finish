# Photo Finish 2.0 — adaptive native route, engineering gate only

This document defines the isolated **scheme C** controller seam introduced on
the integration branch. It is *not* a production claim, edited-photo approval,
new main Skill release or user-authorization bypass.

## What the route does

The packaged `v2_native_entry render ORIGINAL LINEAGE PLAN ZONES OUTPUT RECEIPT`
entrypoint now validates actual original/working image lineage, then invokes
`adaptive_route.choose_adaptive_route` before any output image is written.

Three mutually exclusive actions:

- `RETAIN_ORIGINAL`: only when the real source/working identity matches,
  source review was recorded, and the **explicit** editorial plan decision is
  `retain_original` with a substantive reason. Write a *non-V1* decision JSON,
  do not create another image, do not describe this as a formal restore.
- `ELIGIBLE_MULTIZONE`: only when the plan requests the currently implemented
  non-generative native editor, the source and manually reviewed mask metadata
  are bound to the same real working image, 2–4 zones are declared, and the
  adaptive risk gate passes. This only permits downstream *actual pixel mask*
  audits and pending PNG export. Its candidate receipt always says
  `photographic_quality_accepted=false` and `formal_V1_registered=false`.
- `STOP`: no edited PNG; record an explicit non-V1 technical refusal JSON.
  Missing or contradictory evidence, unsupported global/crop/creative routes,
  or complex edges lacking independent inspection never silently fall back to
  an unrequested edit or “retain original”.

The adapter does **not** generate a scene plan, segment a photograph, connect
an external provider, verify photographic aesthetics, upload to Library,
perform iPhone native display, register formal V1, or restore a version.

## Input/evidence contract

`PLAN.json` must be a valid `EditorialPlan`, including the exact
`source_sha256` of the managed color-correct working PNG.

`ZONES.json` must include:

- `source_sha256` equal to that same working image;
- `source_visually_inspected: true` when there was a real source review;
- for `edit`: `scene_complexity: "simple"|"complex"`,
  `risk_flags` an explicit distinct list from `none`, `mixed_lighting`,
  `deep_shadow`, `architecture_sky_edge`, `foliage_sky_edge`,
  `readable_text`, `fine_object_boundary`, `reflective_surface`,
  `transparent_object`;
- for `edit`: `reviewer_mode: "human"|"assistant_visually_checked"`,
  a concrete `review_observation` (25+ characters), source-specific
  nonempty `geometry_id`, `masks_visually_inspected: true`, and 2–4
  `zones` with individual `reviewed: true` and existing source-bound
  mask/core/allowed/protected PNG file paths and SHA-256 values;
- for every edited zone, a source-reviewed **literal** `target_effect: "brighten"|"darken"`; Gamma below 1 brightens, Gamma above 1 darkens. Missing, neutral, contradictory, nonfinite, or out-of-bounds effect values produce an explicit STOP receipt **before** actual mask loading and pixel rendering. RETAIN_ORIGINAL needs no zone effects. The controller cannot infer the *correct* artistic direction from prose or certify that a declared intent reflects independently reviewed pixels.
- for any high-risk flag, explicit complexity `complex`, or a zone with
  `edge_mode: "pixel_locked"`: `edge_transition_verified: true` and
  `boundary_visually_inspected: true` for **each** zone. Missing any
  evidence yields `STOP`. A strong requested edit also requires verified
  edge transition evidence.

A declared risk flag or boolean is **not independent proof** of perceptual
mask quality; a review observation cannot be forged by a unit test and
promoted to actual field evidence. The subsequent existing `_zones`,
`inspect_mask`, `feather_mask`, protected-pixel, clipping, source/ICC and
output hash checks remain mandatory. In complex photography, the 1:1
photographic edge review remains a separate visual acceptance gate.

## Failure semantics / capabilities

- The current native compositor supports reviewed multi-zone tonal edits only.
- Full-image auto edit, accurate automatic semantic segmentation, crop and
  perspective transforms, external Adobe raw-output materialization, semantic
  visual QA and native iPhone save are **not** implemented by this route.
- Never infer these abilities from `ProvenCapabilities` booleans supplied by
  a JSON document. The local adapter's technical implementation must be
  verified by actual output tests; claimed visual review remains independently
  unverified until a real reviewer examines the specific image and masks.
- The STOP receipt is not a new version, not an accepted photograph and
  not evidence of editing. `RETAIN_ORIGINAL` is an explicit photographic
  choice, never an automatic reclassification of a failed edit.
- If final JSON receipt writing fails after output creation, the existing
  source-sha-bound cleanup may unlink only its own unreceipted unchanged
  candidate. It is not an atomic two-file transaction guarantee.

## Follow-up P0 gates

1. Exercise the real PR #47 controller on three distinct already-authorized
   non-portrait camera originals with inspected source-aligned masks; retain
   private originals and identity records outside the public repository.
2. Obtain actual source-bound files and verify 1:1 architecture/sky boundaries,
   text/material fidelity, overall spatial depth and expressive improvement.
3. Pass at least 2/3 real photographs with **no significant scene-identity
   defects on any of the three** before expanding to nine independent photos.
4. Only after subsequent independent native image/iPhone save, formal V1,
   cross-session zero-render restore, privacy/rollback review and full final
   CI may normal merge, Release and a one-time host installation be considered.

PR #47 remains **Draft / NO-MERGE / NO-RELEASE / NO-INSTALL**.
