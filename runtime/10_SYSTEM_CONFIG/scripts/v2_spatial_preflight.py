"""Source-bound pre-edit composition decision, no automatic visual perception.

This is a read-only preflight: the caller must have really inspected the
photograph and supplied grounded boxes in its exact source pixel geometry.
No image processing, formal V1, quality approval, or automatic crop inference.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from hashlib import sha256
import json

from source_lineage import SourceLineage, verify_source_lineage


@dataclass(frozen=True)
class CompositionDecision:
    action: str  # KEEP_FRAME | CROP_PROPOSED | STOP
    reason: str
    camera_original_sha256: str | None = None
    working_source_sha256: str | None = None
    visual_observation_sha256: str | None = None
    source_bbox_px: tuple[int, int, int, int] | None = None
    retained_source_fraction: float | None = None
    visual_observation: str | None = None
    photographic_intent: str | None = None
    photographic_quality_accepted: bool = False
    formal_V1_registered: bool = False


def _rect(value, size):
    if not isinstance(value, list) or len(value)!=4 or any(type(x) is not int for x in value):
        raise ValueError('four genuine pixel integers required')
    l,t,r,b=value
    if not 0<=l<r<=size[0] or not 0<=t<b<=size[1]:
        raise ValueError('rectangle escapes the exact managed source geometry')
    return tuple(value)


def compile_composition(original, lineage, observation, *, observation_bytes=None):
    if not isinstance(lineage, SourceLineage) or not verify_source_lineage(original,lineage):
        raise ValueError('verified original and ICC managed source lineage required')
    if not isinstance(observation,dict):
        raise ValueError('source specific real visual observation object required')
    if observation_bytes is None:
        observation_bytes=json.dumps(observation,sort_keys=True,ensure_ascii=False).encode('utf8')
    if not isinstance(observation_bytes, bytes):
        raise ValueError('actual observation byte identity required')
    digest=sha256(observation_bytes).hexdigest()
    source=Path(original)
    if source.is_symlink():
        raise ValueError('symlinked camera source not accepted')
    if (observation.get('camera_original_sha256')!=lineage.original_sha256 or
        observation.get('source_sha256')!=lineage.working_sha256 or
        observation.get('observation_origin') not in ('assistant_visual_inspection','human_visual_inspection') or
        observation.get('original_visually_inspected') is not True or
        observation.get('nonportrait_scope') is not True):
        raise ValueError('real user authorized nonportrait source visual evidence missing or mismatched')
    if observation.get('generative_edit_requested') is not False:
        raise ValueError('generative geometry unsupported')
    size=lineage.working_size
    if not isinstance(size,tuple) or len(size)!=2:
        raise ValueError('missing original working source dimensions')
    intent=observation.get('photographic_intent')
    note=observation.get('visual_observation')
    for label,value in [('photographic_intent',intent),('visual_observation',note)]:
        if not isinstance(value,str) or len(value.strip())<45:
            raise ValueError(label+' lacks a concrete source-viewed photographic justification')
    action=observation.get('frame_action')
    if action not in ('keep','crop'):
        return CompositionDecision('STOP','no supported photographic framing decision')
    if action=='keep':
        if observation.get('source_bbox_px') is not None:
            raise ValueError('no-crop route cannot secretly supply a crop')
        return CompositionDecision('KEEP_FRAME', 'observed original composition retained',
            lineage.original_sha256,lineage.working_sha256,digest,None,1.0,note.strip(),intent.strip())
    if observation.get('crop_visually_inspected') is not True:
        raise ValueError('crop requires real visually inspected boundary')
    box=_rect(observation.get('source_bbox_px'),size)
    l,t,r,b=box
    fraction=(r-l)*(b-t)/(size[0]*size[1])
    if fraction<0.70 or fraction>0.96 or min(r-l,b-t)<640:
        raise ValueError('unsupported severe, trivial or undersized crop; no invented resolution')
    anchors=observation.get('reviewed_must_keep_boxes')
    if not isinstance(anchors,list) or not 2<=len(anchors)<=12:
        raise ValueError('two or more independently visually checked content anchors required')
    for anchor in anchors:
        if not isinstance(anchor,dict) or not isinstance(anchor.get('label'),str) or len(anchor['label'])<5:
            raise ValueError('real visually reviewed anchor labels required')
        x0,y0,x1,y1=_rect(anchor.get('bbox_px'),size)
        if not (l<=x0<x1<=r and t<=y0<y1<=b):
            raise ValueError('crop would cut inspected protected scene content: '+anchor['label'])
    return CompositionDecision('CROP_PROPOSED','source-exact candidate crop passes geometric content-anchor preflight only',
        lineage.original_sha256,lineage.working_sha256,digest,box,round(fraction,8),note.strip(),intent.strip())


def bind_to_real_pending(decision, pending):
    """Bind already planned crop to actual same-origin pending image receipt.

    The caller must independently verify the pending PNG bytes and path with
    the existing reframe entrypoint. This compiler never approves photo quality.
    """
    if not isinstance(decision,CompositionDecision) or decision.action!='CROP_PROPOSED':
        raise ValueError('a verified preplanned real-source crop is required')
    if not isinstance(pending,dict) or (
        not isinstance(pending.get('status'),str) or not pending['status'].startswith('PENDING_') or
        pending.get('camera_original_sha256')!=decision.camera_original_sha256 or
        pending.get('working_source_sha256')!=decision.working_source_sha256 or
        pending.get('formal_V1_registered') is not False or
        pending.get('photographic_quality_accepted') is not False or
        not isinstance(pending.get('candidate_sha256'),str) or len(pending['candidate_sha256'])!=64):
        raise ValueError('mismatched pending native candidate receipt')
    return {'camera_original_sha256':decision.camera_original_sha256,
            'working_source_sha256':decision.working_source_sha256,
            'parent_pending_sha256':pending['candidate_sha256'],
            'source_visually_inspected':True,'crop_visually_inspected':True,
            'source_bbox_px':list(decision.source_bbox_px),
            'photographic_intent':decision.photographic_intent,
            'visual_observation':decision.visual_observation,
            'composition_observation_sha256':decision.visual_observation_sha256,
            'photographic_quality_accepted':False,'formal_V1_registered':False}
