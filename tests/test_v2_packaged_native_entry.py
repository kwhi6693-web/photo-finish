"""Isolated subprocess tests for the *packaged runtime* v2 native entry.

Uses generated synthetic photos; success is not real photographic approval,
actual iPhone delivery or official V1 registration. No user images are loaded.
"""
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageCms, ImageDraw


ENTRY = Path(__file__).resolve().parents[1] / 'runtime/10_SYSTEM_CONFIG/scripts/v2_native_entry.py'


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


class PackagedNativeEntryTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.original=self.root/'source.jpg'
        self.working=self.root/'working.png'
        self.lineage=self.root/'lineage.json'
        self.plan=self.root/'plan.json'
        self.zones=self.root/'zones.json'
        self.result=self.root/'candidate.png'
        self.receipt=self.root/'candidate.json'
        self.profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        Image.new('RGB',(96,96),(130,145,155)).save(
            self.original,format='JPEG',quality=95,icc_profile=self.profile)

    def invoke(self,*args):
        return subprocess.run([sys.executable,'-I','-B',str(ENTRY),*map(str,args)],
                              capture_output=True,text=True,encoding='utf-8')

    def fixture(self):
        first=self.invoke('prepare',self.original,self.working,self.lineage)
        self.assertEqual(first.returncode,0,first.stderr)
        lineage=json.loads(self.lineage.read_text(encoding='utf-8'))
        plan=dict(
            source_sha256=lineage['working_sha256'],
            scene='Historic stone buildings with quiet naturally shaded ground',
            spatial_premise='Actual photographed near pavement leads into original buildings',
            attention_entry='Begin at the near shadow then follow the actual stone relief',
            principal_subject='An existing structure is the natural center of attention',
            secondary_discovery='Original plants and pavement supply truthful local context',
            spatial_relationship='Real near-to-far layers are emphasized without changing the scene',
            source_light_evidence='The source itself contains a shaded part and a lighter region',
            lighting_direction='Deepen foreground locally while retaining naturally bright stone',
            color_direction='Preserve original light neutrality and natural stone colors',
            visible_improvement_goal='Improve tonal hierarchy with only authentic recorded pixels',
            fixed_content_to_preserve='No invented building, signage, people or landscape objects',
            failure_conditions='Reject wrong masks, repaired text or novel structural details',
            requires_local_selection=True)
        self.plan.write_text(json.dumps(plan),encoding='utf-8')
        def mask(name,box):
            f=self.root/(name+'.png')
            m=Image.new('L',(96,96),0)
            ImageDraw.Draw(m).rectangle(box,fill=255)
            m.save(f)
            return str(f),digest(f)
        defs=[]
        for name,coords,gamma,allowed,core in [
            ('near-ground',(18,18,42,76),1.24,(8,8,52,86),(21,23,39,69)),
            ('lit-masonry',(54,18,78,76),.84,(44,8,88,86),(57,23,74,69))]:
            spec=dict(name=name,gamma=gamma,saturation=1.0,reviewed=True,
                      purpose='Bounded same-source light shape with no reconstructed pixels')
            for key,rectangle in [('mask',coords),('core',core),('allowed',allowed),
                                   ('protected',(84,32,92,60))]:
                path,checksum=mask(name+'-'+key,rectangle)
                spec[key+'_path']=path
                spec[key+'_sha256']=checksum
            defs.append(spec)
        self.zones.write_text(json.dumps({
            'source_sha256':lineage['working_sha256'],
            'geometry_id':'source96-fully-reviewed-synthetic',
            'scene_complexity':'simple','risk_flags':['none'],
            'reviewer_mode':'human',
            'review_observation':'Synthetic masks inspected over exact source geometry; not photographic approval.',
            'source_visually_inspected':True,'masks_visually_inspected':True,
            'zones':defs}),encoding='utf-8')
        return lineage

    def test_installed_path_writes_real_png_and_pending_receipt(self):
        original_hash=digest(self.original)
        lineage=self.fixture()
        result=self.invoke('render',self.original,self.lineage,self.plan,self.zones,
                           self.result,self.receipt)
        self.assertEqual(result.returncode,0,result.stderr)
        payload=json.loads(self.receipt.read_text(encoding='utf-8'))
        self.assertEqual(payload['candidate_sha256'],digest(self.result))
        self.assertEqual(payload['camera_original_sha256'],original_hash)
        self.assertEqual(payload['working_source_sha256'],lineage['working_sha256'])
        self.assertFalse(payload['formal_V1_registered'])
        self.assertFalse(payload['photographic_quality_accepted'])
        self.assertEqual(payload['route']['action'],'ELIGIBLE_MULTIZONE')
        self.assertTrue(payload['route']['technical_only'])
        self.assertEqual(digest(self.original),original_hash)
        with Image.open(self.result) as image:
            image.load()
            self.assertEqual(image.format,'PNG')
            self.assertEqual(image.size,(96,96))
            self.assertTrue(image.info.get('icc_profile'))

    def test_explicit_retain_original_writes_only_decision_receipt(self):
        original_hash=digest(self.original)
        self.fixture()
        data=json.loads(self.plan.read_text(encoding='utf-8'))
        data['decision']='retain_original'
        data['retain_reason']='Already an effective documentary photograph; preserve its original light.'
        self.plan.write_text(json.dumps(data),encoding='utf-8')
        # A retain decision must work without even requesting a semantic mask.
        z=json.loads(self.zones.read_text(encoding='utf-8'))
        z.pop('zones')
        self.zones.write_text(json.dumps(z),encoding='utf-8')
        response=self.invoke('render',self.original,self.lineage,self.plan,self.zones,
                             self.result,self.receipt)
        self.assertEqual(response.returncode,0,response.stderr)
        output=json.loads(response.stdout)
        self.assertEqual(output['stage'],'RETAIN_ORIGINAL')
        self.assertIsNone(output['native_png_path'])
        self.assertIsNone(output['pending_output_sha256'])
        self.assertFalse(self.result.exists())
        self.assertEqual(digest(self.original),original_hash)
        record=json.loads(self.receipt.read_text(encoding='utf-8'))
        self.assertFalse(record['formal_V1_registered'])

    def test_unclassified_scene_stops_with_no_png_and_audit_receipt(self):
        original_hash=digest(self.original)
        self.fixture()
        z=json.loads(self.zones.read_text(encoding='utf-8'))
        z.pop('scene_complexity')
        self.zones.write_text(json.dumps(z),encoding='utf-8')
        response=self.invoke('render',self.original,self.lineage,self.plan,self.zones,
                             self.result,self.receipt)
        self.assertEqual(response.returncode,0,response.stderr)
        self.assertEqual(json.loads(response.stdout)['stage'],'STOP')
        self.assertFalse(self.result.exists())
        record=json.loads(self.receipt.read_text(encoding='utf-8'))
        self.assertTrue(record['route']['technical_only'])
        self.assertFalse(record['photographic_quality_accepted'])
        self.assertEqual(digest(self.original),original_hash)

    def test_risk_flag_elevates_simple_to_complex_and_blocks_unreviewed_edge(self):
        self.fixture()
        z=json.loads(self.zones.read_text(encoding='utf-8'))
        z['scene_complexity']='simple'
        z['risk_flags']=['architecture_sky_edge']
        self.zones.write_text(json.dumps(z),encoding='utf-8')
        response=self.invoke('render',self.original,self.lineage,self.plan,self.zones,
                             self.result,self.receipt)
        self.assertEqual(response.returncode,0,response.stderr)
        decision=json.loads(self.receipt.read_text(encoding='utf-8'))['route']
        self.assertEqual(decision['action'],'STOP')
        self.assertEqual(decision['complexity'],'complex')
        self.assertTrue(decision['needs_boundary_review'])
        self.assertFalse(self.result.exists())

    def test_complex_scene_with_actual_reviewed_masks_can_render_pending_png(self):
        self.fixture()
        z=json.loads(self.zones.read_text(encoding='utf-8'))
        z['scene_complexity']='complex'
        z['risk_flags']=['architecture_sky_edge']
        z['edge_transition_verified']=True
        for zone in z['zones']:
            zone['boundary_visually_inspected']=True
        self.zones.write_text(json.dumps(z),encoding='utf-8')
        response=self.invoke('render',self.original,self.lineage,self.plan,self.zones,
                             self.result,self.receipt)
        self.assertEqual(response.returncode,0,response.stderr)
        record=json.loads(self.receipt.read_text(encoding='utf-8'))
        self.assertEqual(record['route']['action'],'ELIGIBLE_MULTIZONE')
        self.assertEqual(record['route']['complexity'],'complex')
        self.assertFalse(record['photographic_quality_accepted'])
        self.assertEqual(digest(self.result),record['candidate_sha256'])

    def test_unimplemented_global_route_fails_closed(self):
        self.fixture()
        plan=json.loads(self.plan.read_text(encoding='utf-8'))
        plan['requires_local_selection']=False
        self.plan.write_text(json.dumps(plan),encoding='utf-8')
        r=self.invoke('render',self.original,self.lineage,self.plan,self.zones,
                      self.result,self.receipt)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(self.receipt.read_text())['status'],'STOP')
        self.assertFalse(self.result.exists())

    def test_existing_prepare_receipt_prevents_orphan_working_image(self):
        original_hash=digest(self.original)
        self.lineage.write_text('reserved receipt',encoding='utf-8')
        prior=digest(self.lineage)
        r=self.invoke('prepare',self.original,self.working,self.lineage)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('destination already exists',r.stderr)
        self.assertFalse(self.working.exists())
        self.assertEqual(digest(self.lineage),prior)
        self.assertEqual(digest(self.original),original_hash)

    def test_existing_render_receipt_prevents_orphan_candidate(self):
        original_hash=digest(self.original)
        self.fixture()
        self.receipt.write_text('reserved receipt',encoding='utf-8')
        prior=digest(self.receipt)
        r=self.invoke('render',self.original,self.lineage,self.plan,self.zones,
                      self.result,self.receipt)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('destination already exists',r.stderr)
        self.assertFalse(self.result.exists())
        self.assertEqual(digest(self.receipt),prior)
        self.assertEqual(digest(self.original),original_hash)

    def test_prepare_late_receipt_failure_removes_only_new_working_png(self):
        sys.path.insert(0,str(ENTRY.parent))
        import v2_native_entry as entry
        original_hash=digest(self.original)
        with patch.object(entry,'_exclusive_json',side_effect=OSError('simulated receipt I/O failure')):
            with self.assertRaisesRegex(OSError,'simulated receipt'):
                entry.prepare(self.original,self.working,self.lineage)
        self.assertFalse(self.working.exists())
        self.assertFalse(self.lineage.exists())
        self.assertEqual(digest(self.original),original_hash)

    def test_render_late_receipt_failure_removes_pending_png(self):
        sys.path.insert(0,str(ENTRY.parent))
        import v2_native_entry as entry
        self.fixture()
        original_hash=digest(self.original)
        working_hash=digest(self.working)
        with patch.object(entry,'_exclusive_json',side_effect=OSError('simulated receipt I/O failure')):
            with self.assertRaisesRegex(OSError,'simulated receipt'):
                entry.render(self.original,self.lineage,self.plan,self.zones,
                             self.result,self.receipt)
        self.assertFalse(self.result.exists())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(digest(self.original),original_hash)
        self.assertEqual(digest(self.working),working_hash)

    def test_verified_rollback_never_removes_changed_or_receipted_file(self):
        sys.path.insert(0,str(ENTRY.parent))
        import v2_native_entry as entry
        self.result.write_bytes(b'pending candidate')
        original=digest(self.result)
        self.receipt.write_text('existing user receipt',encoding='utf-8')
        entry._rollback_unreceipted_png(self.result,original,self.receipt)
        self.assertTrue(self.result.exists())
        self.receipt.unlink()
        self.result.write_bytes(b'changed by another actor')
        entry._rollback_unreceipted_png(self.result,original,self.receipt)
        self.assertEqual(self.result.read_bytes(),b'changed by another actor')

    def test_wrong_mask_hash_stops_without_output(self):
        self.fixture()
        data=json.loads(self.zones.read_text(encoding='utf-8'))
        data['zones'][0]['mask_sha256']='0'*64
        self.zones.write_text(json.dumps(data),encoding='utf-8')
        r=self.invoke('render',self.original,self.lineage,self.plan,self.zones,
                      self.result,self.receipt)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('mask component changed',r.stderr)
        self.assertFalse(self.result.exists())
        self.assertFalse(self.receipt.exists())


if __name__=='__main__':
    unittest.main()
