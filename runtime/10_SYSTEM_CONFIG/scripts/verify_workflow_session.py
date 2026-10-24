"""Regression checks for the lightweight workflow controller; no cloud calls."""
from pathlib import Path
import io
from PIL import Image, ImageCms
import photo_workflow
import hashlib
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import session_brief


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / '10_SYSTEM_CONFIG/scripts/workflow_session.py'
def image_bytes(fmt, color=(80,120,160)):
    stream=io.BytesIO()
    profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    Image.new('RGB',(12,16),color).save(stream,format=fmt,icc_profile=profile)
    return stream.getvalue()
PNG = image_bytes('PNG')
JPEG = image_bytes('JPEG')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('workflow_session'),
                             'workflow_session controller is missing')
        self.w = importlib.import_module('workflow_session')
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.source = self.dir / 'source.jpeg'
        self.source.write_bytes(JPEG)
        self.output = self.dir / 'final.png'
        self.output.write_bytes(PNG)
        self.job = self.dir / 'job.json'
        self.w.create_job(self.job, self.source, self.w.bootstrap(ROOT)['workflow_revision'], started_unix_ns=0)
        self.w.set_protections(self.job, [], 'No protected content in synthetic fixture')
        photo_workflow.candidates(self.job, ROOT, [])
        self.w.select_references(self.job, 'PROFESSIONAL_FALLBACK', [], 'Unclassified synthetic fixture; independent judgment')

    def fixture(self, fast_revision=None):
        root = self.dir / 'project'
        for relative in session_brief.SOURCES+session_brief.DOCUMENT_SOURCES:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        policy_path = root / '10_SYSTEM_CONFIG/runtime_policy.json'
        policy = json.loads(policy_path.read_text(encoding='utf-8'))
        policy.pop('fast_edit_workflow', None)
        if fast_revision:
            policy['fast_edit_workflow'] = {'revision': fast_revision}
            policy['beautification_defaults']['fast_edit_workflow'] = policy['fast_edit_workflow']
        policy_path.write_text(json.dumps(policy), encoding='utf-8', newline='\n')
        brief = root / '10_SYSTEM_CONFIG/SESSION_BRIEF.json'
        session_brief.build(root, brief)
        return root, policy_path, brief, policy

    def issue(self):
        self.w.add_issue(self.job, 'structure', ['clock', 'pier'],
                         'Clock and its connected pier need a local correction.')

    def corrected(self, target, scope=None):
        self.w.review_mask(self.job, 'structure', target, sha(self.source),
                           scope or [target], True, 'Inspected the actual scope.')
        self.w.resolve_issue(self.job, 'structure', target, 'corrected',
                             'Visible defect corrected.', output_sha256=sha(self.output))

    def review(self, output=None, **overrides):
        arguments = dict(input_sha256=sha(self.source), visual_passed=True,
                         profile_passed=True, note='Inspected detail and embedded ICC.')
        arguments.update(overrides)
        return self.w.add_review(self.job, output or self.output, **arguments)

    def test_bootstrap_prefers_canonical_fast_revision_and_flags_stale_provider(self):
        root, policy_path, brief, policy = self.fixture('fast.2')
        before = {p: p.read_bytes() for p in (policy_path, brief)}
        result = self.w.bootstrap(root, expected_workflow_revision='fast.2',
                                  observed_skill_revision='old.1')
        self.assertEqual(result['workflow_revision'], 'fast.2')
        self.assertTrue(result['stale_observed_skill'])
        self.assertEqual(result['source_hashes'], session_brief.hashes(root))
        self.assertIn('rule_pointers', result)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertFalse(self.w.bootstrap(root, observed_skill_revision='fast.2')['stale_observed_skill'])

    def test_bootstrap_falls_back_to_development_revision(self):
        root, _, _, policy = self.fixture()
        self.assertEqual(self.w.bootstrap(root)['workflow_revision'],
                         policy['development_workflow']['revision'])
        with self.assertRaisesRegex(ValueError, 'revision'):
            self.w.bootstrap(root, expected_workflow_revision='unexpected')

    def test_bootstrap_falls_back_when_fast_workflow_has_no_revision(self):
        root, policy_path, brief, policy = self.fixture()
        policy['fast_edit_workflow'] = {'note': 'No revision is defined here.'}
        policy['beautification_defaults']['fast_edit_workflow'] = policy['fast_edit_workflow']
        policy_path.write_text(json.dumps(policy), encoding='utf-8', newline='\n')
        session_brief.build(root, brief)
        try:
            actual = self.w.bootstrap(root)['workflow_revision']
        except ValueError as error:
            self.fail('Missing fast revision must fall back to the development revision: ' + str(error))
        self.assertEqual(actual, policy['development_workflow']['revision'])

    def test_bootstrap_refuses_stale_source_hash_without_rebuilding(self):
        root, policy, brief, _ = self.fixture()
        before = brief.read_bytes()
        policy.write_text(policy.read_text(encoding='utf-8') + '\n', encoding='utf-8', newline='\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.w.bootstrap(root, observed_skill_revision='old')
        self.assertEqual(brief.read_bytes(), before)

    def test_bootstrap_refuses_tampered_embedded_policy_even_with_valid_hashes(self):
        root, _, brief, _ = self.fixture()
        data = json.loads(brief.read_text(encoding='utf-8'))
        data['runtime_policy']['development_workflow']['revision'] = 'tampered'
        brief.write_text(json.dumps(data), encoding='utf-8', newline='\n')
        with self.assertRaisesRegex(ValueError, 'inconsistent'):
            self.w.bootstrap(root)

    def test_clock_only_correction_cannot_accept_an_unresolved_connected_pier(self):
        self.issue()
        self.corrected('clock')
        self.review()
        with self.assertRaisesRegex(ValueError, 'pier'):
            self.w.accept_job(self.job, self.output)
        self.corrected('pier')
        self.assertEqual(self.w.accept_job(self.job, self.output)['status'], 'accepted')

    def test_blocked_target_is_a_limited_result_and_never_full_acceptance(self):
        self.issue()
        self.corrected('clock')
        self.w.resolve_issue(self.job, 'structure', 'pier', 'blocked',
                             'Current tool cannot select the connected pier.')
        self.review()
        with self.assertRaisesRegex(ValueError, 'blocked'):
            self.w.accept_job(self.job, self.output)
        self.assertNotEqual(json.loads(self.job.read_text(encoding='utf-8'))['status'], 'accepted')

    def test_not_needed_target_needs_a_reason_but_no_mask(self):
        self.issue()
        self.corrected('clock')
        self.w.resolve_issue(self.job, 'structure', 'pier', 'not_needed',
                             'At native resolution the pier has no visible defect.', output_sha256=sha(self.output))
        self.review()
        self.assertEqual(self.w.accept_job(self.job, self.output)['output']['sha256'], sha(self.output))

    def test_mask_cannot_claim_scope_for_a_target_it_did_not_select(self):
        self.issue()
        self.corrected('clock')
        self.corrected('pier', scope=['clock'])
        self.review()
        with self.assertRaisesRegex(ValueError, 'scope'):
            self.w.accept_job(self.job, self.output)

    def test_masks_reject_wrong_source_and_acceptance_rechecks_source(self):
        self.issue()
        with self.assertRaisesRegex(ValueError, 'input|source'):
            self.w.review_mask(self.job, 'structure', 'clock', '0' * 64,
                               ['clock'], True, 'Wrong source receipt.')
        self.corrected('clock')
        self.w.resolve_issue(self.job, 'structure', 'pier', 'not_needed', 'No visible defect.', output_sha256=sha(self.output))
        self.review()
        self.source.write_bytes(JPEG + b'replaced')
        with self.assertRaisesRegex(ValueError, 'source|Source'):
            self.w.accept_job(self.job, self.output)

    def test_masks_record_actual_intermediate_render_input_with_source_lineage(self):
        self.issue()
        preview = self.dir / 'preview.png'
        preview.write_bytes(image_bytes('PNG', (90,120,160)))
        self.review(preview, visual_passed=False)
        try:
            result = self.w.review_mask(self.job, 'structure', 'clock', sha(preview),
                                        ['clock'], True, 'Actual preview was used to generate this mask.')
        except ValueError as error:
            self.fail('Recorded intermediate render must be a valid actual mask input: ' + str(error))
        receipt = result['issues']['structure']['targets']['clock']['mask_reviews'][-1]
        self.assertEqual(receipt['input_sha256'], sha(preview))
        self.assertEqual(receipt['job_source_sha256'], sha(self.source))
        self.w.resolve_issue(self.job, 'structure', 'clock', 'corrected',
                             'Local correction applied to that preview.', output_sha256=sha(self.output))
        self.w.resolve_issue(self.job, 'structure', 'pier', 'not_needed', 'No visible defect.', output_sha256=sha(self.output))
        self.review(input_sha256=sha(preview))
        self.assertEqual(self.w.accept_job(self.job, self.output)['status'], 'accepted')

    def test_mask_from_unrelated_preview_is_not_valid_for_final_render(self):
        self.issue()
        preview = self.dir / 'unrelated.png'
        preview.write_bytes(image_bytes('PNG', (91,120,160)))
        self.review(preview, visual_passed=False)
        self.w.review_mask(self.job, 'structure', 'clock', sha(preview),
                           ['clock'], True, 'Scope checked on sibling render.')
        self.w.resolve_issue(self.job, 'structure', 'clock', 'corrected',
                             'Claims final correction.', output_sha256=sha(self.output))
        self.w.resolve_issue(self.job, 'structure', 'pier', 'not_needed', 'No visible defect.', output_sha256=sha(self.output))
        self.review()
        with self.assertRaisesRegex(ValueError, 'input|lineage'):
            self.w.accept_job(self.job, self.output)

    def test_verified_and_review_passes_must_be_actual_booleans(self):
        self.issue()
        for value in (None, 'true', 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.w.review_mask(self.job, 'structure', 'clock', sha(self.source),
                                   ['clock'], value, 'Scope checked.')
            with self.subTest(review_value=value), self.assertRaises(ValueError):
                self.review(visual_passed=value)
        self.w.review_mask(self.job, 'structure', 'clock', sha(self.source),
                           ['clock'], False, 'Selection remains incomplete.')
        self.w.resolve_issue(self.job, 'structure', 'clock', 'corrected',
                             'Claimed correction.', output_sha256=sha(self.output))
        self.w.resolve_issue(self.job, 'structure', 'pier', 'not_needed', 'No visible defect.', output_sha256=sha(self.output))
        self.review()
        with self.assertRaisesRegex(ValueError, 'verified'):
            self.w.accept_job(self.job, self.output)

    def test_unknown_targets_and_statuses_are_rejected_without_mutation(self):
        self.issue()
        before = self.job.read_bytes()
        with self.assertRaisesRegex(ValueError, 'target'):
            self.w.resolve_issue(self.job, 'structure', 'sky', 'not_needed', 'No visible defect.', output_sha256=sha(self.output))
        with self.assertRaisesRegex(ValueError, 'target'):
            self.w.review_mask(self.job, 'structure', 'sky', sha(self.source), ['sky'], True, 'Inspected.')
        with self.assertRaisesRegex(ValueError, 'status'):
            self.w.resolve_issue(self.job, 'structure', 'clock', 'done', 'Claimed done.')
        self.assertEqual(self.job.read_bytes(), before)

    def test_empty_reasons_and_duplicate_issue_or_job_are_rejected(self):
        self.issue()
        with self.assertRaises(ValueError):
            self.w.resolve_issue(self.job, 'structure', 'clock', 'not_needed', '  ')
        with self.assertRaises(ValueError):
            self.w.review_mask(self.job, 'structure', 'clock', sha(self.source), ['clock'], True, '')
        with self.assertRaises(ValueError):
            self.w.add_issue(self.job, 'structure', ['pier'], 'Duplicate issue.')
        with self.assertRaises(ValueError):
            self.w.add_issue(self.job, 'empty', [], 'No targets.')
        before = self.job.read_bytes()
        with self.assertRaises(FileExistsError):
            self.w.create_job(self.job, self.source, 'test.2')
        self.assertEqual(self.job.read_bytes(), before)

    def test_acceptance_requires_existing_output_and_passing_exact_hash_reviews(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.w.accept_job(self.job, self.dir / 'missing.png')
        with self.assertRaisesRegex(ValueError, 'review'):
            self.w.accept_job(self.job, self.output)
        self.review(profile_passed=False)
        with self.assertRaisesRegex(ValueError, 'review|profile'):
            self.w.accept_job(self.job, self.output)
        self.review()
        self.output.write_bytes(image_bytes('PNG', (92,120,160)))
        with self.assertRaisesRegex(ValueError, 'review|hash'):
            self.w.accept_job(self.job, self.output)
        self.review()
        self.assertEqual(self.w.accept_job(self.job, self.output)['status'], 'accepted')

    def test_latest_failed_review_invalidates_an_earlier_passing_review(self):
        self.review()
        self.review(visual_passed=False)
        with self.assertRaisesRegex(ValueError, 'review|visual'):
            self.w.accept_job(self.job, self.output)

    def test_review_rejects_wrong_source_hash(self):
        with self.assertRaisesRegex(ValueError, 'input|source'):
            self.review(input_sha256='0' * 64)

    def test_correction_receipts_must_match_the_final_output_hash(self):
        self.issue()
        self.corrected('clock')
        self.corrected('pier')
        self.output.write_bytes(image_bytes('PNG', (93,120,160)))
        self.review()
        with self.assertRaisesRegex(ValueError, 'output|hash'):
            self.w.accept_job(self.job, self.output)

    def test_elapsed_milestones_preserve_missing_values_and_overlap_is_not_added_twice(self):
        self.w.mark(self.job, 'first_render', 3_000_000_000)
        self.w.record_tool(self.job, 'mask', 1_000_000_000, 5_000_000_000)
        self.w.record_tool(self.job, 'download', 4_000_000_000, 8_000_000_000)
        self.w.record_tool(self.job, 'review', 10_000_000_000, 11_000_000_000, status='error')
        result = self.w.timing_summary(self.job)
        self.assertEqual(result['elapsed_seconds']['first_render'], 3)
        self.assertIsNone(result['elapsed_seconds']['visual_accepted'])
        self.assertIsNone(result['elapsed_seconds']['save_completed'])
        self.assertEqual(result['tool_seconds_sum'], 9)
        self.assertEqual(result['tool_seconds_union'], 8)
        self.assertEqual(result['tool_count'], 3)

    def test_reversed_times_and_duplicate_milestones_are_rejected(self):
        with self.assertRaises(ValueError):
            self.w.record_tool(self.job, 'download', 2, 1)
        self.w.mark(self.job, 'first_render', 10)
        with self.assertRaisesRegex(ValueError, 'already|duplicate'):
            self.w.mark(self.job, 'first_render', 20)
        with self.assertRaises(ValueError):
            self.w.mark(self.job, 'visual_accepted', 9)
        self.assertEqual(self.w.timing_summary(self.job)['elapsed_seconds']['first_render'], 10 / 1e9)

    def test_local_ready_and_visual_acceptance_can_happen_in_either_order(self):
        orders = [('local_final_ready', 'visual_accepted'),
                  ('visual_accepted', 'local_final_ready')]
        for index, order in enumerate(orders):
            with self.subTest(order=order):
                job = self.dir / ('order_' + str(index) + '.json')
                self.w.create_job(job, self.source, self.w.bootstrap(ROOT)['workflow_revision'], started_unix_ns=0)
                self.w.mark(job, 'first_render', 10)
                try:
                    self.w.mark(job, order[0], 20)
                    self.w.mark(job, order[1], 30)
                except ValueError as error:
                    self.fail('Local readiness and visual acceptance have no fixed order: ' + str(error))
                self.w.mark(job, 'save_completed', 40)
                observed = self.w.timing_summary(job)['milestone_unix_ns']
                self.assertEqual(observed[order[0]], 20)
                self.assertEqual(observed[order[1]], 30)
                self.assertEqual(observed['save_completed'], 40)

    def test_causal_timing_checks_reject_early_save_and_late_backfilled_render(self):
        self.w.mark(self.job, 'local_final_ready', 20)
        with self.assertRaises(ValueError):
            self.w.mark(self.job, 'first_render', 21)
        self.w.mark(self.job, 'first_render', 10)
        self.w.mark(self.job, 'visual_accepted', 30)
        with self.assertRaises(ValueError):
            self.w.mark(self.job, 'save_completed', 25)
        self.w.mark(self.job, 'save_completed', 40)
        observed = self.w.timing_summary(self.job)['milestone_unix_ns']
        self.assertEqual(observed['first_render'], 10)
        self.assertEqual(observed['save_completed'], 40)

    def test_cli_uses_json_structured_arguments(self):
        result = subprocess.run([sys.executable, str(SCRIPT), 'timing'],
                                input=json.dumps({'path': str(self.job)}),
                                capture_output=True, text=True, check=True, encoding='utf-8')
        self.assertIsNone(json.loads(result.stdout)['elapsed_seconds']['save_completed'])
        invalid = subprocess.run([sys.executable, str(SCRIPT), 'resolve'],
                                 input=json.dumps({'path': str(self.job), 'issue_id': 'absent',
                                                   'target': 'clock', 'status': 'blocked', 'reason': 'Cannot inspect.'}),
                                 capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn('error', json.loads(invalid.stderr))


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/missing':
                    self.send_error(404)
                    return
                body = {'/png': PNG, '/jpeg': JPEG, '/html': b'<html>server error</html>'}[self.path]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('workflow_session'),
                             'workflow_session controller is missing')
        self.w = importlib.import_module('workflow_session')
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.destination = self.dir / 'image.png'
        self.destination.write_bytes(b'previous destination')

    def test_download_accepts_png_and_jpeg_with_expected_integrity(self):
        for endpoint, body in (('/png', PNG), ('/jpeg', JPEG)):
            with self.subTest(endpoint=endpoint):
                destination=self.dir/('fresh.png' if endpoint=='/png' else 'fresh.jpg')
                expected = hashlib.sha256(body).hexdigest()
                result = self.w.download_image(self.url + endpoint, destination, expected_sha256=expected)
                self.assertEqual(destination.read_bytes(), body)
                self.assertEqual(result['sha256'], expected)

    def test_http_invalid_body_and_hash_errors_leave_no_destination(self):
        self.destination.unlink()
        for endpoint, expected in (('/missing', None), ('/html', None), ('/png', '0' * 64)):
            with self.subTest(endpoint=endpoint), self.assertRaises(Exception):
                self.w.download_image(self.url + endpoint, self.destination, expected_sha256=expected)
            self.assertFalse(self.destination.exists())
            self.assertEqual(list(self.dir.iterdir()), [])


if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    unittest.main(verbosity=2)
