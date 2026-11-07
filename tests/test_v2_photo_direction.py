"""Source-bound observed photo-direction regression; synthetic sources only.

A test's claimed visual inspection is NOT a real scene observation or evidence
that the model can perceive photos without the host showing them.
"""
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageCms

ENTRY=Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts/v2_native_entry.py'


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


class ObservedDirectionCLITests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.camera=self.root/'source.jpg'
        self.working=self.root/'working.png'
        self.lineage=self.root/'lineage.json'
        self.observation=self.root/'visual_observation.json'
        self.plan=self.root/'editorial_plan.json'
        self.receipt=self.root/'decision_receipt.json'
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        Image.new('RGB',(96,96),(105,127,148)).save(
            self.camera,format='JPEG',quality=95,icc_profile=icc)
        prep=self.invoke('prepare',self.camera,self.working,self.lineage)
        self.assertEqual(prep.returncode,0,prep.stderr)
        self.l=json.loads(self.lineage.read_text(encoding='utf-8'))
        self.data={
            'camera_original_sha256':sha(self.camera),
            'source_sha256':sha(self.working),
            'observation_origin':'assistant_visual_inspection',
            'original_visually_inspected':True,
            'subject_scope':'nonportrait_scene',
            'geometry_change_requested':False,
            'generative_edit_requested':False,
            'scene':'Observed original historic stone structure in existing natural daylight',
            'attention_entry':'Recorded darker foreground leads toward genuine masonry details',
            'principal_subject':'The genuine photographed historic building facade',
            'secondary_discovery':'The original surrounding walls provide local architectural context',
            'spatial_relationship':'Recorded foreground meets existing distant bright stone surfaces',
            'source_light_evidence':'Original highlights and real deep shadows fall across recorded stone',
            'fixed_content_to_preserve':'Every original character, roof edge, carved detail and nearby sky',
            'visible_improvement_goal':'Clarify source-faithful tonal separation without reconstructing objects',
            'edit_reason':'The photographed shadow depth could better support the existing masonry',
            'review_note':'This is synthetic observation metadata in a unit test, not a photographed visual assessment.',
            'risk_flags':['architecture_sky_edge'],
            'scene_complexity':'simple',  # must elevate to complex
            'critical_edges_visually_inspected':True,
            'edit_necessity':'edit_needed',
            'tonal_strategy':'balance_local_depth',
        }
        self.save()

    def save(self):
        self.observation.write_text(json.dumps(self.data),encoding='utf-8')

    def invoke(self,*args):
        return subprocess.run(
            [sys.executable,'-I','-B',str(ENTRY),*map(str,args)],
            capture_output=True,text=True,encoding='utf-8')

    def decide(self):
        return self.invoke('decide',self.camera,self.lineage,self.observation,
                           self.plan,self.receipt)

    def test_compiles_source_bound_pending_plan_not_an_approved_edit(self):
        original_sha=sha(self.camera)
        result=self.decide()
        self.assertEqual(result.returncode,0,result.stderr)
        payload=json.loads(result.stdout)
        self.assertEqual(payload['stage'],'EDIT_PLAN_READY_MASKS_UNVERIFIED')
        record=json.loads(self.receipt.read_text(encoding='utf-8'))
        plan=json.loads(self.plan.read_text(encoding='utf-8'))
        self.assertEqual(plan['source_sha256'],self.l['working_sha256'])
        self.assertEqual(plan['decision'],'edit')
        self.assertEqual(plan['intensity'],'subtle')
        self.assertTrue(plan['requires_local_selection'])
        self.assertEqual(record['scene_complexity'],'complex')
        self.assertEqual(record['pending_plan_sha256'],sha(self.plan))
        self.assertEqual(record['camera_original_sha256'],original_sha)
        self.assertFalse(record['photographic_quality_accepted'])
        self.assertFalse(record['formal_V1_registered'])
        self.assertFalse(record['masks_visually_inspected'])
        self.assertEqual(sha(self.camera),original_sha)

    def test_retention_distinct_from_unsupported_stop(self):
        self.data['edit_necessity']='retain_original'
        self.data['retain_reason']='The original photograph already has meaningful shape and coherent recorded light.'
        self.data.pop('tonal_strategy')
        self.save()
        r=self.decide()
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['stage'],'RETAIN_ORIGINAL')
        self.assertEqual(json.loads(self.plan.read_text())['decision'],'retain_original')
        self.assertFalse(json.loads(self.receipt.read_text())['formal_V1_registered'])

    def test_uncertain_visual_merit_stops_without_plan(self):
        self.data['edit_necessity']='uncertain'
        self.save()
        r=self.decide()
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['stage'],'STOP')
        self.assertFalse(self.plan.exists())
        self.assertTrue(self.receipt.exists())

    def test_wrong_source_and_nonportrait_scope_stop(self):
        for key,value in [('camera_original_sha256','0'*64),
                          ('source_sha256','0'*64),
                          ('subject_scope','portrait_task')]:
            with self.subTest(key=key):
                former=self.data[key]
                self.data[key]=value
                self.save()
                r=self.decide()
                self.assertEqual(r.returncode,0,r.stderr)
                self.assertEqual(json.loads(r.stdout)['stage'],'STOP')
                self.assertFalse(self.plan.exists())
                self.receipt.unlink()
                self.data[key]=former

    def test_unseen_complex_edges_stop(self):
        self.data['critical_edges_visually_inspected']=False
        self.save()
        r=self.decide()
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['stage'],'STOP')
        self.assertFalse(self.plan.exists())

    def test_unverified_generation_or_geometry_stops(self):
        for name in ('geometry_change_requested','generative_edit_requested'):
            with self.subTest(name=name):
                self.data[name]=True
                self.save()
                r=self.decide()
                self.assertEqual(r.returncode,0,r.stderr)
                self.assertEqual(json.loads(r.stdout)['stage'],'STOP')
                self.assertFalse(self.plan.exists())
                self.receipt.unlink()
                self.data[name]=False

    def test_missing_observation_field_and_unsupported_strategy_stop(self):
        for key,value in [('review_note','short'),('tonal_strategy','create_new_sunlight'),
                          ('risk_flags',['none','architecture_sky_edge']),
                          ('observation_origin','pretend_ai_runtime')]:
            with self.subTest(key=key):
                old=self.data[key]
                self.data[key]=value
                self.save()
                r=self.decide()
                self.assertEqual(r.returncode,0,r.stderr)
                self.assertEqual(json.loads(r.stdout)['stage'],'STOP')
                self.assertFalse(self.plan.exists())
                self.receipt.unlink()
                self.data[key]=old

    def test_source_tamper_blocks_without_any_new_receipt(self):
        self.camera.write_bytes(self.camera.read_bytes()+b'other bytes')
        r=self.decide()
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.receipt.exists())
        self.assertFalse(self.plan.exists())

    def test_existing_plan_or_receipt_fails_before_write(self):
        for occupied in (self.plan,self.receipt):
            occupied.write_text('protected',encoding='utf-8')
            r=self.decide()
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(occupied.read_text(encoding='utf-8'),'protected')
            self.assertFalse((self.receipt if occupied==self.plan else self.plan).exists())
            occupied.unlink()

    def test_late_decision_receipt_failure_rolls_back_only_pending_plan(self):
        sys.path.insert(0,str(ENTRY.parent))
        import v2_native_entry as entry
        own=entry._exclusive_json
        count=[0]
        def fake(path, data):
            count[0]+=1
            if count[0]==2:
                raise OSError('simulated decision receipt failure')
            return own(path,data)
        with patch.object(entry,'_exclusive_json',side_effect=fake):
            with self.assertRaisesRegex(OSError,'simulated decision receipt'):
                entry.decide(self.camera,self.lineage,self.observation,
                             self.plan,self.receipt)
        self.assertFalse(self.plan.exists())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(sha(self.camera),self.data['camera_original_sha256'])


if __name__=='__main__':
    unittest.main()
