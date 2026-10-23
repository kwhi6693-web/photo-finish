"""Actual-file protocol tests; saved IDs and tool boundaries here are synthetic fixtures."""
from pathlib import Path
import json, shutil, tempfile, time, unittest
from PIL import Image,ImageCms
import photo_workflow as p, workflow_session as w, delivery_automation as a, delivery_adapter as d
from export_workflow_runtime import FILES

ROOT=Path(__file__).resolve().parents[2]

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.root=self.base/'project'
        for rel in FILES:
            target=self.root/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
        self.source=self.base/'source.png';self.output=self.base/'generated.png';self.job=self.base/'job.json'
        Image.new('RGB',(30,40),(80,110,100)).save(self.source)
        Image.new('RGB',(30,40),(100,120,90)).save(self.output)
        p.prepare(self.root,self.source,self.job);p.candidates(self.job,self.root,[])
        w.select_references(self.job,'PROFESSIONAL_FALLBACK',[],'Synthetic scene; no visual judgment')
        w.set_protections(self.job,[],'Synthetic featureless image')
        a.direction(self.job,'Synthetic protocol test','flat fixture','not a visual assessment','screen','creative',['fixture'])
        self.args={'prompt':'Synthetic exact prompt; not an actual render','referenced_image_paths':[str(self.source)]}
    def begin(self):return d.begin(self.job,'SYNTHETIC_IMAGE_TOOL',self.args,'platform_auto')['submission_id']
    def finish(self,token,**kwargs):
        now=time.time_ns();return d.finish(self.job,token,'ready',now,now+10,output_path=self.output,presented=True,**kwargs)
    def review(self):
        w.add_review(self.job,self.output,w._file(self.source)['sha256'],True,False,'Synthetic review of a flat fixture only',
                     color_scope='screen_srgb_assumed',color_assumption_reason='Ordinary screen sharing; source encoding not certified')
    def test_returned_local_bytes_are_attached_without_download_or_reupload(self):
        token=self.begin();self.finish(token);state=w._load(self.job)
        self.assertEqual(state['render_result']['acquired'],w._file(self.output));self.assertEqual(a.plan(self.job)['action'],'REVIEW_OUTPUT')
        self.assertEqual(state['render_result']['recipe']['actual_arguments'],self.args)
        self.assertEqual(len(state['tools']),1);self.assertEqual(len([x for x in state['stages'] if x['stage']=='render']),1)
        self.assertNotIn('save_completed',state['milestones'])
    def test_screen_scope_preserves_profile_false_and_waits_for_real_save(self):
        self.finish(self.begin());self.review();w.accept_job(self.job,self.output)
        state=w._load(self.job);self.assertEqual(state['acceptance_scope'],'screen_srgb_assumed');self.assertFalse(state['reviews'][-1]['profile_passed'])
        self.assertEqual(d.status(self.job)['persistence'],'pending_confirmation')
        self.assertEqual(a.plan(self.job)['action'],'AWAIT_PLATFORM_SAVE_CONFIRMATION')
        record=self.base/'record.json';d.snapshot(self.job,record)
        self.assertEqual(json.loads(record.read_text())['record_status'],'pending_platform_confirmation')
    def test_automatic_display_is_not_visual_or_persistence_acceptance(self):
        self.finish(self.begin());value=d.status(self.job)
        self.assertEqual(value['display'],'observed');self.assertEqual(value['quality'],'review_required');self.assertFalse(value['profile_check_passed']);self.assertFalse(value['professional_color_calibrated'])
        self.assertFalse(value['background_reconciliation_installed'])
    def test_duplicate_finish_reuses_receipt_even_after_acceptance(self):
        token=self.begin();now=time.time_ns();payload=dict(path=self.job,submission_id=token,status='ready',start_unix_ns=now,end_unix_ns=now+10,output_path=self.output,presented=True)
        d.finish(**payload);self.review();w.accept_job(self.job,self.output)
        self.assertTrue(d.finish(**payload)['reused']);self.assertEqual(len(w._load(self.job)['tools']),1)
    def test_unknown_call_never_gets_an_automatic_resubmission(self):
        token=self.begin();now=time.time_ns();d.finish(self.job,token,'unknown',now,now+10)
        self.assertEqual(a.plan(self.job)['action'],'INVESTIGATE_RENDER')
        with self.assertRaises(ValueError):self.begin()
    def test_investigated_unknown_result_recovers_without_a_second_render(self):
        token=self.begin();now=time.time_ns();d.finish(self.job,token,'unknown',now,now+10)
        evidence=self.base/'investigation.json';evidence.write_text(json.dumps({'basis':'observed_tool_result','tool_name':'SYNTHETIC_IMAGE_TOOL',
          'input_sha256':w._file(self.source)['sha256'],'status':'ready','output_path':str(self.output),'presented':True,'note':'Synthetic recovered response; no actual cloud observation'}))
        d.resolve_unknown(self.job,token,evidence);self.assertEqual(a.plan(self.job)['action'],'REVIEW_OUTPUT')
        self.assertEqual(len(w._load(self.job)['tools']),1);self.assertTrue(d.resolve_unknown(self.job,token,evidence)['reused'])
        self.assertIsNone(w.timing_summary(self.job)['stages']['save']['seconds_sum'])
    def test_working_polls_keep_same_task_and_register_each_actual_boundary(self):
        token=self.begin();now=time.time_ns();d.finish(self.job,token,'working',now,now+10,task_id='SYNTHETIC_TASK')
        d.finish(self.job,token,'ready',now+20,now+30,output_path=self.output,task_id='SYNTHETIC_TASK',presented=True)
        self.assertEqual(len(w._load(self.job)['tools']),2)
    def test_each_deliberate_step_retains_its_own_unknown_reconciliation(self):
        def unknown(token):
            now=time.time_ns();d.finish(self.job,token,'unknown',now,now+10)
        def evidence(name,input_path,output_path):
            path=self.base/name;path.write_text(json.dumps({'basis':'observed_tool_result','tool_name':'SYNTHETIC_IMAGE_TOOL','input_sha256':w._file(input_path)['sha256'],
              'status':'ready','output_path':str(output_path),'presented':True,'note':'Synthetic separate-step reconciliation'}));return path
        first=self.begin();unknown(first);d.resolve_unknown(self.job,first,evidence('first.json',self.source,self.output));self.review()
        second_output=self.base/'second.png';Image.new('RGB',(30,40),(90,120,100)).save(second_output)
        second=d.next_step(self.job,'SYNTHETIC_IMAGE_TOOL',{'prompt':'Second synthetic step'})['submission_id'];unknown(second)
        d.resolve_unknown(self.job,second,evidence('second.json',self.output,second_output));state=w._load(self.job)
        self.assertEqual(len(state['reconciliation_receipts']),2);self.assertEqual(len(state['tools']),2);self.assertEqual(state['render_result']['acquired'],w._file(second_output))
    def test_call_receipt_rejects_wrong_token_or_backdated_bounds(self):
        self.begin();now=time.time_ns()
        with self.assertRaises(ValueError):d.finish(self.job,'WRONG','ready',now,now+10,output_path=self.output)
        with self.assertRaises(ValueError):d.finish(self.job,w._load(self.job)['execution_adapter']['submission_id'],'unknown',now,now-1)
    def test_declared_p3_cannot_use_untagged_screen_assumption(self):
        import struct,zlib
        raw=self.output.read_bytes();body=b'cICP'+bytes((12,13,0,1));chunk=struct.pack('>I',4)+body+struct.pack('>I',zlib.crc32(body)&0xffffffff)
        self.output.write_bytes(raw[:33]+chunk+raw[33:])
        with self.assertRaises(ValueError):self.review()
    def test_print_scope_cannot_inherit_screen_assumption(self):
        self.finish(self.begin());self.review();state=w._load(self.job);state['professional_direction']['output_use']='print_proof_requested';w._save(self.job,state)
        with self.assertRaises(ValueError):w.accept_job(self.job,self.output)
    def test_invalid_color_metadata_is_not_an_untagged_assumption(self):
        from PIL import PngImagePlugin
        info=PngImagePlugin.PngInfo();info.add_text('PCSColorPolicy','[]');Image.new('RGB',(30,40)).save(self.output,pnginfo=info)
        with self.assertRaises(ValueError):self.review()
    def test_known_recreated_content_needs_compared_regions(self):
        state=w._load(self.job);state['protection_plan']['targets']['plaque']={'level':'semantic_identity','requirement':'Visible-source writing','reviews':[]};w._save(self.job,state)
        token=d.begin(self.job,'SYNTHETIC_IMAGE_TOOL',self.args,'platform_auto',{'plaque':['visible letters and layout']})['submission_id'];self.finish(token);self.review()
        with self.assertRaises(ValueError):w.review_protection(self.job,'plaque',w._file(self.output)['sha256'],'met','manual_detail_comparison',True,'Synthetic review')
        with self.assertRaises(ValueError):w.review_protection(self.job,'plaque',w._file(self.output)['sha256'],'met','manual_detail_comparison',True,'Synthetic wrong region',comparison_scope=['unrelated background'])
        w.review_protection(self.job,'plaque',w._file(self.output)['sha256'],'met','manual_detail_comparison',True,'Synthetic regions; no real content claim',comparison_scope=['visible letters and layout'])
    def test_save_confirmation_requires_exact_invocation_and_hash(self):
        token=self.begin();self.finish(token);self.review();w.accept_job(self.job,self.output);receipt=self.base/'receipt.json'
        value={'status':'succeeded','source':'platform_save_receipt','library_file_id':'SYNTHETIC_SAVED_ID','output_sha256':w._file(self.output)['sha256'],'submission_id':'WRONG'}
        receipt.write_text(json.dumps(value))
        with self.assertRaises(ValueError):d.confirm_platform_save(self.job,receipt)
        value['submission_id']=token;receipt.write_text(json.dumps(value));d.confirm_platform_save(self.job,receipt)
        self.assertEqual(d.status(self.job)['persistence'],'confirmed');self.assertEqual(a.plan(self.job)['action'],'BUILD_RECORD')
        rec=self.base/'final.json';a.complete(self.job,receipt,rec);save=self.base/'record-save.json';a.record_intent(self.job,rec,save)
        save.write_text(json.dumps({'results':[{'local_path':str(rec),'status':'succeeded','local_metadata_applied':True,'library_file_id':'SYNTHETIC_RECORD'}]}))
        a.record_saved(self.job,save);self.assertEqual(a.plan(self.job)['action'],'DELIVER');self.assertFalse(a.plan(self.job)['display_needed'])
    def test_deliberate_next_step_reuses_reviewed_lineage_and_keeps_prior_receipts(self):
        self.finish(self.begin());self.review();second=self.base/'second.png';Image.new('RGB',(30,40),(90,110,100)).save(second)
        token=d.next_step(self.job,'SYNTHETIC_IMAGE_TOOL',{'prompt':'Deliberate refinement of synthetic fixture'})['submission_id']
        now=time.time_ns();d.finish(self.job,token,'ready',now,now+10,output_path=second,presented=True)
        value=w._load(self.job);self.assertEqual(len(value['external_call_receipts']),2);self.assertEqual(value['render_result']['input_sha256'],w._file(self.output)['sha256'])
    def test_changed_formal_bytes_cannot_be_accepted(self):
        self.finish(self.begin());self.review();Image.new('RGB',(30,40),(90,90,90)).save(self.output)
        with self.assertRaises(ValueError):w.accept_job(self.job,self.output)
    def test_failed_receipt_registration_is_atomic_and_does_not_count_a_tool(self):
        token=self.begin();before=self.job.read_bytes();now=time.time_ns()
        with self.assertRaises(OSError):d.finish(self.job,token,'ready',now,now+10,output_path=self.base/'missing.png',presented=True)
        self.assertEqual(before,self.job.read_bytes());self.assertEqual(len(w._load(self.job)['tools']),0)
    def test_metadata_ranking_is_integrated_into_source_bound_candidates(self):
        from session_brief import build
        index_path=self.root/'10_SYSTEM_CONFIG/reference_index.json'
        index=[{'id':f'SYNTHETIC-{i}','original_filename':f'synthetic-{i}.png','style_weight':1,
                'relative_path':f'private-local/synthetic-{i}.png'} for i in range(3)]
        for item in index:item.update(tags=['A'],include_in_dna=True,subject='道路车辆',individual_note='')
        index[1]['subject']='园林日光灰瓦木窗';index_path.write_text(json.dumps(index));build(self.root,self.root/'10_SYSTEM_CONFIG/SESSION_BRIEF.json')
        new=self.base/'semantic-job.json';p.prepare(self.root,self.source,new)
        result=p.candidates(new,self.root,['A'],intent={'subject':['garden','architecture'],'material':['tile','wood']})
        self.assertEqual(result['candidates'][0]['reference_id'],index[1]['id']);self.assertEqual(result['semantic_method'],'intent_metadata_v1');self.assertFalse(result['visual_suitability_established'])

class SemanticTests(unittest.TestCase):
    def test_metadata_evidence_is_explained_and_never_a_visual_verdict(self):
        from reference_semantics import assess,normalize_intent
        intent=normalize_intent({'subject':['architecture','garden'],'material':['tile'],'light':['sunlight']})
        garden=assess(intent,{'subject':'园林亭阁灰瓦与日光'});city=assess(intent,{'subject':'道路车辆'})
        self.assertGreater(garden['retrieval_score'],city['retrieval_score']);self.assertFalse(garden['aesthetic_quality_established']);self.assertIsNone(garden['match_probability'])
    def test_empty_intent_preserves_legacy_ranking_weight(self):
        from reference_semantics import assess
        self.assertEqual(assess({}, {'subject':'园林亭阁'})['retrieval_score'],0)
    def test_unsupported_or_unbounded_intent_is_rejected(self):
        from reference_semantics import normalize_intent
        with self.assertRaises(ValueError):normalize_intent({'subject':['invented']})
        with self.assertRaises(ValueError):normalize_intent({'unknown':[]})

if __name__=='__main__':unittest.main()
