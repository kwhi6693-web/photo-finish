"""Verified source-content-only rectangular reframe of a pending native PNG.

Never renders new scene pixels, does not make a semantic crop selection,
does not accept photographic quality, register formal V1 or upload content.
For an existing, source-linked, actual v2 candidate only.
"""
from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

from PIL import Image

from editorial_pipeline import hash_file
from source_lineage import SourceLineage, verify_source_lineage


@dataclass(frozen=True)
class PendingFrame:
    status: str
    camera_original_sha256: str
    working_source_sha256: str
    parent_pending_sha256: str
    parent_pending_path: str
    output_path: str
    output_sha256: str
    output_size: tuple[int, int]
    source_bbox_px: tuple[int, int, int, int]
    photographic_intent: str
    visual_observation: str
    pixel_origin: str = 'exact_crop_from_verified_native_pending_pixels'
    photographic_quality_accepted: bool = False
    formal_V1_registered: bool = False


def _regular(path, label):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(label + ': real existing regular file required')
    return path.resolve(strict=True)


def _crop_region(geometry, size):
    if not isinstance(geometry, list) or len(geometry) != 4 or any(type(v) is not int for v in geometry):
        raise ValueError('crop rectangle requires four source-pixel integer coordinates')
    l, t, r, b = geometry
    if not (0 <= l < r <= size[0] and 0 <= t < b <= size[1]):
        raise ValueError('crop rectangle outside verified working-source bounds')
    if r-l < 64 or b-t < 64:
        raise ValueError('crop must retain at least 64x64 pixels for technical viability')
    return (l,t,r,b)


def reframe_pending_native(original, lineage, native_png, native_receipt,
                           frame_plan, output_path):
    if not isinstance(lineage, SourceLineage) or not verify_source_lineage(original, lineage):
        raise ValueError('actual source and ICC conversion lineage did not verify')
    src = _regular(original, 'camera original')
    old = _regular(native_png, 'actual native pending candidate')
    if not isinstance(native_receipt, dict) or not isinstance(frame_plan, dict):
        raise ValueError('actual native pending receipt and framing plan required')
    if (not isinstance(native_receipt.get('status'),str) or
        not native_receipt['status'].startswith('PENDING_') or
        native_receipt.get('formal_V1_registered') is not False or
        native_receipt.get('photographic_quality_accepted') is not False):
        raise ValueError('only native pending non-V1 candidates may be reframed')
    if (native_receipt.get('camera_original_sha256') != lineage.original_sha256 or
        native_receipt.get('working_source_sha256') != lineage.working_sha256 or
        native_receipt.get('candidate_sha256') != hash_file(old) or
        not isinstance(native_receipt.get('candidate_path'),str) or
        Path(native_receipt['candidate_path']).resolve() != old):
        raise ValueError('native candidate does not match actual pending source receipt')
    if (frame_plan.get('camera_original_sha256') != lineage.original_sha256 or
        frame_plan.get('working_source_sha256') != lineage.working_sha256 or
        frame_plan.get('parent_pending_sha256') != native_receipt['candidate_sha256']):
        raise ValueError('crop instruction does not bind to source and exact parent candidate')
    if (frame_plan.get('source_visually_inspected') is not True or
        frame_plan.get('crop_visually_inspected') is not True):
        raise ValueError('source and intended crop require actual visual inspection')
    intent = frame_plan.get('photographic_intent')
    observation = frame_plan.get('visual_observation')
    if (not isinstance(intent, str) or len(intent.strip()) < 28 or
        not isinstance(observation,str) or len(observation.strip()) < 28):
        raise ValueError('concrete photographic intent and source-observation evidence required')
    target = Path(output_path)
    if target.suffix.lower() != '.png':
        raise ValueError('reframed candidate must be lossless .png')
    target = target.parent.resolve(strict=True)/target.name
    if os.path.lexists(target) or target in (src,old,Path(lineage.working_path).resolve()):
        raise FileExistsError('reframed output exists or aliases source')
    with Image.open(lineage.working_path) as managed:
        managed.load()
        if managed.format != 'PNG' or managed.mode != 'RGB':
            raise ValueError('managed original must be RGB PNG')
        source_icc = managed.info.get('icc_profile')
        if not source_icc or managed.size != lineage.working_size:
            raise ValueError('working source dimensions/ICC missing')
    with Image.open(old) as im:
        im.load()
        if (im.format != 'PNG' or im.mode != 'RGB' or
            im.size != lineage.working_size or
            im.info.get('icc_profile') != source_icc or
            im.getexif().get(274,1) != 1):
            raise ValueError('pending PNG format, source geometry or ICC mismatch')
        frame = _crop_region(frame_plan.get('source_bbox_px'),im.size)
        crop = im.crop(frame)
    parent_sha = hash_file(old)
    if parent_sha != native_receipt['candidate_sha256']:
        raise ValueError('parent PNG changed during crop preparation')
    temp = None
    published = False
    try:
        with tempfile.NamedTemporaryFile('wb',dir=target.parent,suffix='.png',delete=False) as f:
            temp = Path(f.name)
            crop.save(f,format='PNG',icc_profile=source_icc)
        with Image.open(temp) as verified:
            verified.load()
            if (verified.mode != 'RGB' or verified.format != 'PNG' or
                verified.info.get('icc_profile') != source_icc or
                verified.size != crop.size or verified.tobytes() != crop.tobytes()):
                raise ValueError('reframed PNG pixels or color profile changed during writing')
        if (hash_file(old) != parent_sha or not verify_source_lineage(original,lineage)):
            raise ValueError('camera original, working file or pending parent changed during export')
        sha = hash_file(temp)
        os.link(temp,target)  # exclusively publish; no overwrite
        published = True
        if hash_file(target) != sha:
            raise ValueError('reframed output bytes mutated during publication')
        return PendingFrame(
            status='PENDING_SOURCE_FAITHFUL_FRAMING_REVIEW_AND_FORMAL_V1',
            camera_original_sha256=lineage.original_sha256,
            working_source_sha256=lineage.working_sha256,
            parent_pending_sha256=parent_sha,
            parent_pending_path=str(old),
            output_path=str(target),output_sha256=sha,
            output_size=crop.size,source_bbox_px=frame,
            photographic_intent=intent.strip(),visual_observation=observation.strip())
    except BaseException:
        if published and temp is not None and os.path.lexists(target):
            try:
                if target.stat().st_ino == temp.stat().st_ino:
                    target.unlink()
            except OSError:
                pass
        raise
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
