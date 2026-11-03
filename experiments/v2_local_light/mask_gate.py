"""Experimental, human-audited mask safety gate for Photo Finish 2.0.

This module validates *selection evidence*, not pixels, artistic quality,
or whether the reviewer actually judged a mask correctly. It has no image
editing, network, write, or user-asset access.
"""
from dataclasses import dataclass
from math import isfinite
from urllib.parse import urlparse


@dataclass(frozen=True)
class SelectionReceipt:
    """A mask from an editor plus an explicit visual review.

    geometry_id identifies immutable scene geometry (same original/crop/
    perspective). Pure color edits may share it; cropping or transforming
    geometry must mint a new id. A matching dimension alone is not enough.
    """
    region: str
    geometry_id: str
    mask_url: str
    normalized_bbox: tuple[float, float, float, float]
    visual_status: str  # verified | partial | leaking | wrong_target | unverified
    reviewer_note: str


@dataclass(frozen=True)
class EditDecision:
    allowed: bool
    reason: str


def _valid_bbox(bbox):
    if not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
        return False
    try:
        x, y, w, h = bbox
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in bbox):
            return False
        if not all(isfinite(v) for v in bbox):
            return False
        return 0 <= x < 1 and 0 <= y < 1 and 0 < w <= 1 and 0 < h <= 1 and x + w <= 1.000001 and y + h <= 1.000001
    except (TypeError, ValueError):
        return False


def allow_local_edit(receipt, *, current_geometry_id, region, intensity="moderate",
                     fixed_content_protected=True, image_preview_inspected=False):
    """Fail closed before an Adobe/local masked-edit request.

    A verified selection only means a human/assistant viewed the *mask* and
    judged its intended region. It is not a learned segmentation accuracy
    estimate, nor a certificate of original-scene fidelity or artistic merit.
    """
    if receipt is None or not isinstance(receipt, SelectionReceipt):
        return EditDecision(False, "no mask receipt")
    if not isinstance(current_geometry_id, str) or not current_geometry_id.strip():
        return EditDecision(False, "missing current geometry identity")
    if receipt.geometry_id != current_geometry_id:
        return EditDecision(False, "mask geometry no longer matches current image")
    if not isinstance(region, str) or not region.strip() or region != receipt.region:
        return EditDecision(False, "mask region differs from editing target")
    if intensity not in ("subtle", "moderate", "strong"):
        return EditDecision(False, "unsupported edit intensity")
    if not fixed_content_protected:
        return EditDecision(False, "fixed objects or exact content are unprotected")
    if not image_preview_inspected:
        return EditDecision(False, "visual inspection of actual image missing")
    if not _valid_bbox(receipt.normalized_bbox):
        return EditDecision(False, "invalid or unverified mask bounding box")
    if not isinstance(receipt.mask_url, str):
        return EditDecision(False, "mask output is not a URL")
    parsed = urlparse(receipt.mask_url)
    if parsed.scheme != "https" or not parsed.netloc:
        return EditDecision(False, "mask output must be an actual HTTPS asset")
    if receipt.visual_status != "verified":
        return EditDecision(False, "mask review is not verified: " + str(receipt.visual_status))
    if not isinstance(receipt.reviewer_note, str) or len(receipt.reviewer_note.strip()) < 15:
        return EditDecision(False, "mask review lacks concrete visual observations")
    return EditDecision(True, "mask routing permitted; edited result still requires image-to-source review")


def edited_photo_acceptable(*, real_tool_output, original_and_result_compared,
                            fixed_content_preserved, coherent_photographic_look,
                            expressive_improvement):
    """Separate final photo acceptance from mask structure validation."""
    return (real_tool_output is True and original_and_result_compared is True
            and fixed_content_preserved is True
            and coherent_photographic_look is True
            and expressive_improvement is True)
