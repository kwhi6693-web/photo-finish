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
from math import isfinite, ceil, sqrt, pi

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


@dataclass(frozen=True)
class GradedAlphaReceipt(FeatherReceipt):
    """Continuous large-scale alpha built only from an audited binary mask."""
    sigma_px: int = 0
    peak_alpha: int = 0
    max_neighbor_step: int = 0
    neighbor_step_budget: int = 0


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


MAX_GRADED_SIGMA_PX = 120
_MIN_PEAK_BEFORE_NORMALIZATION = 64


def _max_neighbor_step(alpha):
    """Largest 8-bit jump between horizontally or vertically adjacent pixels."""
    width, height = alpha.size
    horizontal = vertical = 0
    if width > 1:
        horizontal = ImageChops.difference(alpha.crop((1, 0, width, height)),
                                           alpha.crop((0, 0, width - 1, height))).getextrema()[1]
    if height > 1:
        vertical = ImageChops.difference(alpha.crop((0, 1, width, height)),
                                         alpha.crop((0, 0, width, height - 1))).getextrema()[1]
    return max(horizontal, vertical)


def graded_alpha(raw, *, audit, target_core, allowed_zone, protected, sigma_px,
                 protected_margin_px=3, max_neighbor_step=None,
                 min_core_weight=0.6, peak_normalize=True):
    """Continuous large-scale alpha from an audited binary selection.

    ``feather_mask`` is capped at a 10 px radius, which gives a transition band
    of roughly 50 px: right for crisp subject edges, too narrow for a soft
    light falloff or a graduated darkening. This function accepts the same
    audited selection, but blurs it with a larger sigma, then verifies the
    *actual* result instead of trusting the parameters:

    * the nonzero alpha support must lie inside the reviewed allowed zone
      (STOP rather than clip into a visible hard boundary);
    * protected pixels (plus margin) are exactly zero, approached through a
      smooth fade rather than a step;
    * no two adjacent pixels differ by more than ``max_neighbor_step`` levels,
      so there is no 0/255 jump anywhere in the alpha;
    * the reviewed target core keeps at least ``min_core_weight`` of full
      strength, so protected content close to the selection cannot quietly
      fade the intended edit away while the receipt still looks successful.

    It does not judge whether the falloff looks good.
    """
    _same_size(raw, target_core, allowed_zone, protected)
    if not isinstance(audit, PixelMaskAudit) or not audit.passed:
        raise ValueError("a passing pixel mask audit is required")
    binary = _binary(raw)
    if _digest(binary) != audit.mask_sha256:
        raise ValueError("source mask bytes changed since audit")
    core = _binary(target_core)
    if _digest(core) != audit.core_sha256:
        raise ValueError("target core changed since mask audit")
    if (isinstance(min_core_weight, bool) or not isinstance(min_core_weight, (int, float))
            or not isfinite(min_core_weight) or not 0 < min_core_weight <= 1):
        raise ValueError("min core weight must be a finite number in (0,1]")
    if type(sigma_px) is not int or not (4 <= sigma_px <= MAX_GRADED_SIGMA_PX):
        raise ValueError("graded sigma must be integer 4..%d pixels" % MAX_GRADED_SIGMA_PX)
    if type(protected_margin_px) is not int or not (0 <= protected_margin_px <= 12):
        raise ValueError("protected margin must be integer 0..12 pixels")
    if max_neighbor_step is not None and (type(max_neighbor_step) is not int or not (1 <= max_neighbor_step <= 64)):
        raise ValueError("max neighbor step must be integer 1..64 levels")
    if type(peak_normalize) is not bool:
        raise ValueError("peak_normalize must be a bool")
    allowed = _binary(allowed_zone)
    fixed = _binary(protected)
    if _digest(allowed) != audit.allowed_sha256 or _digest(fixed) != audit.protected_sha256:
        raise ValueError("allowed zone or protected content changed since mask audit")
    alpha = binary.filter(ImageFilter.GaussianBlur(sigma_px))
    peak = alpha.getextrema()[1]
    if peak == 0:
        raise ValueError("graded alpha vanished: selection is far too small for this sigma")
    if peak_normalize:
        if peak < _MIN_PEAK_BEFORE_NORMALIZATION:
            raise ValueError("selection is too small relative to sigma to normalize; "
                             "enlarge the reviewed selection or reduce sigma")
        table = [min(255, round(i * 255 / peak)) for i in range(256)]
        alpha = alpha.point(table)
    # Gaussian step derivative (including peak normalization), plus quantization.
    # This is a numerical continuity budget, not a calibrated photographic score.
    normalization = 255 / peak if peak_normalize else 1.0
    derived_budget = ceil(255 * normalization / (sigma_px * sqrt(2*pi))) + 2
    guard = fixed.filter(ImageFilter.MaxFilter(protected_margin_px * 2 + 1)) if protected_margin_px else fixed
    if _count(guard):
        # Fade out toward protected content instead of cutting a step into alpha.
        fade_sigma = max(3, sigma_px // 2)
        derived_budget += ceil(255 / (fade_sigma * sqrt(2*pi))) + 2
        outer = guard.filter(ImageFilter.GaussianBlur(fade_sigma)).point(lambda v: 255 if v >= 6 else 0)
        factor = ImageChops.invert(outer.filter(ImageFilter.GaussianBlur(fade_sigma)))
        alpha = ImageChops.multiply(alpha, factor)
        alpha = ImageChops.subtract(alpha, guard)
    if ImageChops.multiply(alpha, fixed).getbbox():
        raise AssertionError("protected mask pixels were not excluded")
    support = alpha.point(lambda v: 255 if v else 0)
    if ImageChops.multiply(support, ImageChops.invert(allowed)).getbbox():
        raise ValueError("graded alpha tail would escape allowed region; "
                         "enlarge inspected ROI or reduce sigma")
    core_count = _count(core)
    core_weight = ImageStat.Stat(alpha, mask=core).mean[0] / 255 if core_count else 0.0
    if core_weight < min_core_weight:
        raise ValueError("protected content or sigma leaves the target core under-edited "
                         "(core weight %.2f < %.2f)" % (core_weight, min_core_weight))
    step = _max_neighbor_step(alpha)
    if max_neighbor_step is None:
        max_neighbor_step = min(64, derived_budget)
    if step > max_neighbor_step:
        raise ValueError("graded alpha is too steep: neighbor step %d exceeds %d"
                         % (step, max_neighbor_step))
    return GradedAlphaReceipt(
        alpha=alpha, alpha_sha256=_digest(alpha), radius_px=sigma_px,
        source_mask_sha256=audit.mask_sha256, protected_pixel_count=_count(guard),
        sigma_px=sigma_px, peak_alpha=alpha.getextrema()[1], max_neighbor_step=step,
        neighbor_step_budget=max_neighbor_step)


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
