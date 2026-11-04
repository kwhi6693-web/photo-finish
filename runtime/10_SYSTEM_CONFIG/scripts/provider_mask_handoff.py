"""Private, source-exact provider-mask byte handoff for v2 pending trials.

No URL fetching, no assumption that a preview is an original mask, no
semantic acceptance. The host must materialize BOTH the provider's original
source bytes and its raw PNG mask locally from actual tool responses.
These files, identities and receipts remain private and unpublished.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os
import tempfile

from PIL import Image, ImageChops

from editorial_pipeline import hash_file
from source_lineage import SourceLineage, verify_source_lineage


@dataclass(frozen=True)
class MaskHandoff:
    camera_original_sha256: str
    working_source_sha256: str
    provider_source_sha256: str
    raw_mask_sha256: str
    canonical_mask_sha256: str
    canonical_mask_path: str
    mask_dimensions: tuple[int, int]
    selected_fraction: float
    tool_request_id: str
    provider: str = "Adobe"
    status: str = "RAW_MASK_BYTES_VERIFIED_NOT_SEMANTICALLY_ACCEPTED"
    semantic_mask_accepted: bool = False
    photographic_quality_accepted: bool = False
    formal_V1_registered: bool = False


def _regular(path, label):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(label + " must be a real readable regular file")
    return path.resolve(strict=True)


def _exact_luma(raw, expected_dimensions):
    """Accept only lossless full-size PNG with exact achromatic channels."""
    with Image.open(raw) as image:
        image.load()
        if image.format != "PNG" or image.size != expected_dimensions:
            raise ValueError("provider mask must be lossless PNG on exact source geometry")
        if image.mode == "L":
            output = image.copy()
        elif image.mode in ("RGB", "RGBA"):
            channels = image.split()
            if (ImageChops.difference(channels[0], channels[1]).getbbox() or
                    ImageChops.difference(channels[0], channels[2]).getbbox()):
                raise ValueError("provider mask RGB channels are not identical grayscale")
            if image.mode == "RGBA" and channels[3].getextrema() != (255, 255):
                raise ValueError("provider mask has nonopaque alpha requiring explicit interpretation")
            output = channels[0].copy()
        else:
            raise ValueError("provider mask must be 8-bit L/RGB/RGBA; no lossy or palette masks")
    hist = output.histogram()
    selected = sum(hist[128:])
    ratio = selected / (output.width * output.height)
    if not .005 < ratio < .95:
        raise ValueError("provider mask is empty, near-empty or implausibly full-frame")
    return output, ratio


def import_exact_provider_mask(original, lineage, provider_source, raw_mask,
                               provider_result, destination):
    """Bridge only authentic raw bytes to a pending grayscale mask.

    provider_result is captured external-tool metadata and *not* a signature.
    Its semantic assertions cannot replace visual inspection or independent
    per-zone core/allowed/protected mask QA.
    """
    if not isinstance(lineage, SourceLineage) or not verify_source_lineage(original, lineage):
        raise ValueError("real source lineage is required")
    src = _regular(original, "camera original")
    external_src = _regular(provider_source, "provider downloaded source")
    if external_src == src:
        raise ValueError("provider input must be independently materialized, not an alias of camera original")
    source_hash = hash_file(src)
    if hash_file(external_src) != source_hash or source_hash != lineage.original_sha256:
        raise ValueError("provider source bytes differ from the camera original")
    raw = _regular(raw_mask, "raw provider PNG mask")
    raw_hash = hash_file(raw)
    if not isinstance(provider_result, dict) or provider_result.get("success") is not True:
        raise ValueError("genuine successful provider response metadata required")
    if provider_result.get("provider") != "Adobe" or provider_result.get("operation") != "image_select_by_prompt":
        raise ValueError("provider operation unsupported by this exact handoff")
    request_id = provider_result.get("requestId")
    if not isinstance(request_id, str) or len(request_id.strip()) < 12:
        raise ValueError("provider request identifier missing")
    if provider_result.get("outputMediaType") != "image/png":
        raise ValueError("provider output was not authoritative PNG")
    meta = provider_result.get("metadata")
    expected = lineage.working_size
    if not isinstance(meta, dict) or any(
        type(meta.get(name)) is not int or meta.get(name) != expected[index]
        for name, index in (
            ("source_width", 0), ("source_height", 1),
            ("mask_width", 0), ("mask_height", 1))
    ):
        raise ValueError("provider mask/source dimensions differ from working geometry")
    mask, ratio = _exact_luma(raw, expected)
    # No output path may alias any input, including pre-existing symlinks.
    target = Path(destination)
    if target.suffix.lower() != ".png":
        raise ValueError("canonical mask destination must be .png")
    target = target.parent.resolve(strict=True) / target.name
    if target in (src, external_src, raw) or os.path.lexists(target):
        raise FileExistsError("mask destination exists or aliases an input")
    temp = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=target.parent,
                                         suffix=".png", delete=False) as out:
            temp = Path(out.name)
            mask.save(out, format="PNG")
        with Image.open(temp) as confirmed:
            confirmed.load()
            if (confirmed.format != "PNG" or confirmed.mode != "L"
                    or confirmed.size != expected
                    or confirmed.tobytes() != mask.tobytes()):
                raise ValueError("canonical mask pixels changed during export")
        # Verify original and supplied provider bytes didn't change mid-process.
        if (hash_file(src) != source_hash or hash_file(external_src) != source_hash
                or hash_file(raw) != raw_hash
                or not verify_source_lineage(original, lineage)):
            raise ValueError("source or provider mask changed during handoff")
        canonical_hash = hash_file(temp)
        os.link(temp, target)  # exclusively publish; never overwrite
        if hash_file(target) != canonical_hash:
            raise ValueError("published mask bytes changed unexpectedly")
        return MaskHandoff(
            camera_original_sha256=source_hash,
            working_source_sha256=lineage.working_sha256,
            provider_source_sha256=source_hash,
            raw_mask_sha256=raw_hash,
            canonical_mask_sha256=canonical_hash,
            canonical_mask_path=str(target),
            mask_dimensions=expected,
            selected_fraction=ratio,
            tool_request_id=request_id)
    except BaseException:
        if temp is not None and os.path.lexists(target):
            try:
                if target.stat().st_ino == temp.stat().st_ino:
                    target.unlink()
            except OSError:
                pass
        raise
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
