"""Source-bound, bounded global tonal route. Experimental pending PNG only.

This is NOT a semantic preservation or aesthetic certification engine. It cannot
honor pixel-exact locks without exclusion masks and therefore fails closed.
"""
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import os
import tempfile

from PIL import Image, ImageChops

from editorial_contract import EditorialPlan, controller_direction
from editorial_pipeline import hash_file
from source_lineage import SourceLineage, verify_source_lineage
from multizone_editor import _sha_pixels

SUPPORTED = {'gentle_shadow_lift', 'restrain_bright_regions', 'mild_tonal_contrast'}
STRENGTHS = {'subtle', 'moderate'}


@dataclass(frozen=True)
class GlobalOperation:
    original_sha256: str
    source_sha256: str
    observation_sha256: str
    operation: str
    strength: str
    photographic_goal: str
    expected_visual_change: str
    reject_conditions: str
    protected_content_observation: str
    hard_pixel_lock: bool = False
    source_reviewed: bool = True
    technical_only: bool = True


def _real_sentence(value, label, minimum=35):
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ValueError(label+' needs a specific photographed-scene observation')
    return value.strip()


def compile_global_operation(plan, evidence, lineage, *, observation_sha256):
    """Map one actually observed photographic goal to one supported operation.

    Do not trust evidence flags as automatic verification of the actual scene;
    the photographic reviewer and user's authorization are separate gates.
    """
    controller_direction(plan)
    if not isinstance(lineage, SourceLineage) or not isinstance(evidence, dict):
        raise ValueError('actual source lineage and global operation evidence required')
    if (plan.decision != 'edit' or plan.edit_route != 'native' or
            plan.requires_local_selection or plan.requests_geometry_change or
            plan.output_use != 'screen'):
        raise ValueError('unsupported global operation context: must be native screen edit without local selection')
    if plan.source_sha256 != lineage.working_sha256:
        raise ValueError('plan does not belong to actual working source')
    if (evidence.get('camera_original_sha256') != lineage.original_sha256 or
            evidence.get('source_sha256') != lineage.working_sha256 or
            evidence.get('observation_sha256') != observation_sha256):
        raise ValueError('global operation evidence belongs to a different original/observation')
    if (evidence.get('source_visually_inspected') is not True or
            evidence.get('all_critical_content_visually_reviewed') is not True):
        raise ValueError('actual global scene and critical-content visual review missing')
    if evidence.get('pixel_exact_lock') is not False:
        raise ValueError('global route prohibited when any content requires pixel-exact protection')
    if evidence.get('protection_scope') != 'semantic_geometry_only':
        raise ValueError('global tonal route cannot guarantee unchanged color/pixels of protected content')
    if evidence.get('geometry_reinterpretation') is not False:
        raise ValueError('global tonal route cannot change source geometry')
    operation = evidence.get('operation')
    strength = evidence.get('strength')
    if operation not in SUPPORTED or strength not in STRENGTHS:
        raise ValueError('operation or strength unsupported by actual global engine')
    if strength == 'moderate' and plan.intensity == 'subtle':
        raise ValueError('operation strength exceeds constrained photographic plan')
    goal = _real_sentence(evidence.get('photographic_goal'), 'photographic goal')
    expected = _real_sentence(evidence.get('expected_visual_change'), 'expected visual change')
    reject = _real_sentence(evidence.get('reject_conditions'), 'reject conditions')
    protected = _real_sentence(evidence.get('protected_content_observation'), 'protected content review')
    return GlobalOperation(lineage.original_sha256,lineage.working_sha256,
                           observation_sha256,operation,strength,goal,
                           expected,reject,protected)


def _lut(operation, strength):
    amount = 18.0 if strength == 'moderate' else 10.0
    def tonal(i):
        x = i / 255.0
        if operation == 'gentle_shadow_lift':
            offset = amount * 4.0 * x * (1-x)**2
        elif operation == 'restrain_bright_regions':
            offset = -amount * 4.0 * x*x*(1-x)
        else:
            offset = (amount * 1.15) * 4.0 * x * (1-x) * (x-0.5)
        v = int(round(i + offset))
        # No new clipped full-white channel values, retain existing white.
        return max(0,min(254 if i < 255 else 255,v))
    values=[tonal(i) for i in range(256)]
    if any(a>b for a,b in zip(values,values[1:])):
        raise AssertionError('global curve is not monotonic')
    return values


def export_pending_global(original, lineage, plan, operation, output):
    """Actual Pillow render; derived checks are based on bytes, not flags."""
    if not isinstance(operation, GlobalOperation) or not isinstance(lineage, SourceLineage):
        raise ValueError('compiled operation and lineage required')
    if (plan.source_sha256 != lineage.working_sha256 or
            operation.source_sha256 != lineage.working_sha256 or
            operation.original_sha256 != lineage.original_sha256):
        raise ValueError('operation lineage mismatch')
    if not verify_source_lineage(original,lineage):
        raise ValueError('real original-to-working color lineage missing')
    working=Path(lineage.working_path)
    target=Path(output)
    if target.suffix.lower()!='.png':
        raise ValueError('pending output must be PNG')
    target=target.parent.resolve(strict=True)/target.name
    if os.path.lexists(target) or target in (working.resolve(),Path(original).resolve()):
        raise FileExistsError('existing or source-alias output refused')
    with Image.open(working) as im:
        im.load()
        profile=im.info.get('icc_profile')
        if im.mode!='RGB' or im.format!='PNG' or not profile or im.size != lineage.working_size:
            raise ValueError('verified ICC-managed RGB working PNG required')
        before=im.copy()
    lut=_lut(operation.operation,operation.strength)
    after=before.point(lut*3)
    after.info['icc_profile']=profile
    if ImageChops.difference(after,before).getbbox() is None:
        raise ValueError('global engine generated no actual pixel change')
    # Check no original full-white channel was newly clipped.
    old=before.tobytes(); new=after.tobytes()
    if any(a<255 and b==255 for a,b in zip(old,new)):
        raise ValueError('global output created new clipped channel value')
    temp=None
    published=False
    try:
        with tempfile.NamedTemporaryFile('wb',dir=target.parent,suffix='.png',delete=False) as f:
            temp=Path(f.name)
            after.save(f,format='PNG',icc_profile=profile)
        with Image.open(temp) as im:
            im.load()
            if (im.format!='PNG' or im.mode!='RGB' or im.size!=before.size or
                    im.info.get('icc_profile') != profile or im.tobytes()!=after.tobytes()):
                raise ValueError('pending output PNG pixels, ICC or geometry changed')
        if hash_file(working)!=lineage.working_sha256 or not verify_source_lineage(original,lineage):
            raise ValueError('actual source changed during global export')
        computed=hash_file(temp)
        os.link(temp,target)
        published=True
        if hash_file(target)!=computed:
            raise ValueError('output changed during exclusive publication')
        return {'status':'PENDING_GLOBAL_PHOTOGRAPHIC_REVIEW',
                'camera_original_sha256':lineage.original_sha256,
                'working_source_sha256':lineage.working_sha256,
                'observation_sha256':operation.observation_sha256,
                'operation':asdict(operation),
                'candidate_path':str(target),'candidate_sha256':computed,
                'source_pixel_sha256':_sha_pixels(before),
                'output_pixel_sha256':_sha_pixels(after),
                'geometry_verified':after.size==lineage.working_size,
                'icc_sha256':sha256(profile).hexdigest(),
                'pixel_change_verified':True,'no_new_clip_verified':True,
                'semantic_content_preserved':'PENDING_REAL_VISUAL_REVIEW',
                'photographic_quality_accepted':False,
                'formal_V1_registered':False}
    except BaseException:
        if published and temp is not None and os.path.lexists(target):
            try:
                if target.stat().st_ino==temp.stat().st_ino:
                    target.unlink()
            except OSError:
                pass
        raise
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
