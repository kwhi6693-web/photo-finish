"""Synthetic mask/feather QA; no real-photo or aesthetic claims."""
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "v2_local_light"))
from pixel_mask_qa import inspect_mask, feather_mask, compose_only_tonal_output, verify_protected_pixels


def rect(box=None):
    image = Image.new("L", (96, 96), 0)
    if box is not None:
        ImageDraw.Draw(image).rectangle(box, fill=255)
    return image


def fixture():
    core = rect((36, 36, 55, 55))
    subject = rect((28, 28, 63, 63))
    allowed = rect((14, 14, 77, 77))
    protected = rect((72, 31, 80, 55))
    return subject, core, allowed, protected


class PixelMaskQATests(unittest.TestCase):
    def test_correct_subject_has_real_pixel_audit(self):
        s, c, a, p = fixture()
        result = inspect_mask(s, target_core=c, allowed_zone=a, protected=p)
        self.assertTrue(result.passed, result.reason)
        self.assertAlmostEqual(result.target_core_recall, 1.0)
        self.assertEqual(result.protected_overlap, 0)
        self.assertTrue(result.observed_bbox[2] < .5)

    def test_sky_instead_of_stone_fails(self):
        s, c, a, p = fixture()
        sky = Image.new("L", s.size, 255)
        ImageDraw.Draw(sky).rectangle((14, 14, 77, 77), fill=0)
        result = inspect_mask(sky, target_core=c, allowed_zone=a, protected=p)
        self.assertFalse(result.passed)

    def test_partial_street_mask_fails_core_coverage(self):
        s, c, a, p = fixture()
        partial = rect((36, 36, 40, 40))
        r = inspect_mask(partial, target_core=c, allowed_zone=a, protected=p)
        self.assertFalse(r.passed)
        self.assertIn("omitted", r.reason)

    def test_sign_leakage_fails_even_if_fraction_small(self):
        s, c, a, p = fixture()
        ImageDraw.Draw(s).rectangle((75, 42, 76, 44), fill=255)
        r = inspect_mask(s, target_core=c, allowed_zone=a, protected=p)
        self.assertFalse(r.passed)
        self.assertGreater(r.protected_overlap, 0)

    def test_mask_outside_expected_region_fails(self):
        s, c, a, p = fixture()
        ImageDraw.Draw(s).rectangle((1, 70, 12, 85), fill=255)
        self.assertFalse(inspect_mask(s, target_core=c, allowed_zone=a, protected=p).passed)

    def test_empty_and_full_frame_mask_fail(self):
        s, c, a, p = fixture()
        self.assertFalse(inspect_mask(rect(), target_core=c, allowed_zone=a, protected=p).passed)
        self.assertFalse(inspect_mask(Image.new("L", s.size, 255), target_core=c, allowed_zone=a, protected=p).passed)

    def test_mismatched_dimensions_fail_closed(self):
        s, c, a, p = fixture()
        with self.assertRaises(ValueError):
            inspect_mask(s, target_core=c.resize((100, 96)), allowed_zone=a, protected=p)

    def test_feather_has_smooth_alpha_and_is_protected(self):
        s, c, a, p = fixture()
        audit = inspect_mask(s, target_core=c, allowed_zone=a, protected=p)
        out = feather_mask(s, audit=audit, allowed_zone=a, protected=p, radius_px=3)
        self.assertEqual(out.alpha.getpixel((47, 47)), 255)
        self.assertEqual(out.alpha.getpixel((75, 43)), 0)
        edge = out.alpha.getpixel((27, 45))
        self.assertTrue(0 < edge < 255, edge)
        self.assertEqual(out.alpha.getpixel((8, 8)), 0)

    def test_changed_protection_zone_blocks_feather_even_after_passed_audit(self):
        s, c, a, p = fixture()
        audit = inspect_mask(s, target_core=c, allowed_zone=a, protected=p)
        ImageDraw.Draw(p).rectangle((26, 26, 31, 31), fill=255)
        with self.assertRaisesRegex(ValueError, "changed since mask audit"):
            feather_mask(s, audit=audit, allowed_zone=a, protected=p)

    def test_no_crop_of_feather_tail_inside_inspected_region(self):
        s, c, a, p = fixture()
        audit = inspect_mask(s, target_core=c, allowed_zone=a, protected=p)
        with self.assertRaisesRegex(ValueError, "escape allowed region"):
            feather_mask(s, audit=audit, allowed_zone=a, protected=p, radius_px=6)

    def test_raw_mask_mutation_invalidates_receipt(self):
        s, c, a, p = fixture()
        audit = inspect_mask(s, target_core=c, allowed_zone=a, protected=p)
        s.putpixel((2, 2), 255)
        with self.assertRaisesRegex(ValueError, "changed since audit"):
            feather_mask(s, audit=audit, allowed_zone=a, protected=p)

    def test_composite_preserves_protected_pixels_and_geometry(self):
        s, c, a, p = fixture()
        audit = inspect_mask(s, target_core=c, allowed_zone=a, protected=p)
        fr = feather_mask(s, audit=audit, allowed_zone=a, protected=p)
        before = Image.new("RGB", (96, 96), (30, 60, 100))
        after_candidate = Image.new("RGB", (96, 96), (110, 90, 130))
        result = compose_only_tonal_output(before, after_candidate, receipt=fr)
        self.assertTrue(verify_protected_pixels(before, result, protected=p))
        self.assertEqual(result.size, before.size)
        self.assertNotEqual(result.getpixel((47, 47)), before.getpixel((47, 47)))
        self.assertEqual(result.getpixel((8, 8)), before.getpixel((8, 8)))

    def test_composite_rejects_stale_alpha_and_geometry(self):
        s, c, a, p = fixture()
        fr = feather_mask(s, audit=inspect_mask(s, target_core=c, allowed_zone=a, protected=p),
                          allowed_zone=a, protected=p)
        original = Image.new("RGB", (96, 96), "black")
        candidate = Image.new("RGB", (96, 95), "white")
        with self.assertRaisesRegex(ValueError, "different dimensions"):
            compose_only_tonal_output(original, candidate, receipt=fr)
        fr.alpha.putpixel((47, 47), 1)
        with self.assertRaisesRegex(ValueError, "changed after feather"):
            compose_only_tonal_output(original, Image.new("RGB", (96, 96), "white"), receipt=fr)

    def test_protected_pixel_verifier_catches_one_level_color_change(self):
        source = Image.new("RGB", (96, 96), "black")
        result = source.copy()
        p = rect((70, 30, 80, 50))
        result.putpixel((75, 40), (0, 0, 1))
        self.assertFalse(verify_protected_pixels(source, result, protected=p))


if __name__ == "__main__":
    unittest.main()
