"""Only synthetic spatial light protocol tests; not real photo quality evaluation."""
import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'v2_local_light'))
from spatial_light_field import LightNode, edit_spatially, _tone_curve

H = 'a' * 64


def region(bounds=None):
    out = Image.new('L', (96, 96), 0)
    if bounds is not None:
        ImageDraw.Draw(out).rectangle(bounds, fill=255)
    return out


def fixture():
    original = Image.new('RGB', (96, 96), (90, 90, 90))
    light = LightNode(
        name='actual sunlit stone relief',
        center=(.5, .5), radius=(.34, .34), strength=.68,
        mask=region((26, 26, 70, 70)),
        target_core=region((39, 39, 60, 60)),
        allowed=region((12, 12, 84, 84)),
        protected=region((73, 33, 83, 60)))
    return original, light


def run(source=None, node=None, **overrides):
    original, light = fixture()
    original = original if source is None else source
    light = light if node is None else node
    params = dict(verified_source_sha256=H, observed_source_sha256=H,
                  expected_source_pixel_sha256=hashlib.sha256(original.tobytes()).hexdigest(),
                  masks_visually_reviewed=True)
    params.update(overrides)
    return edit_spatially(original, [light], **params)


class SpatialLightTests(unittest.TestCase):
    def test_midtones_change_while_background_is_bit_exact(self):
        original, node = fixture()
        result, receipt = run(original, node)
        self.assertNotEqual(result.getpixel((48, 48)), original.getpixel((48, 48)))
        self.assertEqual(result.getpixel((5, 5)), original.getpixel((5, 5)))
        self.assertEqual(result.getpixel((78, 48)), original.getpixel((78, 48)))
        self.assertTrue(receipt['protected_pixel_verified'])
        self.assertEqual(receipt['output_status'], 'PENDING_USER_VISUAL_REVIEW')

    def test_negative_depth_tone_is_local(self):
        original, node = fixture()
        result, _ = run(original, replace(node, strength=-.5))
        self.assertLess(result.getpixel((48, 48))[0], original.getpixel((48, 48))[0])
        self.assertEqual(result.getpixel((5, 5)), original.getpixel((5, 5)))

    def test_focal_location_changes_actual_pixel_pattern(self):
        original, node = fixture()
        left, _ = run(original, replace(node, center=(.35, .5)))
        right, _ = run(original, replace(node, center=(.65, .5)))
        self.assertNotEqual(left.getpixel((36, 48)), right.getpixel((36, 48)))

    def test_no_mask_review_stops(self):
        with self.assertRaisesRegex(ValueError, 'visually checked'):
            run(masks_visually_reviewed=False)

    def test_source_identity_and_pixel_fingerprint_both_required(self):
        with self.assertRaisesRegex(ValueError, 'source identity'):
            run(observed_source_sha256='b' * 64)
        with self.assertRaisesRegex(ValueError, 'pixel fingerprint'):
            run(expected_source_pixel_sha256='b' * 64)

    def test_partial_target_mask_rejected(self):
        original, node = fixture()
        with self.assertRaisesRegex(ValueError, 'target-core'):
            run(original, replace(node, mask=region((26, 26, 31, 31))))

    def test_unreviewed_area_rejected(self):
        original, node = fixture()
        with self.assertRaisesRegex(ValueError, 'reviewed allowed'):
            run(original, replace(node, allowed=region((40, 40, 54, 54))))

    def test_protected_intersection_rejected(self):
        original, node = fixture()
        with self.assertRaisesRegex(ValueError, 'overlaps protected'):
            run(original, replace(node, protected=region((48, 48, 55, 55))))

    def test_protected_pixels_stay_identical(self):
        original, node = fixture()
        result, _ = run(original, node)
        self.assertEqual(result.getpixel((74, 48)), original.getpixel((74, 48)))

    def test_no_newly_clipped_channel(self):
        original = Image.new('RGB', (96, 96), (253, 254, 200))
        result, _ = run(source=original)
        self.assertNotIn(255, result.getpixel((48, 48)))
        self.assertEqual(_tone_curve(.8)[255], 255)
        self.assertEqual(_tone_curve(.8)[254], 254)

    def test_original_not_mutated(self):
        original, node = fixture()
        before = original.tobytes()
        run(original, node)
        self.assertEqual(original.tobytes(), before)

    def test_unbounded_intensity_rejected(self):
        original, node = fixture()
        with self.assertRaisesRegex(ValueError, 'bounded nontrivial'):
            run(original, replace(node, strength=1.5))

    def test_invalid_masks_and_focal_coordinates_rejected(self):
        original, node = fixture()
        with self.assertRaisesRegex(ValueError, 'mask geometry'):
            run(original, replace(node, mask=Image.new('L', (30, 30))))
        with self.assertRaisesRegex(ValueError, 'normalized focal'):
            run(original, replace(node, center=(2, 2)))

    def test_two_light_nodes_different_directions(self):
        original, node = fixture()
        result, receipt = edit_spatially(
            original, [node, replace(node, name='recess shadow', center=(.65, .63), strength=-.38)],
            verified_source_sha256=H, observed_source_sha256=H,
            expected_source_pixel_sha256=hashlib.sha256(original.tobytes()).hexdigest(),
            masks_visually_reviewed=True)
        self.assertEqual(len(receipt['nodes']), 2)
        self.assertEqual(result.getpixel((4, 4)), original.getpixel((4, 4)))


if __name__ == '__main__':
    unittest.main()
