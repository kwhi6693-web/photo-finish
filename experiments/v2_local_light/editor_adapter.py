"""Experimental Photo Finish 2.0 adapter for *verified* tonal-only same-geometry results.

This file is not a photographic editing provider or a Skill runtime entrypoint.
It combines externally-produced tonal candidates and masks only after explicit
mask-pixel/geometry/ICC/protected-content checks. Never treat it as evidence
that an API-generated candidate preserved fixed scene geometry or that a photo
is aesthetically good. Human/source-output visual review remains mandatory.
"""
from dataclasses import dataclass
from hashlib import sha256

from PIL import Image, ImageChops

from pixel_mask_qa import (inspect_mask, feather_mask, compose_only_tonal_output,
                           verify_protected_pixels)


@dataclass(frozen=True)
class AdapterReceipt:
    source_pixel_hash: str
    candidate_pixel_hash: str
    output_pixel_hash: str
    source_geometry_id: str
    mask_sha256: str
    alpha_sha256: str
    target_core_recall: float
    off_target_fraction: float
    protected_unchanged: bool
    max_channel_delta: int
    status: str = "technical_candidate_only_not_visual_acceptance"


def _digest_pixels(image):
    return sha256(image.mode.encode('ascii') + repr(image.size).encode('ascii') +
                  image.tobytes()).hexdigest()


def _max_channel_delta(source, candidate):
    r, g, b = ImageChops.difference(source.convert('RGB'), candidate.convert('RGB')).split()
    return max(channel.getextrema()[1] for channel in (r, g, b))


def integrate_verified_tonal_edit(source, candidate, mask, *, target_core, allowed_zone,
                                  protected, source_geometry_id, candidate_geometry_id,
                                  approved_operation, masked_region_reviewed,
                                  source_pixels_hash, radius_px=3, max_channel_delta=60,
                                  require_icc=True):
    """Return (image, receipt) or fail-closed; never mark a V5 accepted automatically.

    'candidate' must be an output from an externally authenticated, strictly
    non-generative *tonal* editor, produced on the exact source geometry.
    This adapter cannot validate that provenance independently.
    """
    if approved_operation != 'non_generative_tonal_only':
        raise ValueError('editor provenance is not approved as tonal-only')
    if masked_region_reviewed is not True:
        raise ValueError('the actual mask and target must be visually reviewed')
    if not isinstance(source_geometry_id, str) or not source_geometry_id.strip():
        raise ValueError('source geometry identity must be nonempty')
    if source_geometry_id != candidate_geometry_id:
        raise ValueError('source and candidate have different geometry identities')
    if not isinstance(source, Image.Image) or not isinstance(candidate, Image.Image):
        raise ValueError('decoded source and tonal candidate images required')
    if source.mode != 'RGB' or candidate.mode != 'RGB' or source.size != candidate.size:
        raise ValueError('images must be identically sized and rendered as RGB')
    if source.getexif().get(274, 1) != 1 or candidate.getexif().get(274, 1) != 1:
        raise ValueError('EXIF orientation needs explicit prior normalization')
    if _digest_pixels(source) != source_pixels_hash:
        raise ValueError('source pixels differ from the identified source')
    src_profile, dst_profile = source.info.get('icc_profile'), candidate.info.get('icc_profile')
    if require_icc and (not src_profile or not dst_profile):
        raise ValueError('both images must contain actual ICC metadata for real use')
    if src_profile != dst_profile:
        raise ValueError('ICC profiles differ: normalize color space before compositing')
    if type(max_channel_delta) is not int or not 1 <= max_channel_delta <= 100:
        raise ValueError('invalid local tone-change ceiling')
    observed_max = _max_channel_delta(source, candidate)
    if observed_max > max_channel_delta:
        raise ValueError('candidate brightness/color change exceeds controlled tonal limit')
    audit = inspect_mask(mask, target_core=target_core,
                         allowed_zone=allowed_zone, protected=protected)
    if not audit.passed:
        raise ValueError('mask QA failed: ' + audit.reason)
    feather = feather_mask(mask, audit=audit, allowed_zone=allowed_zone,
                           protected=protected, radius_px=radius_px)
    output = compose_only_tonal_output(source, candidate, receipt=feather)
    if not verify_protected_pixels(source, output, protected=protected):
        raise ValueError('protected source pixels changed after compositing')
    changed = ImageChops.difference(output, source)
    red, green, blue = changed.split()
    any_changed = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    approved_pixels = allowed_zone.point(lambda v: 255 if v >= 128 else 0)
    if ImageChops.multiply(any_changed, ImageChops.invert(approved_pixels)).getbbox():
        raise ValueError('changed pixels escaped the inspected allowed region')
    output.info['icc_profile'] = src_profile
    return output, AdapterReceipt(
        source_pixel_hash=source_pixels_hash,
        candidate_pixel_hash=_digest_pixels(candidate),
        output_pixel_hash=_digest_pixels(output),
        source_geometry_id=source_geometry_id,
        mask_sha256=audit.mask_sha256, alpha_sha256=feather.alpha_sha256,
        target_core_recall=audit.target_core_recall,
        off_target_fraction=audit.off_target_fraction,
        protected_unchanged=True, max_channel_delta=observed_max)
