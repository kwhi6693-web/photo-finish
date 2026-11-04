"""Synthetic exact-source provider-mask bridge tests. No user photos or claims.

A synthetic result dict is *not* proof that Adobe supplied bytes in real usage.
"""
from hashlib import sha256
from pathlib import Path
from shutil import copyfile
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageCms, ImageDraw


ENTRY=Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts/v2_native_entry.py'


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


class ProviderHandoffTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.original=self.root/'camera.jpeg'
        self.working=self.root/'managed.png'
        self.lineage=self.root/'lineage.json'
        self.provider_source=self.root/'provider-source.jpeg'
        self.raw_mask=self.root/'provider-mask.png'
        self.response=self.root/'provider-response.json'
        self.mask=self.root/'canonical-mask.png'
        self.receipt=self.root/'handoff-receipt.json'
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        Image.new('RGB',(96,96),(116,139,152)).save(
            self.original,format='JPEG',quality=95,icc_profile=icc)
        copyfile(self.original,self.provider_source)
        m=Image.new('L',(96,96),0)
        ImageDraw.Draw(m).rectangle((15,15,72,78),fill=255)
        m.save(self.raw_mask,format='PNG')
        self.response.write_text(json.dumps({
            'success':True,'provider':'Adobe','operation':'image_select_by_prompt',
            'requestId':'synthetic-only-12345','outputMediaType':'image/png',
            'metadata':{'source_width':96,'source_height':96,
                        'mask_width':96,'mask_height':96}}),encoding='utf-8')
        prepared=self.invoke('prepare',self.original,self.working,self.lineage)
        self.assertEqual(prepared.returncode,0,prepared.stderr)

    def invoke(self,*args):
        return subprocess.run([sys.executable,'-I','-B',str(ENTRY),*map(str,args)],
                              capture_output=True,text=True,encoding='utf-8')

    def ingest(self, provider_source=None,raw_mask=None):
        return self.invoke('ingest-mask',self.original,self.lineage,
                           provider_source or self.provider_source,
                           raw_mask or self.raw_mask,self.response,
                           self.mask,self.receipt)

    def test_source_exact_png_handoff_remains_unreviewed(self):
        original_hash=digest(self.original)
        response=self.ingest()
        self.assertEqual(response.returncode,0,response.stderr)
        payload=json.loads(response.stdout)
        receipt=json.loads(self.receipt.read_text(encoding='utf-8'))
        self.assertEqual(payload['stage'],'RAW_MASK_BYTES_VERIFIED_NOT_SEMANTICALLY_ACCEPTED')
        self.assertEqual(receipt['camera_original_sha256'],original_hash)
        self.assertEqual(receipt['provider_source_sha256'],original_hash)
        self.assertEqual(receipt['canonical_mask_sha256'],digest(self.mask))
        self.assertFalse(receipt['mask_visually_inspected'])
        self.assertFalse(receipt['semantic_mask_accepted'])
        self.assertFalse(receipt['formal_V1_registered'])
        self.assertFalse(receipt['photographic_quality_accepted'])
        with Image.open(self.mask) as im:
            im.load()
            self.assertEqual(im.mode,'L')
            self.assertEqual(im.size,(96,96))
            self.assertEqual(im.format,'PNG')
        self.assertEqual(digest(self.original),original_hash)

    def test_provider_source_must_match_original_bytes_not_just_dimensions(self):
        with self.provider_source.open('ab') as fd:
            fd.write(b'changed')
        r=self.ingest()
        self.assertNotEqual(r.returncode,0)
        self.assertIn('differ from the camera original',r.stderr)
        self.assertFalse(self.mask.exists())
        self.assertFalse(self.receipt.exists())

    def test_jpeg_preview_cannot_be_accepted_as_raw_png(self):
        preview=self.root/'preview.jpg'
        Image.open(self.raw_mask).convert('RGB').save(preview,format='JPEG')
        r=self.ingest(raw_mask=preview)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('lossless PNG',r.stderr)
        self.assertFalse(self.mask.exists())

    def test_mismatched_geometry_stops(self):
        p=json.loads(self.response.read_text())
        p['metadata']['mask_width']=450
        self.response.write_text(json.dumps(p),encoding='utf-8')
        r=self.ingest()
        self.assertNotEqual(r.returncode,0)
        self.assertIn('dimensions differ',r.stderr)
        self.assertFalse(self.mask.exists())

    def test_unaligned_raw_pixels_stops_even_if_metadata_claims_correct_size(self):
        Image.new('L',(450,600),255).save(self.raw_mask,format='PNG')
        r=self.ingest()
        self.assertNotEqual(r.returncode,0)
        self.assertIn('exact source geometry',r.stderr)
        self.assertFalse(self.mask.exists())

    def test_chromatic_and_alpha_masks_rejected(self):
        m=Image.new('RGB',(96,96),(0,0,0))
        ImageDraw.Draw(m).rectangle((15,15,72,78),fill=(255,248,255))
        m.save(self.raw_mask,format='PNG')
        r=self.ingest()
        self.assertNotEqual(r.returncode,0)
        self.assertIn('not identical grayscale',r.stderr)
        self.assertFalse(self.mask.exists())

    def test_nearly_empty_and_full_frame_masks_rejected(self):
        for tone in (0,255):
            Image.new('L',(96,96),tone).save(self.raw_mask,format='PNG')
            r=self.ingest()
            self.assertNotEqual(r.returncode,0)
            self.assertIn('implausibly',r.stderr)
            self.assertFalse(self.mask.exists())

    def test_existing_output_preserved(self):
        self.mask.write_text('protected prior file')
        old=digest(self.mask)
        r=self.ingest()
        self.assertNotEqual(r.returncode,0)
        self.assertIn('destination already exists',r.stderr)
        self.assertEqual(digest(self.mask),old)
        self.assertFalse(self.receipt.exists())

    def test_late_receipt_io_error_rolls_back_only_new_mask(self):
        sys.path.insert(0,str(ENTRY.parent))
        import v2_native_entry as entry
        original_hash=digest(self.original)
        raw_hash=digest(self.raw_mask)
        with patch.object(entry,'_exclusive_json',side_effect=OSError('simulated write failure')):
            with self.assertRaisesRegex(OSError,'simulated write failure'):
                entry.ingest_mask(self.original,self.lineage,self.provider_source,
                                  self.raw_mask,self.response,self.mask,self.receipt)
        self.assertFalse(self.mask.exists())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(digest(self.original),original_hash)
        self.assertEqual(digest(self.raw_mask),raw_hash)

    def test_same_original_not_independent_provider_copy(self):
        r=self.ingest(provider_source=self.original)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('independently materialized',r.stderr)
        self.assertFalse(self.mask.exists())


if __name__=='__main__':
    unittest.main()
