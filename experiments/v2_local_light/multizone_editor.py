"""V2 experimental multi-zone photographic tonal compositor.

Pure Pillow; no model, segmentation, edit-service or storage capabilities.
Expects human-inspected masks on exactly the decoded source geometry. This
module enforces technical bounds; it never certifies aesthetic quality.
"""
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from PIL import Image, ImageChops, ImageEnhance

from local_edit_qa import inspect_output_edges, measure_pixel_change

from pixel_mask_qa import (inspect_mask, feather_mask, graded_alpha,
                           verify_protected_pixels)


@dataclass(frozen=True)
class ToneZone:
    name: str
    mask: Image.Image
    core: Image.Image
    allowed: Image.Image
    protected: Image.Image
    gamma: float
    saturation: float = 1.0
    purpose: str = ''
    edge_mode: str = 'soft'  # soft | pixel_locked | graded
    boundary_visually_inspected: bool = False
    # graded only: Gaussian sigma (px) of the continuous alpha, 4..120.
    sigma_px: int = 0
    # Bounded Cb/Cr shift in 8-bit levels, applied inside the zone only.
    # Warm = (negative Cb, positive Cr); cool = (positive Cb, negative Cr).
    chroma_shift: tuple = (0.0, 0.0)


MAX_CHROMA_SHIFT = 12.0


def validate_chroma_shift(value):
    """Return a (cb, cr) float tuple, or raise ValueError."""
    if (not isinstance(value, (tuple, list)) or len(value) != 2 or
            any(type(v) not in (int, float) or not isfinite(v) for v in value) or
            any(abs(v) > MAX_CHROMA_SHIFT for v in value)):
        raise ValueError('chroma shift must be two finite numbers within +/-%g levels' % MAX_CHROMA_SHIFT)
    return (float(value[0]), float(value[1]))


def _sha_pixels(im):
    return sha256(im.mode.encode() + str(im.size).encode() + im.tobytes()).hexdigest()


def _grade(image, gamma, saturation, chroma_shift=(0.0, 0.0)):
    if any(type(v) not in (int, float) or not isfinite(v) for v in (gamma, saturation)):
        raise ValueError('finite tone strength required')
    if not 0.65 <= gamma <= 1.6 or not .65 <= saturation <= 1.35:
        raise ValueError('grade strength beyond bounded experimental range')
    d_cb, d_cr = validate_chroma_shift(chroma_shift)
    y, cb, cr = image.convert('YCbCr').split()
    lut = [min(254, round(255 * (i / 255) ** gamma)) if i < 255 else 255 for i in range(256)]
    if d_cb:
        cb = cb.point([max(0, min(255, round(i + d_cb))) for i in range(256)])
    if d_cr:
        cr = cr.point([max(0, min(255, round(i + d_cr))) for i in range(256)])
    candidate = Image.merge('YCbCr', (y.point(lut), cb, cr)).convert('RGB')
    if saturation != 1.0:
        candidate = ImageEnhance.Color(candidate).enhance(saturation)
    return candidate


def _one_any255(image):
    red, green, blue = image.split()
    channels = [band.point(lambda i: 255 if i == 255 else 0) for band in (red, green, blue)]
    return ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])


def _remove_newly_clipped(image, prior_source):
    """No new RGB 255 values; preserve originally clipped channel pixels."""
    bands = []
    for band, old in zip(image.split(), prior_source.split()):
        new_data = band.tobytes()
        old_data = old.tobytes()
        bands.append(Image.frombytes('L', band.size, bytes(
            (254 if n == 255 and o != 255 else n for n, o in zip(new_data, old_data)))))
    return Image.merge('RGB', tuple(bands))


def composite_zones(source, zones, *, observed_source_pixel_sha256,
                    source_visually_inspected, masks_visually_inspected,
                    spatial_intent, expected_icc_bytes, geometry_id,
                    radius_px=3):
    if not isinstance(source, Image.Image) or source.mode != 'RGB':
        raise ValueError('same-geometry decoded RGB source required')
    if not isinstance(geometry_id, str) or not geometry_id.strip():
        raise ValueError('geometry identity required')
    if observed_source_pixel_sha256 != _sha_pixels(source):
        raise ValueError('decoded source pixel digest mismatched')
    if source_visually_inspected is not True or masks_visually_inspected is not True:
        raise ValueError('human/assistant real pixel and mask inspection required')
    if not isinstance(spatial_intent, str) or len(spatial_intent.strip()) < 30:
        raise ValueError('concrete spatial viewing path and photographic intention required')
    if not isinstance(expected_icc_bytes, bytes) or not expected_icc_bytes or source.info.get('icc_profile') != expected_icc_bytes:
        raise ValueError('real source ICC bytes required and must match')
    if not isinstance(zones, (list, tuple)) or not 2 <= len(zones) <= 4:
        raise ValueError('two to four separately reviewed spatial zones required')
    if any(not isinstance(z, ToneZone) for z in zones):
        raise ValueError('invalid zone type')
    # Combine ALL protected content before rendering. Region B cannot damage
    # something that was only labeled protected by region A.
    protected = Image.new('L', source.size, 0)
    for z in zones:
        if not isinstance(z.protected, Image.Image) or z.protected.mode != 'L' or z.protected.size != source.size:
            raise ValueError('invalid protected region')
        protected = ImageChops.lighter(protected, z.protected.point(lambda i: 255 if i >= 128 else 0))
    current = source.copy()
    current.info['icc_profile'] = expected_icc_bytes
    all_allowed = Image.new('L', source.size, 0)
    receipts = []
    prepared = []
    # Audit every region before the first tonal operation, not between renders.
    for z in zones:
        if (not isinstance(z.name, str) or not z.name.strip() or
                not isinstance(z.purpose, str) or len(z.purpose.strip()) < 16):
            raise ValueError('zone must carry concrete spatial purpose')
        audit = inspect_mask(z.mask, target_core=z.core, allowed_zone=z.allowed, protected=protected)
        if not audit.passed:
            raise ValueError('rejected mask ' + z.name + ': ' + audit.reason)
        if z.edge_mode not in ('soft', 'pixel_locked', 'graded'):
            raise ValueError('unsupported edge policy')
        if z.edge_mode == 'pixel_locked' and z.boundary_visually_inspected is not True:
            raise ValueError('sharp content edge requires real mask-boundary inspection')
        if z.edge_mode == 'graded' and z.boundary_visually_inspected is not True:
            raise ValueError('graded edge requires real mask-boundary inspection')
        validate_chroma_shift(z.chroma_shift)
        graded_receipt = None
        if z.edge_mode != 'graded' and z.sigma_px != 0:
            raise ValueError('sigma_px is only valid for graded edge mode')
        if z.edge_mode == 'graded':
            graded_receipt = graded_alpha(z.mask, audit=audit, target_core=z.core,
                                          allowed_zone=z.allowed, protected=protected,
                                          sigma_px=z.sigma_px)
            alpha = graded_receipt.alpha
        elif z.edge_mode == 'soft':
            feather = feather_mask(z.mask, audit=audit, allowed_zone=z.allowed,
                                   protected=protected, radius_px=radius_px)
            alpha = feather.alpha
        else:
            # An inspected hard architectural/sky boundary must not be blended
            # into masonry. A blurred sky alpha can manufacture a visible halo.
            alpha = ImageChops.subtract(z.mask.point(lambda x: 255 if x >= 128 else 0), protected)
        prepared.append((z, audit, alpha, graded_receipt))
    for z, audit, alpha, graded_receipt in prepared:
        before = current
        candidate = _grade(current, z.gamma, z.saturation, z.chroma_shift)
        candidate.info['icc_profile'] = expected_icc_bytes
        raw = Image.composite(candidate, current, alpha)
        current = _remove_newly_clipped(raw, source)
        current.info['icc_profile'] = expected_icc_bytes
        all_allowed = ImageChops.lighter(all_allowed, z.allowed.point(lambda i: 255 if i >= 128 else 0))
        receipt = {'name': z.name, 'purpose': z.purpose,
                   'coverage': audit.coverage, 'mask_sha256': audit.mask_sha256,
                   'edge_mode': z.edge_mode,
                   'mask_boundary_preflight_verified': True,
                   'output_edge_qa': inspect_output_edges(before, current, candidate, alpha),
                   'actual_region_change': measure_pixel_change(before, current, alpha),
                   'source_to_current_core_change': measure_pixel_change(source, current, z.core)}
        if graded_receipt is not None:
            receipt.update({'sigma_px': graded_receipt.sigma_px,
                            'alpha_sha256': graded_receipt.alpha_sha256,
                            'peak_alpha': graded_receipt.peak_alpha,
                            'neighbor_step_budget': graded_receipt.neighbor_step_budget,
                            'max_neighbor_step': graded_receipt.max_neighbor_step})
        if z.chroma_shift != (0.0, 0.0) and tuple(z.chroma_shift) != (0, 0):
            receipt['chroma_shift'] = list(validate_chroma_shift(z.chroma_shift))
        receipts.append(receipt)
    if not verify_protected_pixels(source, current, protected=protected):
        raise ValueError('protected fixed scene pixel changed')
    red, green, blue = ImageChops.difference(source, current).split()
    changed = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    if ImageChops.multiply(changed, ImageChops.invert(all_allowed)).getbbox():
        raise ValueError('change escaped inspected permitted regions')
    if ImageChops.subtract(_one_any255(current), _one_any255(source)).getbbox():
        raise ValueError('newly clipped RGB high values')
    if _sha_pixels(source) != observed_source_pixel_sha256:
        raise ValueError('source pixels mutated during edit')
    current.info['icc_profile'] = expected_icc_bytes
    return current, {'status': 'PENDING_REAL_IMAGE_EDITORIAL_REVIEW',
                     'source_pixel_sha256': observed_source_pixel_sha256,
                     'output_pixel_sha256': _sha_pixels(current),
                     'geometry_id': geometry_id, 'zones': receipts,
                     'mask_boundary_preflight_verified': True,
                     'output_edge_qa_passed': True, 'visual_edge_review': 'PENDING',
                     'overlap_order': [z.name for z in zones],
                     'overlap_policy': 'list order; later grade applies to current pixels; all protected regions unioned',
                     'protected_pixel_check': True, 'new_clip_check': True,
                     'photographic_quality_accepted': False}
