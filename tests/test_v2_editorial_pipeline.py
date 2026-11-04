"""Synthetic end-to-end contract; not a photographic aesthetic test."""
from dataclasses import replace
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'v2_local_light'))
from editorial_contract import EditorialPlan, ProvenCapabilities
from editorial_pipeline import run_masked_tonal_trial, hash_file


def rect(coords=None):
    mask = Image.new('L', (96, 96), 0)
    if coords:
        ImageDraw.Draw(mask).rectangle(coords, fill=255)
    return mask


def real_plan(source_hash):
    return EditorialPlan(source_sha256=source_hash, scene='Synthetic city street study',
        spatial_premise='Foreground observer with lighted destination down the avenue',
        attention_entry='Start at the paved road and a nearby human-scale edge',
        principal_subject='Existing lit facade that forms a distant visual landmark',
        secondary_discovery='Ambient side structures give the real place visual context',
        spatial_relationship='Near street flows into far architectural light and dark sky',
        source_light_evidence='The original source contains actual lamps and nearby shadows',
        lighting_direction='Shape only the true subject under the certified mask',
        color_direction='Existing warm light stays plausible and dark areas remain deep',
        visible_improvement_goal='More legible scene hierarchy while retaining realistic detail',
        fixed_content_to_preserve='Unchanged fixed architecture and every protected label',
        failure_conditions='Reject missing masks, changed text, edge halos or poor emphasis',
        requires_local_selection=True)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'source.png'
        profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        img = Image.new('RGB', (96, 96), (30, 60, 100))
        img.save(self.path, icc_profile=profile)
        self.source = Image.open(self.path)
        self.source.load()
        self.candidate = Image.new('RGB', (96, 96), (55, 75, 120))
        self.candidate.info['icc_profile'] = profile
        self.kw = dict(source_path=self.path, candidate=self.candidate,
                       mask=rect((28, 28, 63, 63)), target_core=rect((36, 36, 55, 55)),
                       allowed_zone=rect((14, 14, 77, 77)), protected=rect((72, 31, 80, 55)),
                       geometry_id='G0:actual-source', candidate_geometry_id='G0:actual-source',
                       source_visually_inspected=True, masked_region_reviewed=True,
                       capabilities=ProvenCapabilities(True, True, True, True, verified_local_masks=True))
        self.plan = real_plan(hash_file(self.path))

    def test_real_source_bytes_are_unchanged_and_output_not_accepted(self):
        before = self.path.read_bytes()
        result = run_masked_tonal_trial(self.plan, **self.kw)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(result.status, 'PENDING_SPATIAL_NATURALNESS_EXPRESSIVE_VISUAL_REVIEW')
        self.assertEqual(result.technical_receipt.status, 'technical_candidate_only_not_visual_acceptance')
        self.assertIn('hierarchy', result.controller_direction)
        self.assertNotEqual(result.image.getpixel((45, 45)), self.source.getpixel((45, 45)))
        self.assertEqual(result.image.getpixel((75, 43)), self.source.getpixel((75, 43)))

    def test_wrong_source_does_not_render(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            run_masked_tonal_trial(replace(self.plan, source_sha256='a' * 64), **self.kw)

    def test_unreviewed_mask_does_not_render(self):
        with self.assertRaisesRegex(ValueError, 'reviewed'):
            run_masked_tonal_trial(self.plan, **dict(self.kw, masked_region_reviewed=False))

    def test_wrong_geometry_does_not_render(self):
        with self.assertRaisesRegex(ValueError, 'geometry identities'):
            run_masked_tonal_trial(self.plan, **dict(self.kw, candidate_geometry_id='G1'))

    def test_wrong_color_profile_does_not_render(self):
        broken = self.candidate.copy()
        broken.info['icc_profile'] = b'wrong'
        with self.assertRaisesRegex(ValueError, 'ICC profiles differ'):
            run_masked_tonal_trial(self.plan, **dict(self.kw, candidate=broken))

    def test_unverified_local_mask_capability_does_not_render(self):
        cap = replace(self.kw['capabilities'], verified_local_masks=False)
        with self.assertRaisesRegex(ValueError, 'mask not actually verified'):
            run_masked_tonal_trial(self.plan, **dict(self.kw, capabilities=cap))

    def test_wrong_selected_region_does_not_render(self):
        with self.assertRaisesRegex(ValueError, 'mask QA failed'):
            run_masked_tonal_trial(self.plan, **dict(self.kw, mask=rect((79, 8, 94, 25))))

    def test_geometry_changing_plan_is_separate_branch(self):
        p = replace(self.plan, requests_geometry_change=True)
        with self.assertRaisesRegex(ValueError, 'separately verified edit step'):
            run_masked_tonal_trial(p, **dict(self.kw,
                capabilities=replace(self.kw['capabilities'], supports_crop=True)))

    def test_misrepresented_editor_provenance_fails(self):
        with self.assertRaisesRegex(ValueError, 'not approved as tonal-only'):
            run_masked_tonal_trial(self.plan, **dict(self.kw, approved_operation='generate'))


if __name__ == '__main__':
    unittest.main()
