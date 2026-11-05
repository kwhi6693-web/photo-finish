"""Synthetic source-bound composition tests. Not a real photographic review."""
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image, ImageCms

SCRIPTS=Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'
sys.path.insert(0,str(SCRIPTS))
from source_lineage import prepare_working_source, verify_source_lineage
from v2_spatial_preflight import compile_composition,bind_to_real_pending

class SpatialPreflightTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        root=Path(folder.name)
        self.original=root/'actual_source.jpeg'
        self.working=root/'working.png'
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        im=Image.new('RGB',(800,1000),(123,98,74))
        im.save(self.original,format='JPEG',icc_profile=icc,quality=92)
        self.proof=prepare_working_source(self.original,self.working)
        self.record={'camera_original_sha256':self.proof.original_sha256,
                     'source_sha256':self.proof.working_sha256,
                     'observation_origin':'assistant_visual_inspection',
                     'original_visually_inspected':True,'nonportrait_scope':True,
                     'generative_edit_requested':False,'frame_action':'crop',
                     'crop_visually_inspected':True,
                     'source_bbox_px':[40,70,760,990],
                     'reviewed_must_keep_boxes':[
                         {'label':'actual facade roof edge','bbox_px':[100,120,450,500]},
                         {'label':'source dark framing line','bbox_px':[48,180,82,850]}],
                     'photographic_intent':'Keep photographed facade and genuine dark foreground while reducing unnecessary empty sky.',
                     'visual_observation':'Synthetic visible-source fixture description, not a real scene assessment or artistic acceptance.'}
        self.assertTrue(verify_source_lineage(self.original,self.proof))
    def decide(self):return compile_composition(self.original,self.proof,self.record)
    def test_accepted_crop_is_only_pending_proposal(self):
        proof=self.decide()
        self.assertEqual(proof.action,'CROP_PROPOSED')
        self.assertEqual(proof.source_bbox_px,(40,70,760,990))
        self.assertFalse(proof.photographic_quality_accepted)
        self.assertFalse(proof.formal_V1_registered)
        self.assertGreater(proof.retained_source_fraction,0.8)
    def test_keep_frame_does_not_emit_crop(self):
        self.record['frame_action']='keep';self.record['source_bbox_px']=None
        x=self.decide()
        self.assertEqual(x.action,'KEEP_FRAME')
        self.assertIsNone(x.source_bbox_px)
        self.assertFalse(x.formal_V1_registered)
        with self.assertRaisesRegex(ValueError,'preplanned'):
            bind_to_real_pending(x,{})
    def test_wrong_original_sha_rejected(self):
        self.record['camera_original_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'missing or mismatched'):
            self.decide()
    def test_actual_original_tamper_rejected(self):
        with self.original.open('ab') as stream:stream.write(b'changed')
        with self.assertRaisesRegex(ValueError,'lineage|original bytes changed'):
            self.decide()
    def test_crop_cannot_cut_content_anchor(self):
        self.record['source_bbox_px']=[130,70,760,990]
        with self.assertRaisesRegex(ValueError,'severe|content'):
            self.decide()
    def test_severe_or_trivial_crop_rejected(self):
        for rect in ([240,200,750,800],[0,0,800,1000],[0,0,700,0]):
            with self.subTest(rect=rect):
                self.record['source_bbox_px']=rect
                with self.assertRaises(ValueError):self.decide()
    def test_requires_real_crop_boundary_review(self):
        self.record['crop_visually_inspected']=False
        with self.assertRaisesRegex(ValueError,'visually'):
            self.decide()
    def test_requires_nonportrait_scope_and_no_generator(self):
        for key,value in [('nonportrait_scope',False),('generative_edit_requested',True),
                          ('original_visually_inspected',False)]:
            with self.subTest(key=key):
                old=self.record[key];self.record[key]=value
                with self.assertRaises(ValueError):self.decide()
                self.record[key]=old
    def test_unknown_decision_returns_stop(self):
        self.record['frame_action']='invent_new_subject'
        self.assertEqual(self.decide().action,'STOP')
    def test_content_boxes_and_type_checks(self):
        for box in ([False,70,760,990],[-1,20,700,800],[0,0,800]):
            with self.subTest(box=box):
                self.record['source_bbox_px']=box
                with self.assertRaises(ValueError):self.decide()
    def test_bind_parent_receipt_requires_exact_identity(self):
        d=self.decide()
        pending={'status':'PENDING_GLOBAL_PHOTOGRAPHIC_REVIEW',
                 'camera_original_sha256':d.camera_original_sha256,
                 'working_source_sha256':d.working_source_sha256,
                 'candidate_sha256':'a'*64,'photographic_quality_accepted':False,
                 'formal_V1_registered':False}
        seal=bind_to_real_pending(d,pending)
        self.assertEqual(seal['source_bbox_px'],[40,70,760,990])
        self.assertFalse(seal['formal_V1_registered'])
        pending['camera_original_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'mismatched'):
            bind_to_real_pending(d,pending)
    def test_bound_replay_cannot_accept_formal_v1(self):
        d=self.decide()
        pending={'status':'PENDING_GLOBAL_PHOTOGRAPHIC_REVIEW',
                 'camera_original_sha256':d.camera_original_sha256,
                 'working_source_sha256':d.working_source_sha256,
                 'candidate_sha256':'a'*64,'photographic_quality_accepted':False,
                 'formal_V1_registered':True}
        with self.assertRaises(ValueError):bind_to_real_pending(d,pending)

if __name__=='__main__':unittest.main()
