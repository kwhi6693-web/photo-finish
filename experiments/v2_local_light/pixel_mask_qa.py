"""Isolated Photo Finish 2.0 pixel-mask and feathering prototype.

No image assets, remote calls, account data or changes to released Skill.
Every mask requires an independently inspected, source-aligned target-core,
allowed zone and protected-details map. These maps are *evidence supplied
by the caller*, not inferred by this program.

This module verifies pixel-level mask geometry, deterministic feathering,
and preservation of explicitly protected pixels. It cannot judge semantic
selection correctness, human visual realism, or magazine-grade aesthetics.
"""
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite

from PIL import Image, ImageChops, ImageFilter, ImageStat


@dataclass(frozen=True)
class PixelMaskAudit:
    passed: bool
    reason: str
    mask_sha256: str
    core_sha256: str
    allowed_sha256: str
    protected_sha256: str
    coverage: float
    target_core_recall: float
    off_target_fraction: float
    protected_overlap: int
    observed_bbox: tuple[float, float, float, float] | None


@dataclass(frozen=True)
class FeatherReceipt:
    alpha: Image.Image
    alpha_sha256: str
    radius_px: int
    source_mask_sha256: str
    protected_pixel_count: int


def _same_size(*images):
    if any(not isinstance(i, Image.Image) or i.mode != "L" for i in images):
        raise ValueError("all masks must be decoded 8-bit grayscale PIL Images")
    if len({i.size for i in images}) != 1:
        raise ValueError("mask, core, allowed zone and protected region must share exact geometry")
    width, height = images[0].size
    if not (1 <= width <= 12000 and 1 <= height <= 12000 and width * height <= 60_000_000):
        raise ValueError("invalid or unreasonably large mask dimensions")


def _binary(image):
    # Provider grays are thresholded; feathering is our deterministic step.
    return image.point(lambda px: 255 if px >= 128 else 0)


def _count(image):
    return int(round(ImageStat.Stat(image).sum[0] / 255))


def _digest(image):
    return sha256(image.mode.encode() + b"|" + str(image.size).encode() + b"|" + image.tobytes()).hexdigest()


def inspect_mask(raw, *, target_core, allowed_zone, protected,
                 min_core_recall=0.80, max_off_target_fraction=0.03,
                 max_coverage=0.80):
    """Pixel checks anchored in independently reviewed target/support maps.

    target_core: unmistakable pixels the mask MUST include.
    allowed_zone: entire area the edit is permitted to touch, broader than core.
    protected: pixels which MUST NOT be changed, such as exact signage.
    The caller must visually compare these maps against the source first.
    """
    _same_size(raw, target_core, allowed_zone, protected)
    for value in (min_core_recall, max_off_target_fraction, max_coverage):
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) or not 0 <= value <= 1:
            raise ValueError("mask acceptance fractions must be finite numbers in [0,1]")
    binary = _binary(raw)
    core, allowed, fixed = (_binary(i) for i in (target_core, allowed_zone, protected))
    chosen = _count(binary)
    core_count = _count(core)
    covered_core = _count(ImageChops.multiply(binary, core))
    off_target = _count(ImageChops.subtract(binary, allowed))
    protected_overlap = _count(ImageChops.multiply(binary, fixed))
    bbox = binary.getbbox()
    if bbox:
        x0, y0, x1, y1 = bbox
        x, y = binary.size
        observed_bbox = (x0/x, y0/y, (x1-x0)/x, (y1-y0)/y)
    else:
        observed_bbox = None
    selected_fraction = chosen / (binary.width * binary.height)
    core_recall = covered_core / core_count if core_count else 0.0
    off_fraction = off_target / chosen if chosen else 1.0
    if core_count == 0:
        reason = "target core is missing: an independently verified target is required"
    elif chosen == 0:
        reason = "empty mask"
    elif chosen == binary.width * binary.height or selected_fraction > max_coverage:
        reason = "oversized mask covering an implausibly large part of frame"
    elif _count(ImageChops.subtract(core, allowed)):
        reason = "target core extends outside allowed region"
    elif protected_overlap:
        reason = "mask already overlaps protected content"
    elif core_recall < min_core_recall:
        reason = "mask omitted required target-core pixels"
    elif off_fraction > max_off_target_fraction:
        reason = "mask extends beyond independently verified allowed region"
    else:
        reason = "eligible for bounded feathering only; semantic and final visual review still required"
    return PixelMaskAudit(
        passed=reason.startswith("eligible"), reason=reason,
        mask_sha256=_digest(binary), core_sha256=_digest(core),
        allowed_sha256=_digest(allowed), protected_sha256=_digest(fixed),
        coverage=selected_fraction, target_core_recall=core_recall,
        off_target_fraction=off_fraction, protected_overlap=protected_overlap,
        observed_bbox=observed_bbox)


def feather_mask(raw, *, audit, allowed_zone, protected, radius_px=3,
                 protected_margin_px=3):
    """Bounded grayscale alpha, with protected details kept unchanged.

    The dilated selection must fit inside the allowed region. Otherwise STOP
    instead of silently creating a sharp clipped adjustment boundary.
    """
    _same_size(raw, allowed_zone, protected)
    if not isinstance(audit, PixelMaskAudit) or not audit.passed:
        raise ValueError("a passing pixel mask audit is required")
    binary = _binary(raw)
    if _digest(binary) != audit.mask_sha256:
        raise ValueError("source mask bytes changed since audit")
    if type(radius_px) is not int or not (1 <= radius_px <= 10):
        raise ValueError("feather radius must be integer 1..10 pixels")
    if type(protected_margin_px) is not int or not (0 <= protected_margin_px <= 12):
        raise ValueError("protected margin must be integer 0..12 pixels")
    allowed = _binary(allowed_zone)
    fixed = _binary(protected)
    if _digest(allowed) != audit.allowed_sha256 or _digest(fixed) != audit.protected_sha256:
        raise ValueError("allowed zone or protected content changed since mask audit")
    # 3 sigma bounds the visible Gaussian falloff in 8-bit alpha.
    support_radius = min(3 * radius_px, 30)
    expanded = binary.filter(ImageFilter.MaxFilter(support_radius * 2 + 1))
    if _count(ImageChops.subtract(expanded, allowed)):
        raise ValueError("feather tail would escape allowed region; enlarge inspected ROI or reduce radius")
    alpha = binary.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(radius_px))
    if protected_margin_px:
        fixed = fixed.filter(ImageFilter.MaxFilter(protected_margin_px * 2 + 1))
    alpha = ImageChops.subtract(alpha, fixed)
    if ImageChops.multiply(alpha, fixed).getbbox():
        raise AssertionError("protected mask pixels were not excluded")
    return FeatherReceipt(alpha=alpha, alpha_sha256=_digest(alpha),
                          radius_px=radius_px, source_mask_sha256=audit.mask_sha256,
                          protected_pixel_count=_count(fixed))


def compose_only_tonal_output(source, processed_same_geometry, *, receipt):
    """Composite a same-source, tonal-only candidate with a reviewed soft alpha.

    This cannot align geometry, detect generated objects or manage color
    profiles. Export adapters must preserve/convert ICC separately.
    """
    if not isinstance(receipt, FeatherReceipt) or not isinstance(receipt.alpha, Image.Image):
        raise ValueError("feather receipt missing")
    if not isinstance(source, Image.Image) or not isinstance(processed_same_geometry, Image.Image):
        raise ValueError("source and candidate must be image objects")
    if source.size != processed_same_geometry.size or source.size != receipt.alpha.size:
        raise ValueError("source, toned candidate and reviewed alpha have different dimensions")
    if source.mode not in ("RGB", "RGBA") or source.mode != processed_same_geometry.mode:
        raise ValueError("source and toned candidate must have identical RGB/RGBA modes")
    if _digest(receipt.alpha) != receipt.alpha_sha256:
        raise ValueError("alpha changed after feather receipt")
    return Image.composite(processed_same_geometry, source, receipt.alpha)


def verify_protected_pixels(source, output, *, protected):
    """Bit-exact verification of protected pixels, including 1-level differences."""
    if source.size != output.size or source.mode != output.mode:
        return False
    if protected.size != source.size or protected.mode != "L":
        return False
    protected_binary = _binary(protected)
    changed = ImageChops.difference(source.convert("RGB"), output.convert("RGB"))
    red, green, blue = changed.split()
    changed_any_channel = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    return not ImageChops.multiply(changed_any_channel, protected_binary).getbbox()
