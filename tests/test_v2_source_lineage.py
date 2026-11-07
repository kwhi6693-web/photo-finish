"""Synthetic source-to-managed-working-PNG lineage tests, without real user photos."""
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image, ImageCms

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'v2_local_light'))
from editorial_pipeline import hash_file
from source_lineage import prepare_working_source, verify_source_lineage, _canonical_srgb_bytes


class ColorManagedLineageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'original.jpg'
        self.output = self.root / 'managed.png'
        profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        self.icc = profile
        original = Image.new('RGB', (88, 96), (119, 140, 165))
        original.save(self.source, format='JPEG', quality=96, icc_profile=profile)

    def test_icc_creation_time_is_stable_without_changing_color_tags(self):
        generated = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        earlier, later = bytearray(generated), bytearray(generated)
        earlier[24:36] = bytes.fromhex('07e500010001000000000000')
        later[24:36] = bytes.fromhex('07ea000b000400130011000f')
        normalized_a = _canonical_srgb_bytes(bytes(earlier))
        normalized_b = _canonical_srgb_bytes(bytes(later))
        self.assertEqual(normalized_a, normalized_b)
        self.assertEqual(normalized_a[:24], generated[:24])
        self.assertEqual(normalized_a[36:], generated[36:])
        # Profile stays parseable: color primaries, TRCs and gamut untouched.
        self.assertEqual(ImageCms.getProfileDescription(
            ImageCms.ImageCmsProfile(BytesIO(normalized_a))).strip(),
            ImageCms.getProfileDescription(
                ImageCms.ImageCmsProfile(BytesIO(generated))).strip())

    def test_icc_stability_repeated_prepare_and_verify(self):
        proof = prepare_working_source(self.source, self.output)
        for _ in range(3):
            self.assertTrue(verify_source_lineage(self.source, proof))
        self.assertEqual(hash_file(self.output), proof.working_sha256)

    def test_srgb_source_roundtrip_is_independently_verifiable(self):
        original_sha = hash_file(self.source)
        proof = prepare_working_source(self.source, self.output)
        self.assertEqual(proof.original_sha256, original_sha)
        self.assertEqual(proof.working_sha256, hash_file(self.output))
        self.assertEqual(proof.original_size, (88, 96))
        self.assertEqual(proof.working_size, (88, 96))
        self.assertEqual(proof.status, 'VERIFIED_WORKING_SOURCE_NOT_PHOTOGRAPHIC_ACCEPTANCE')
        self.assertTrue(verify_source_lineage(self.source, proof))
        self.assertEqual(hash_file(self.source), original_sha)
        with Image.open(self.output) as image:
            image.load()
            self.assertEqual(image.format, 'PNG')
            self.assertEqual(image.mode, 'RGB')
            self.assertTrue(image.info.get('icc_profile'))

    def test_existing_destination_never_overwritten(self):
        self.output.write_bytes(b'old independent file')
        with self.assertRaises(FileExistsError):
            prepare_working_source(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), b'old independent file')

    def test_missing_color_profile_is_not_guessed(self):
        bare = self.root / 'untagged-source.jpg'
        Image.new('RGB', (88, 96), (120, 140, 161)).save(bare)
        with self.assertRaisesRegex(ValueError, 'ICC'):
            prepare_working_source(bare, self.output)
        self.assertFalse(self.output.exists())

    def test_source_mutation_invalidates_proof(self):
        proof = prepare_working_source(self.source, self.output)
        self.source.write_bytes(self.source.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'original bytes changed'):
            verify_source_lineage(self.source, proof)

    def test_working_mutation_invalidates_proof(self):
        proof = prepare_working_source(self.source, self.output)
        self.output.write_bytes(self.output.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'working PNG bytes changed'):
            verify_source_lineage(self.source, proof)

    def test_wrong_destination_extension_rejected(self):
        with self.assertRaisesRegex(ValueError, 'PNG'):
            prepare_working_source(self.source, self.root / 'fake.jpeg')

    def test_source_and_destination_must_differ(self):
        with self.assertRaisesRegex(ValueError, 'PNG'):
            prepare_working_source(self.source, self.source)


if __name__ == '__main__':
    unittest.main()
