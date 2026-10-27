"""Anonymous protocol regressions; never display, upload or edit real photos."""
import json
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/10_SYSTEM_CONFIG/scripts'))
import experience
import photo_edit as e
import task_history as h
import workflow_session as w
import verify_photo_edit as fixtures


class ManualDisplayTests(unittest.TestCase):
    setUp = fixtures.LeanEditTests.setUp
    events = fixtures.LeanEditTests.events

    def accepted(self):
        ticket = e.submit(self.job, {'requirements': [], 'reason': 'Synthetic blank'},
                          {'branch': 'PROFESSIONAL_FALLBACK', 'decisions': [], 'reason': 'Synthetic'},
                          'SYNTHETIC_TOOL', {}, {}, display_mode='manual', direction=self.direction)
        import time
        now = time.time_ns()
        e.returned(self.job, ticket['submission_id'], 'ready', now, now + 10,
                   output_path=self.output, presented=False)
        e.review(self.job, self.events(), self.output)
        self.session = self.base / 'private-session'

    def test_current_manual_confirmation_is_reported_without_rewriting_job(self):
        self.accepted()
        before = self.job.read_bytes()
        photo = self.output.read_bytes()
        with patch.object(e, 'submit', side_effect=AssertionError('unexpected edit')):
            result = h.delivered(self.job, self.session, presented=True)
        self.assertTrue(result['experience']['display_observed'])
        self.assertEqual(result['experience']['display_observation_source'], 'current_manual_confirmation')
        self.assertEqual(result['experience']['display_observation_scope'], 'current_delivery_response')
        self.assertFalse(result['experience']['persistence_confirmed'])
        self.assertEqual(result['version']['label'], 'V1')
        self.assertEqual(before, self.job.read_bytes())
        self.assertEqual(photo, self.output.read_bytes())
        self.assertNotIn('platform_delivery', w._load(self.job))

    def test_repeat_confirmation_does_not_infer_from_first_hint_or_add_version(self):
        self.accepted()
        first = h.delivered(self.job, self.session, presented=True)
        before = self.job.read_bytes()
        second = h.delivered(self.job, self.session, presented=True)
        self.assertTrue(first['experience']['display_observed'])
        self.assertTrue(second['experience']['display_observed'])
        self.assertTrue(first['hint'])
        self.assertEqual(second['hint'], '')
        self.assertEqual(first['version'], second['version'])
        with sqlite3.connect(self.session / 'tasks.sqlite3') as db:
            self.assertEqual(db.execute('SELECT number, delivered FROM versions').fetchall(), [(1, 1)])
        self.assertEqual(before, self.job.read_bytes())

    def test_invalid_confirmation_rejected_before_index_or_job_mutation(self):
        self.accepted()
        before = self.job.read_bytes()
        for value in (False, None, 0, 1, 'true', [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                h.delivered(self.job, self.session, presented=value)
        self.assertFalse(self.session.exists())
        self.assertEqual(before, self.job.read_bytes())

    def test_saved_or_legacy_delivered_does_not_upgrade_session_free_status(self):
        self.accepted()
        state = w._load(self.job)
        state['delivery_receipt'] = {'file_id': 'SYNTHETIC_SAVE'}
        w._save(self.job, state)
        h.delivered(self.job, self.session, presented=True)
        before = self.job.read_bytes()
        result = e._response(self.job)['experience']
        self.assertTrue(result['persistence_confirmed'])
        self.assertFalse(result['display_observed'])
        self.assertEqual(result['display_observation_scope'], 'platform_ledger')
        self.assertEqual(result['display_observation_source'], 'unobserved')
        self.assertEqual(before, self.job.read_bytes())

    def assert_changed_confirmation_rejected(self, change):
        self.accepted()
        h.register(self.job, self.session)
        before_db = (self.session / 'tasks.sqlite3').read_bytes()
        if change == 'output':
            self.output.write_bytes(b'changed synthetic output')
        else:
            state = w._load(self.job)
            state['professional_direction']['intent'] = 'changed synthetic contract'
            w._save(self.job, state)
        before = self.job.read_bytes()
        with self.assertRaises(ValueError):
            h.delivered(self.job, self.session, presented=True)
        self.assertEqual(before, self.job.read_bytes())
        self.assertEqual(before_db, (self.session / 'tasks.sqlite3').read_bytes())

    def test_changed_output_rejects_confirmation_without_index_change(self):
        self.assert_changed_confirmation_rejected('output')

    def test_changed_contract_rejects_confirmation_without_index_change(self):
        self.assert_changed_confirmation_rejected('contract')


class DisplayScopeTests(unittest.TestCase):
    def test_explicit_confirmation_and_platform_observation_keep_save_independent(self):
        for platform, saved, confirmation, want in (
                (False, False, False, False), (False, True, False, False),
                (True, False, False, True), (False, True, True, True),
                (True, False, True, True)):
            with self.subTest(platform=platform, saved=saved, confirmation=confirmation):
                state = {'status': 'accepted', 'render_result': {'output_url': 'synthetic-url'},
                         'platform_delivery': {'display': {'status': 'observed' if platform else 'unobserved'},
                                               'save': {'status': 'pending_confirmation'}}}
                if saved:
                    state['delivery_receipt'] = {'file_id': 'SYNTHETIC_SAVE'}
                before = json.dumps(state, sort_keys=True)
                result = experience.describe(state, 'DELIVER', manual_presented=confirmation)
                self.assertEqual(result['display_observed'], want)
                self.assertEqual(result['persistence_confirmed'], saved)
                self.assertEqual(result['display_observation_source'],
                                 'current_manual_confirmation' if confirmation else
                                 ('platform_delivery' if platform else 'unobserved'))
                self.assertEqual(before, json.dumps(state, sort_keys=True))

    def test_experience_rejects_truthy_non_boolean_confirmation(self):
        for value in (None, 0, 1, 'true', [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                experience.describe({'status': 'accepted'}, 'DELIVER', manual_presented=value)
