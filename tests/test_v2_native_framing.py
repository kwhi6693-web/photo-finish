"""Synthetic source-bound framing regressions. Not photographic quality tests."""
from hashlib import sha256
from pathlib import Path
import json, subprocess, sys, tempfile, unittest
from unittest.mock import patch
from PIL import Image, ImageCms

ENTRY=Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts/v2_native_entry.py'
def checksum(p): return sha256(Path(p).read_bytes()).hexdigest()

class NativeFrameTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.original=self.root/'camera.jpeg'
        self.working=self.root/'managed.png'
        self.lineage=self.root/'lineage.json'
        self.parent=self.root/'pending.png'
        self.parent_receipt=self.root/'pending_receipt.json'
        self.plan=self.root/'frame_plan.json'
        self.output=self.root/'cropped.png'
        self.receipt=self.root/'frame_receipt.json'
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        image=Image.new('RGB',(96,96))
        image.putdata([((x*7)%255,(y*9)%255,((x+y)*13)%255) for y in range(96) for x in range(96)])
        image.save(self.original,format='JPEG',icc_profile=icc,quality=93)
        prep=self.invoke('prepare',self.original,self.working,self.lineage)
        self.assertEqual(prep.returncode,0,prep.stderr)
        self.L=json.loads(self.lineage.read_text())
        with Image.open(self.working) as image:
            image.load();image.save(self.parent,format='PNG',icc_profile=image.info['icc_profile'])
        self.P={'status':'PENDING_ACTUAL_PHOTOGRAPHIC_REVIEW_AND_FORMAL_V1',
                'camera_original_sha256':checksum(self.original),
                'working_source_sha256':checksum(self.working),
                'candidate_sha256':checksum(self.parent),
                'candidate_path':str(self.parent),
                'photographic_quality_accepted':False,'formal_V1_registered':False}
        self.F={'camera_original_sha256':self.P['camera_original_sha256'],
                'working_source_sha256':self.P['working_source_sha256'],
                'parent_pending_sha256':self.P['candidate_sha256'],
                'source_bbox_px':[8,6,87,89],
                'source_visually_inspected':True,'crop_visually_inspected':True,
                'photographic_intent':'Place existing architectural structure at a clearer visual scale without invention.',
                'visual_observation':'Synthetic test evidence only, not an actual photographic scene visual acceptance.'}
        self.write()
    def write(self):
        self.plan.write_text(json.dumps(self.F),encoding='utf-8')
        self.parent_receipt.write_text(json.dumps(self.P),encoding='utf-8')
    def invoke(self,*args):
        return subprocess.run([sys.executable,'-I','-B',str(ENTRY),*map(str,args)],capture_output=True,text=True)
    def frame(self):
        return self.invoke('reframe',self.original,self.lineage,self.parent,
                           self.parent_receipt,self.plan,self.output,self.receipt)
    def test_source_exact_crop_icc_receipt_no_edit_acceptance(self):
        original=checksum(self.original);old=checksum(self.parent)
        r=self.frame();self.assertEqual(r.returncode,0,r.stderr)
        record=json.loads(self.receipt.read_text())
        self.assertEqual(record['output_sha256'],checksum(self.output))
        self.assertEqual(record['parent_pending_sha256'],old)
        self.assertFalse(record['photographic_quality_accepted'])
        self.assertFalse(record['formal_V1_registered'])
        with Image.open(self.parent) as p,Image.open(self.output) as c:
            p.load();c.load()
            self.assertEqual(c.size,(79,83))
            self.assertEqual(c.info['icc_profile'],p.info['icc_profile'])
            self.assertEqual(c.tobytes(),p.crop((8,6,87,89)).tobytes())
        self.assertEqual(checksum(self.original),original)
        self.assertEqual(checksum(self.parent),old)
    def test_existing_and_replay_byte_stable(self):
        self.assertEqual(self.frame().returncode,0)
        h=checksum(self.output)
        self.assertNotEqual(self.frame().returncode,0)
        self.assertEqual(checksum(self.output),h)
        r=self.invoke('reframe',self.original,self.lineage,self.parent,
                      self.parent_receipt,self.plan,self.root/'second.png',self.root/'second.json')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(checksum(self.root/'second.png'),h)
    def test_camera_source_tamper_stops(self):
        with self.original.open('ab') as fd:fd.write(b'changed')
        self.assertNotEqual(self.frame().returncode,0)
        self.assertFalse(self.output.exists())
    def test_wrong_pending_identity_rejected(self):
        for key,value in [('candidate_sha256','0'*64),('candidate_path','wrong.png')]:
            with self.subTest(key=key):
                old=self.P[key];self.P[key]=value;self.write()
                self.assertNotEqual(self.frame().returncode,0)
                self.assertFalse(self.output.exists());self.P[key]=old
    def test_accepted_or_nonpending_parent_rejected(self):
        for key,value in [('status','DELIVERED'),('formal_V1_registered',True),
                          ('photographic_quality_accepted',True)]:
            with self.subTest(key=key):
                old=self.P[key];self.P[key]=value;self.write()
                self.assertNotEqual(self.frame().returncode,0)
                self.assertFalse(self.output.exists());self.P[key]=old
    def test_fake_source_and_visual_evidence_stop(self):
        for key,value in [('camera_original_sha256','0'*64),('parent_pending_sha256','1'*64),
                          ('source_visually_inspected',False),('crop_visually_inspected',False),
                          ('photographic_intent','no'),('visual_observation','no')]:
            with self.subTest(key=key):
                old=self.F[key];self.F[key]=value;self.write()
                self.assertNotEqual(self.frame().returncode,0)
                self.assertFalse(self.output.exists());self.F[key]=old
    def test_invalid_crop_pixels_fail_closed(self):
        for rect in [[0,0,100,80],[0,0,4,5],[True,0,94,94],
                     [3,3,3,89],[-1,0,96,96], [0,0,95], [2.5,3,90,95]]:
            with self.subTest(rect=rect):
                self.F['source_bbox_px']=rect;self.write()
                self.assertNotEqual(self.frame().returncode,0)
                self.assertFalse(self.output.exists())
    def test_missing_icc_rejected(self):
        with Image.open(self.parent) as image:
            image.load();copy=image.copy();copy.info.pop('icc_profile',None)
            copy.save(self.parent,format='PNG')
        self.P['candidate_sha256']=checksum(self.parent)
        self.F['parent_pending_sha256']=self.P['candidate_sha256'];self.write()
        self.assertNotEqual(self.frame().returncode,0)
        self.assertFalse(self.output.exists())
    def test_pending_symlink_rejected(self):
        link=self.root/'alias.png'
        try:link.symlink_to(self.parent)
        except (OSError,NotImplementedError):self.skipTest('symlink unavailable')
        self.P['candidate_path']=str(link);self.write()
        r=self.invoke('reframe',self.original,self.lineage,link,
                      self.parent_receipt,self.plan,self.output,self.receipt)
        self.assertNotEqual(r.returncode,0);self.assertFalse(self.output.exists())
    def test_no_overwrite(self):
        for occupied in (self.output,self.receipt):
            occupied.write_text('existing data')
            self.assertNotEqual(self.frame().returncode,0)
            self.assertEqual(occupied.read_text(),'existing data')
            occupied.unlink()
    def test_late_receipt_failure_only_removes_owned_unreceipted_png(self):
        sys.path.insert(0,str(ENTRY.parent))
        import v2_native_entry as entry
        old=checksum(self.parent)
        with patch.object(entry,'_exclusive_json',side_effect=OSError('late simulated fault')):
            with self.assertRaisesRegex(OSError,'late simulated fault'):
                entry.reframe(self.original,self.lineage,self.parent,self.parent_receipt,
                              self.plan,self.output,self.receipt)
        self.assertFalse(self.output.exists());self.assertFalse(self.receipt.exists())
        self.assertEqual(checksum(self.parent),old)

if __name__=='__main__':unittest.main()
