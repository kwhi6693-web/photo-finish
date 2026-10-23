"""Color-declaration and non-destructive PNG delivery regressions."""
from pathlib import Path
import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from PIL import Image, ImageCms, PngImagePlugin
import photo_workflow as photo


class ColorDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.png'
        self.output = self.root / 'web.png'
        self.receipt = self.root / 'receipt.json'
        Image.new('RGB', (16, 12), (74, 120, 168)).save(self.source)

    def add_chunk(self, kind, value):
        data = self.source.read_bytes()
        chunk = struct.pack('>I', len(value)) + kind + value
        chunk += struct.pack('>I', zlib.crc32(kind + value) & 0xffffffff)
        self.source.write_bytes(data[:33] + chunk + data[33:])

    def export(self, **kwargs):
        function = getattr(photo, 'export_web', None)
        self.assertTrue(callable(function), 'A metadata-only web export route is required')
        return function(str(self.source), str(self.output), receipt_path=str(self.receipt), **kwargs)

    def test_srgb_chunk_is_a_color_declaration_without_icc(self):
        self.add_chunk(b'sRGB', b'\x00')
        info = photo.inspect_image(self.source)
        self.assertEqual(info.get('color', {}).get('encoding'), 'sRGB')
        self.assertEqual(info['color']['status'], 'declared')
        self.assertEqual(info['icc']['status'], 'missing')

    def test_cicp_display_p3_is_recognized(self):
        self.add_chunk(b'cICP', bytes((12, 13, 0, 1)))
        self.assertEqual(photo.inspect_image(self.source).get('color', {}).get('encoding'), 'Display P3')

    def test_higher_priority_declaration_controls_lower_fallback(self):
        self.add_chunk(b'sRGB', b'\x00')
        self.add_chunk(b'cICP', bytes((12, 13, 0, 1)))
        self.assertEqual(photo.inspect_image(self.source)['color']['encoding'], 'Display P3')
        self.assertEqual(photo.inspect_image(self.source)['color']['status'], 'declared')

    def test_untagged_is_unknown_not_proven_srgb(self):
        self.assertEqual(photo.inspect_image(self.source).get('color', {}).get('status'), 'unknown')

    def test_nonobject_delivery_metadata_is_flagged_without_trusting_it(self):
        self.add_chunk(b'tEXt', b'PCSColorPolicy\x00[1]')
        self.assertEqual(photo.inspect_image(self.source).get('color', {}).get('status'), 'invalid')
        with self.assertRaisesRegex(ValueError, 'review'):
            self.export(assume_untagged_srgb=True, assumption_reason='Ordinary sharing')

    def test_export_requires_explicit_assumption_for_untagged(self):
        with self.assertRaisesRegex(ValueError, 'assumption'):
            self.export()
        self.assertFalse(self.output.exists())

    def test_assumption_export_preserves_source_pixels_and_records_limit(self):
        before = self.source.read_bytes()
        self.add_chunk(b'caBX', b'fixture-authenticity-manifest')
        before = self.source.read_bytes()
        result = self.export(assume_untagged_srgb=True,
                             assumption_reason='Web delivery follows the sRGB interpretation of untagged RGB.')
        self.assertEqual(self.source.read_bytes(), before)
        with Image.open(self.source) as a, Image.open(self.output) as b:
            self.assertEqual(a.tobytes(), b.tobytes())
            self.assertEqual(a.size, b.size)
            self.assertEqual(ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(__import__('io').BytesIO(b.info['icc_profile']))).strip(), 'sRGB built-in')
        self.assertTrue(result['pixels_unchanged'])
        self.assertTrue(result['assumption_used'])
        self.assertFalse(result['source_encoding_verified'])
        self.assertTrue(result['inherited_manifest_removed'])
        self.assertEqual(result['delivery_scope'], 'web_srgb_assumed')
        self.assertEqual(json.loads(self.receipt.read_text(encoding='utf-8'))['output_sha256'], hashlib.sha256(self.output.read_bytes()).hexdigest())
        info = photo.inspect_image(self.output)
        self.assertEqual(info['color']['encoding'], 'sRGB')
        self.assertEqual(info['color']['basis'], 'web_srgb_assumption')

    def test_declared_srgb_needs_no_assumption(self):
        self.add_chunk(b'sRGB', b'\x00')
        result = self.export()
        self.assertFalse(result['assumption_used'])
        self.assertTrue(result['source_encoding_verified'])

    def test_p3_cannot_be_relabelled_as_srgb(self):
        self.add_chunk(b'cICP', bytes((12, 13, 0, 1)))
        with self.assertRaisesRegex(ValueError, 'conversion'):
            self.export(assume_untagged_srgb=True, assumption_reason='Not a permission to relabel P3')
        self.assertFalse(self.output.exists())

    def test_existing_destination_and_source_are_never_overwritten(self):
        self.output.write_bytes(b'keep existing file')
        with self.assertRaises(FileExistsError):
            self.export(assume_untagged_srgb=True, assumption_reason='Web interpretation')
        self.assertEqual(self.output.read_bytes(), b'keep existing file')
        function = getattr(photo, 'export_web', None)
        self.assertTrue(callable(function))
        with self.assertRaises(ValueError):
            function(str(self.source), str(self.source), assume_untagged_srgb=True,
                     assumption_reason='Web interpretation')

    def test_invalid_crc_is_rejected_without_writing_output(self):
        data = bytearray(self.source.read_bytes()); data[29] ^= 1
        self.source.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'CRC'):
            self.export(assume_untagged_srgb=True, assumption_reason='Web interpretation')
        self.assertFalse(self.output.exists())

    def test_receipt_cannot_overwrite_source(self):
        function = getattr(photo, 'export_web', None)
        self.assertTrue(callable(function))
        before = self.source.read_bytes()
        with self.assertRaises(ValueError):
            function(str(self.source), str(self.output), receipt_path=str(self.source),
                     assume_untagged_srgb=True, assumption_reason='Web interpretation')
        self.assertEqual(self.source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
