# Focused upstream design adoption — Draft v2.0.0

Baseline: fef9fe7ce299b8a9eccd08b54dbf8710bfb3b258. This work stays on PR #47; no merge, release, installation, historical ledger migration or automatic photographic acceptance.

| Capability | Baseline status | Action |
|---|---|---|
| Source/ICC/strict operation contracts; graded Alpha | Implemented and verified | Reuse unchanged defaults and STOP |
| Scene observation → color/light/intensity | Implemented but incomplete | Preserve explicitly observed color/light direction and bounded intensity |
| Source-luma and directional reach inside audited geometry | Missing | Add optional multiplicative refinements inside existing graded route; never grow semantic selection |
| Semantic sky/subject segmentation | Blocked/unavailable | Do not claim a reliable segmentation engine; retain refusal for failed masks |
| Actual runtime capability evidence | Declarations only | Add real local self-test and explicit unavailable external engines |
| Actual Alpha/intermediate capture | Private tracing experiment | Save exact execution images in the render call, eliminating diagnostic rerender |
| Same-source photographic comparisons | Private manual workflow | Add read-only distributions and honest same-geometry reports; no aesthetic score |
| Native acceptance/save/readback/V1 | Implemented; user approval still required | Audit pending delivery and revalidate GO before registration |
| Mature conversation history bridge | Missing | Reuse task_history index for explicitly accepted native records; synthetic V1/V2/restore only until user GO |
| Independent cross-conversation restore | Historical T07 verified; new output unverified | Preserve historical GO; export handoff, never relabel subprocess test |

## Sources and licensing

All implementation is independently written for the existing Pillow controller. No upstream source is copied, vendored, linked or installed.

| Reference | Pinned commit | Observed useful design | License at audited commit |
|---|---|---|---|
| chipi/chemigram | 77e95f2636373e45a05c191c6675d225702b4ec1 | Apply-time spatial specs; explicit parameter reach; narrow operation surface | MIT |
| f1shh/my-skills | 812a674f1c8fd55c7d40c49e15a4ecfba8d269ff | Actual runtime mask review, geometry-aware region comparison, tonal distributions and subject/environment relationships | MIT |
| Timverhoogt/raw-photo-agent | 31ef01a4538d59deb12293c9f1291d7037f5bd32 | Bind native state and rendered pixels separately; uncertainty is not permission to retry | MIT |
| editmamei/editmamei | 0623bce46f72619df38ed5365bc085bf125d3387 | Distinguish detected editor from operational capability; return useful context | FSL-1.1-MIT, restricted current terms; no implementation reuse |
| mmcc-xx/darktable-api-mcp | b3b91a5dad70820fcb10559a5e5cba773879b093 | Parametric blend reach, per-region change diagnostics | GPL-3.0; no implementation reuse |
| joshua5201/mcp-photo-edit | 1a63799265f643b3ce749d93a2f60f364fbaac31 | Separate supported controls, rendering and state/export; typed boundaries | GPL-3.0; no implementation reuse |

References are design evidence, not proof that their engines exist on this host or that our photography improved. Chemigram ADR-074 is superseded; use it only as historical rationale alongside accepted ADR-084/085, not as a current feature claim. Portrait-specific techniques in upstream guides are excluded.

## Chosen implementation

Extend existing modules with optional source-luma/directional weighting, direct actual-artifact capture, read-only capability/quality/delivery diagnostics and an explicitly gated history adapter. Keep gamma/saturation/chroma and source protection bounds. Do not install darktable, RawTherapee, Photoshop, GIMP, models or new dependencies. A new engine would cost more and lacks host verification; documentation-only changes would leave the measured Alpha capture and delivery gaps.
