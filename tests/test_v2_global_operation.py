"""Fail-closed bounded global route tests, synthetic images only.

Synthetic declarations of 'inspected' are unit test inputs, NOT real scene reviews.
"""
import json
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image,ImageCms

ENTRY=Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts/v2_native_entry.py'
def checksum(path): return sha256(Path(path).read_bytes()).hexdigest()


class SourceBoundGlobalTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.source=self.root/'source.jpeg'
        self.working=self.root/'working.png'
        self.lineage=self.root/'lineage.json'
        self.observation=self.root/'observation.json'
        self.plan=self.root/'plan.json'
        self.decision=self.root/'decision.json'
        self.operation=self.root/'operation.json'
        self.output=self.root/'output.png'
        self.receipt=self.root/'receipt.json'
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        image=Image.new('RGB',(96,96))
        image.putdata([((x*2+y)%255,(x+y*2)%255, (x*3+y*2)%255) for y in range(96) for x in range(96)])
        image.save(self.source,format='JPEG',quality=93,icc_profile=icc)
        result=self.call('prepare',self.source,self.working,self.lineage)
        self.assertEqual(result.returncode,0,result.stderr)
        proof=json.loads(self.lineage.read_text())
        self.observation_record={
            'camera_original_sha256':checksum(self.source),
            'source_sha256':checksum(self.working),
            'observation_origin':'assistant_visual_inspection',
            'original_visually_inspected':True,'subject_scope':'nonportrait_scene',
            'geometry_change_requested':False,'generative_edit_requested':False,
            'scene':'Synthetic nighttime city street with real shop signs in the source',
            'attention_entry':'Original road draws the eye into source photograph depth',
            'principal_subject':'Existing street and all observed architectural structures',
            'secondary_discovery':'Existing signs and incidental figures remain unchanged structurally',
            'spatial_relationship':'The near road leads toward the original receding city architecture',
            'source_light_evidence':'Photographed illuminated signs contrast with dark roadway shadows',
            'fixed_content_to_preserve':'All existing shop text and existing pedestrian identities',
            'visible_improvement_goal':'Subtly improve midtone readability without scene reconstruction',
            'edit_reason':'The photographed road midtones could be more clearly readable',
            'review_note':'A synthetic description for a unit test, not an actual scene inspection or approved edit.',
            'risk_flags':['readable_text'],'scene_complexity':'complex',
            'critical_edges_visually_inspected':True,
            'edit_necessity':'edit_needed','tonal_strategy':'balance_local_depth',
            'route_preference':'global','global_appearance_authorized':True,
            'pixel_exact_lock':False,
            'global_scope_reason':'A small whole-frame tonal change is proposed instead of risky object masks.'
        }
        self.save_obs()
        result=self.call('decide',self.source,self.lineage,self.observation,
                         self.plan,self.decision)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['stage'],'EDIT_PLAN_READY_GLOBAL_UNVERIFIED')
        self.op={
            'camera_original_sha256':proof['original_sha256'],
            'source_sha256':proof['working_sha256'],
            'observation_sha256':checksum(self.observation),
            'source_visually_inspected':True,
            'all_critical_content_visually_reviewed':True,
            'pixel_exact_lock':False,
            'protection_scope':'semantic_geometry_only',
            'geometry_reinterpretation':False,
            'operation':'gentle_shadow_lift',
            'strength':'subtle',
            'photographic_goal':'Reveal original dark road midtones without replacing any photographed subject or text',
            'expected_visual_change':'Slightly better roadway legibility while retaining natural lit sign and road relationship',
            'reject_conditions':'Reject if any real lettering or identity changes or sky, texture and shadows look false',
            'protected_content_observation':'Existing human figures and source signage are semantically protected, without exact pixel locks'
        }
        self.save_op()
    def save_obs(self):self.observation.write_text(json.dumps(self.observation_record),encoding='utf-8')
    def save_op(self):self.operation.write_text(json.dumps(self.op),encoding='utf-8')
    def call(self,*args):
        return subprocess.run([sys.executable,'-I','-B',str(ENTRY),*map(str,args)],capture_output=True,text=True)
    def render(self):
        return self.call('render-global',self.source,self.lineage,self.plan,
                         self.decision,self.operation,self.output,self.receipt)

    def test_actual_png_and_provenance_are_pending_not_v1(self):
        original=checksum(self.source)
        result=self.render()
        self.assertEqual(result.returncode,0,result.stderr)
        receipt=json.loads(self.receipt.read_text())
        self.assertEqual(receipt['status'],'PENDING_GLOBAL_PHOTOGRAPHIC_REVIEW')
        self.assertFalse(receipt['photographic_quality_accepted'])
        self.assertFalse(receipt['formal_V1_registered'])
        self.assertEqual(receipt['candidate_sha256'],checksum(self.output))
        self.assertEqual(receipt['semantic_content_preserved'],'PENDING_REAL_VISUAL_REVIEW')
        self.assertTrue(receipt['no_new_clip_verified'])
        with Image.open(self.working) as a,Image.open(self.output) as b:
            a.load();b.load()
            self.assertEqual(a.size,b.size)
            self.assertEqual(a.info['icc_profile'],b.info['icc_profile'])
            self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(checksum(self.source),original)

    def test_exclusive_no_overwrite_and_deterministic_replay(self):
        self.assertEqual(self.render().returncode,0)
        expected=checksum(self.output)
        self.assertNotEqual(self.render().returncode,0)
        self.assertEqual(checksum(self.output),expected)
        r=self.call('render-global',self.source,self.lineage,self.plan,self.decision,
                    self.operation,self.root/'second.png',self.root/'second.json')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(expected,checksum(self.root/'second.png'))

    def test_changed_camera_source_refused_before_output(self):
        with self.source.open('ab') as file:file.write(b'unexpected')
        self.assertNotEqual(self.render().returncode,0)
        self.assertFalse(self.output.exists())

    def test_mismatched_operation_provenance_is_refused(self):
        for field in ('camera_original_sha256','source_sha256','observation_sha256'):
            with self.subTest(field=field):
                old=self.op[field]
                self.op[field]='0'*64
                self.save_op()
                self.assertNotEqual(self.render().returncode,0)
                self.assertFalse(self.output.exists())
                self.op[field]=old

    def test_exact_pixel_lock_and_uninspected_critical_content_are_rejected(self):
        for field,value in [('pixel_exact_lock',True),
                            ('protection_scope','exact_pixels'),
                            ('all_critical_content_visually_reviewed',False),
                            ('geometry_reinterpretation',True)]:
            with self.subTest(field=field):
                old=self.op[field]
                self.op[field]=value
                self.save_op()
                self.assertNotEqual(self.render().returncode,0)
                self.assertFalse(self.output.exists())
                self.op[field]=old

    def test_unimplemented_or_oversized_operations_rejected(self):
        for field,value in [('operation','invent_new_lighting'),
                            ('strength','strong'),('photographic_goal','short')]:
            with self.subTest(field=field):
                old=self.op[field]
                self.op[field]=value
                self.save_op()
                self.assertNotEqual(self.render().returncode,0)
                self.assertFalse(self.output.exists())
                self.op[field]=old

    def test_global_path_rejects_stale_decide_receipt(self):
        decision=json.loads(self.decision.read_text())
        decision['status']='EDIT_PLAN_READY_MASKS_UNVERIFIED'
        self.decision.write_text(json.dumps(decision))
        self.assertNotEqual(self.render().returncode,0)
        self.assertFalse(self.output.exists())

    def test_bad_global_request_correctly_stops_during_decision(self):
        for field,value in [('route_preference','unsupported'),
                            ('pixel_exact_lock',True),
                            ('global_appearance_authorized',False)]:
            with self.subTest(field=field):
                old=self.observation_record[field]
                self.observation_record[field]=value
                self.save_obs()
                trial_plan=self.root/'trial_plan.json'
                trial_dec=self.root/'trial_dec.json'
                result=self.call('decide',self.source,self.lineage,self.observation,trial_plan,trial_dec)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(json.loads(result.stdout)['stage'],'STOP')
                self.assertFalse(trial_plan.exists())
                trial_dec.unlink()
                self.observation_record[field]=old

    def test_existing_output_symlink_is_not_overwritten(self):
        try:self.output.symlink_to(self.source)
        except (OSError,NotImplementedError):self.skipTest('symlink unavailable')
        self.assertNotEqual(self.render().returncode,0)
        self.assertTrue(self.output.is_symlink())

if __name__=='__main__':
    unittest.main()
