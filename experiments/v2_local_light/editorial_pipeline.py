"""V2 proof-of-concept connection: spatial decision -> tonal mask adapter -> pending review.

Only for trusted, locally accessible, separately reviewed tonal candidate/masks.
Does not authorize an image service, edit persistent originals, save a version,
perform platform delivery or certify photographic quality.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from PIL import Image

from editorial_contract import EditorialPlan, ProvenCapabilities, preflight
from editor_adapter import integrate_verified_tonal_edit, _digest_pixels


@dataclass(frozen=True)
class PendingEditorialOutput:
    image: Image.Image
    source_file_sha256: str
    current_source_geometry_id: str
    controller_direction: dict
    technical_receipt: object
    status: str = 'PENDING_SPATIAL_NATURALNESS_EXPRESSIVE_VISUAL_REVIEW'


def hash_file(path):
    digest = sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run_masked_tonal_trial(plan, *, source_path, candidate, mask, target_core,
                           allowed_zone, protected, geometry_id,
                           candidate_geometry_id, source_visually_inspected,
                           masked_region_reviewed, capabilities,
                           approved_operation='non_generative_tonal_only',
                           radius_px=3):
    """A single local trial, never an accepted or saved image.

    Geometry/semantic source lineage and provider provenance are caller claims.
    The adapter additionally checks image dimensions, ICC bytes and pixel QA.
    """
    if not isinstance(plan, EditorialPlan):
        raise ValueError('a real V2 spatial plan is required')
    path = Path(source_path).resolve(strict=True)
    if not path.is_file():
        raise ValueError('source is not a file')
    byte_hash = hash_file(path)
    checked = preflight(plan, observed_source_sha256=byte_hash,
                        source_visually_inspected=source_visually_inspected,
                        capabilities=capabilities)
    if checked.action != 'READY':
        raise ValueError('editorial preflight cannot edit: ' + checked.reason)
    if plan.requests_geometry_change:
        raise ValueError('geometry-changing crop must be a separately verified edit step')
    if not plan.requires_local_selection:
        raise ValueError('this experimental entrypoint is only for verified local selections')
    if not isinstance(geometry_id, str) or not geometry_id.strip():
        raise ValueError('source geometry identity is missing')
    if not isinstance(capabilities, ProvenCapabilities) or not capabilities.verified_local_masks:
        raise ValueError('mask capability is not verified')
    with Image.open(path) as loaded:
        loaded.load()
        source = loaded.copy()
        source.info.update(loaded.info)
    if hash_file(path) != byte_hash:
        raise ValueError('source bytes changed during image decoding')
    output, technical = integrate_verified_tonal_edit(
        source, candidate, mask,
        target_core=target_core, allowed_zone=allowed_zone,
        protected=protected, source_geometry_id=geometry_id,
        candidate_geometry_id=candidate_geometry_id,
        approved_operation=approved_operation,
        masked_region_reviewed=masked_region_reviewed,
        source_pixels_hash=_digest_pixels(source), radius_px=radius_px)
    if hash_file(path) != byte_hash:
        raise ValueError('source bytes changed during tonal compositing')
    return PendingEditorialOutput(output, byte_hash, geometry_id,
                                  checked.direction, technical)
