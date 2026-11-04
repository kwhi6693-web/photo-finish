"""V2 native image workflow: independently proven source lineage -> edit -> PNG.

Runs on the actual host working files. Never selects semantic masks itself,
approves a photo visually, calls Adobe, saves to Library, or writes a formal V1.
The caller must supply source-aligned real masks and review observations.
"""
from dataclasses import dataclass
from pathlib import Path

from editorial_contract import EditorialPlan, ProvenCapabilities
from multizone_workflow import run_multizone_trial
from native_candidate_export import export_pending_png
from source_lineage import SourceLineage, verify_source_lineage


@dataclass(frozen=True)
class PendingNativePhoto:
    camera_original_sha256: str
    working_source_sha256: str
    candidate_sha256: str
    candidate_path: str
    source_lineage: SourceLineage
    spatial_direction: dict
    technical_receipt: dict
    status: str = 'PENDING_ACTUAL_PHOTOGRAPHIC_REVIEW_AND_FORMAL_V1'


def run_native_photo_trial(original_photo_path, lineage, plan, zones, *,
                           source_visually_inspected, masks_visually_inspected,
                           capabilities, geometry_id, expected_icc_bytes,
                           destination):
    """Use actual source-bound masks, never a model-inferred success assertion.

    The working source must already exist. The caller must have reviewed the
    converted pixels and created per-zone masks on that exact working geometry.
    A successful result is only a pending, real PNG file on the local host.
    """
    if not isinstance(lineage, SourceLineage):
        raise ValueError('actual original-to-working source evidence missing')
    if not verify_source_lineage(original_photo_path, lineage):
        raise ValueError('original-to-working file lineage is not verified')
    if not isinstance(plan, EditorialPlan) or plan.source_sha256 != lineage.working_sha256:
        raise ValueError('editorial plan is not bound to real managed working source')
    if not isinstance(capabilities, ProvenCapabilities):
        raise ValueError('real editor capability attestation absent')
    if Path(destination).resolve() == Path(lineage.working_path).resolve():
        raise ValueError('do not overwrite verified working source')
    pending = run_multizone_trial(
        plan, source_path=lineage.working_path, zones=zones,
        source_visually_inspected=source_visually_inspected,
        masks_visually_inspected=masks_visually_inspected,
        capabilities=capabilities, geometry_id=geometry_id,
        expected_source_pixel_sha256=lineage.working_pixel_sha256,
        expected_icc_bytes=expected_icc_bytes)
    exported = export_pending_png(pending, working_source_path=lineage.working_path,
                                  destination=destination)
    if not verify_source_lineage(original_photo_path, lineage):
        raise ValueError('original or working file was modified during editing')
    if exported.source_sha256 != lineage.working_sha256:
        raise ValueError('native candidate does not match managed source')
    return PendingNativePhoto(
        camera_original_sha256=lineage.original_sha256,
        working_source_sha256=lineage.working_sha256,
        candidate_sha256=exported.sha256,
        candidate_path=exported.path,
        source_lineage=lineage, spatial_direction=pending.spatial_direction,
        technical_receipt=pending.technical_receipt)
