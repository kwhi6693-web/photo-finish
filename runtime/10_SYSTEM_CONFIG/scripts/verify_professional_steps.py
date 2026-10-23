"""Protocol tests use synthetic images; these are not aesthetic certification."""
import json, shutil, unittest
from unittest.mock import patch
import verify_delivery_automation as fixture
import delivery_automation as a, workflow_session as w

class ProfessionalSteps(unittest.TestCase):
 setUp=fixture.AutomationTests.setUp
 def direction(self):
  return a.direction(self.j, intent='Quiet window light', hierarchy='Window then wood',
   light_material='Mixed daylight and tungsten; retain separation',
   output_use='screen', route='native', qa_focus=['Window edge','Wood grain'])
 def fetched(self):
  t=a.begin_render(self.j,'native',w._file(self.s)['sha256'])['submission_id']
  a.render_result(self.j,'native',w._file(self.s)['sha256'],'ready',output_url='https://example.invalid/render',submission_id=t)
  with patch.object(w,'download_image',side_effect=lambda u,d,**kw:shutil.copyfile(self.o,d)):
   a.fetch(self.j,self.d/'first.png')
 def test_direction_is_source_bound_and_not_a_quality_pass(self):
  v=self.direction();self.assertEqual(v['source_sha256'],w._file(self.s)['sha256']);self.assertFalse(v['quality_certified'])
 def test_direction_requires_real_use_scope(self):
  with self.assertRaises(ValueError):a.direction(self.j,intent='x',hierarchy='x',light_material='x',output_use='print_approved',route='native',qa_focus=['x'])
 def test_direction_locks_before_external_submission(self):
  self.direction();self.fetched()
  with self.assertRaises(ValueError):self.direction()
 def test_unreviewed_step_cannot_be_chained(self):
  self.fetched();before=self.j.read_bytes()
  with self.assertRaises(ValueError):a.next_render(self.j,'crop',{'reason':'Composition'})
  self.assertEqual(before,self.j.read_bytes())
 def test_next_step_uses_current_reviewed_output_and_retains_history(self):
  self.direction();self.fetched();first=self.d/'first.png';w.add_review(self.j,first,w._file(self.s)['sha256'],True,True,'Fixture verified')
  v=a.next_render(self.j,'crop',{'reason':'Composition'});state=w._load(self.j)
  self.assertEqual(state['render_result']['input_sha256'],w._file(first)['sha256']);self.assertEqual(len(state['render_history']),1);self.assertTrue(v['submission_id'])
  self.assertEqual(a.plan(self.j)['action'],'INVESTIGATE_RENDER')
  with self.assertRaises(ValueError):w.accept_job(self.j,first)
 def test_changed_prior_output_blocks_chain(self):
  self.fetched();first=self.d/'first.png';w.add_review(self.j,first,w._file(self.s)['sha256'],True,True,'Fixture verified');first.write_bytes(b'changed')
  with self.assertRaises(ValueError):a.next_render(self.j,'crop',{})
 def test_plan_never_accepts_review_from_other_output(self):
  self.fetched();w.add_review(self.j,self.s,w._file(self.s)['sha256'],True,True,'Different fixture')
  self.assertEqual(a.plan(self.j)['action'],'REVIEW_OUTPUT')
