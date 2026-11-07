"""Synthetic end-to-end native curve controller tests; no user photo or GO."""
from hashlib import sha256
from pathlib import Path
import json
import tempfile
import unittest
from PIL import Image, ImageCms
from tests.test_v2_global_operation import SourceBoundGlobalTests, checksum


class NativeBoundedCurveControllerTests(unittest.TestCase):
    def setUp(self):
        # Reuse the EXISTING real controller fixture and provenance model.
        SourceBoundGlobalTests.setUp(self)
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        image=Image.new('RGB',(96,96))
        image.putdata([(79+x//4+y//16,92+x//4+y//16,105+x//4+y//16)
                       for y in range(96) for x in range(96)])
        image.save(self.source,format='JPEG',quality=95,icc_profile=icc)
        for path in (self.working,self.lineage,self.observation,self.plan,self.decision):
            path.unlink()
        prep=self.call('prepare',self.source,self.working,self.lineage)
        self.assertEqual(prep.returncode,0,prep.stderr)
        proof=json.loads(self.lineage.read_text())
        self.observation_record['camera_original_sha256']=checksum(self.source)
        self.observation_record['source_sha256']=checksum(self.working)
        self.observation_record['scene']='Synthetic open blue sky with a smooth midtone gradient and no pixel-exact locks'
        self.observation_record['fixed_content_to_preserve']='Sky shape and each existing gradation must not be redrawn or generated'
        self.observation_record['visible_improvement_goal']='Create a naturally wider scene tonal range without content fabrication'
        self.observation_record['edit_reason']='Original sky has compressed tones needing a bounded global improvement'
        self.observation_record['risk_flags']=[]
        self.observation_record['scene_complexity']='simple'
        self.save_obs()
        decision=self.call('decide',self.source,self.lineage,self.observation,self.plan,self.decision)
        self.assertEqual(decision.returncode,0,decision.stderr)
        self.assertEqual(json.loads(decision.stdout)['stage'],'EDIT_PLAN_READY_GLOBAL_UNVERIFIED')
        self.op.update({'camera_original_sha256':proof['original_sha256'],
                        'source_sha256':proof['working_sha256'],
                        'observation_sha256':checksum(self.observation),
                        'operation':'bounded_color_curve',
                        'strength':'subtle',
                        'photographic_goal':'Expand the existing source sky gradient with a bounded monotone curve and no fabrication',
                        'expected_visual_change':'A noticeably brighter native candidate without new clipped channels or synthetic clouds',
                        'reject_conditions':'Reject suspicious stair-step banding or brightness overextension on the actual sky 1:1 review',
                        'protected_content_observation':'The complete existing sky remains one actual source image and keeps all true structure'})
        self.save_op()

    def test_native_render_returns_source_bound_pending_receipt(self):
        raw=checksum(self.source)
        result=self.render()
        self.assertEqual(result.returncode,0,result.stderr)
        receipt=json.loads(self.receipt.read_text())
        self.assertEqual(receipt['status'],'PENDING_GLOBAL_PHOTOGRAPHIC_REVIEW')
        self.assertEqual(receipt['operation']['operation'],'bounded_color_curve')
        self.assertEqual(receipt['candidate_sha256'],checksum(self.output))
        self.assertEqual(receipt['camera_original_sha256'],raw)
        self.assertEqual(receipt['curve_safety']['dither_strength'],.7)
        self.assertLessEqual(receipt['curve_safety']['smooth_max_slope'],2.500001)
        self.assertIn(receipt['curve_safety']['status'],('STRENGTH_LIMITED','WITHIN_LIMITS'))
        self.assertEqual(receipt['curve_safety']['photographic_goal_met'],'NOT_AUTOMATICALLY_DECIDED')
        self.assertFalse(receipt['photographic_quality_accepted'])
        self.assertFalse(receipt['formal_V1_registered'])
        with Image.open(self.output) as candidate,Image.open(self.working) as source:
            self.assertEqual(candidate.size,source.size)
            self.assertEqual(candidate.info['icc_profile'],source.info['icc_profile'])
        self.assertEqual(checksum(self.source),raw)

    def test_repeat_same_source_is_deterministic_and_no_overwrite(self):
        self.assertEqual(self.render().returncode,0)
        frozen=checksum(self.output)
        self.assertNotEqual(self.render().returncode,0)
        self.assertEqual(checksum(self.output),frozen)
        output2=self.root/'replay.png'
        receipt2=self.root/'replay.json'
        result=self.call('render-global',self.source,self.lineage,self.plan,
                         self.decision,self.operation,output2,receipt2)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(checksum(output2),frozen)

    def test_existing_protected_content_refusal_applies(self):
        self.op['pixel_exact_lock']=True
        self.save_op()
        trial=self.render()
        self.assertNotEqual(trial.returncode,0)
        self.assertFalse(self.output.exists())


if __name__=='__main__':
    unittest.main()
