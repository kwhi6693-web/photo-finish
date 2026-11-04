"""Source-photo -> managed RGB working PNG lineage for Photo Finish 2.0.

No creative image synthesis. The original file is read-only; output identity,
source/profile evidence and normalized orientation are recorded. Does not
grant permission to edit, self-certify style, accept V1 or publish user data.
"""
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import os
import tempfile

from PIL import Image, ImageCms, ImageOps

from editorial_pipeline import hash_file
from multizone_editor import _sha_pixels

MAX_PIXELS = 60_000_000


def _canonical_srgb_bytes(raw):
    """Freeze volatile ICC header creation timestamp; never change color tags."""
    if not isinstance(raw, bytes) or len(raw) < 128 or raw[36:40] != b'acsp':
        raise ValueError('invalid built-in sRGB ICC profile')
    stable = bytearray(raw)
    # ICC v2/v4 header UTC date: 2000-01-01 00:00:00 (six big-endian u16).
    stable[24:36] = bytes.fromhex('07d000010001000000000000')
    return bytes(stable)


@dataclass(frozen=True)
class SourceLineage:
    original_sha256: str
    original_profile_sha256: str
    original_size: tuple[int, int]
    original_exif_orientation: int
    working_path: str
    working_sha256: str
    working_pixel_sha256: str
    working_size: tuple[int, int]
    working_icc_sha256: str
    conversion: str = 'embedded_ICC_to_sRGB_ImageCms_and_normalized_EXIF'
    status: str = 'VERIFIED_WORKING_SOURCE_NOT_PHOTOGRAPHIC_ACCEPTANCE'


def _working_srgb(source):
    if not isinstance(source, Image.Image) or source.width*source.height > MAX_PIXELS:
        raise ValueError('source is invalid or exceeds safe pixel limit')
    embedded = source.info.get('icc_profile')
    if not isinstance(embedded, bytes) or not embedded:
        raise ValueError('source requires a real embedded ICC profile; no silent P3/sRGB guess')
    try:
        input_profile = ImageCms.ImageCmsProfile(BytesIO(embedded))
        # LittleCMS embeds wall-clock creation time (ICC header bytes 24..35).
        # Recreating a semantically identical sRGB profile during independent
        # lineage verification otherwise changes its bytes across seconds.
        # Canonicalize ONLY the ICC creation date; preserve all color tags.
        srgb_icc = _canonical_srgb_bytes(
            ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
        output_profile = ImageCms.ImageCmsProfile(BytesIO(srgb_icc))
    except (OSError, ValueError, SyntaxError) as error:
        raise ValueError('source ICC profile is invalid or unsupported') from error
    upright = ImageOps.exif_transpose(source)
    rgb = upright.convert('RGB')
    try:
        managed = ImageCms.profileToProfile(rgb, input_profile, output_profile, outputMode='RGB')
    except (OSError, ValueError, SyntaxError) as error:
        raise ValueError('ICC color conversion could not be verified') from error
    managed.info['icc_profile'] = srgb_icc
    if managed.getexif().get(274, 1) != 1:
        raise ValueError('working PNG still has unnormalized EXIF orientation')
    return managed, srgb_icc


def prepare_working_source(original_path, working_png_path):
    original_raw = Path(original_path)
    if original_raw.is_symlink():
        raise ValueError('original cannot be a symlink')
    original = original_raw.resolve(strict=True)
    if not original.is_file():
        raise ValueError('actual user original file is required')
    original_hash = hash_file(original)
    with Image.open(original) as image:
        image.load()
        profile = image.info.get('icc_profile')
        original_size = image.size
        orientation = image.getexif().get(274, 1)
        working, icc = _working_srgb(image)
    if hash_file(original) != original_hash:
        raise ValueError('original changed during color conversion')
    requested = Path(working_png_path)
    if requested.suffix.lower() != '.png':
        raise ValueError('working photo must be a PNG')
    target = requested.parent.resolve(strict=True) / requested.name
    if target == original or os.path.lexists(target):
        raise FileExistsError('working destination exists or aliases original')
    temp = None
    try:
        with tempfile.NamedTemporaryFile('wb', dir=target.parent, delete=False, suffix='.png') as file:
            temp = Path(file.name)
            working.save(file, format='PNG', icc_profile=icc)
        with Image.open(temp) as decoded:
            decoded.load()
            if (decoded.format != 'PNG' or decoded.mode != 'RGB'
                    or decoded.size != working.size
                    or decoded.info.get('icc_profile') != icc
                    or _sha_pixels(decoded) != _sha_pixels(working)):
                raise ValueError('working PNG did not preserve actual converted pixels/ICC')
        if hash_file(original) != original_hash:
            raise ValueError('original mutated before publication')
        output_hash = hash_file(temp)
        os.link(temp, target)  # No overwrite, including dangling symlinks.
        if hash_file(target) != output_hash:
            raise ValueError('working file unexpectedly changed after publication')
        return SourceLineage(
            original_sha256=original_hash,
            original_profile_sha256=sha256(profile).hexdigest(),
            original_size=original_size, original_exif_orientation=orientation,
            working_path=str(target), working_sha256=output_hash,
            working_pixel_sha256=_sha_pixels(working), working_size=working.size,
            working_icc_sha256=sha256(icc).hexdigest())
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


def verify_source_lineage(original_path, receipt):
    if not isinstance(receipt, SourceLineage):
        raise ValueError('authenticated SourceLineage receipt required')
    raw = Path(original_path)
    if raw.is_symlink():
        raise ValueError('original cannot be a symlink')
    original = raw.resolve(strict=True)
    working = Path(receipt.working_path)
    if working.is_symlink() or not working.is_file():
        raise ValueError('verified working file missing or linked')
    if hash_file(original) != receipt.original_sha256:
        raise ValueError('original bytes changed after working export')
    if hash_file(working) != receipt.working_sha256:
        raise ValueError('working PNG bytes changed after color management')
    with Image.open(original) as image:
        image.load()
        if (image.size != receipt.original_size
                or image.getexif().get(274, 1) != receipt.original_exif_orientation
                or sha256(image.info.get('icc_profile', b'')).hexdigest() != receipt.original_profile_sha256):
            raise ValueError('original profile/geometry no longer matches source receipt')
        converted, icc = _working_srgb(image)
    with Image.open(working) as final:
        final.load()
        if (final.format != 'PNG' or final.mode != 'RGB'
                or final.size != receipt.working_size
                or final.info.get('icc_profile') != icc
                or sha256(icc).hexdigest() != receipt.working_icc_sha256
                or _sha_pixels(final) != receipt.working_pixel_sha256
                or _sha_pixels(final) != _sha_pixels(converted)):
            raise ValueError('working PNG no longer matches independent ICC conversion')
    return True
