"""Source-faithful creative-boundary policy contract, no photo/PII access.

These tests verify the rule was adopted without silently changing live native
mask semantics or treating draft QA categories as implemented runtime states.
"""
import json
from pathlib import Path
import unittest


ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'runtime/10_SYSTEM_CONFIG'


class AdoptedBoundaryPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads((CFG/'runtime_policy.json').read_text(encoding='utf-8'))
        cls.defaults=json.loads((CFG/'BEAUTIFICATION_POLICY.json').read_text(encoding='utf-8'))

    def test_protection_mirror_and_normal_semantic_default(self):
        current=self.policy['protection_policy']
        self.assertEqual(current,self.defaults['protection_policy'])
        protocol=current['boundary_protocol']
        self.assertEqual(protocol['default_content_level'],'semantic_identity')
        self.assertIn('exact RGB equality',protocol['semantic_light_color_adjustment'])
        self.assertIn('explicit RGB pixel preservation',protocol['pixel_exact_lock'])

    def test_old_wp4_exact_mask_stays_locked(self):
        protocol=self.policy['protection_policy']['boundary_protocol']
        self.assertIn('WP4',protocol['prior_task_locks'])
        self.assertIn('unchanged',protocol['runtime_migration'])
        editor=(CFG/'scripts/multizone_editor.py').read_text(encoding='utf-8')
        self.assertIn('verify_protected_pixels',editor)
        self.assertIn('protected',editor)

    def test_creative_freedom_does_not_advertise_unimplemented_engine(self):
        protocol=self.policy['protection_policy']['boundary_protocol']
        self.assertIn('Gamma/LUT',protocol['creative_freedom'])
        self.assertIn('not available in production', (ROOT/'docs/V2_FIDELITY_CREATIVE_BOUNDARY.md').read_text(encoding='utf-8'))
        self.assertIn('non-generative',protocol['experiment_scope'])

    def test_policy_does_not_weaken_identity_or_portrait_scope(self):
        scope=self.defaults['product_scope']
        self.assertFalse(scope['portrait_photographs'])
        self.assertFalse(scope['portrait_beautification'])
        self.assertEqual(self.policy['protection_policy']['levels']['semantic_identity'],
                         self.defaults['protection_policy']['levels']['semantic_identity'])

    def test_history_and_engineering_photography_distinguished(self):
        protocol=self.policy['protection_policy']['boundary_protocol']
        self.assertIn('RETAIN_ORIGINAL',protocol['outcome_states'])
        self.assertIn('PENDING_REVIEW',protocol['outcome_states'])
        self.assertIn('NO_GO_QUALITY',protocol['outcome_states'])
        self.assertIn('separate proven implementation',protocol['runtime_migration'])


if __name__=='__main__':
    unittest.main()
