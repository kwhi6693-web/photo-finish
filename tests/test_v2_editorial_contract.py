"""Synthetic protocol tests; no actual photo/artistic-quality pass is asserted."""
from dataclasses import replace
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'v2_local_light'))
from editorial_contract import (EditorialPlan, ProvenCapabilities, EditorialReview,
                                controller_direction, preflight, review_editorial)

H = 'a' * 64


def plan():
    return EditorialPlan(source_sha256=H, scene='Historic street after sunset',
        spatial_premise='People and pharmacy signs establish lived city scale beside the lit hotel',
        attention_entry='The foreground pedestrians and the diagonal road line invite entry',
        principal_subject='Warm golden architecture follows the receding road as visual destination',
        secondary_discovery='Street pedestrians and readable shop signage add ordinary life',
        spatial_relationship='From street-level daily life into the distant glowing hotel facade',
        source_light_evidence='Actual storefront lights and yellow hotel edge lights, black sky',
        lighting_direction='Protect people and signage while shaping existing hotel light hierarchy',
        color_direction='Retain warm hotel lights and quiet cooler street tones without exaggerated neon',
        visible_improvement_goal='Clearer first-to-second attention and authentic editorial city depth',
        fixed_content_to_preserve='Exact Chinese sign lettering, buildings, people and physical structures',
        failure_conditions='Stop for altered writing, invented structures, halo edges or flat visual hierarchy',
        requires_local_selection=True)


def capabilities():
    return ProvenCapabilities(True, True, True, True, verified_local_masks=True,
                              edge_transition_verified=True, supports_crop=True)


def feedback():
    return EditorialReview(H, 'b' * 64, True, True, True, True, True, True, True,
        'Viewer enters from nearby figures into receding road and lit structure',
        'Warm hotel has stronger presence while neon labels remain legible and realistic')


def reviewed(p=None, f=None):
    plan_value = plan() if p is None else p
    feedback_value = feedback() if f is None else f
    return review_editorial(plan_value, feedback_value,
                            observed_source_sha256=H, observed_output_sha256='b' * 64)


class EditorialProtocolTests(unittest.TestCase):
    def test_output_six_fields_are_compatible_with_existing_controller(self):
        fields = controller_direction(plan())
        self.assertEqual(set(fields), {'intent', 'hierarchy', 'light_material', 'output_use', 'route', 'qa_focus'})
        self.assertEqual(fields['route'], 'native')
        self.assertIn('空间叙事', fields['intent'])
        self.assertEqual(len(fields['qa_focus']), 4)
        from delivery_automation import direction_details
        self.assertEqual(direction_details(**fields), fields)

    def test_uninspected_or_different_source_stops(self):
        self.assertEqual(preflight(plan(), observed_source_sha256='x' * 64,
            source_visually_inspected=True, capabilities=capabilities()).action, 'STOP')
        self.assertEqual(preflight(plan(), observed_source_sha256=H,
            source_visually_inspected=False, capabilities=capabilities()).action, 'STOP')

    def test_missing_real_editor_or_mask_stops(self):
        self.assertEqual(preflight(plan(), observed_source_sha256=H, source_visually_inspected=True,
            capabilities=ProvenCapabilities(False, True, True, True)).action, 'STOP')
        self.assertEqual(preflight(plan(), observed_source_sha256=H, source_visually_inspected=True,
            capabilities=replace(capabilities(), verified_local_masks=False)).action, 'STOP')

    def test_no_silent_downgrade_on_unverified_strong_edges(self):
        p = replace(plan(), intensity='strong')
        self.assertEqual(preflight(p, observed_source_sha256=H, source_visually_inspected=True,
            capabilities=replace(capabilities(), edge_transition_verified=False)).action, 'STOP')

    def test_strong_is_not_automatically_equivalent_to_unnatural(self):
        p = replace(plan(), intensity='strong')
        self.assertEqual(preflight(p, observed_source_sha256=H, source_visually_inspected=True,
            capabilities=capabilities()).action, 'READY')

    def test_crop_requires_real_capability(self):
        p = replace(plan(), requests_geometry_change=True)
        self.assertEqual(preflight(p, observed_source_sha256=H, source_visually_inspected=True,
            capabilities=replace(capabilities(), supports_crop=False)).action, 'STOP')

    def test_unsupported_creative_route_must_not_be_misrepresented_as_native(self):
        p = replace(plan(), edit_route='creative')
        self.assertEqual(preflight(p, observed_source_sha256=H, source_visually_inspected=True,
            capabilities=capabilities()).action, 'STOP')

    def test_valid_route_returns_existing_shape(self):
        r = preflight(plan(), observed_source_sha256=H, source_visually_inspected=True,
                      capabilities=capabilities())
        self.assertEqual(r.action, 'READY')
        self.assertIn('hierarchy', r.direction)

    def test_genuinely_excellent_original_can_be_retained_with_reason(self):
        p = replace(plan(), decision='retain_original',
                    retain_reason='Original has complete spatial narrative and no credible post edit improvement')
        self.assertEqual(preflight(p, observed_source_sha256=H, source_visually_inspected=True,
            capabilities=None).action, 'RETAIN_ORIGINAL')

    def test_shallow_decisions_rejected(self):
        with self.assertRaises(ValueError):
            controller_direction(replace(plan(), visible_improvement_goal='better'))

    def test_real_review_all_three_axes_required(self):
        self.assertTrue(reviewed().accepted)
        for key in ('fixed_content_preserved', 'natural_coherence',
                    'spatial_story_improved', 'expressive_improvement'):
            with self.subTest(key=key):
                self.assertFalse(reviewed(f=replace(feedback(), **{key: False})).accepted)

    def test_night_street_positive_does_not_certify_portfolio_automatically(self):
        r = reviewed(f=replace(feedback(), user_feedback='positive'))
        self.assertTrue(r.accepted)
        self.assertFalse(r.certified_portfolio_grade)

    def test_courtyard_negative_feedback_blocks_even_technical_pass(self):
        r = reviewed(f=replace(feedback(), user_feedback='negative'))
        self.assertFalse(r.accepted)

    def test_unseen_real_output_never_passes(self):
        self.assertFalse(reviewed(f=replace(feedback(), real_output_verified=False)).accepted)

    def test_wrong_output_and_source_never_pass(self):
        self.assertFalse(reviewed(f=replace(feedback(), output_sha256='?')).accepted)
        self.assertFalse(reviewed(f=replace(feedback(), source_sha256='c' * 64)).accepted)

    def test_actual_file_hash_change_blocks_reused_visual_feedback(self):
        self.assertFalse(review_editorial(plan(), feedback(),
            observed_source_sha256=H, observed_output_sha256='c' * 64).accepted)
        self.assertFalse(review_editorial(plan(), feedback(),
            observed_source_sha256='c' * 64, observed_output_sha256='b' * 64).accepted)

    def test_unspecific_visual_observation_rejected(self):
        self.assertFalse(reviewed(f=replace(feedback(), reviewer_observation='nice')).accepted)


if __name__ == '__main__':
    unittest.main()
