"""Experimental source-pixel spatial lighting. Not a released Skill/photo acceptance.

Requires actual reviewed scene-aligned masks, source file provenance and
manual comparison. Does not perform object segmentation, generation or saving.
"""
from dataclasses import dataclass
import hashlib
import math
from PIL import Image, ImageChops, ImageDraw, ImageFilter


@dataclass(frozen=True)
class LightNode:
    name: str
    center: tuple[float, float]
    radius: tuple[float, float]
    strength: float  # bounded signed tone amplitude, NOT photographic EV
    mask: Image.Image
    target_core: Image.Image
    allowed: Image.Image
    protected: Image.Image


def _binary(im):
    if not isinstance(im, Image.Image) or im.mode != 'L':
        raise ValueError('8-bit grayscale mask required')
    return im.point(lambda value: 255 if value >= 128 else 0)


def _sum_pixels(im):
    return sum(index * count for index, count in enumerate(im.histogram())) / 255


def spotlight(size, center, radius, *, steps=64):
    w, h = size
    cx, cy = center
    rx, ry = radius
    if not (all(type(v) in (int, float) and math.isfinite(v)
                for v in (cx, cy, rx, ry))
            and 0 <= cx <= 1 and 0 <= cy <= 1
            and .02 <= rx <= 1 and .02 <= ry <= 1):
        raise ValueError('invalid normalized focal field')
    output = Image.new('L', size, 0)
    draw = ImageDraw.Draw(output)
    for k in range(steps, 0, -1):
        fraction = k / steps
        weight = (1 - fraction * fraction) ** 2
        left = round((cx - rx * fraction) * w)
        top = round((cy - ry * fraction) * h)
        right = round((cx + rx * fraction) * w)
        bottom = round((cy + ry * fraction) * h)
        draw.ellipse((left, top, right, bottom), fill=round(255 * weight))
    return output.filter(ImageFilter.GaussianBlur(2.2))


def _tone_curve(strength):
    # Smooth bounded midtone-only tonal shoulder; no newly saturated 255.
    return [max(0, min(255 if i == 255 else 254,
                       round(i + strength * i * (255 - i) / 255)))
            for i in range(256)]


def edit_spatially(source, nodes, *, verified_source_sha256,
                   observed_source_sha256, expected_source_pixel_sha256,
                   masks_visually_reviewed, max_channel_delta=90):
    """Produce only a pending visual review image and a technical receipt.

    The file SHA values must originate in the host's verified actual file.
    This function also checks decoded pixels, but cannot authenticate the
    user's semantic mask observations or external provider lineage.
    """
    if not isinstance(source, Image.Image) or source.mode != 'RGB':
        raise ValueError('decoded RGB source required')
    if not isinstance(verified_source_sha256, str) or len(verified_source_sha256) != 64 or verified_source_sha256 != observed_source_sha256:
        raise ValueError('source identity verification failed')
    if hashlib.sha256(source.tobytes()).hexdigest() != expected_source_pixel_sha256:
        raise ValueError('decoded source pixel fingerprint changed')
    if masks_visually_reviewed is not True:
        raise ValueError('actual scene-aligned masks must be visually checked')
    if not isinstance(nodes, (list, tuple)) or not 1 <= len(nodes) <= 4:
        raise ValueError('one to four editorial light nodes required')
    if type(max_channel_delta) is not int or not 1 <= max_channel_delta <= 100:
        raise ValueError('invalid channel-delta bound')
    result = source.copy()
    protected_union = Image.new('L', source.size, 0)
    stats = []
    for node in nodes:
        if not isinstance(node, LightNode) or not isinstance(node.name, str) or not node.name.strip():
            raise ValueError('concrete light node required')
        if (type(node.strength) not in (int, float)
                or not math.isfinite(node.strength)
                or not .06 <= abs(node.strength) <= .8):
            raise ValueError('light strength must be a bounded nontrivial number')
        maps = (node.mask, node.target_core, node.allowed, node.protected)
        if any(not isinstance(item, Image.Image) or item.mode != 'L' or item.size != source.size for item in maps):
            raise ValueError('mask geometry/mode mismatch')
        selected, core, allowed, protected = map(_binary, maps)
        core_pixels = _sum_pixels(core)
        if core_pixels <= 0 or _sum_pixels(ImageChops.multiply(selected, core)) / core_pixels < .80:
            raise ValueError('mask fails independent target-core coverage')
        if ImageChops.subtract(core, allowed).getbbox():
            raise ValueError('target core escapes reviewed allowed area')
        if ImageChops.multiply(selected, protected).getbbox():
            raise ValueError('mask overlaps protected scene')
        if ImageChops.subtract(selected, allowed).getbbox():
            raise ValueError('mask exceeds reviewed allowed area')
        support = selected.filter(ImageFilter.MaxFilter(19))
        if ImageChops.subtract(support, allowed).getbbox():
            raise ValueError('soft mask would escape reviewed area')
        alpha = selected.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(3))
        alpha = ImageChops.multiply(alpha, spotlight(source.size, node.center, node.radius))
        alpha = ImageChops.subtract(alpha, protected)
        if not alpha.getbbox():
            raise ValueError('focal field has no actual on-source image coverage')
        if ImageChops.subtract(alpha, allowed).getbbox():
            raise ValueError('light field touches unreviewed region')
        protected_union = ImageChops.lighter(protected_union, protected)
        corrected = result.point(_tone_curve(node.strength) * 3)
        result = Image.composite(corrected, result, alpha)
        stats.append({'name': node.name, 'strength': node.strength,
                      'active_alpha_pixels': _sum_pixels(alpha)})
    delta = ImageChops.difference(result, source)
    extrema = delta.getextrema()
    largest_change = max(high for low, high in extrema)
    if largest_change > max_channel_delta:
        raise ValueError('local image intensity exceeds tested bound')
    if any(ImageChops.multiply(band, protected_union).getbbox() for band in delta.split()):
        raise ValueError('protected scene changed')
    total_allowed = Image.new('L', source.size, 0)
    for node in nodes:
        total_allowed = ImageChops.lighter(total_allowed, _binary(node.allowed))
    for band in delta.split():
        if ImageChops.multiply(band, ImageChops.invert(total_allowed)).getbbox():
            raise ValueError('unreviewed background changed')

    def saturated_any(img):
        bands = [band.point(lambda v: 255 if v == 255 else 0) for band in img.split()]
        return ImageChops.lighter(ImageChops.lighter(bands[0], bands[1]), bands[2])

    if ImageChops.subtract(saturated_any(result), saturated_any(source)).getbbox():
        raise ValueError('newly saturated channel pixels present')
    result.info['icc_profile'] = source.info.get('icc_profile')
    return result, {'nodes': stats, 'protected_pixel_verified': True,
                    'no_new_clipped_channels': True,
                    'output_status': 'PENDING_USER_VISUAL_REVIEW',
                    'max_channel_delta': largest_change}
