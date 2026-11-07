# Photo Finish 2.0 | Graded (large-scale continuous) local edges and zone colour shift (experimental)

`edge_mode: soft` is capped at a 10 px feather, which gives a transition band of roughly 50 px. That suits crisp subject edges, not a soft light falloff or a graduated darkening. `edge_mode: graded` uses the same audited binary selection with a larger Gaussian sigma (`sigma_px`, integer 4..120) and verifies the *actual* alpha rather than trusting parameters.

**A graded zone requires**: `boundary_visually_inspected: true` (also enforced by the router), an integer `sigma_px`, and a selection that passes the same `inspect_mask` audit (core recall, off-target, protected overlap, coverage). `sigma_px` is rejected on non-graded zones.

**What `graded_alpha` checks on the real alpha**
- the nonzero alpha support lies inside the reviewed `allowed` zone; otherwise STOP (enlarge the reviewed ROI or reduce sigma). A selection that touches the image border needs an `allowed` zone that reaches the border;
- protected pixels (plus a 3 px margin) are exactly zero and are approached through a smooth fade; protected content hugging the selection STOPs rather than leaving a step;
- neighbor steps use a sigma-dependent Gaussian derivative budget, including peak normalization, protection fade and integer rounding (capped at 64); an explicitly supplied stricter budget is enforced. This numerical bound is not a calibrated aesthetic threshold;
- the reviewed target core keeps at least 0.6 of full strength, so nearby protected content cannot quietly fade the edit away;
- peak alpha is normalized to 255, and a selection too small for its sigma STOPs.

**Zone colour shift**: `chroma_shift: [cb, cr]`, two finite numbers within +/-12 levels, applied inside the zone only. Warm is negative Cb and positive Cr; cool is the opposite. Each zone must still brighten or darken (`target_effect`); the colour shift is additional. New 255-clipped channels are still blocked.

**Vignette**: do not use a formula-driven radial vignette. A vignette is a graded darkening zone over the frame periphery, with its own reviewed mask, core, allowed and protected maps.

Not judged by any of this: whether the falloff looks good. The receipt records `sigma_px`, `peak_alpha`, `max_neighbor_step`, `alpha_sha256` and `chroma_shift` per zone, and `photographic_quality_accepted` stays false.

Schema version 1 rejects unknown plan and zone fields, nonfinite numbers, boolean numbers, unsupported edge controls, and unsupported global controls. Local intent refusal returns actual `stage: STOP`, no PNG and no V1. Invalid source/global inputs may raise an explicit error without a receipt; exit code alone never certifies a candidate.

All masks are audited and actual Alpha constructed before the first grade (`mask_boundary_preflight_verified`). After each rendered zone, `output_edge_qa_passed` tests actual RGB differences against the alpha/texture product-rule budget and rounding residual. Final PNG export requires both gates and independently verifies decoded pixels/ICC. These are numerical integrity checks; `visual_edge_review: PENDING` remains until real output full-frame and 1:1 inspection. Preflight is never post-render visual evidence.

Overlapping zones execute in listed order on current pixels. All protected maps are unioned before any rendering. Actual nonzero-alpha support and source-to-current core monitoring report maximum/mean RGB change, changed fraction and encoded luma delta relative to the complement. `under_powered: null` and `PENDING_REAL_MULTI_CATEGORY_CALIBRATION` mean no threshold has been calibrated; the diagnostic is advisory and never forces aesthetic acceptance or refusal.

`graded` synthesizes continuous 8-bit Alpha from audited thresholded binary geometry. `soft` retains the existing bounded feather behavior; `pixel_locked` retains hard binary edges. Neither route preserves arbitrary provider continuous Alpha. Local Cb/Cr shift is relative color, not Kelvin. Global split tone is tonal, not semantic sky grading.
