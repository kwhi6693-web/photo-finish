"""Isolated V2 spatial plan -> real source -> multi-zone trial -> pending review.

This experimental entrypoint neither drives a production editor nor claims
actual aesthetic improvement. All actual semantic inspection flags are supplied
by the invoking reviewer; use truthful evidence, never fabricated attestations.
No file is written, no user data is published, and no installed Skill is changed.
"""
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from editorial_contract import EditorialPlan, ProvenCapabilities, preflight
from editorial_pipeline import hash_file
from multizone_editor import ToneZone, composite_zones, _sha_pixels


@dataclass(frozen=True)
class PendingMultizoneTrial:
    image: Image.Image
    source_file_sha256: str
    output_pixel_sha256: str
    spatial_direction: dict
    technical_receipt: dict
    status: str = 'PENDING_REAL_PHOTO_THREE_AXIS_REVIEW'


def run_multizone_trial(plan, *, source_path, zones, source_visually_inspected,
                        masks_visually_inspected, capabilities, geometry_id,
                        expected_source_pixel_sha256, expected_icc_bytes):
    """Validate source-bound multi-region work; never finalize or export here.

    The source is a *prevalidated working image* with embedded ICC. For photos
    converted from Display P3 JPEG to sRGB PNG, the caller must separately
    retain and validate the original -> working-image conversion lineage.
    """
    if not isinstance(plan, EditorialPlan):
        raise ValueError('specific photographed-scene plan required')
    path = Path(source_path).resolve(strict=True)
    if not path.is_file():
        raise ValueError('source path must point to a real file')
    actual_hash = hash_file(path)
    checked = preflight(plan, observed_source_sha256=actual_hash,
                        source_visually_inspected=source_visually_inspected,
                        capabilities=capabilities)
    if checked.action != 'READY':
        raise ValueError('editorial preflight stopped: ' + checked.reason)
    if plan.edit_route != 'native' or plan.decision != 'edit':
        raise ValueError('only verified source-based native edits supported')
    if plan.requests_geometry_change:
        raise ValueError('crop and perspective changes need separate geometry lineage')
    if plan.requires_local_selection is not True:
        raise ValueError('multiple zones require an explicit mask plan')
    if masks_visually_inspected is not True or not capabilities.verified_local_masks:
        raise ValueError('actual source-aligned masks have not been inspected')
    if not isinstance(expected_icc_bytes, bytes) or not expected_icc_bytes:
        raise ValueError('actual working color profile bytes are required')
    if not isinstance(geometry_id, str) or not geometry_id.strip():
        raise ValueError('working scene geometry identity required')
    if not isinstance(zones, (tuple, list)) or not 2 <= len(zones) <= 4:
        raise ValueError('two to four independently reviewed zones required')
    if any(not isinstance(zone, ToneZone) for zone in zones):
        raise ValueError('all zones must be inspected ToneZone objects')
    if any(zone.edge_mode == 'pixel_locked' and zone.boundary_visually_inspected is not True for zone in zones):
        raise ValueError('actual architectural edge must be inspected, not inferred')
    with Image.open(path) as decoded:
        decoded.load()
        source = decoded.copy()
        source.info.update(decoded.info)
    if hash_file(path) != actual_hash:
        raise ValueError('source file mutated during decoding')
    if source.mode != 'RGB':
        raise ValueError('working source must be decoded RGB with recorded ICC')
    if source.getexif().get(274, 1) != 1:
        raise ValueError('EXIF orientation must be normalized before experiment')
    if _sha_pixels(source) != expected_source_pixel_sha256:
        raise ValueError('source working pixels do not match reviewed original')
    if source.info.get('icc_profile') != expected_icc_bytes:
        raise ValueError('working ICC is missing or differs')
    output, technical = composite_zones(
        source, zones, observed_source_pixel_sha256=expected_source_pixel_sha256,
        source_visually_inspected=source_visually_inspected,
        masks_visually_inspected=masks_visually_inspected,
        spatial_intent=checked.direction['hierarchy'],
        expected_icc_bytes=expected_icc_bytes, geometry_id=geometry_id)
    if hash_file(path) != actual_hash:
        raise ValueError('source file mutated during processing')
    if technical.get('photographic_quality_accepted') is not False:
        raise ValueError('technical compositor cannot self-certify aesthetics')
    return PendingMultizoneTrial(
        image=output, source_file_sha256=actual_hash,
        output_pixel_sha256=technical['output_pixel_sha256'],
        spatial_direction=checked.direction, technical_receipt=technical)
