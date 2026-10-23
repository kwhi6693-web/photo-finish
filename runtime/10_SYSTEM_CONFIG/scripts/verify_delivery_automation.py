"""Automation state/receipt tests. All generated files and save identities are synthetic."""
from pathlib import Path
import importlib.util, json, shutil, tempfile, time, unittest
from unittest.mock import patch
from PIL import Image,ImageCms
import photo_workflow as p,workflow_session as w
from export_workflow_runtime import FILES
ROOT=Path(__file__).resolve().parents[2]

class AutomationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.d=Path(self.tmp.name);self.root=self.d/'project'
  for rel in FILES:
   to=self.root/rel;to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,to)
  self.s=self.d/'source.png';self.o=self.d/'output.png';self.j=self.d/'job.json';self.rec=self.d/'record.json';self.receipt=self.d/'photo_save.json'
  icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes();Image.new('RGB',(32,48),(70,90,110)).save(self.s,icc_profile=icc);Image.new('RGB',(32,48),(80,100,120)).save(self.o,icc_profile=icc)
  p.prepare(self.root,self.s,self.j);p.candidates(self.j,self.root,[]);w.select_references(self.j,'PROFESSIONAL_FALLBACK',[],'Synthetic scene');w.set_protections(self.j,[],'Synthetic blank fixture')
 def api(self):
  self.assertIsNotNone(importlib.util.find_spec('delivery_automation'),'Missing automated delivery controller');import delivery_automation;return delivery_automation
 def accept(self):w.add_review(self.j,self.o,w._file(self.s)['sha256'],True,True,'Synthetic receipt for protocol tests only');w.accept_job(self.j,self.o)
 def save_fixture(self,path,local,identity):path.write_text(json.dumps({'results':[{'local_path':str(local),'status':'succeeded','local_metadata_applied':True,'library_file_id':identity}]}))
 def test_old_provider_revision_routes_to_verified_current_context(self):
  a=self.api();v=a.entry(self.root,'2026-10-22.7');self.assertTrue(v['stale_observed_skill']);self.assertEqual(v['effective_revision'],w.bootstrap(self.root)['workflow_revision']);self.assertFalse(v['provider_cache_repaired'])
 def test_plan_is_read_only_and_does_not_repeat_render(self):
  a=self.api();before=self.j.read_bytes();self.assertEqual(a.plan(self.j)['action'],'RENDER');self.assertEqual(before,self.j.read_bytes())
  a.render_result(self.j,'test-native',w._file(self.s)['sha256'],'working',task_id='SYNTHETIC_TASK');self.assertEqual(a.plan(self.j)['action'],'POLL_RENDER')
  with self.assertRaises(ValueError):a.render_result(self.j,'other',w._file(self.s)['sha256'],'ready',output_url='https://example.invalid/x.png',request_id='DIFFERENT')
 def test_unknown_submission_is_never_automatically_resubmitted(self):
  a=self.api();a.render_result(self.j,'test-native',w._file(self.s)['sha256'],'unknown');self.assertEqual(a.plan(self.j)['action'],'INVESTIGATE_RENDER')
 def test_submission_intent_survives_interruption_and_only_matching_call_can_resolve(self):
  a=self.api();start=getattr(a,'begin_render',None);self.assertTrue(callable(start),'Submission must be registered before external call')
  token=start(self.j,'test-native',w._file(self.s)['sha256'])['submission_id'];self.assertEqual(a.plan(self.j)['action'],'INVESTIGATE_RENDER')
  with self.assertRaises(ValueError):start(self.j,'test-native',w._file(self.s)['sha256'])
  with self.assertRaises(ValueError):a.render_result(self.j,'test-native',w._file(self.s)['sha256'],'ready',output_url='https://example.invalid/x.png',submission_id='WRONG')
  a.render_result(self.j,'test-native',w._file(self.s)['sha256'],'ready',output_url='https://example.invalid/x.png',submission_id=token);self.assertEqual(a.plan(self.j)['action'],'FETCH_OUTPUT')
 def test_fetch_reuses_hash_verified_output_without_network(self):
  a=self.api();a.render_result(self.j,'test-native',w._file(self.s)['sha256'],'ready',output_url='https://example.invalid/x.png',request_id='SYNTHETIC_REQUEST')
  def download(url,destination,**kw):shutil.copyfile(self.o,destination);return w._file(destination)
  target=self.d/'fetched.png'
  with patch.object(w,'download_image',side_effect=download) as network:
   a.fetch(self.j,target);a.fetch(self.j,target);self.assertEqual(network.call_count,1)
  self.assertEqual(a.plan(self.j)['action'],'REVIEW_OUTPUT')
 def test_modified_download_cannot_be_silently_reused_or_overwritten(self):
  a=self.api();a.render_result(self.j,'test-native',w._file(self.s)['sha256'],'ready',output_url='https://example.invalid/x.png');target=self.d/'fetched.png'
  with patch.object(w,'download_image',side_effect=lambda u,d,**k:(shutil.copyfile(self.o,d),w._file(d))[1]):a.fetch(self.j,target)
  target.write_bytes(b'changed');before=target.read_bytes()
  with self.assertRaises(ValueError):a.fetch(self.j,target)
  self.assertEqual(before,target.read_bytes())
 def test_duplicate_completion_reuses_record_and_save_endpoint(self):
  a=self.api();self.accept();w.save_intent(self.j,self.receipt);self.save_fixture(self.receipt,self.o,'SYNTHETIC_PHOTO')
  a.complete(self.j,self.receipt,self.rec,recipe={'test':True});old=self.rec.read_bytes();endpoint=json.loads(self.j.read_text())['milestones']['save_completed'];a.complete(self.j,self.receipt,self.rec,recipe={'test':True})
  self.assertEqual(old,self.rec.read_bytes());self.assertEqual(endpoint,json.loads(self.j.read_text())['milestones']['save_completed'])
 def test_unknown_save_result_is_investigated_without_resave(self):
  a=self.api();self.accept();w.save_intent(self.j,self.receipt);self.receipt.write_text('{incomplete');self.assertEqual(a.plan(self.j)['action'],'INVESTIGATE_PHOTO_SAVE')
 def test_record_save_is_required_before_deliver(self):
  a=self.api();self.accept();w.save_intent(self.j,self.receipt);self.save_fixture(self.receipt,self.o,'SYNTHETIC_PHOTO');a.complete(self.j,self.receipt,self.rec)
  self.assertEqual(a.plan(self.j)['action'],'PREPARE_RECORD_SAVE');res=self.d/'record_save.json';a.record_intent(self.j,self.rec,res);self.assertEqual(a.plan(self.j)['action'],'SAVE_RECORD')
  self.save_fixture(res,self.rec,'SYNTHETIC_RECORD');a.record_saved(self.j,res);self.assertEqual(a.plan(self.j)['action'],'DELIVER')
 def test_wrong_record_save_receipt_is_rejected(self):
  a=self.api();self.accept();w.save_intent(self.j,self.receipt);self.save_fixture(self.receipt,self.o,'SYNTHETIC_PHOTO');a.complete(self.j,self.receipt,self.rec);res=self.d/'record_save.json';a.record_intent(self.j,self.rec,res);self.save_fixture(res,self.o,'SYNTHETIC_WRONG')
  with self.assertRaises(ValueError):a.record_saved(self.j,res)
  self.assertNotEqual(a.plan(self.j)['action'],'DELIVER')
 def test_stale_context_blocks_automatic_continuation(self):
  a=self.api();master=self.root/'我的照片美化偏好与修图标准.md';master.write_text(master.read_text()+'\nchanged\n');self.assertEqual(a.plan(self.j)['action'],'RESTART_CONTEXT')
 def test_failed_task_requires_new_task_not_silent_reopen(self):
  a=self.api();w.finish_job(self.j,'failed','Fixture failure');before=self.j.read_bytes();self.assertEqual(a.plan(self.j)['action'],'STOP');self.assertEqual(before,self.j.read_bytes())
 def test_context_loading_is_timed_inside_intake_without_an_extra_read(self):
  t=w.timing_summary(self.j);self.assertGreater(t['stages']['context_read']['seconds_sum'] or 0,0)

if __name__=='__main__':unittest.main()
