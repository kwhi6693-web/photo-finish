"""Synthetic protocol tests only. No Library service or private user data."""
from pathlib import Path
from contextlib import closing
import json
import os
import shutil
import sqlite3
import sys
import unittest
from unittest.mock import patch
import zipfile
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/10_SYSTEM_CONFIG/scripts'))
import verify_delivery_automation as fixture
import delivery_automation as delivery
import recovery_archive as recovery
import task_history as history
import workflow_session as workflow


class RecoveryArchiveTests(unittest.TestCase):
    setUp = fixture.AutomationTests.setUp
    accept = fixture.AutomationTests.accept
    save_fixture = fixture.AutomationTests.save_fixture

    def ready(self):
        self.accept()
        workflow.save_intent(self.j, self.receipt)
        self.save_fixture(self.receipt, self.o.resolve(), 'SYNTHETIC_OUTPUT')
        delivery.complete(self.j, self.receipt, self.rec)
        receipt = self.d / 'record-save.json'
        delivery.record_intent(self.j, self.rec, receipt)
        self.save_fixture(receipt, self.rec.resolve(), 'SYNTHETIC_RECORD')
        delivery.record_saved(self.j, receipt)
        self.session = self.d.resolve() / 'session'
        self.item = history.delivered(self.j, self.session, True)['version']
        self.args = dict(session_root=str(self.session), series=self.item['series'], version='V1')
        self.cloud = []
        for path, identity in [(self.s, 'SYNTHETIC_SOURCE'), (self.o, 'SYNTHETIC_OUTPUT')]:
            result = self.d / (path.stem + '-materialize.json')
            self.materialization(result, path, identity)
            self.cloud.append({'path': str(path), 'result_path': str(result)})

    def materialization(self, result, path, identity):
        result.write_text(json.dumps({'structuredContent': {'transfers': [
            {'workspace_path': str(path.resolve()), 'library_file_id': identity,
             'current_version_number': 0}]}}), encoding='utf-8')

    def prepare(self):
        return recovery.prepare(self.j, self.session, 'SYNTHETIC_PRIVATE_FOLDER', self.cloud)

    def archive_receipt(self, state):
        path = self.d / 'archive-save.json'
        self.save_fixture(path, Path(state['archive']['path']), 'SYNTHETIC_ARCHIVE')
        return path

    def readback(self, state, identity='SYNTHETIC_ARCHIVE'):
        path = self.d / 'readback.zip'
        shutil.copyfile(state['archive']['path'], path)
        result = self.d / 'readback-transfer.json'
        self.materialization(result, path, identity)
        return result, path

    def test_success_requires_readback_and_preserves_originals_and_index(self):
        self.ready()
        protected = [self.j, self.rec, self.o, self.s, self.session / 'tasks.sqlite3']
        before = [p.read_bytes() for p in protected]
        state = self.prepare()
        self.assertEqual(state['status'], 'credentials_pending')
        self.assertFalse(state['archive_confirmed'])
        self.assertTrue(recovery.claim(**self.args)['write_allowed'])
        state = recovery.observe(**self.args, result_path=self.archive_receipt(state))
        self.assertEqual(state['status'], 'uploaded_unverified')
        self.assertFalse(state['archive_confirmed'])
        result, path = self.readback(state)
        state = recovery.confirm(**self.args, result_path=result, materialized_path=path)
        self.assertEqual(state['status'], 'archive_confirmed')
        self.assertEqual(state['library_file_id'], 'SYNTHETIC_ARCHIVE')
        self.assertFalse(state['background_automation_installed'])
        self.assertEqual(before, [p.read_bytes() for p in protected])

    def test_duplicate_prepare_and_claim_never_register_or_render(self):
        self.ready()
        with patch.object(history, 'register', side_effect=AssertionError('new version')):
            first = self.prepare()
            second = self.prepare()
            self.assertEqual(first['archive'], second['archive'])
            self.assertEqual(first['operation_id'], second['operation_id'])
            recovery.claim(**self.args)
            self.assertFalse(recovery.claim(**self.args)['write_allowed'])
        self.assertEqual(len(history.history(self.session, self.item['series'])['versions']), 1)

    def test_lost_response_can_be_reconciled_by_materialized_bytes(self):
        self.ready()
        state = self.prepare()
        recovery.claim(**self.args)
        self.assertEqual(recovery.status(**self.args)['host_action'], 'HOST_QUERY_EXISTING')
        result, path = self.readback(state)
        confirmed = recovery.confirm(**self.args, result_path=result, materialized_path=path)
        self.assertTrue(confirmed['archive_confirmed'])
        self.assertFalse(recovery.claim(**self.args)['write_allowed'])

    def test_failed_partial_and_malformed_results_are_retained_without_retry(self):
        self.ready()
        self.prepare()
        recovery.claim(**self.args)
        path = self.d / 'failed.json'
        for raw in ['{"results":[{"status":"failed"}]}', '{"results":[]}', '{incomplete']:
            path.write_text(raw, encoding='utf-8')
            state = recovery.observe(**self.args, result_path=path)
            self.assertEqual(state['status'], 'result_unknown')
            self.assertFalse(recovery.claim(**self.args)['write_allowed'])
        self.assertEqual(len(state['events']), 3)

    def test_partial_batch_keeps_the_matching_success(self):
        self.ready()
        state = self.prepare()
        recovery.claim(**self.args)
        path = self.archive_receipt(state)
        raw = json.loads(path.read_text())
        raw['results'].append({'local_path': '/synthetic-unrelated-operation', 'status': 'failed'})
        path.write_text(json.dumps(raw), encoding='utf-8')
        state = recovery.observe(**self.args, result_path=path)
        self.assertEqual(state['status'], 'uploaded_unverified')
        self.assertFalse(recovery.claim(**self.args)['write_allowed'])

    def test_readback_hash_or_identity_conflict_stops_without_overwrite(self):
        self.ready()
        state = self.prepare()
        recovery.claim(**self.args)
        recovery.observe(**self.args, result_path=self.archive_receipt(state))
        result, path = self.readback(state, 'CONFLICTING_ARCHIVE')
        with self.assertRaisesRegex(ValueError, 'identity conflict'):
            recovery.confirm(**self.args, result_path=result, materialized_path=path)
        self.materialization(result, path, 'SYNTHETIC_ARCHIVE')
        path.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'bytes conflict'):
            recovery.confirm(**self.args, result_path=result, materialized_path=path)
        self.assertEqual(recovery.status(**self.args)['status'], 'uploaded_unverified')

    def test_missing_cloud_source_and_unconfirmed_delivery_block_preparation(self):
        self.ready()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            recovery.prepare(self.j, self.session, 'SYNTHETIC_PRIVATE_FOLDER', self.cloud[1:])
        state = workflow._load(self.j)
        del state['record_delivery']
        workflow._save(self.j, state)
        with self.assertRaisesRegex(ValueError, 'confirmed saves'):
            self.prepare()

    def test_changed_same_version_evidence_cannot_replace_existing_archive(self):
        self.ready()
        first = self.prepare()
        archive = Path(first['archive']['path']).read_bytes()
        state = workflow._load(self.j)
        state['synthetic_noncontract_note'] = 'changed same version evidence'
        workflow._save(self.j, state)
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.prepare()
        self.assertEqual(Path(first['archive']['path']).read_bytes(), archive)

    def test_scoped_snapshot_excludes_unrelated_rows_and_session_cursor(self):
        self.ready()
        with history._index(self.session, True) as db:
            db.execute('INSERT INTO versions VALUES(?,?,?,?,?)', ('f' * 32, 1, '/unrelated', '{"private":"unrelated"}', 1))
            db.execute('INSERT OR REPLACE INTO session VALUES(?,?)', ('synthetic-secret', 'unrelated'))
        state = self.prepare()
        with zipfile.ZipFile(state['archive']['path']) as archive:
            names = archive.namelist()
            self.assertFalse(any(n.endswith('.png') for n in names))
            data = archive.read('versions.sqlite3')
            dest = self.d / 'scoped.sqlite3'
            dest.write_bytes(data)
            with closing(sqlite3.connect(dest)) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM versions').fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT count(*) FROM sqlite_master WHERE name='session'").fetchone()[0], 0)

    def test_shared_private_receipt_is_not_silently_uploaded(self):
        self.ready()
        raw = json.loads(self.receipt.read_text())
        raw['results'].append({'local_path': '/synthetic-other-private-photo', 'status': 'succeeded'})
        self.receipt.write_text(json.dumps(raw), encoding='utf-8')
        # Original receipt hash now differs, so either check must reject it.
        with self.assertRaises(ValueError):
            self.prepare()

    def test_prepare_resumes_after_local_state_publication_failure(self):
        self.ready()
        durable = recovery.checkpoint._durable_json
        def fail_state(path, state):
            if Path(path).name == 'state.json':
                raise OSError('Synthetic state publication loss')
            return durable(path, state)
        with patch.object(recovery.checkpoint, '_durable_json', side_effect=fail_state):
            with self.assertRaises(OSError):
                self.prepare()
        with self.assertRaisesRegex(ValueError, 'reconciliation'):
            self.prepare()

    def test_stale_lock_and_git_storage_are_rejected(self):
        self.ready()
        self.prepare()
        lock = self.session / 'recovery-archives/writer.lock'
        lock.write_text('synthetic process loss')
        with self.assertRaises(FileExistsError):
            recovery.claim(**self.args)
        self.assertTrue(lock.exists())
        with self.assertRaises(ValueError):
            recovery.prepare(self.j, Path(__file__).resolve().parents[1], 'SYNTHETIC_PRIVATE_FOLDER', self.cloud)

    def test_delivered_host_adapter_generates_credentials_without_new_version(self):
        self.ready()
        result = history.delivered(self.j, self.session, True, recovery={
            'directory_id': 'SYNTHETIC_PRIVATE_FOLDER', 'cloud_files': self.cloud})
        self.assertEqual(result['version']['label'], 'V1')
        self.assertEqual(result['recovery']['status'], 'credentials_pending')
        self.assertEqual(result['hint'], '')

    def test_claim_flush_failure_does_not_grant_upload_permission(self):
        self.ready()
        self.prepare()
        with patch.object(recovery.checkpoint, '_durable_json', side_effect=OSError('Synthetic flush loss')):
            with self.assertRaises(OSError):
                recovery.claim(**self.args)
        self.assertFalse(recovery.claim(**self.args)['write_allowed'])

    def test_duplicate_confirmation_is_stable_and_late_failure_does_not_erase_success(self):
        self.ready()
        state = self.prepare()
        recovery.claim(**self.args)
        result, path = self.readback(state)
        first = recovery.confirm(**self.args, result_path=result, materialized_path=path)
        second = recovery.confirm(**self.args, result_path=result, materialized_path=path)
        self.assertEqual(first, second)
        failed = self.d / 'late-failure.json'
        failed.write_text('{"results":[]}', encoding='utf-8')
        self.assertTrue(recovery.observe(**self.args, result_path=failed)['archive_confirmed'])


    def test_lost_state_after_claim_never_recreates_upload_permission(self):
        self.ready()
        self.prepare()
        recovery.claim(**self.args)
        slot = recovery._slot(self.session, self.item['series'], 'V1')
        (slot / 'state.json').unlink()
        with self.assertRaisesRegex(ValueError, 'reconciliation'):
            self.prepare()

    def test_wrong_record_cloud_id_is_rejected(self):
        self.ready()
        state = workflow._load(self.j)
        state['record_delivery']['file_id'] = 'WRONG_RECORD_ID'
        workflow._save(self.j, state)
        with self.assertRaisesRegex(ValueError, 'Record cloud identity'):
            self.prepare()

    def test_archive_error_does_not_mask_successful_delivery(self):
        self.ready()
        result = history.delivered(self.j, self.session, True, recovery={
            'directory_id':'SYNTHETIC_PRIVATE_FOLDER', 'cloud_files':[]})
        self.assertEqual(result['version']['label'], 'V1')
        self.assertEqual(result['recovery']['status'], 'archive_blocked')
        self.assertFalse(result['recovery']['write_allowed'])

    def test_concurrent_local_claims_grant_at_most_one_host_create(self):
        self.ready()
        self.prepare()
        barrier = Barrier(2)
        def claim():
            barrier.wait(timeout=10)
            try:
                return recovery.claim(**self.args)['write_allowed']
            except FileExistsError:
                return False  # Contention stops; never retries a host create.
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))
        self.assertEqual(results.count(True), 1)
        self.assertFalse(recovery.claim(**self.args)['write_allowed'])

    def test_readback_confirmation_flush_loss_reconciles_without_new_upload(self):
        self.ready()
        state = self.prepare()
        recovery.claim(**self.args)
        result, path = self.readback(state)
        with patch.object(recovery.checkpoint, '_durable_json', side_effect=OSError('Synthetic confirmation loss')):
            with self.assertRaises(OSError):
                recovery.confirm(**self.args, result_path=result, materialized_path=path)
        self.assertFalse(recovery.claim(**self.args)['write_allowed'])
        self.assertTrue(recovery.confirm(**self.args, result_path=result, materialized_path=path)['archive_confirmed'])

if __name__ == '__main__':
    unittest.main()
