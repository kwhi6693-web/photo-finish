"""Contracts, protection strategies and observational statistics; synthetic only."""
from pathlib import Path
import copy,json,subprocess,sys,tempfile,time,unittest
from unittest.mock import patch
from PIL import Image
import photo_edit as e,workflow_session as w,photo_workflow as p
import review_contract as c,delivery_metrics as m
from verify_photo_edit import LeanEditTests

ROOT=Path(__file__).resolve().parents[2]

class ContractTests(LeanEditTests):
    # Inherit fixture only, not the base suite again (see load_tests below).
    def protected_submit(self,strategy='generative_compare',level='semantic_identity'):
        return e.submit(self.job,{'requirements':[{'target':'text','level':level,'requirement':'Synthetic glyph shape'}],'reason':'Synthetic protection'},
            {'branch':'PROFESSIONAL_FALLBACK','decisions':[],'reason':'Synthetic fixture'},'SYNTHETIC_TOOL',{'prompt':'Synthetic fixture'},
            {'text':['glyph region']},fidelity={'text':{'strategy':strategy,'capability_basis':'Synthetic test capability only','repair_route':'Synthetic correction fixture'}})
    def protection(self,recreated=True):
        return {'action':'protection','arguments':{'target':'text','output_sha256':w._file(self.output)['sha256'],'status':'met','method':'manual_detail_comparison','content_recreated':recreated,'comparison_scope':['glyph region'],'reason':'Synthetic comparison only'}}
    def test_region_string_fails_before_transaction_with_actionable_field(self):
        self.returned(self.protected_submit());events=self.events()+[self.protection()];events[-1]['arguments']['comparison_scope']='glyph region';before=self.job.read_bytes()
        with patch.object(w,'transact',wraps=w.transact) as transaction:
            with self.assertRaises(c.InputError) as error:e.review(self.job,events,self.output)
            transaction.assert_not_called()
        self.assertIn('comparison_scope',error.exception.field);self.assertEqual(before,self.job.read_bytes())
    def test_wrong_mask_target_fails_before_transaction(self):
        self.returned(self.submit(issues=[{'issue_id':'i','targets':['depth'],'observation':'Synthetic depth'}]));events=self.events()+[{'action':'mask','arguments':{'issue_id':'i','target':'depth','input_sha256':w._file(self.source)['sha256'],'actual_scope':['description, not target'],'verified':True,'reason':'Synthetic fixture'}}]
        with self.assertRaisesRegex(c.InputError,'exact target ID'):e.review(self.job,events,self.output)
    def test_nonobject_event_returns_structured_cli_error(self):
        self.returned(self.submit());events=self.events()+['bad'];process=subprocess.run([sys.executable,str(ROOT/'10_SYSTEM_CONFIG/scripts/photo_edit.py'),'review'],input=json.dumps({'path':str(self.job),'events':events,'output_path':str(self.output)}),text=True,capture_output=True)
        self.assertEqual(process.returncode,1);error=json.loads(process.stderr);self.assertEqual(error['field'],'events[1]');self.assertEqual(error['code'],'INVALID_REVIEW_INPUT')
    def test_returned_supplies_structural_requirements_without_approval(self):
        result=self.returned(self.protected_submit());req=result['review_requirements'];self.assertEqual(req['protection_comparison_scopes'],{'text':['glyph region']});self.assertNotIn('visual_passed',req)
    def test_missing_fidelity_plan_is_rejected_before_lock(self):
        before=self.job.read_bytes()
        with self.assertRaises(c.InputError):e.submit(self.job,{'requirements':[{'target':'text'}],'reason':'Synthetic'}, {},'SYNTHETIC',{}, {'text':['glyph']})
        self.assertEqual(before,self.job.read_bytes())
    def test_exact_content_rejects_reconstruction_before_tool(self):
        before=self.job.read_bytes()
        with self.assertRaisesRegex(c.InputError,'exact_content'):self.protected_submit(level='exact_content')
        self.assertEqual(before,self.job.read_bytes())
    def test_preserved_route_cannot_claim_recreated_content_pass(self):
        self.returned(self.protected_submit(strategy='native_preserved'))
        with self.assertRaisesRegex(c.InputError,'contradicts'):e.review(self.job,self.events()+[self.protection(True)],self.output)
    def test_semantic_reconstruction_requires_and_accepts_actual_comparison(self):
        self.returned(self.protected_submit());result=e.review(self.job,self.events()+[self.protection()],self.output)
        self.assertEqual(result['quality_observation']['quality_status'],'accepted')
    def test_bad_direction_publishes_no_partial_job(self):
        target=self.base/'bad.json'
        with self.assertRaises(ValueError):e.prepare(self.root,self.source,target,dict(self.direction,route='invalid'),[])
        self.assertFalse(target.exists())
    def test_bad_tags_publish_no_partial_job(self):
        target=self.base/'bad.json'
        with self.assertRaises(ValueError):e.prepare(self.root,self.source,target,self.direction,['INVALID'])
        self.assertFalse(target.exists())
    def test_unknown_review_argument_is_identified_before_transaction(self):
        self.returned(self.submit());events=self.events();events[0]['arguments']['made_up']=True
        with self.assertRaisesRegex(c.InputError,'made_up'):e.review(self.job,events,self.output)


class MetricsTests(LeanEditTests):
    def accepted(self):
        state=w._load(self.job);state['evaluation']={'kind':'live','scenario':'synthetic-unit-fixture-labelled-live-only-to-test-grouping'};w._save(self.job,state)
        self.returned(self.submit());e.review(self.job,self.events(),self.output)
        return w._load(self.job)
    def test_form_errors_are_separate_from_first_output_acceptance(self):
        self.returned(self.submit())
        with self.assertRaises(c.InputError):e.review(self.job,['bad'],self.output)
        e.review(self.job,self.events(),self.output);sample=m.sample(self.job)
        self.assertTrue(sample['first_output_accepted']);self.assertEqual(sample['validation_failure_count'],1)
    def test_missing_save_endpoint_is_null(self):
        self.accepted();sample=m.sample(self.job);self.assertIsNone(sample['photo_save_elapsed_seconds']);self.assertFalse(sample['persistence_confirmed'])
    def test_polling_same_submission_does_not_inflate_render_count(self):
        state=self.accepted();state['external_call_receipts'].append(copy.deepcopy(state['external_call_receipts'][0]))
        sample=m.observe(state);self.assertEqual(sample['render_submissions_observed'],1);self.assertTrue(sample['first_output_accepted'])
    def test_repeated_snapshots_of_same_task_are_deduplicated(self):
        self.accepted();report=m.report([self.job,self.job]);self.assertEqual(report['groups']['live']['tasks'],1);self.assertEqual(report['duplicate_records_omitted'],1)
    def test_synthetic_is_excluded_from_live_denominator(self):
        state=self.accepted();state['evaluation']['kind']='synthetic';w._save(self.job,state)
        report=m.report([self.job]);self.assertEqual(report['groups']['live']['first_output_acceptance']['denominator'],0);self.assertIsNone(report['groups']['live']['first_output_acceptance']['rate']);self.assertEqual(report['groups']['synthetic']['tasks'],1)
    def test_quality_failure_before_pass_is_not_first_output_success(self):
        state=self.accepted();state['reviews'].insert(0,dict(state['reviews'][0],visual_passed=False));sample=m.observe(state);self.assertFalse(sample['first_output_accepted'])
    def test_deliberate_refinement_counts_image_revision(self):
        state=self.accepted();state['render_history']=[copy.deepcopy(state['render_result'])];sample=m.observe(state);self.assertEqual(sample['image_revision_count'],1);self.assertFalse(sample['first_output_accepted'])
    def test_snapshot_contains_observation_in_existing_save(self):
        self.returned(self.submit());target=self.base/'pending.json';e.review(self.job,self.events(),self.output,target)
        record=json.loads(target.read_text(encoding='utf-8'));self.assertIn('quality_observation',record);self.assertEqual(record['quality_observation']['kind'],'unclassified')

def load_tests(loader,tests,pattern):
    suite=unittest.TestSuite()
    for cls in (ContractTests,MetricsTests):
        for name in cls.__dict__:
            if name.startswith('test_'):suite.addTest(cls(name))
    return suite
if __name__=='__main__':unittest.main()
