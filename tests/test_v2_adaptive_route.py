"""Synthetic safety tests for adaptive route decisions; NOT real-photo quality."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       'runtime/10_SYSTEM_CONFIG/scripts'))
from editorial_contract import EditorialPlan
from adaptive_route import choose_adaptive_route

SOURCE='a'*64


def plan(**changes):
    base=EditorialPlan(
        source_sha256=SOURCE,
        scene='A photographed urban structure under real daylight',
        spatial_premise='Observed foreground and middle ground support a viewing path',
        attention_entry='Enter via original foreground geometry and natural shadows',
        principal_subject='Existing architecture is the primary documentary subject',
        secondary_discovery='Original street and foliage create genuine scene context',
        spatial_relationship='Real foreground and background retain their actual spatial relation',
        source_light_evidence='Visible original daylight and shadow shape the materials',
        lighting_direction='Subtle source-faithful tonal separation of photographed zones',
        color_direction='Keep existing daylight color and architectural textures realistic',
        visible_improvement_goal='Increase true subject hierarchy only when warranted',
        fixed_content_to_preserve='Preserve exact text, roofs, sky and all observed objects',
        failure_conditions='Reject false masks, halos, altered lettering or fabricated light',
        requires_local_selection=True)
    return replace(base,**changes)


def evidence(**changes):
    base={
        'source_sha256':SOURCE,
        'source_visually_inspected':True,
        'scene_complexity':'simple',
        'risk_flags':['none'],
        'masks_visually_inspected':True,
        'reviewer_mode':'human',
        'review_observation':'Synthetic masks inspected on exact working source geometry; no visual certification.',
        'geometry_id':'synthetic-reviewed-g96',
        'zones':[{'reviewed':True,'edge_mode':'soft'},
                 {'reviewed':True,'edge_mode':'soft'}]}
    base.update(changes)
    return base


def route(p=None, e=None, source=SOURCE, inspected=True):
    return choose_adaptive_route(p or plan(),observed_source_sha256=source,
                                 source_visually_inspected=inspected,
                                 evidence=e if e is not None else evidence())


class AdaptiveRouteTests(unittest.TestCase):
    def test_normal_reviewed_multizone_is_only_eligible(self):
        value=route()
        self.assertEqual(value.action,'ELIGIBLE_MULTIZONE')
        self.assertTrue(value.technical_only)
        self.assertEqual(value.complexity,'simple')

    def test_scene_risk_elevates_wrongly_labelled_simple_to_complex(self):
        value=route(e=evidence(risk_flags=['architecture_sky_edge']))
        self.assertEqual(value.action,'STOP')
        self.assertEqual(value.complexity,'complex')
        self.assertTrue(value.needs_boundary_review)

    def test_locked_edge_also_elevates_complexity(self):
        z=[{'reviewed':True,'edge_mode':'pixel_locked'},
           {'reviewed':True,'edge_mode':'soft'}]
        value=route(e=evidence(zones=z))
        self.assertEqual(value.action,'STOP')
        self.assertEqual(value.complexity,'complex')

    def test_reviewed_complex_is_eligible_not_accepted(self):
        z=[{'reviewed':True,'edge_mode':'pixel_locked','boundary_visually_inspected':True},
           {'reviewed':True,'edge_mode':'soft','boundary_visually_inspected':True}]
        value=route(e=evidence(zones=z,risk_flags=['architecture_sky_edge'],
                               edge_transition_verified=True))
        self.assertEqual(value.action,'ELIGIBLE_MULTIZONE')
        self.assertTrue(value.technical_only)
        self.assertEqual(value.complexity,'complex')

    def test_explicit_retain_is_distinct_from_failure(self):
        p=plan(decision='retain_original',
               retain_reason='Source photograph is already visually complete and natural.')
        e=evidence()
        e.pop('zones')
        value=route(p,e)
        self.assertEqual(value.action,'RETAIN_ORIGINAL')
        self.assertNotEqual(route(p,e,source='b'*64).action,'RETAIN_ORIGINAL')

    def test_missing_evidence_fails_closed_not_retain(self):
        self.assertEqual(route(e={}).action,'STOP')
        self.assertEqual(route(inspected=False).action,'STOP')
        self.assertEqual(route(source='b'*64).action,'STOP')
        self.assertEqual(route(e=evidence(scene_complexity='unknown')).action,'STOP')
        self.assertEqual(route(e=evidence(risk_flags=['unrecognized_risk'])).action,'STOP')
        self.assertEqual(route(e=evidence(risk_flags=['none','readable_text'])).action,'STOP')
        self.assertEqual(route(e=evidence(risk_flags=['none','none'])).action,'STOP')
        self.assertEqual(route(e=evidence(reviewer_mode='nobody')).action,'STOP')
        self.assertEqual(route(e=evidence(review_observation='yes')).action,'STOP')
        self.assertEqual(route(e=evidence(geometry_id='  ')).action,'STOP')
        self.assertEqual(route(e=evidence(zones=[])).action,'STOP')

    def test_unsupported_operations_do_not_silently_downgrade(self):
        self.assertEqual(route(plan(requires_local_selection=False)).action,'STOP')
        self.assertEqual(route(plan(requests_geometry_change=True)).action,'STOP')
        self.assertEqual(route(plan(edit_route='creative')).action,'STOP')
        self.assertEqual(route(plan(intensity='strong')).action,'STOP')
        self.assertEqual(route(e=evidence(masks_visually_inspected=False)).action,'STOP')
        self.assertEqual(route(e=evidence(zones=[
            {'reviewed':True,'edge_mode':'soft'},
            {'reviewed':False,'edge_mode':'soft'}])).action,'STOP')


if __name__=='__main__':
    unittest.main()
