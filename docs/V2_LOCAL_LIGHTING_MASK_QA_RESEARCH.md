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
- requires known edit strength, explicit fixed-object protection and actual image preview;
- independently gates final visual-acceptance claims.

**Limitations:** It does not inspect any mask pixels itself, compute segmentation IoU, feather boundaries, call Adobe, edit photos, compare photographic aesthetics, store user media, or modify the existing Skill. The calling editor/reviewer must provide real evidence and will still need integration. A dishonest reviewer could still mark a mask verified; this module cannot detect that. No claim of better real photos is justified by passing these protocol tests.

## Promotion gates

- [ ] Implement a real editor adapter supplying reviewed masks and geometry lineage.
- [ ] Add real-photo negative cases (wrong sky/facade inversion, partial street selection, frame leakage) privately, without uploading photos to public Git.
- [ ] Confirm the same-source V3 vs V4 result actually improves at least two of the three authorized scenes; gather user preference and inspect real pixel edges/wording.
- [ ] Integrate with the rewritten Skill directions, preserving STOP and old versions; do not silently enable the experimental contract for installed v1.5.7.
- [ ] Run full existing CI/manifest requirements and independent review on a new version-specific candidate, then broader 9-photo study only after initial quality gates pass.

This is research evidence and an integration starting point, not a release milestone.
