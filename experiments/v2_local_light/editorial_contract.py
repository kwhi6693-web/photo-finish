"""Experimental, no-I/O Photo Finish 2.0 editorial decision/acceptance contract.

Compatibility bridge to the existing six-key delivery_automation.direction_details
API; not a released Skill runtime or an image editor. The caller supplies actual
image observations; this module cannot perceive a scene or certify aesthetics.
"""
from dataclasses import dataclass
import re

SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _phrase(value, label):
    if not isinstance(value, str) or len(value.strip()) < 10:
        raise ValueError(label + " requires a concrete observed description")
    return value.strip()


@dataclass(frozen=True)
class EditorialPlan:
    source_sha256: str
    scene: str
    spatial_premise: str
    attention_entry: str
    principal_subject: str
    secondary_discovery: str
    spatial_relationship: str
    source_light_evidence: str
    lighting_direction: str
    color_direction: str
    visible_improvement_goal: str
    fixed_content_to_preserve: str
    failure_conditions: str
    edit_route: str = 'native'  # existing controller vocabulary
    output_use: str = 'screen'
    requires_local_selection: bool = False
    requests_geometry_change: bool = False
    intensity: str = 'moderate'
    decision: str = 'edit'  # edit | retain_original
    retain_reason: str = ''


@dataclass(frozen=True)
class ProvenCapabilities:
    non_generative_tonal_editor: bool
    actual_output_file: bool
    source_geometry_lineage: bool
    icc_managed: bool
    verified_local_masks: bool = False
    edge_transition_verified: bool = False
    supports_crop: bool = False


@dataclass(frozen=True)
class Preflight:
    action: str    # READY | RETAIN_ORIGINAL | STOP
    reason: str
    direction: dict | None = None


def controller_direction(plan):
    """Map a V2 spatial plan to the *existing* v1 six-field direction shape.

    This is a compatibility adapter, not an upgrade of the current runtime.
    """
    if not isinstance(plan, EditorialPlan):
        raise ValueError('requires an explicit EditorialPlan')
    if not SHA256.fullmatch(plan.source_sha256):
        raise ValueError('source SHA-256 is absent or invalid')
    if plan.edit_route not in ('native', 'hybrid', 'creative'):
        raise ValueError('route is not supported by existing controller')
    if plan.output_use not in ('screen', 'print_proof_requested'):
        raise ValueError('output use is not supported by existing controller')
    if plan.decision not in ('edit', 'retain_original'):
        raise ValueError('invalid editorial decision')
    if plan.intensity not in ('subtle', 'moderate', 'strong'):
        raise ValueError('invalid requested intensity')
    if type(plan.requires_local_selection) is not bool or type(plan.requests_geometry_change) is not bool:
        raise ValueError('editing capability requirements must be actual booleans')
    fields = ('scene', 'spatial_premise', 'attention_entry', 'principal_subject',
              'secondary_discovery', 'spatial_relationship', 'source_light_evidence',
              'lighting_direction', 'color_direction', 'visible_improvement_goal',
              'fixed_content_to_preserve', 'failure_conditions')
    for name in fields:
        _phrase(getattr(plan, name), name)
    if plan.decision == 'retain_original' and not isinstance(plan.retain_reason, str):
        raise ValueError('retain reason must be an actual sentence')
    if plan.decision == 'retain_original':
        _phrase(plan.retain_reason, 'retain_reason')
    return {
        'intent': f'{plan.scene}｜空间叙事：{plan.spatial_premise}；目标：{plan.visible_improvement_goal}',
        'hierarchy': (f'视觉进入：{plan.attention_entry}；主体：{plan.principal_subject}；'
                      f'其次：{plan.secondary_discovery}；空间关系：{plan.spatial_relationship}'),
        'light_material': (f'原片真实光线：{plan.source_light_evidence}；'
                           f'局部塑光：{plan.lighting_direction}；色彩：{plan.color_direction}'),
        'output_use': plan.output_use, 'route': plan.edit_route,
        'qa_focus': [f'空间叙事是否真正改善：{plan.spatial_relationship}',
                     f'正常观看尺寸是否显著提升：{plan.visible_improvement_goal}',
                     f'结构与真实材质保护：{plan.fixed_content_to_preserve}',
                     f'失败/STOP：{plan.failure_conditions}']}


def preflight(plan, *, observed_source_sha256, source_visually_inspected,
              capabilities):
    """Require actually verified capabilities; otherwise STOP rather than downgrade silently."""
    direction = controller_direction(plan)
    if observed_source_sha256 != plan.source_sha256:
        return Preflight('STOP', 'original file identity does not match the plan')
    if source_visually_inspected is not True:
        return Preflight('STOP', 'original pixels have not been visually inspected')
    if plan.decision == 'retain_original':
        return Preflight('RETAIN_ORIGINAL', plan.retain_reason)
    if not isinstance(capabilities, ProvenCapabilities):
        return Preflight('STOP', 'real editor capabilities have not been verified')
    if any(type(getattr(capabilities, key)) is not bool for key in
           ('non_generative_tonal_editor', 'actual_output_file',
            'source_geometry_lineage', 'icc_managed', 'verified_local_masks',
            'edge_transition_verified', 'supports_crop')):
        return Preflight('STOP', 'editor capabilities require actual boolean evidence')
    if not all((capabilities.non_generative_tonal_editor,
                capabilities.actual_output_file,
                capabilities.source_geometry_lineage,
                capabilities.icc_managed)):
        return Preflight('STOP', 'no verified same-source tonal file/ICC route')
    if plan.edit_route != 'native':
        return Preflight('STOP', 'experimental adapter supports native route only')
    if plan.requires_local_selection and not capabilities.verified_local_masks:
        return Preflight('STOP', 'local subject mask not actually verified')
    if plan.requests_geometry_change and not capabilities.supports_crop:
        return Preflight('STOP', 'geometry edit route not verified')
    if plan.intensity == 'strong' and plan.requires_local_selection and not capabilities.edge_transition_verified:
        return Preflight('STOP', 'strong local edit needs verified halo-free edges')
    return Preflight('READY', 'direction is source-bound; edit has not occurred', direction)


@dataclass(frozen=True)
class EditorialReview:
    source_sha256: str
    output_sha256: str
    real_output_verified: bool
    same_source_comparison: bool
    normal_and_detail_viewed: bool
    fixed_content_preserved: bool
    natural_coherence: bool
    spatial_story_improved: bool
    expressive_improvement: bool
    viewing_path_observation: str
    reviewer_observation: str
    user_feedback: str = 'not_collected'  # positive | negative | not_collected
    edge_detail_reviewed: bool = False
    halo_or_seam_absent: bool = False


@dataclass(frozen=True)
class ReviewDecision:
    accepted: bool
    reason: str
    certified_portfolio_grade: bool = False


def review_editorial(plan, review, *, observed_source_sha256, observed_output_sha256):
    """Evidence-based three-axis *human* review; never an AI aesthetic score.

    A quality acceptance requires explicit real-photo review and separately
    recorded judgments; it cannot be inferred from numerical mask tests or
    from successful image creation. Portfolio-grade is never self-certified.
    """
    if not isinstance(plan, EditorialPlan) or not isinstance(review, EditorialReview):
        return ReviewDecision(False, 'real plan and explicit visual review required')
    if review.source_sha256 != plan.source_sha256 or observed_source_sha256 != plan.source_sha256:
        return ReviewDecision(False, 'review and actual original source SHA-256 do not agree')
    if (not isinstance(review.output_sha256, str) or not SHA256.fullmatch(review.output_sha256)
            or review.output_sha256 != observed_output_sha256):
        return ReviewDecision(False, 'review output SHA-256 differs from actual file')
    if review.user_feedback not in ('positive', 'negative', 'not_collected'):
        return ReviewDecision(False, 'unknown user feedback')
    if review.user_feedback == 'negative':
        return ReviewDecision(False, 'user explicitly rejects expressive gain')
    if not all((review.real_output_verified is True,
                review.same_source_comparison is True,
                review.normal_and_detail_viewed is True)):
        return ReviewDecision(False, 'real same-source full/detail photographic comparison incomplete')
    if plan.requires_local_selection and not (review.edge_detail_reviewed is True and review.halo_or_seam_absent is True):
        return ReviewDecision(False, 'actual output mask edges need 1:1 inspection and explicit halo/seam-free review')
    if not isinstance(review.viewing_path_observation, str) or len(review.viewing_path_observation.strip()) < 16:
        return ReviewDecision(False, 'spatial viewing path lacks concrete observations')
    if not isinstance(review.reviewer_observation, str) or len(review.reviewer_observation.strip()) < 20:
        return ReviewDecision(False, 'photographic review lacks concrete observations')
    if review.fixed_content_preserved is not True or review.natural_coherence is not True:
        return ReviewDecision(False, 'fixed scene identity or natural photographic look failed')
    if review.spatial_story_improved is not True:
        return ReviewDecision(False, 'spatial narrative did not meaningfully improve')
    if review.expressive_improvement is not True:
        return ReviewDecision(False, 'editorial expressive improvement did not pass')
    return ReviewDecision(True, 'three-axis visual review passed; user preference may still be pending')
