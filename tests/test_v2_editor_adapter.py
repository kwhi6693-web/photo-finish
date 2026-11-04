"""Synthetic-only adapter tests; never a real-photograph acceptance verdict."""
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageCms

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'v2_local_light'))
from editor_adapter import integrate_verified_tonal_edit, _digest_pixels


def area(box=None):
    image = Image.new('L', (96, 96), 0)
    if box:
        ImageDraw.Draw(image).rectangle(box, fill=255)
    return image


def params():
    src = Image.new('RGB', (96, 96), (30, 60, 100))
    dst = Image.new('RGB', (96, 96), (60, 70, 115))
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    src.info['icc_profile'] = profile
    dst.info['icc_profile'] = profile
    return dict(source=src, candidate=dst, mask=area((28, 28, 63, 63)),
        target_core=area((36, 36, 55, 55)),
        allowed_zone=area((14, 14, 77, 77)),
        protected=area((72, 31, 80, 55)),
        source_geometry_id='photo-1:G0', candidate_geometry_id='photo-1:G0',
        approved_operation='non_generative_tonal_only', masked_region_reviewed=True,
        source_pixels_hash=_digest_pixels(src), radius_px=3)


class AdapterTests(unittest.TestCase):
    def test_good_candidate_is_technical_only(self):
        p = params()
        img, receipt = integrate_verified_tonal_edit(**p)
        self.assertEqual(receipt.status, 'technical_candidate_only_not_visual_acceptance')
        self.assertTrue(receipt.protected_unchanged)
        self.assertNotEqual(img.getpixel((47, 47)), p['source'].getpixel((47, 47)))
        self.assertEqual(img.getpixel((75, 43)), p['source'].getpixel((75, 43)))
        self.assertEqual(img.info['icc_profile'], p['source'].info['icc_profile'])

    def test_wrong_geometry_fails(self):
        p = params(); p['candidate_geometry_id'] = 'photo-1:G1'
        with self.assertRaisesRegex(ValueError, 'geometry identities'):
            integrate_verified_tonal_edit(**p)

    def test_wrong_source_hash_fails(self):
        p = params(); p['source_pixels_hash'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'identified source'):
            integrate_verified_tonal_edit(**p)

    def test_different_icc_fails(self):
        p = params(); p['candidate'].info['icc_profile'] = b'wrong'
        with self.assertRaisesRegex(ValueError, 'ICC profiles differ'):
            integrate_verified_tonal_edit(**p)

    def test_missing_icc_fails_real_route(self):
        p = params(); p['candidate'].info.pop('icc_profile')
        with self.assertRaisesRegex(ValueError, 'actual ICC'):
            integrate_verified_tonal_edit(**p)

    def test_mis_selected_sky_fails(self):
        p = params(); p['mask'] = area((78, 1, 95, 18))
        with self.assertRaisesRegex(ValueError, 'mask QA failed'):
            integrate_verified_tonal_edit(**p)

    def test_mutated_protected_pixels_in_input_are_not_directly_trusted(self):
        p = params(); p['candidate'].putpixel((75, 43), (80, 90, 110))
        img, receipt = integrate_verified_tonal_edit(**p)
        self.assertEqual(img.getpixel((75, 43)), p['source'].getpixel((75, 43)))
        self.assertTrue(receipt.protected_unchanged)

    def test_larger_tonal_delta_fails(self):
        p = params()
        p['candidate'] = Image.new('RGB', (96, 96), 'white')
        p['candidate'].info['icc_profile'] = p['source'].info['icc_profile']
        with self.assertRaisesRegex(ValueError, 'exceeds controlled'):
            integrate_verified_tonal_edit(**p)

    def test_no_external_editor_provenance_fails(self):
        p = params(); p['approved_operation'] = 'generate_and_replace'
        with self.assertRaisesRegex(ValueError, 'tonal-only'):
            integrate_verified_tonal_edit(**p)

    def test_excess_new_highlight_clipping_is_rejected(self):
        p = params()
        p['source'] = Image.new('RGB', (96, 96), (235, 240, 242))
        p['source'].info['icc_profile'] = p['candidate'].info['icc_profile']
        p['candidate'] = Image.new('RGB', (96, 96), (255, 255, 255))
        p['candidate'].info['icc_profile'] = p['source'].info['icc_profile']
        p['source_pixels_hash'] = _digest_pixels(p['source'])
        with self.assertRaisesRegex(ValueError, 'clipped highlights'):
            integrate_verified_tonal_edit(**p)

    def test_highlight_tolerance_requires_bounded_number(self):
        p = params()
        with self.assertRaisesRegex(ValueError, 'highlight clipping tolerance'):
            integrate_verified_tonal_edit(**p, max_newly_clipped_fraction='yes')

    def test_unreviewed_mask_fails(self):
        p = params(); p['masked_region_reviewed'] = False
        with self.assertRaisesRegex(ValueError, 'visually reviewed'):
            integrate_verified_tonal_edit(**p)


if __name__ == '__main__':
    unittest.main()
