"""V2 full local-camera-file to pending edited native PNG synthetic integration."""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image, ImageCms, ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'/'v2_local_light'))
from source_lineage import prepare_working_source, verify_source_lineage
from native_workflow import run_native_photo_trial
from editorial_contract import EditorialPlan, ProvenCapabilities
from multizone_editor import ToneZone
from editorial_pipeline import hash_file


def mask(box):
    i=Image.new('L',(96,96),0)
    ImageDraw.Draw(i).rectangle(box,fill=255)
    return i


class FullNativePhotoTrialTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.original=Path(tmp.name)/'actual_original.jpg'
        self.working=Path(tmp.name)/'managed_working.png'
        self.output=Path(tmp.name)/'pending_edit.png'
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        Image.new('RGB',(96,96),(120,140,160)).save(self.original,format='JPEG',quality=95,icc_profile=icc)
        self.original_hash=hash_file(self.original)
        self.lineage=prepare_working_source(self.original,self.working)
        with Image.open(self.working) as image:
            image.load()
            self.icc=image.info['icc_profile']
        self.plan=EditorialPlan(
            source_sha256=self.lineage.working_sha256,
            scene='A photographed old building with shaded natural foreground',
            spatial_premise='Near pavement leads into the existing building light',
            attention_entry='Begin in quiet shaded ground and look toward architecture',
            principal_subject='Existing real stone structure remains the visual subject',
            secondary_discovery='Original pavement and tree shadows keep local context',
            spatial_relationship='Source-grounded near-to-far luminous depth guides viewing',
            source_light_evidence='The photographed building is naturally lighter than the road',
            lighting_direction='Gently separate the authentic foreground and architectural midground',
            color_direction='Use neutral natural daylight and realistic stone color',
            visible_improvement_goal='Emphasize actual image depth without adding any object or graphic',
            fixed_content_to_preserve='Do not rebuild stone, text, people or trees from the photo',
            failure_conditions='Reject false masks, halo edges or reconstructed structure',
            requires_local_selection=True)
        self.zones=[
            ToneZone('foreground',mask((18,18,42,76)),mask((21,23,39,69)),
                     mask((8,8,52,86)),mask((84,32,92,60)),1.22,1,
                     'Quiet photographic near field without inventing lighting'),
            ToneZone('architecture',mask((54,18,78,76)),mask((57,23,74,69)),
                     mask((44,8,88,86)),mask((84,32,92,60)),.84,1,
                     'Preserve actual historic stone while guiding the viewing path')]
        self.kwargs=dict(
            source_visually_inspected=True,masks_visually_inspected=True,
            capabilities=ProvenCapabilities(True,True,True,True,verified_local_masks=True),
            geometry_id='g96-reviewed-synthetic',expected_icc_bytes=self.icc,
            destination=self.output)

    def test_camera_file_to_real_native_png_remains_pending(self):
        result=run_native_photo_trial(self.original,self.lineage,self.plan,self.zones,**self.kwargs)
        self.assertEqual(result.camera_original_sha256,self.original_hash)
        self.assertEqual(result.working_source_sha256,hash_file(self.working))
        self.assertEqual(result.candidate_sha256,hash_file(self.output))
        self.assertEqual(result.status,'PENDING_ACTUAL_PHOTOGRAPHIC_REVIEW_AND_FORMAL_V1')
        self.assertFalse(result.technical_receipt['photographic_quality_accepted'])
        self.assertTrue(verify_source_lineage(self.original,self.lineage))
        self.assertEqual(hash_file(self.original),self.original_hash)
        with Image.open(self.output) as out:
            out.load()
            self.assertEqual(out.format,'PNG')
            self.assertEqual(out.info['icc_profile'],self.icc)

    def test_source_changed_after_normalization_stops_without_output(self):
        self.original.write_bytes(self.original.read_bytes()+b'different')
        with self.assertRaisesRegex(ValueError,'original bytes changed'):
            run_native_photo_trial(self.original,self.lineage,self.plan,self.zones,**self.kwargs)
        self.assertFalse(self.output.exists())

    def test_source_change_after_export_removes_own_unreceipted_candidate(self):
        from unittest.mock import patch
        import native_workflow as workflow
        export=workflow.export_pending_png
        def change_after_export(*args,**kwargs):
            result=export(*args,**kwargs)
            self.original.write_bytes(self.original.read_bytes()+b'changed-after-export')
            return result
        with patch.object(workflow,'export_pending_png',side_effect=change_after_export):
            with self.assertRaisesRegex(ValueError,'changed'):
                workflow.run_native_photo_trial(self.original,self.lineage,self.plan,self.zones,**self.kwargs)
        self.assertFalse(self.output.exists())

    def test_plan_for_another_photo_fails_before_output(self):
        plan=replace(self.plan,source_sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'not bound'):
            run_native_photo_trial(self.original,self.lineage,plan,self.zones,**self.kwargs)
        self.assertFalse(self.output.exists())

    def test_unreviewed_masks_fail_before_output(self):
        with self.assertRaisesRegex(ValueError,'inspected'):
            run_native_photo_trial(self.original,self.lineage,self.plan,self.zones,
                                   **dict(self.kwargs,masks_visually_inspected=False))
        self.assertFalse(self.output.exists())


if __name__=='__main__':
    unittest.main()
