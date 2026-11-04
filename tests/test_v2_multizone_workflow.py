"""V2 workflow integration contract tests; synthetic images, no Adobe/photos."""
from dataclasses import replace
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageCms

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'v2_local_light'))
from editorial_contract import EditorialPlan, ProvenCapabilities
from editorial_pipeline import hash_file
from multizone_editor import ToneZone, _sha_pixels
from multizone_workflow import run_multizone_trial


def region(box):
    image = Image.new('L', (96, 96))
    ImageDraw.Draw(image).rectangle(box, fill=255)
    return image


def plan(source_hash):
    return EditorialPlan(
        source_sha256=source_hash, scene='Stone building beside an evening road',
        spatial_premise='Shaded near street leads into a naturally illuminated historical facade',
        attention_entry='Look through the quiet shaded street foreground and central path',
        principal_subject='A sunlit historic facade is the main point of photographic interest',
        secondary_discovery='Ambient trees, pavement and old architecture show local life',
        spatial_relationship='Viewer travels from dark nearby pavement toward distant lit buildings',
        source_light_evidence='Original pixels show muted pavement and naturally bright facade',
        lighting_direction='Preserve the real illuminated structure and deepen the quieter foreground',
        color_direction='Keep realistic warmth, soft neutral shadows and actual surface texture',
        visible_improvement_goal='Increase visual hierarchy and depth without reconstructing any structures',
        fixed_content_to_preserve='Keep every historic building, sign, individual and tree recognizable',
        failure_conditions='Reject wrong masks, changed signs, false halos or absent spatial expression',
        requires_local_selection=True)


class WorkflowIntegrationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / 'working_srgb.png'
        self.icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        original = Image.new('RGB', (96, 96), (105, 130, 160))
        original.save(self.path, icc_profile=self.icc)
        with Image.open(self.path) as decoded:
            decoded.load()
            self.source = decoded.copy()
            self.source.info.update(decoded.info)
        self.zones = [
            ToneZone('shaded near space', region((18, 18, 42, 76)),
                     region((21, 23, 39, 69)), region((8, 8, 52, 86)),
                     region((84, 32, 92, 60)), 1.25, 1.0,
                     'Reduce near-field competition while preserving true scene'),
            ToneZone('lit architecture', region((54, 18, 78, 76)),
                     region((57, 23, 74, 69)), region((44, 8, 88, 86)),
                     region((84, 32, 92, 60)), .82, 1.0,
                     'Place original lit facade above the quieter visual field'),
        ]
        self.plan = plan(hash_file(self.path))
        self.args = dict(
            source_path=self.path, zones=self.zones, source_visually_inspected=True,
            masks_visually_inspected=True,
            capabilities=ProvenCapabilities(True, True, True, True,
                                             verified_local_masks=True,
                                             edge_transition_verified=False),
            geometry_id='source-frame:0',
            expected_source_pixel_sha256=_sha_pixels(self.source),
            expected_icc_bytes=self.icc)

    def test_end_to_end_outputs_only_pending_visual_review(self):
        original_bytes = self.path.read_bytes()
        result = run_multizone_trial(self.plan, **self.args)
        self.assertEqual(result.status, 'PENDING_REAL_PHOTO_THREE_AXIS_REVIEW')
        self.assertEqual(result.technical_receipt['photographic_quality_accepted'], False)
        self.assertEqual(result.source_file_sha256, self.plan.source_sha256)
        self.assertIn('空间关系', result.spatial_direction['hierarchy'])
        self.assertEqual(self.path.read_bytes(), original_bytes)
        self.assertEqual(result.image.getpixel((5, 5)), self.source.getpixel((5, 5)))
        self.assertNotEqual(result.image.getpixel((30, 40)), self.source.getpixel((30, 40)))

    def test_wrong_byte_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            run_multizone_trial(replace(self.plan, source_sha256='0'*64), **self.args)

    def test_wrong_decoded_pixel_lineage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'working pixels'):
            run_multizone_trial(self.plan, **dict(self.args, expected_source_pixel_sha256='0'*64))

    def test_missing_visual_mask_review_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'inspected'):
            run_multizone_trial(self.plan, **dict(self.args, masks_visually_inspected=False))

    def test_missing_real_editor_capabilities_is_rejected(self):
        caps = replace(self.args['capabilities'], non_generative_tonal_editor=False)
        with self.assertRaisesRegex(ValueError, 'preflight'):
            run_multizone_trial(self.plan, **dict(self.args, capabilities=caps))

    def test_high_intensity_requires_edge_transition_evidence(self):
        strong = replace(self.plan, intensity='strong')
        with self.assertRaisesRegex(ValueError, 'preflight'):
            run_multizone_trial(strong, **self.args)

    def test_crop_requires_another_route(self):
        requested = replace(self.plan, requests_geometry_change=True)
        caps = replace(self.args['capabilities'], supports_crop=True)
        with self.assertRaisesRegex(ValueError, 'separate geometry'):
            run_multizone_trial(requested, **dict(self.args, capabilities=caps))

    def test_wrong_color_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ICC'):
            run_multizone_trial(self.plan, **dict(self.args, expected_icc_bytes=b'wrong'))

    def test_unreviewed_architectural_boundary_is_rejected(self):
        zones = [replace(self.zones[0], edge_mode='pixel_locked',
                         boundary_visually_inspected=False), self.zones[1]]
        with self.assertRaisesRegex(ValueError, 'architectural edge'):
            run_multizone_trial(self.plan, **dict(self.args, zones=zones))

    def test_context_protected_by_other_zone_rejects_overlapping_mask(self):
        zone = replace(self.zones[0], protected=region((60, 40, 65, 45)))
        with self.assertRaisesRegex(ValueError, 'mask'):
            run_multizone_trial(self.plan, **dict(self.args, zones=[zone, self.zones[1]]))


if __name__ == '__main__':
    unittest.main()
