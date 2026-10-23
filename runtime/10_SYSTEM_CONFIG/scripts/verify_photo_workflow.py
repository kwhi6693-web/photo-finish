"""Local regressions for batched receipts and early file checks; no rendering."""
from pathlib import Path
import hashlib
import inspect
import json
import tempfile
import unittest
from PIL import Image, ImageCms
import photo_workflow as photo
import workflow_session as workflow

ROOT = Path(__file__).resolve().parents[2]


class PhotoWorkflowTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / 'source.png'
        self.output = self.directory / 'output.png'
        self.job = self.directory / 'job.json'
        self.icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        self.save(self.source, (100, 100, 100))
        self.save(self.output, (110, 110, 110))
        photo.prepare(ROOT, self.source, self.job, started_unix_ns=0)
        workflow.set_protections(self.job, [], 'Synthetic fixture has no protected identity')
        photo.candidates(self.job, ROOT, [])
        workflow.select_references(self.job, 'PROFESSIONAL_FALLBACK', [], 'Unclassified fixture')

    def save(self, path, color, size=(6, 8), profile=True):
        Image.new('RGB', size, color).save(path, icc_profile=self.icc if profile else None)

    def digest(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def review(self, **overrides):
        if 'color_scope' in overrides:
            self.assertIn('color_scope', inspect.signature(workflow.add_review).parameters,
                          'Review must distinguish web assumptions from managed color')
        arguments = dict(output_path=str(self.output), input_sha256=self.digest(self.source),
                         visual_passed=True, profile_passed=True, note='Actual test fixture review.')
        arguments.update(overrides)
        return {'action': 'review', 'arguments': arguments}

    def test_prepare_records_native_baseline_without_changing_source(self):
        state = json.loads(self.job.read_text())
        self.assertEqual(state['source_inspection']['dimensions'], [6, 8])
        self.assertEqual(state['source_inspection']['icc']['status'], 'parseable')
        self.assertEqual(state['source_inspection']['sha256'], self.digest(self.source))
        with self.assertRaises(FileExistsError):
            photo.prepare(ROOT, self.source, self.job)

    def test_early_check_flags_clipping_but_does_not_auto_accept_or_reject_art(self):
        self.save(self.output, (255, 110, 110))
        result = photo.check(self.job, self.output)
        self.assertEqual(result['any_channel_255_delta'], 48)
        self.assertIn('clipping_increased_review_before_local_edits', result['flags'])
        self.assertFalse(result['accepted'])
        self.assertTrue(result['visual_review_required'])

    def test_geometry_freedom_and_profile_change_are_not_false_comparisons(self):
        self.save(self.output, (255, 0, 0), size=(3, 4), profile=False)
        result = photo.check(self.job, self.output, geometry_changed=True)
        self.assertFalse(result['clipping_comparable'])
        self.assertIsNone(result['any_channel_255_delta'])
        self.assertNotIn('unrecorded_geometry_change', result['flags'])
        self.assertIn('icc_changed_requires_color_review', result['flags'])

    def test_mask_check_detects_outside_change_without_claiming_semantic_scope(self):
        mask = self.directory / 'mask.png'
        Image.new('L', (6, 8), 0).save(mask)
        result = photo.check(self.job, self.output, input_path=self.source, mask_path=mask)
        self.assertEqual(result['locality']['outside_mask_changed_pixels'], 48)
        self.assertFalse(result['locality']['semantic_scope_verified'])
        Image.new('L', (6, 8), 255).save(mask)
        result = photo.check(self.job, self.output, input_path=self.source, mask_path=mask)
        self.assertEqual(result['locality']['outside_mask_changed_pixels'], 0)

    def test_two_missing_profiles_do_not_establish_comparable_color_space(self):
        source = self.directory / 'unprofiled.png'
        job = self.directory / 'unprofiled_job.json'
        self.save(source, (100, 100, 100), profile=False)
        self.save(self.output, (255, 100, 100), profile=False)
        photo.prepare(ROOT, source, job)
        result = photo.check(job, self.output)
        self.assertIsNone(result['any_channel_255_delta'])
        self.assertFalse(result['clipping_comparable'])
        self.assertIn('icc_missing', result['flags'])

    def test_checks_reject_changed_source_and_unknown_actual_mask_input(self):
        mask = self.directory / 'mask.png'
        Image.new('L', (6, 8), 255).save(mask)
        with self.assertRaisesRegex(ValueError, 'lineage'):
            photo.check(self.job, self.output, input_path=self.output, mask_path=mask)
        self.save(self.source, (101, 100, 100))
        with self.assertRaisesRegex(ValueError, 'source changed'):
            photo.check(self.job, self.output)

    def test_receipt_cannot_overwrite_photographs_or_ledger(self):
        for destination in (self.source, self.output, self.job):
            before = destination.read_bytes()
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                photo.check(self.job, self.output, receipt_path=destination)
            self.assertEqual(destination.read_bytes(), before)

    def test_atomic_batch_closes_valid_receipts_and_returns_compact_result(self):
        result = workflow.transact(self.job, [self.review()], accept_output_path=self.output)
        self.assertEqual(result['status'], 'accepted')
        self.assertNotIn('reviews', result)
        self.assertEqual(json.loads(self.job.read_text())['reviews'][0]['output']['sha256'], self.digest(self.output))
        with self.assertRaisesRegex(ValueError, 'immutable'):
            workflow.transact(self.job, [self.review()])

    def test_batch_failed_acceptance_rolls_back_every_event_byte_for_byte(self):
        before = self.job.read_bytes()
        issue = {'action': 'issue', 'arguments': {'issue_id': 'art', 'targets': ['text'],
                                                 'observation': 'Text needs inspection.'}}
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            workflow.transact(self.job, [issue, self.review()], accept_output_path=self.output)
        self.assertEqual(self.job.read_bytes(), before)

    def test_web_assumption_acceptance_records_its_scope(self):
        result = workflow.transact(self.job, [self.review(color_scope='web_srgb_assumed')],
                                   accept_output_path=self.output)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(json.loads(self.job.read_text()).get('acceptance_scope'), 'web_srgb_assumed')

    def test_visual_only_cannot_claim_profile_pass(self):
        before = self.job.read_bytes()
        with self.assertRaisesRegex(ValueError, 'visual_only'):
            workflow.transact(self.job, [self.review(color_scope='visual_only')])
        self.assertEqual(self.job.read_bytes(), before)

    def test_unknown_color_scope_is_rejected(self):
        before = self.job.read_bytes()
        with self.assertRaisesRegex(ValueError, 'color_scope'):
            workflow.transact(self.job, [self.review(color_scope='arbitrary')])
        self.assertEqual(self.job.read_bytes(), before)

    def test_batch_cannot_override_job_path_or_nest(self):
        before = self.job.read_bytes()
        for event in ({'action': 'review', 'arguments': {'path': 'other'}},
                      {'action': 'transact', 'arguments': {}}):
            with self.assertRaises(ValueError):
                workflow.transact(self.job, [self.review(), event])
            self.assertEqual(self.job.read_bytes(), before)

    def test_batch_does_not_omit_target_or_false_visual_checks(self):
        before = self.job.read_bytes()
        with self.assertRaisesRegex(ValueError, 'visual'):
            workflow.transact(self.job, [self.review(visual_passed=False)], accept_output_path=self.output)
        self.assertEqual(self.job.read_bytes(), before)

    def test_coverage_requires_observed_end_and_clips_later_report_tools(self):
        workflow.record_tool(self.job, 'render', 1_000_000_000, 4_000_000_000)
        workflow.record_tool(self.job, 'overlap', 3_000_000_000, 6_000_000_000)
        workflow.record_tool(self.job, 'later_report', 11_000_000_000, 15_000_000_000)
        self.assertIsNone(workflow.timing_summary(self.job)['coverage'])
        workflow.mark(self.job, 'save_completed', 5_000_000_000)
        result = workflow.timing_summary(self.job)
        self.assertEqual(result['tool_seconds_union'], 9)
        self.assertEqual(result['coverage']['tool_seconds_union_in_scope'], 4)
        self.assertEqual(result['coverage']['outside_recorded_tools_seconds'], 1)
        self.assertEqual(result['coverage']['tool_coverage_fraction'], .8)


if __name__ == '__main__':
    unittest.main()
