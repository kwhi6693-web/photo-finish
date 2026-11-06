"""Source-aligned overlapping-zone order regression; no photography acceptance."""
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, ImageCms, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime' / '10_SYSTEM_CONFIG' / 'scripts'))
from multizone_editor import ToneZone, composite_zones, _sha_pixels


W, H = 256, 256

def rect(box):
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rectangle(box, fill=255)
    return m


class OverlapOrderTests(unittest.TestCase):
    def setUp(self):
        self.source = Image.new('RGB', (W, H), (110, 130, 150))
        self.icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        self.source.info['icc_profile'] = self.icc
        # Every target and boundary is explicit; protected content is identical for both zones.
        self.protected = rect((12, 12, 22, 22))
        allowed = rect((0, 0, W-1, H-1))
        self.a = ToneZone('light-warm', rect((45, 55, 165, 190)), rect((80, 90, 135, 145)),
                          allowed, self.protected, 0.72, 1.0,
                          'Gradually lift and warm the middle area without touching the reference corner',
                          edge_mode='graded', boundary_visually_inspected=True,
                          sigma_px=12, chroma_shift=(-6, 6))
        self.b = ToneZone('dark-cool', rect((105, 70, 210, 210)), rect((125, 110, 175, 165)),
                          allowed, self.protected, 1.35, 1.0,
                          'Gradually lower and cool the adjacent overlapping area with a second mask',
                          edge_mode='graded', boundary_visually_inspected=True,
                          sigma_px=12, chroma_shift=(6, -6))
        self.args = dict(
            observed_source_pixel_sha256=_sha_pixels(self.source),
            source_visually_inspected=True, masks_visually_inspected=True,
            spatial_intent='Two overlapping graded tonal zones create a controlled example for studying deterministic order',
            expected_icc_bytes=self.icc, geometry_id='synthetic-source:0')

    def test_order_is_stable_but_reverse_order_is_not_silently_conflated(self):
        ab, receipt_ab = composite_zones(self.source, [self.a, self.b], **self.args)
        repeated, receipt_repeat = composite_zones(self.source, [self.a, self.b], **self.args)
        ba, receipt_ba = composite_zones(self.source, [self.b, self.a], **self.args)
        self.assertEqual(ab.tobytes(), repeated.tobytes())
        self.assertNotEqual(ab.tobytes(), ba.tobytes(), 'overlapping noncommutative zones must expose their order')
        self.assertEqual(ab.getpixel((17, 17)), self.source.getpixel((17, 17)))
        self.assertEqual(ba.getpixel((17, 17)), self.source.getpixel((17, 17)))
        self.assertIsNotNone(ImageChops.difference(ab,ba).getbbox())
        # Current PR #47 records the actual execution order; this MUST be pinned.
        self.assertEqual(receipt_ab['overlap_order'], [self.a.name, self.b.name])
        self.assertEqual(receipt_ba['overlap_order'], [self.b.name, self.a.name])
        self.assertEqual(receipt_repeat['overlap_order'], receipt_ab['overlap_order'])
        self.assertFalse(receipt_ab.get('photographic_quality_accepted'))


if __name__ == '__main__':
    unittest.main()
