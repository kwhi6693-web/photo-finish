"""PNG color declarations and metadata-only sRGB delivery; never retouch pixels."""
from pathlib import Path
import hashlib
import io
import json
import os
import struct
import tempfile
import zlib
from functools import lru_cache
from PIL import Image, ImageCms
from runtime_io import atomic_json

SIGNATURE = b'\x89PNG\r\n\x1a\n'
POLICY_KEY = b'PCSColorPolicy\x00'
COLOR_CHUNKS = {b'iCCP', b'sRGB', b'cICP', b'gAMA', b'cHRM'}


def chunks(data):
    if not data.startswith(SIGNATURE):
        raise ValueError('Metadata-only export requires a PNG')
    result, offset = [], 8
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('Truncated PNG chunk')
        size = struct.unpack_from('>I', data, offset)[0]
        end = offset + 12 + size
        if end > len(data):
            raise ValueError('Truncated PNG payload')
        kind, payload = data[offset + 4:offset + 8], data[offset + 8:end - 4]
        crc = struct.unpack_from('>I', data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError('PNG CRC mismatch')
        result.append((kind, payload))
        offset = end
        if kind == b'IEND':
            break
    if not result or result[0][0] != b'IHDR' or len(result[0][1]) != 13:
        raise ValueError('Invalid PNG header')
    if result[-1] != (b'IEND', b'') or offset != len(data):
        raise ValueError('Invalid PNG end')
    return result


def _chunk(kind, value):
    return (struct.pack('>I', len(value)) + kind + value
            + struct.pack('>I', zlib.crc32(kind + value) & 0xffffffff))


def _icc_characterization(raw):
    """Compare color-bearing tags, excluding human-readable labels and timestamps."""
    if len(raw) < 132 or raw[36:40] != b'acsp' or int.from_bytes(raw[:4], 'big') != len(raw):
        raise ValueError('Invalid ICC header')
    count = int.from_bytes(raw[128:132], 'big')
    if 132 + count * 12 > len(raw):
        raise ValueError('Truncated ICC tag table')
    tags = {}
    for offset in range(132, 132 + count * 12, 12):
        key, start, size = struct.unpack_from('>4sII', raw, offset)
        if start + size > len(raw) or key in tags:
            raise ValueError('Invalid ICC tag bounds or duplicate tag')
        tags[key] = raw[start:start + size]
    return {k: v for k, v in tags.items() if k not in
            (b'desc', b'cprt', b'dmnd', b'dmdd', b'vued', b'meta')}


@lru_cache(maxsize=1)
def _srgb_profile():
    raw = bytearray(ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
    # Stable metadata makes interrupted exports reproducible across retries.
    raw[24:36] = struct.pack('>6H', 2000, 1, 1, 0, 0, 0)
    return bytes(raw)


def declaration(path, image, profile_status):
    entries, faults, warnings, policy = [], [], [], None
    parts = chunks(Path(path).read_bytes()) if image.format == 'PNG' else []
    profile = image.info.get('icc_profile')
    if profile_status == 'parseable':
        try:
            tags = _icc_characterization(profile)
            model = profile[16:20].decode('ascii').strip()
            expected = ('GRAY' if parts and parts[0][1][9] in (0, 4) else
                        'RGB' if parts else {'RGB':'RGB','RGBA':'RGB','L':'GRAY','LA':'GRAY',
                                             'CMYK':'CMYK','LAB':'Lab'}.get(image.mode))
            if model != expected:
                faults.append('icc_pixel_model_mismatch')
            encoding = ('sRGB' if model == 'RGB' and tags == _icc_characterization(_srgb_profile())
                        else 'ICC:' + hashlib.sha256(profile).hexdigest()[:16])
            entries.append({'type': 'iCCP' if parts else 'ICC', 'encoding': encoding,
                            'supported': True, 'model': model,
                            'description': ImageCms.getProfileDescription(
                                ImageCms.ImageCmsProfile(io.BytesIO(profile))).strip()})
        except (ValueError, UnicodeError, OSError):
            faults.append('invalid_icc')
    elif profile_status == 'invalid':
        faults.append('invalid_icc')
    seen = {}
    for kind, value in parts:
        if kind in COLOR_CHUNKS:
            if kind in seen:
                faults.append(('conflicting_' if seen[kind] != value else 'duplicate_') + kind.decode())
            seen[kind] = value
        if kind == b'iCCP':
            # Pillow may expose corrupt iCCP as None; it is still a declaration,
            # never an untagged source eligible for an sRGB assumption.
            try:
                label, compressed = value.split(b'\x00', 1)
                if not 1 <= len(label) <= 79 or not compressed or compressed[0] != 0:
                    raise ValueError('Invalid iCCP framing')
                if profile_status != 'parseable' or zlib.decompress(compressed[1:]) != profile:
                    raise ValueError('Invalid iCCP profile')
            except (ValueError, zlib.error):
                faults.append('invalid_icc')
        if kind == b'sRGB':
            if len(value) == 1 and value[0] <= 3:
                entries.append({'type':'sRGB', 'encoding':'sRGB', 'supported':True})
            else:
                faults.append('invalid_sRGB')
        elif kind == b'cICP':
            names = {(1,13,0,1):'sRGB', (12,13,0,1):'Display P3'}
            valid = (len(value) == 4 and value[0] in {1,2,4,5,6,7,8,9,10,11,12,22}
                     and value[1] in {1,2,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18}
                     and value[2:] == bytes((0,1)))
            if not valid:
                faults.append('invalid_cICP')
            else:
                encoding = names.get(tuple(value))
                entries.append({'type':'cICP', 'encoding':encoding, 'supported':encoding is not None,
                                'values':list(value)})
                if encoding is None:
                    warnings.append('unsupported_cICP')
        elif kind == b'gAMA' and (len(value) != 4 or int.from_bytes(value, 'big') == 0):
            faults.append('invalid_gAMA')
        elif kind == b'cHRM' and len(value) != 32:
            faults.append('invalid_cHRM')
        elif kind == b'tEXt' and value.startswith(POLICY_KEY):
            try:
                if policy is not None:
                    raise ValueError('Duplicate delivery note')
                policy = json.loads(value[len(POLICY_KEY):])
                if not isinstance(policy, dict):
                    raise ValueError('Delivery note must be an object')
                if 'assumption_used' in policy and type(policy['assumption_used']) is not bool:
                    raise ValueError('Invalid assumption flag')
                if policy.get('source_encoding_verified') is False and policy.get('assumption_used') is not True:
                    raise ValueError('Inconsistent delivery note')
            except (ValueError, UnicodeError):
                faults.append('invalid_delivery_note'); policy = None
    rank = {'cICP':0,'iCCP':1,'ICC':1,'sRGB':2}
    effective = min(entries, key=lambda x:rank[x['type']]) if entries else None
    if not entries and (b'gAMA' in seen or b'cHRM' in seen):
        warnings.append('gamma_or_chromaticity_unsupported')
    status = ('conflict' if any(x.startswith('conflicting_') for x in faults) else
              'invalid' if faults else 'unsupported' if (effective and not effective['supported']) or warnings else
              'declared' if effective else 'unknown')
    return {'status':status, 'encoding':effective['encoding'] if effective else None,
            'effective_type':effective['type'] if effective else None, 'declarations':entries,
            'warnings':faults + warnings,
            'basis':'web_srgb_assumption' if isinstance(policy,dict) and policy.get('assumption_used') is True
                    else 'file_declaration' if entries else 'unverified', 'delivery_note':policy}


def export_web(input_path, output_path, assume_untagged_srgb=False,
               assumption_reason=None, receipt_path=None, source_kind='unknown', resume_existing=False):
    """Embed sRGB only for known sRGB or an explicit untagged-web assumption.

    No gamut conversion. Non-sRGB declarations require a separate real conversion.
    Preserve IDAT and decoded pixels. Retain the original signed file; remove its
    now-stale caBX manifest from the derivative and record the source hash/origin.
    """
    source, destination = Path(input_path).resolve(strict=True), Path(output_path).resolve()
    receipt = Path(receipt_path).resolve() if receipt_path is not None else None
    if destination == source or receipt in (source, destination):
        raise ValueError('Export/receipt cannot overwrite source or each other')
    if not resume_existing and (destination.exists() or (receipt is not None and receipt.exists())):
        raise FileExistsError('Export destination or receipt already exists')
    if type(resume_existing) is not bool:
        raise ValueError('resume_existing must be boolean')
    if type(assume_untagged_srgb) is not bool:
        raise ValueError('assume_untagged_srgb must be boolean')
    if source_kind not in ('generated', 'photograph', 'unknown'):
        raise ValueError('Invalid source_kind')
    data = source.read_bytes()
    parts = chunks(data)
    header = parts[0][1]
    if header[8] != 8 or header[9] not in (2, 6) or any(k in (b'acTL', b'fdAT') for k, _ in parts):
        raise ValueError('Metadata-only export supports static 8-bit RGB/RGBA PNG')
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        profile = image.info.get('icc_profile')
        profile_status = 'missing'
        if profile:
            try:
                ImageCms.ImageCmsProfile(io.BytesIO(profile))
                profile_status = 'parseable'
            except (ValueError, TypeError, OSError):
                profile_status = 'invalid'
        color = declaration(source, image, profile_status)
        original_pixels = image.tobytes()
    if color['status'] in ('invalid', 'conflict', 'unsupported'):
        raise ValueError('Color declarations need review before conversion or export')
    if color['status'] == 'declared' and color['encoding'] != 'sRGB':
        raise ValueError('Non-sRGB source requires actual color conversion; relabelling refused')
    if profile:
        # A display name alone is insufficient evidence for a metadata-only retag.
        builtin = _srgb_profile()
        normalized = lambda b: b[:24] + b[36:84] + b[100:]
        if normalized(profile) != normalized(builtin):
            raise ValueError('Existing ICC requires a verified color conversion or preserved original')
    assumed = color['status'] == 'unknown'
    if assumed and (not assume_untagged_srgb or not isinstance(assumption_reason, str)
                    or not assumption_reason.strip()):
        raise ValueError('Untagged export requires an explicit sRGB assumption and reason')
    prior = color.get('delivery_note') or {}
    inherited_assumption = prior.get('assumption_used') is True
    note = {'operation': 'metadata_only_srgb_delivery', 'source_sha256': hashlib.sha256(data).hexdigest(),
            'source_kind': source_kind, 'assumption_used': assumed or inherited_assumption,
            'assumption_reason': assumption_reason if assumed else prior.get('assumption_reason'),
            'source_encoding_verified': not (assumed or inherited_assumption),
            'delivery_scope': 'web_srgb_assumed' if assumed or inherited_assumption else 'declared_srgb',
            'conversion_performed': False, 'pixels_unchanged': True,
            'compressed_image_data_unchanged': True,
            'inherited_manifest_removed': any(k == b'caBX' for k, _ in parts),
            'provenance': 'Original retained unchanged; this derivative is not covered by its original authenticity signature.'}
    icc = _srgb_profile()
    additions = [(b'iCCP', b'sRGB\x00\x00' + zlib.compress(icc)),
                 (b'tEXt', POLICY_KEY + json.dumps(note, ensure_ascii=True, separators=(',', ':')).encode('ascii'))]
    output_parts = [parts[0]] + additions + [
        (k, v) for k, v in parts[1:] if k not in COLOR_CHUNKS | {b'caBX'}
        and not (k == b'tEXt' and v.startswith(POLICY_KEY))]
    output = SIGNATURE + b''.join(_chunk(k, v) for k, v in output_parts)
    if [v for k, v in parts if k == b'IDAT'] != [v for k, v in chunks(output) if k == b'IDAT']:
        raise ValueError('Compressed image data changed')
    with Image.open(io.BytesIO(output)) as check:
        check.load()
        if check.tobytes() != original_pixels:
            raise ValueError('Decoded pixels changed')
    if source.read_bytes() != data:
        raise ValueError('Source changed during export')
    result = dict(note, source_path=str(source), output_path=str(destination),
                  output_sha256=hashlib.sha256(output).hexdigest(), icc_bytes=len(icc))
    artifacts = [(destination, output)]
    if receipt is not None:
        artifacts.append((receipt, (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()))
    # Preflight every parent and stage both files before publishing either.
    for target, _ in artifacts:
        target.parent.mkdir(parents=True, exist_ok=True)
    staged, published = [], []
    try:
        for target, payload in artifacts:
            if target.exists():
                if resume_existing and target.read_bytes() == payload:
                    continue
                raise FileExistsError('Existing artifact does not match a resumable export')
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name); staged.append((temporary, target))
                stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        for temporary, target in staged:
            os.link(temporary, target)
            published.append((temporary, target))
    except BaseException:
        for temporary, target in reversed(published):
            # Remove only the inode created here; never delete a concurrent replacement.
            if target.exists() and os.path.samestat(temporary.stat(), target.stat()):
                target.unlink()
        raise
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    return result
