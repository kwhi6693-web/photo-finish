"""Source-bound editorial direction compiler for Photo Finish 2.0.

This module does NOT perceive pixels. A trusted visual observer (human or
assistant viewing the actual photo) supplies observations; the controller
validates them, compiles a bounded EditorialPlan and refuses to invent source
facts, mask geometry, editor capability or photographic approval.
"""
from dataclasses import dataclass
from editorial_contract import EditorialPlan, controller_direction
from adaptive_route import _ALLOWED_RISKS, _HIGH_RISKS

_STRATEGIES = {
    'preserve_highlights': 'Gently retain recorded bright-region texture without inventing light',
    'balance_local_depth': 'Separate existing foreground and background tones without fabricating illumination',
    'lift_subject_shadows': 'Lift authentic subject shadows while preserving naturally dark anchor regions',
    'subdue_distractions': 'Quiet distracting existing regions while keeping source-relative tonal continuity',
}
_ORIGINS = frozenset(('assistant_visual_inspection', 'human_visual_inspection'))
_REQUIRED_FIELDS = (
    'scene', 'attention_entry', 'principal_subject',
    'secondary_discovery', 'spatial_relationship',
    'source_light_evidence', 'fixed_content_to_preserve',
    'visible_improvement_goal', 'edit_reason', 'review_note',
)


@dataclass(frozen=True)
class ObservedDirection:
    action: str  # EDIT_PLAN_READY_MASKS_UNVERIFIED | RETAIN_ORIGINAL | STOP
    reason: str
    plan: EditorialPlan | None
    risk_flags: tuple[str, ...]
    scene_complexity: str
    source_visually_inspected: bool
    masks_visually_inspected: bool = False
    photographic_quality_accepted: bool = False
    formal_V1_registered: bool = False


def compile_observed_direction(observation, *, camera_original_sha256,
                               working_source_sha256):
    """Compile only explicit, source-matched real-photo observations.

    No inferred scene semantics or artificial ability claims. A STOP decision
    is distinct from an affirmative, photographed retain-original decision.
    """
    def stop(reason):
        return ObservedDirection('STOP', reason, None, (), 'unknown', False)

    if not isinstance(observation, dict):
        return stop('real visual observation object missing')
    if (observation.get('camera_original_sha256') != camera_original_sha256 or
            observation.get('source_sha256') != working_source_sha256):
        return stop('visual observation belongs to different camera or working bytes')
    if (observation.get('observation_origin') not in _ORIGINS or
            observation.get('original_visually_inspected') is not True):
        return stop('actual visual inspection provenance is not recorded')
    if observation.get('subject_scope') != 'nonportrait_scene':
        return stop('only non-portrait photography is in the current scope')
    if observation.get('geometry_change_requested') is not False:
        return stop('source-preserving native route cannot promise geometry edits')
    if observation.get('generative_edit_requested') is not False:
        return stop('generative editing is outside source-faithful native route')
    fields = {}
    for name in _REQUIRED_FIELDS:
        value = observation.get(name)
        if not isinstance(value, str) or len(value.strip()) < (25 if name=='review_note' else 12):
            return stop('source-specific photographed observation absent: ' + name)
        fields[name] = value.strip()
    need = observation.get('edit_necessity')
    if need not in ('edit_needed', 'retain_original', 'uncertain'):
        return stop('edit necessity must be explicitly observed')
    if need == 'uncertain':
        return stop('uncertain photographic benefit; do not edit or falsely retain')
    risks = observation.get('risk_flags')
    if (not isinstance(risks, list) or len(risks)==0 or
            any(type(item) is not str or item not in _ALLOWED_RISKS for item in risks) or
            len(risks) != len(set(risks)) or
            ('none' in risks and len(risks)>1)):
        return stop('explicit supported distinct risk flags required')
    complexity = observation.get('scene_complexity')
    if complexity not in ('simple','complex'):
        return stop('actual photographed scene complexity not described')
    if (complexity == 'complex' or any(r in _HIGH_RISKS for r in risks)):
        complexity = 'complex'
    if (complexity == 'complex' and
            observation.get('critical_edges_visually_inspected') is not True):
        return stop('complex photographed boundaries lack direct visual review')
    strategy = observation.get('tonal_strategy')
    if need == 'edit_needed' and strategy not in _STRATEGIES:
        return stop('unsupported or absent source-faithful tonal strategy')
    if need == 'retain_original':
        retain = observation.get('retain_reason')
        if not isinstance(retain,str) or len(retain.strip())<25:
            return stop('explicit positive retain-original evidence required')
        light_direction='Preserve the original, already effective source light without additional edits'
    else:
        retain=''
        light_direction=_STRATEGIES[strategy]
    plan=EditorialPlan(
        source_sha256=working_source_sha256,
        scene=fields['scene'],
        spatial_premise=fields['spatial_relationship'],
        attention_entry=fields['attention_entry'],
        principal_subject=fields['principal_subject'],
        secondary_discovery=fields['secondary_discovery'],
        spatial_relationship=fields['spatial_relationship'],
        source_light_evidence=fields['source_light_evidence'],
        lighting_direction=light_direction,
        color_direction='Preserve source-recorded color, material identity and real illumination',
        visible_improvement_goal=fields['visible_improvement_goal'],
        fixed_content_to_preserve=fields['fixed_content_to_preserve'],
        failure_conditions='STOP on false selection, changed text, edge halos, lost source identity or invented light',
        edit_route='native',
        requires_local_selection=(need=='edit_needed'),
        requests_geometry_change=False,
        intensity='subtle' if complexity=='complex' else 'moderate',
        decision='edit' if need=='edit_needed' else 'retain_original',
        retain_reason=retain)
    controller_direction(plan)
    if need == 'retain_original':
        return ObservedDirection('RETAIN_ORIGINAL', retain, plan,
                                 tuple(risks),complexity,True)
    return ObservedDirection(
        'EDIT_PLAN_READY_MASKS_UNVERIFIED',
        'source-bound photographic plan compiled; actual reviewed masks, pixel audit and tool ability still required',
        plan,tuple(risks),complexity,True)
