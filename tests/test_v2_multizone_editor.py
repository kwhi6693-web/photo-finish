"""Synthetic tests for experimental multi-zone compositing, not visual quality."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from PIL import Image, ImageDraw, ImageCms

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'v2_local_light'))
from multizone_editor import ToneZone, composite_zones, _sha_pixels


def rect(box=None, size=(96, 96)):
    im = Image.new('L', size, 0)
    if box:
        ImageDraw.Draw(im).rectangle(box, fill=255)
    return im


class MultiZoneTests(unittest.TestCase):
    def setUp(self):
        self.source = Image.new('RGB', (96, 96), (105, 130, 160))
        self.icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        self.source.info['icc_profile'] = self.icc
        self.zoneA = ToneZone('foreground shadow', rect((18, 18, 42, 76)),
            rect((21, 23, 39, 69)), rect((8, 8, 52, 86)),
            rect((84, 32, 92, 60)), 1.25, 1.0,
            'Move foreground visually behind the photo subject')
        self.zoneB = ToneZone('main subject', rect((54, 18, 78, 76)),
            rect((57, 23, 74, 69)), rect((44, 8, 88, 86)),
            rect((84, 32, 92, 60)), .82, 1.0,
            'Give the existing lit architecture a legible focus')
        self.args = dict(observed_source_pixel_sha256=_sha_pixels(self.source),
            source_visually_inspected=True, masks_visually_inspected=True,
            spatial_intent='Viewer enters through shaded foreground to a lit real subject with depth',
            expected_icc_bytes=self.icc, geometry_id='source:G0')

    def trial(self, zones=None, **overrides):
        kwargs = dict(self.args)
        kwargs.update(overrides)
        return composite_zones(self.source,
            [self.zoneA, self.zoneB] if zones is None else zones, **kwargs)

    def test_different_tones_create_real_narrative_priority_without_changing_source(self):
        before = self.source.tobytes()
        out, receipt = self.trial()
        self.assertEqual(self.source.tobytes(), before)
        self.assertLess(out.getpixel((30, 40))[0], self.source.getpixel((30, 40))[0])
        self.assertGreater(out.getpixel((68, 40))[0], self.source.getpixel((68, 40))[0])
        self.assertEqual(out.getpixel((5, 5)), self.source.getpixel((5, 5)))
        self.assertEqual(receipt['status'], 'PENDING_REAL_IMAGE_EDITORIAL_REVIEW')
        self.assertFalse(receipt['photographic_quality_accepted'])

    def test_protection_in_one_region_blocks_a_different_region(self):
        zone = replace(self.zoneA, protected=rect((62, 44, 66, 50)))
        with self.assertRaisesRegex(ValueError, 'protected'):
            self.trial([zone, self.zoneB])

    def test_source_digest_is_mandatory(self):
        with self.assertRaisesRegex(ValueError, 'digest'):
            self.trial(observed_source_pixel_sha256='0' * 64)

    def test_real_source_review_is_required(self):
        with self.assertRaisesRegex(ValueError, 'inspection'):
            self.trial(source_visually_inspected=False)

    def test_spatial_goal_is_not_only_a_filter_name(self):
        with self.assertRaisesRegex(ValueError, 'spatial'):
            self.trial(spatial_intent='nice')

    def test_wrong_target_core_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'mask'):
            self.trial([replace(self.zoneA, core=rect((82, 82, 83, 83))), self.zoneB])

    def test_whole_frame_selection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'mask'):
            self.trial([replace(self.zoneA, mask=Image.new('L', (96, 96), 255)), self.zoneB])

    def test_color_space_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ICC'):
            self.trial(expected_icc_bytes=b'wrong')

    def test_new_white_clipping_is_blocked(self):
        self.source = Image.new('RGB', (96, 96), (254, 254, 254))
        self.source.info['icc_profile'] = self.icc
        output, _ = self.trial(observed_source_pixel_sha256=_sha_pixels(self.source))
        self.assertNotIn(255, output.getpixel((68, 40)))

    def test_unselected_area_stays_exactly_identical(self):
        output, _ = self.trial()
        self.assertEqual(output.getpixel((95, 95)), self.source.getpixel((95, 95)))

    def test_pixel_locked_architecture_boundary_never_changes_outside_mask(self):
        locked = replace(self.zoneA, edge_mode='pixel_locked',
                         boundary_visually_inspected=True)
        output, _ = self.trial([locked, self.zoneB])
        self.assertEqual(output.getpixel((15, 40)), self.source.getpixel((15, 40)))
        self.assertLess(output.getpixel((20, 40))[0], self.source.getpixel((20, 40))[0])

    def test_unreviewed_hard_edge_is_rejected(self):
        locked = replace(self.zoneA, edge_mode='pixel_locked',
                         boundary_visually_inspected=False)
        with self.assertRaisesRegex(ValueError, 'mask-boundary inspection'):
            self.trial([locked, self.zoneB])

    def test_unbounded_gamma_fails(self):
        with self.assertRaisesRegex(ValueError, 'grade strength'):
            self.trial([replace(self.zoneA, gamma=9.0), self.zoneB])

    def test_truthy_string_does_not_impersonate_inspection(self):
        with self.assertRaisesRegex(ValueError, 'inspection'):
            self.trial(masks_visually_inspected='yes')


if __name__ == '__main__':
    unittest.main()
