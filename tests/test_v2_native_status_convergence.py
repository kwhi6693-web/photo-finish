"""Regression of one read-only next-action projection, never a host GO fixture."""
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from tests import test_v2_delivery as fixture
import delivery_automation as a
import v2_delivery as d
import workflow_session as w


class NativeStatusConvergenceTests(TestCase):
    def setUp(self):
        self.h=fixture.DeliveryTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        h=self.h
        self.pending=h.write('pending.json',{
            'camera_original_sha256':d.hash_file(h.source),
            'candidate_sha256':d.hash_file(h.photo),
            'status':'PENDING_REAL_IMAGE_EDITORIAL_REVIEW',
            'formal_V1_registered':False})
    def status(self,**extras):
        return a.native_status(self.h.source,self.h.photo,self.pending,**extras)
    def host(self):
        h=self.h;identity='libfile_synthetic'
        save=h.write('save.json',{'structuredContent':{
            'library_file_id':identity,'file_id':'file_synthetic','status':'succeeded'}})
        readback=h.write('readback.json',{'transfers':[{
            'library_file_id':identity,'workspace_path':str(h.photo),
            'workspace_sha256':d.hash_file(h.photo)}]})
        return dict(save_json=save,readback_json=readback,readback_image=h.photo,
                    library_file_id=identity)
    def inventory(self):
        return {p.name:p.read_bytes() for p in self.h.root.iterdir() if p.is_file()}

    def test_pending_reread_does_not_render_register_or_replace_user_go(self):
        before=self.inventory()
        first=self.status()
        self.assertEqual(first['action'],'WAITING_ACCEPTANCE_RECORD')
        self.assertTrue(first['terminal_for_turn'])
        self.assertFalse(first['new_render_allowed'])
        self.assertFalse(first['formal_V1_registered'])
        self.assertEqual(first,self.status())
        self.assertEqual(self.inventory(),before)

    def test_accepted_exact_png_without_host_evidence_ends_current_turn(self):
        self.h.accept();accepted=self.h.root/'accepted.json'
        before=self.inventory()
        first=self.status(accepted_json=accepted)
        self.assertEqual(first['action'],'WAITING_EXTERNAL')
        self.assertEqual(first['user_photographic_GO'],'RECORDED_FOR_EXACT_PNG')
        self.assertTrue(first['terminal_for_turn'])
        self.assertEqual(first,self.status(accepted_json=accepted))
        self.assertEqual(self.inventory(),before)

    def test_new_actual_host_evidence_resumes_only_registration_then_readonly(self):
        self.h.accept();accepted=self.h.root/'accepted.json'
        host=self.host()
        before=self.inventory()
        ready=self.status(accepted_json=accepted,**host)
        self.assertEqual(ready['action'],'REGISTER_V1')
        self.assertFalse(ready['terminal_for_turn'])
        self.assertEqual(ready,self.status(accepted_json=accepted,**host))
        self.assertEqual(self.inventory(),before)
        d.register(accepted,host['save_json'],host['readback_json'],
                   self.h.photo,'libfile_synthetic',self.h.root/'v1.json')
        after=self.inventory()
        done=self.status(accepted_json=accepted,version_json=self.h.root/'v1.json',**host)
        self.assertEqual(done['action'],'FORMAL_V1_VERIFIED')
        self.assertTrue(done['formal_V1_registered'])
        self.assertTrue(done['terminal_for_turn'])
        self.assertFalse(done['iphone_save_confirmed'])
        self.assertFalse(done['cross_conversation_restore_verified'])
        self.assertEqual(done,self.status(accepted_json=accepted,
                                          version_json=self.h.root/'v1.json',**host))
        self.assertEqual(after,self.inventory())

    def test_missing_or_failed_real_host_receipt_never_registers(self):
        self.h.accept();accepted=self.h.root/'accepted.json';host=self.host()
        self.h.write('save.json',{'status':'failed','file_id':'file_synthetic',
                                  'library_file_id':'libfile_synthetic'})
        with self.assertRaises(ValueError):
            self.status(accepted_json=accepted,**host)
        self.assertFalse((self.h.root/'v1.json').exists())
        with self.assertRaises(ValueError):
            self.status(save_json=host['save_json'])

    def test_pending_hash_and_formal_record_mutations_fail_closed(self):
        self.h.accept();accepted=self.h.root/'accepted.json';host=self.host()
        self.h.write('pending.json',dict(
            status='PENDING_REAL_IMAGE_EDITORIAL_REVIEW',
            formal_V1_registered=False,
            camera_original_sha256='0'*64,
            candidate_sha256=d.hash_file(self.h.photo)))
        with self.assertRaises(ValueError):
            self.status(accepted_json=accepted,**host)
        self.h.write('pending.json',dict(
            status='PENDING_REAL_IMAGE_EDITORIAL_REVIEW',
            formal_V1_registered=False,
            camera_original_sha256=d.hash_file(self.h.source),
            candidate_sha256=d.hash_file(self.h.photo)))
        d.register(accepted,host['save_json'],host['readback_json'],
                   self.h.photo,'libfile_synthetic',self.h.root/'v1.json')
        version=json.loads((self.h.root/'v1.json').read_text())
        version['library_file_id']='libfile_unrelated'
        self.h.write('wrong-v1.json',version)
        with self.assertRaises(ValueError):
            self.status(accepted_json=accepted,version_json=self.h.root/'wrong-v1.json',**host)

    def test_legacy_accepted_auto_save_wait_is_a_terminal_turn(self):
        h=self.h
        output=dict(path=str(h.photo),sha256=d.hash_file(h.photo))
        state=dict(status='accepted',workflow_revision='test',source=output,
                   output=output,reviews=[],render_result={},
                   platform_delivery={'save':{'status':'pending_confirmation'},
                                      'display':{'status':'observed'}},
                   milestones={})
        with patch.object(w,'_load',return_value=state),\
             patch.object(a,'_fresh',return_value=state),\
             patch.object(w,'_file',return_value=output):
            status=a.plan(h.root/'ledger.json')
        self.assertEqual(status['action'],'AWAIT_PLATFORM_SAVE_CONFIRMATION')
        self.assertTrue(status['terminal_for_turn'])
        self.assertTrue(status['resume_requires_new_evidence'])
        self.assertFalse(status['automatic_visual_acceptance'])
