"""Isolated synthetic fault injection; no Adobe/Library calls or visual claims."""
import json
import shutil
import unittest
from unittest.mock import patch
import delivery_adapter as d
import workflow_session as w


class FaultInjectionReleaseTests(unittest.TestCase):
    def setUp(self):
        from verify_delivery_automation import AutomationTests
        self.f = AutomationTests(methodName='runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.a = self.f.api()

    def test_timeout_then_query_reconciles_same_reservation(self):
        f = self.f
        self.a.direction(f.j, 'Synthetic', 'Synthetic', 'Synthetic', 'screen', 'native', ['synthetic'])
        token = d.begin(f.j, 'SYNTHETIC_PROVIDER', {})['submission_id']
        # External request was reserved, then its response was lost. Do not resubmit.
        def timed_out():
            raise TimeoutError('Injected response loss, not a real provider outage')
        with self.assertRaises(TimeoutError):
            timed_out()
        before = f.j.read_bytes()
        self.assertEqual(self.a.plan(f.j)['action'], 'INVESTIGATE_RENDER')
        with self.assertRaises(ValueError):
            d.begin(f.j, 'SYNTHETIC_PROVIDER', {})
        self.assertEqual(f.j.read_bytes(), before)
        evidence = f.d / 'synthetic-query.json'
        evidence.write_text(json.dumps(dict(basis='observed_tool_result',
            tool_name='SYNTHETIC_PROVIDER', input_sha256=w._file(f.s)['sha256'],
            status='ready', output_url='https://example.invalid/synthetic.png',
            note='SYNTHETIC query response, not real service evidence')))
        d.resolve_unknown(f.j, token, evidence)
        resolved = f.j.read_bytes()
        self.assertTrue(d.resolve_unknown(f.j, token, evidence)['reused'])
        self.assertEqual(f.j.read_bytes(), resolved)
        self.assertEqual(self.a.plan(f.j)['action'], 'FETCH_OUTPUT')
        with patch.object(w, 'download_image', side_effect=TimeoutError('Injected fetch timeout')):
            with self.assertRaises(TimeoutError):
                self.a.fetch(f.j, f.d / 'fetched.png')
        self.assertEqual(f.j.read_bytes(), resolved)
        def fetch(url, target, **kwargs):
            shutil.copyfile(f.o, target)
        with patch.object(w, 'download_image', side_effect=fetch) as network:
            self.a.fetch(f.j, f.d / 'fetched.png')
            self.a.fetch(f.j, f.d / 'fetched.png')
            self.assertEqual(network.call_count, 1)

    def test_failed_save_then_query_receipt_does_not_repeat_write(self):
        f = self.f
        f.accept()
        w.save_intent(f.j, f.receipt)
        before = f.j.read_bytes()
        f.receipt.write_text(json.dumps({'results': [{'status': 'failed',
            'local_path': str(f.o), 'error': 'SYNTHETIC save failure'}]}))
        self.assertEqual(self.a.plan(f.j)['action'], 'INVESTIGATE_PHOTO_SAVE')
        with self.assertRaises(ValueError):
            w.complete_save(f.j, f.receipt)
        self.assertEqual(before, f.j.read_bytes())
        # Isolated provider-query fixture resolves the same intent; no remote upload.
        f.save_fixture(f.receipt, f.o, 'SYNTHETIC_QUERY_CONFIRMED')
        self.a.complete(f.j, f.receipt, f.rec)
        completed = f.j.read_bytes()
        self.a.complete(f.j, f.receipt, f.rec)
        self.assertEqual(completed, f.j.read_bytes())
        self.assertEqual(self.a.plan(f.j)['action'], 'PREPARE_RECORD_SAVE')
        record_receipt = f.d / 'record-save.json'
        self.a.record_intent(f.j, f.rec, record_receipt)
        record_receipt.write_text('{incomplete')
        self.assertEqual(self.a.plan(f.j)['action'], 'INVESTIGATE_RECORD_SAVE')
        f.save_fixture(record_receipt, f.rec, 'SYNTHETIC_RECORD_QUERY')
        self.a.record_saved(f.j, record_receipt)
        self.assertEqual(self.a.plan(f.j)['action'], 'DELIVER')
