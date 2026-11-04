"""Fail-closed capability/risk routing for Photo Finish 2.0 local native trials.

This module classifies *reported* scene risk, not image pixels. It never makes
an image selection, certifies a mask, executes editing or approves aesthetics.
Only the downstream source-bound mask audit and editor can produce a candidate.
"""
from dataclasses import dataclass

from editorial_contract import controller_direction

_HIGH_RISKS = frozenset({
    'architecture_sky_edge', 'foliage_sky_edge', 'readable_text',
    'fine_object_boundary', 'reflective_surface', 'transparent_object',
})
_ALLOWED_RISKS = _HIGH_RISKS | frozenset({'none', 'mixed_lighting', 'deep_shadow'})
_ALLOWED_COMPLEXITY = frozenset({'simple', 'complex'})
_ALLOWED_REVIEWERS = frozenset({'human', 'assistant_visually_checked'})


@dataclass(frozen=True)
class AdaptiveRoute:
    action: str  # RETAIN_ORIGINAL | ELIGIBLE_MULTIZONE | STOP
    reason: str
    complexity: str  # simple | complex | unknown
    needs_boundary_review: bool
    technical_only: bool = True


def choose_adaptive_route(plan, *, observed_source_sha256,
                          source_visually_inspected, evidence):
    """Choose only supported operations. All review claims remain untrusted.

    Strict complexity evidence is required before edit. A high-risk tag or
    pixel_locked edge ALWAYS elevates the request to complex; a low-risk caller
    cannot downgrade it by specifying 'simple'. Real masks must subsequently
    pass a separate actual-pixel/ICC audit; supplied booleans are not proof.
    """
    controller_direction(plan)  # Validate required photographic context.

    def stop(reason, complexity='unknown', boundary=False):
        return AdaptiveRoute('STOP', reason, complexity, boundary)

    if not isinstance(evidence, dict):
        return stop('source-bound scene/mask evidence missing')
    if observed_source_sha256 != plan.source_sha256 or evidence.get('source_sha256') != plan.source_sha256:
        return stop('photographic plan and scene evidence identify different source bytes')
    if source_visually_inspected is not True or evidence.get('source_visually_inspected') is not True:
        return stop('real source has not been visually inspected')
    if plan.decision == 'retain_original':
        return AdaptiveRoute('RETAIN_ORIGINAL', plan.retain_reason, 'unknown', False)
    if plan.decision != 'edit' or plan.edit_route != 'native':
        return stop('only source-faithful native tonal edits are implemented')
    if plan.requests_geometry_change:
        return stop('crop/perspective lineage is not implemented by this adapter')
    if plan.requires_local_selection is not True:
        return stop('a verified global-edit route is not yet implemented')

    complexity = evidence.get('scene_complexity')
    risk_flags = evidence.get('risk_flags')
    if complexity not in _ALLOWED_COMPLEXITY:
        return stop('scene complexity must be explicitly inspected and classified')
    if (not isinstance(risk_flags, list) or
            any(not isinstance(x, str) or x not in _ALLOWED_RISKS for x in risk_flags) or
            len(risk_flags) != len(set(risk_flags))):
        return stop('risk_flags must be an explicit list of supported distinct risks')
    if 'none' in risk_flags and len(risk_flags) > 1:
        return stop('none cannot be combined with other scene risks')
    zones = evidence.get('zones')
    if not isinstance(zones, list) or not 2 <= len(zones) <= 4:
        return stop('two to four real reviewed masks are required')
    has_hard_edge = any(isinstance(z, dict) and z.get('edge_mode', 'soft') == 'pixel_locked'
                        for z in zones)
    complex_route = complexity == 'complex' or any(x in _HIGH_RISKS for x in risk_flags) or has_hard_edge
    resolved = 'complex' if complex_route else 'simple'
    if evidence.get('masks_visually_inspected') is not True:
        return stop('mask visual inspection missing', resolved, complex_route)
    if evidence.get('reviewer_mode') not in _ALLOWED_REVIEWERS:
        return stop('real mask reviewer category missing', resolved, complex_route)
    observation = evidence.get('review_observation')
    if not isinstance(observation, str) or len(observation.strip()) < 25:
        return stop('specific mask review observations are absent', resolved, complex_route)
    geometry_id = evidence.get('geometry_id')
    if not isinstance(geometry_id, str) or not geometry_id.strip():
        return stop('source mask geometry identity absent', resolved, complex_route)
    if not all(isinstance(z, dict) and z.get('reviewed') is True and
               z.get('edge_mode', 'soft') in ('soft', 'pixel_locked') for z in zones):
        return stop('one or more zones have no independent review', resolved, complex_route)
    if complex_route and (evidence.get('edge_transition_verified') is not True or
                          any(z.get('boundary_visually_inspected') is not True for z in zones)):
        return stop('complex scene boundary inspection/transition evidence insufficient', resolved, True)
    if plan.intensity == 'strong' and evidence.get('edge_transition_verified') is not True:
        return stop('strong tonal change lacks inspected edge transition', resolved, True)
    return AdaptiveRoute(
        'ELIGIBLE_MULTIZONE',
        'eligible for real mask pixel audit and pending native PNG only; not visually accepted',
        resolved, complex_route)
