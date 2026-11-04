"""Synthetic v2 native PNG handoff/identity regressions. No user photos or Adobe."""
from dataclasses import replace
from pathlib import Path
import os
import sys
import tempfile
import unittest

from PIL import Image, ImageCms, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'v2_local_light'))
from editorial_contract import EditorialPlan, ProvenCapabilities
from editorial_pipeline import hash_file
from multizone_editor import ToneZone, _sha_pixels
from multizone_workflow import run_multizone_trial
from native_candidate_export import export_pending_png


def region(box):
    mask = Image.new('L', (96, 96), 0)
    ImageDraw.Draw(mask).rectangle(box, fill=255)
    return mask


class NativePNGHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source_path = Path(self.temp.name) / 'reviewed_source_srgb.png'
        self.output_path = Path(self.temp.name) / 'edited_candidate.png'
        self.icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        initial = Image.new('RGB', (96, 96), (120, 132, 151))
        initial.save(self.source_path, icc_profile=self.icc)
        with Image.open(self.source_path) as handle:
            handle.load()
            self.source = handle.copy()
            self.source.info.update(handle.info)
        self.hash = hash_file(self.source_path)
        self.plan = EditorialPlan(
            source_sha256=self.hash,
            scene='Historic stone plaza with real daylight and shaded pavement',
            spatial_premise='Pavement is quiet while architecture receives source-derived light',
            attention_entry='Start at the dim foreground and travel toward sunlit architecture',
            principal_subject='Source-matched masonry remains the principal subject of interest',
            secondary_discovery='Shaded pavement and distant facades give context and depth',
            spatial_relationship='Dark near-field directs the eye toward actual brighter structure',
            source_light_evidence='Original pixels contain plausible shade and an existing warm building',
            lighting_direction='Gently separate foreground from sunlit architecture without redraw',
            color_direction='Keep real daylight neutral and every stone and surface unchanged',
            visible_improvement_goal='Make existing source spatial hierarchy more clearly readable',
            fixed_content_to_preserve='All signs, architecture and contextual scene objects stay truthful',
            failure_conditions='Stop on wrong mask, altered stone boundary or unnatural halo',
            requires_local_selection=True)
        self.zones = [
            ToneZone('near pavement', region((18, 18, 42, 76)),
                     region((21, 23, 39, 69)), region((8, 8, 52, 86)),
                     region((84, 32, 92, 60)), 1.23, 1.0,
                     'Quiet near pavement supports existing depth of the original'),
            ToneZone('distant architecture', region((54, 18, 78, 76)),
                     region((57, 23, 74, 69)), region((44, 8, 88, 86)),
                     region((84, 32, 92, 60)), .83, 1.0,
                     'Gently elevate original building while preserving true geometry'),
        ]
        self.trial = run_multizone_trial(
            self.plan, source_path=self.source_path, zones=self.zones,
            source_visually_inspected=True, masks_visually_inspected=True,
            capabilities=ProvenCapabilities(True, True, True, True, verified_local_masks=True),
            geometry_id='same-geometry-synthetic-source',
            expected_source_pixel_sha256=_sha_pixels(self.source),
            expected_icc_bytes=self.icc)

    def test_png_byte_and_icc_round_trip_pending_not_accepted(self):
        original = self.source_path.read_bytes()
        receipt = export_pending_png(self.trial, working_source_path=self.source_path,
                                     destination=self.output_path)
        self.assertEqual(receipt.status, 'PENDING_REAL_PHOTOGRAPHIC_REVIEW_AND_FORMAL_SAVE')
        self.assertFalse(receipt.photographic_quality_accepted)
        self.assertFalse(receipt.formal_V1_registered)
        self.assertEqual(receipt.sha256, hash_file(self.output_path))
        self.assertEqual(receipt.source_sha256, self.hash)
        self.assertEqual(receipt.dimensions, (96, 96))
        self.assertEqual(self.source_path.read_bytes(), original)
        with Image.open(self.output_path) as actual:
            actual.load()
            self.assertEqual(actual.format, 'PNG')
            self.assertEqual(actual.info['icc_profile'], self.icc)
            self.assertEqual(_sha_pixels(actual), self.trial.output_pixel_sha256)

    def test_existing_output_not_overwritten(self):
        self.output_path.write_bytes(b'original destination')
        with self.assertRaises(FileExistsError):
            export_pending_png(self.trial, working_source_path=self.source_path,
                               destination=self.output_path)
        self.assertEqual(self.output_path.read_bytes(), b'original destination')

    def test_source_changed_after_trial_rejected(self):
        self.source_path.write_bytes(self.source_path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError, 'identity'):
            export_pending_png(self.trial, working_source_path=self.source_path,
                               destination=self.output_path)
        self.assertFalse(self.output_path.exists())

    def test_outdated_icc_is_rejected(self):
        changed = self.trial.image.copy()
        changed.info['icc_profile'] = b'unknown-colorspace'
        with self.assertRaisesRegex(ValueError, 'ICC'):
            export_pending_png(replace(self.trial, image=changed),
                               working_source_path=self.source_path,
                               destination=self.output_path)
        self.assertFalse(self.output_path.exists())

    def test_pixels_modified_after_mask_qa_are_rejected(self):
        changed = self.trial.image.copy()
        changed.info.update(self.trial.image.info)
        changed.putpixel((25, 35), (2, 4, 8))
        with self.assertRaisesRegex(ValueError, 'mutated'):
            export_pending_png(replace(self.trial, image=changed),
                               working_source_path=self.source_path,
                               destination=self.output_path)

    def test_forged_visual_acceptance_rejected(self):
        receipt = dict(self.trial.technical_receipt, photographic_quality_accepted=True)
        with self.assertRaisesRegex(ValueError, 'technical'):
            export_pending_png(replace(self.trial, technical_receipt=receipt),
                               working_source_path=self.source_path,
                               destination=self.output_path)

    def test_not_a_png_filename_rejected(self):
        with self.assertRaisesRegex(ValueError, 'PNG'):
            export_pending_png(self.trial, working_source_path=self.source_path,
                               destination=Path(self.temp.name)/'fake.jpg')

    @unittest.skipIf(os.name == 'nt', 'Windows symlink creation needs elevated policy')
    def test_destination_symlink_not_overwritten(self):
        self.output_path.symlink_to(Path(self.temp.name)/'missing-original.png')
        with self.assertRaises(FileExistsError):
            export_pending_png(self.trial, working_source_path=self.source_path,
                               destination=self.output_path)
        self.assertTrue(self.output_path.is_symlink())

    def test_invalid_pending_status_rejected(self):
        with self.assertRaisesRegex(ValueError, 'pending review'):
            export_pending_png(replace(self.trial, status='ACCEPTED'),
                               working_source_path=self.source_path,
                               destination=self.output_path)


if __name__ == '__main__':
    unittest.main()
