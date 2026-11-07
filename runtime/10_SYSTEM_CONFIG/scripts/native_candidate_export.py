"""Experimental Photo Finish 2.0 native PNG handoff with exact source/ICC lineage.

This is a *candidate exporter*, not a visual acceptance judge, cloud save
client, installed Skill entrypoint or publisher. It is never safe to label the
output a formally accepted V1 until the existing review/save/ledger gates pass.
"""
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import os
import tempfile

from PIL import Image, ImageCms

from editorial_pipeline import hash_file
from multizone_editor import _sha_pixels
from multizone_workflow import PendingMultizoneTrial


@dataclass(frozen=True)
class PendingNativePNG:
    path: str
    sha256: str
    source_sha256: str
    bytes: int
    dimensions: tuple[int, int]
    icc_sha256: str
    content_type: str = 'image/png'
    status: str = 'PENDING_REAL_PHOTOGRAPHIC_REVIEW_AND_FORMAL_SAVE'
    photographic_quality_accepted: bool = False
    formal_V1_registered: bool = False


def export_pending_png(trial, *, working_source_path, destination):
    """Write a source-bound pending PNG exactly once; never replace an old file.

    The caller must verify the original camera-image -> working RGB sRGB/P3 file
    conversion separately. This method authenticates the *working* source bytes
    and the technical multi-zone candidate, not visual/semantic aesthetic merit.
    """
    if not isinstance(trial, PendingMultizoneTrial):
        raise ValueError('Only an actual pending multizone trial may be exported')
    if trial.status != 'PENDING_REAL_PHOTO_THREE_AXIS_REVIEW':
        raise ValueError('trial is not in pending review state')
    technical = trial.technical_receipt
    if (not isinstance(technical, dict)
            or technical.get('status') != 'PENDING_REAL_IMAGE_EDITORIAL_REVIEW'
            or technical.get('photographic_quality_accepted') is not False
            or technical.get('protected_pixel_check') is not True
            or technical.get('new_clip_check') is not True
            or technical.get('mask_boundary_preflight_verified') is not True
            or technical.get('output_edge_qa_passed') is not True
            or technical.get('output_pixel_sha256') != trial.output_pixel_sha256):
        raise ValueError('technical mask and original-scene protection receipt missing')
    src_raw = Path(working_source_path)
    if src_raw.is_symlink():
        raise ValueError('working source must be a regular non-symlink file')
    src_path = src_raw.resolve(strict=True)
    if not src_path.is_file():
        raise ValueError('working source must be an existing regular file')
    src_hash = hash_file(src_path)
    if src_hash != trial.source_file_sha256:
        raise ValueError('pending edit source identity does not match working original')

    with Image.open(src_path) as image:
        image.load()
        source = image.copy()
        source.info.update(image.info)
    edited = trial.image
    if not isinstance(edited, Image.Image) or source.mode != 'RGB' or edited.mode != 'RGB':
        raise ValueError('decoded source and pending result must be RGB')
    if source.size != edited.size or not 1 <= source.width*source.height <= 60_000_000:
        raise ValueError('edited image geometry does not match protected source')
    if source.getexif().get(274, 1) != 1 or edited.getexif().get(274, 1) != 1:
        raise ValueError('EXIF orientation must be normalized first')
    icc = source.info.get('icc_profile')
    if not isinstance(icc, bytes) or not icc or edited.info.get('icc_profile') != icc:
        raise ValueError('working source/result require identical actual ICC bytes')
    try:
        ImageCms.ImageCmsProfile(BytesIO(icc))
    except (OSError, ValueError, SyntaxError) as exc:
        raise ValueError('embedded ICC profile is invalid') from exc
    if technical.get('source_pixel_sha256') != _sha_pixels(source):
        raise ValueError('technical receipt source pixel identity differs')
    if _sha_pixels(edited) != trial.output_pixel_sha256:
        raise ValueError('pending output was mutated after technical checks')
    if _sha_pixels(source) == trial.output_pixel_sha256:
        raise ValueError('no actual edit; preserve original rather than claiming output')
    if hash_file(src_path) != src_hash:
        raise ValueError('source changed during candidate validation')

    target = Path(destination)
    if target.suffix.lower() != '.png':
        raise ValueError('pending source-faithful deliverable must be PNG')
    # Resolve the parent, not the output, so a dangling destination symlink is
    # detected rather than silently followed or overwritten.
    parent = target.parent.resolve(strict=True)
    target = parent / target.name
    if target == src_path or os.path.lexists(target):
        raise FileExistsError('output exists or aliases protected source')
    temp = None
    try:
        with tempfile.NamedTemporaryFile('wb', dir=parent, delete=False, suffix='.png') as out:
            temp = Path(out.name)
            edited.save(out, format='PNG', icc_profile=icc)
        with Image.open(temp) as actual:
            actual.load()
            if (actual.format != 'PNG' or actual.mode != 'RGB'
                    or actual.size != source.size
                    or actual.info.get('icc_profile') != icc
                    or _sha_pixels(actual) != trial.output_pixel_sha256):
                raise ValueError('original PNG bytes do not round-trip exact pixels/ICC')
        if hash_file(src_path) != src_hash:
            raise ValueError('source changed during PNG export')
        output_hash = hash_file(temp)
        size = temp.stat().st_size
        os.link(temp, target)  # Exclusive same-directory publish (no overwrite).
        if hash_file(target) != output_hash:
            raise ValueError('published output changed unexpectedly')
        return PendingNativePNG(str(target), output_hash, src_hash, size,
                                source.size, sha256(icc).hexdigest())
    except BaseException:
        # An incomplete/unsafe output must never be presented as accepted.
        if target.exists() and temp is not None and target.stat().st_ino == temp.stat().st_ino:
            target.unlink()
        raise
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
