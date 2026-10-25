"""Anonymous synthetic protocol fixtures; no editor or host is mocked as real."""
import json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import verify_photo_edit as fixtures
import photo_edit as e, workflow_session as w

class VersionTests(unittest.TestCase):
    setUp=fixtures.LeanEditTests.setUp
    submit=fixtures.LeanEditTests.submit
    returned=fixtures.LeanEditTests.returned
    events=fixtures.LeanEditTests.events

    def accepted(self):
        self.returned(self.submit());e.review(self.job,self.events(),self.output)
        self.session=self.base/'private-session'
        import task_history as h
        return h.register(self.job,self.session)

    def test_duplicate_registration_and_cross_turn_restore_do_not_render_or_mutate_history(self):
        row=self.accepted();import task_history as h
        before=self.job.read_bytes();photo=self.output.read_bytes()
        self.assertEqual(row['label'],'V1')
        self.assertEqual(h.register(self.job,self.session)['label'],'V1')
        with patch.object(e,'submit',side_effect=AssertionError('rollback rendered')):
            restored=h.restore(self.session,row['series'],'V1')
        self.assertEqual(restored['output'],w._file(self.output))
        self.assertEqual(before,self.job.read_bytes());self.assertEqual(photo,self.output.read_bytes())
        self.assertEqual(h.current(self.session)['label'],'V1')

    def test_changed_or_missing_historical_output_fails_without_render(self):
        row=self.accepted();import task_history as h
        self.output.write_bytes(b'changed')
        with self.assertRaises(ValueError):h.restore(self.session,row['series'],'V1')
        self.output.unlink()
        with self.assertRaises((ValueError,OSError)):h.restore(self.session,row['series'],'V1')

    def test_hint_claim_is_atomic_once_and_disabled_across_calls(self):
        row=self.accepted();import task_history as h
        self.assertIn('更自然',h.delivered(self.job,self.session,presented=True)['hint'])
        self.assertEqual(h.delivered(self.job,self.session,presented=True)['hint'],'')
        h.hints(self.session,False)
        self.assertFalse(h.hints(self.session)['enabled'])
        self.assertNotIn('preferences',list(self.session.iterdir()))

    def test_unobserved_delivery_cannot_consume_hint(self):
        self.accepted();import task_history as h
        with self.assertRaises(ValueError):h.delivered(self.job,self.session,presented=False)
        self.assertTrue(h.delivered(self.job,self.session,presented=True)['hint'])

    def test_revision_uses_selected_output_and_inherits_local_protections(self):
        row=self.accepted();import task_history as h
        child=self.base/'child.json';before=self.job.read_bytes()
        result=h.revise(self.session,row['series'],'V1',child,'只改天空，让层次更明显',local=True)
        state=w._load(child)
        self.assertEqual(state['source'],w._file(self.output))
        self.assertEqual(state['revision']['original_source'],w._file(self.source))
        self.assertEqual(state['revision']['parent_version'],'V1')
        targets={x['target'] for x in result['protections']['requirements']}
        self.assertTrue({'composition','people','approved_direction'}<=targets)
        self.assertEqual(before,self.job.read_bytes())
        self.assertIn('Synthetic fixture',result['inherited_direction']['intent'])

    def test_inherited_contract_cannot_be_dropped_by_low_level_protect(self):
        row=self.accepted();import task_history as h
        child=self.base/'child.json';h.revise(self.session,row['series'],'V1',child,'保持构图只调色')
        before=child.read_bytes()
        with self.assertRaises(ValueError):w.set_protections(child,[],'drop inherited')
        self.assertEqual(before,child.read_bytes())

    def test_comparison_pairs_same_version_source_and_formal_output(self):
        row=self.accepted();import task_history as h
        pair=h.compare(self.session,row['series'],'V1')
        self.assertEqual(pair['before'],w._file(self.source))
        self.assertEqual(pair['after'],w._file(self.output))
        self.assertEqual(pair['render_calls'],0)

    def test_branching_revision_gets_next_version_and_keeps_parent(self):
        row=self.accepted();import task_history as h
        from PIL import Image
        child=self.base/'child.json';result=h.revise(self.session,row['series'],'V1',child,'更自然')
        ticket=e.submit(child,result['protections'],{'branch':'PROFESSIONAL_FALLBACK','decisions':[],'reason':'Synthetic revision'},
                        'SYNTHETIC_TOOL',{'prompt':'Synthetic natural revision','referenced_image_paths':[str(self.output)]},result['protected_regions'],direction=self.direction)
        second=self.base/'second.png';Image.new('RGB',(32,48),(85,105,115)).save(second)
        import time
        now=time.time_ns();e.returned(child,ticket['submission_id'],'ready',now,now+10,output_path=second,presented=True)
        events=[{'action':'review','arguments':{'output_path':str(second),'input_sha256':w._file(self.output)['sha256'],
          'visual_passed':True,'profile_passed':False,'color_scope':'screen_srgb_assumed',
          'color_assumption_reason':'Synthetic screen fixture','note':'Synthetic protocol review'}}]
        e.review(child,events,second)
        v2=h.register(child,self.session);self.assertEqual(v2['label'],'V2');self.assertEqual(v2['parent_version'],'V1')
        h.restore(self.session,row['series'],'V1')
        self.assertEqual(h.current(self.session)['label'],'V1')
        self.assertEqual(len(h.history(self.session,row['series'])['versions']),2)

    def test_revision_rejects_replaced_original_before_submission(self):
        row=self.accepted();import task_history as h
        child=self.base/'child.json';h.revise(self.session,row['series'],'V1',child,'更自然')
        self.source.write_bytes(b'changed original')
        with self.assertRaises(ValueError):__import__('delivery_automation')._fresh(child)

    def test_index_detects_changed_accepted_contract_without_blocking_save_metadata(self):
        row=self.accepted();import task_history as h
        state=w._load(self.job);state['delivery_receipt']={'file_id':'SYNTHETIC_LATE_SAVE'};w._save(self.job,state)
        self.assertEqual(h.get(self.session,row['series'],'V1')['label'],'V1')
        state['professional_direction']['intent']='changed historical direction';w._save(self.job,state)
        with self.assertRaises(ValueError):h.restore(self.session,row['series'],'V1')

    def test_status_plans_once_without_mutating_task(self):
        before=self.job.read_bytes()
        with patch.object(e.a,'plan',wraps=e.a.plan) as plan:
            e._response(self.job)
        self.assertEqual(plan.call_count,1);self.assertEqual(before,self.job.read_bytes())

    def test_local_tool_inputs_must_include_selected_version_when_supplied(self):
        row=self.accepted();import task_history as h
        child=self.base/'child.json';result=h.revise(self.session,row['series'],'V1',child,'更自然')
        before=child.read_bytes()
        with self.assertRaises(ValueError):
            e.submit(child,result['protections'],{'branch':'PROFESSIONAL_FALLBACK','decisions':[],'reason':'Synthetic'},
                     'SYNTHETIC_TOOL',{'prompt':'Fixture','referenced_image_paths':[str(self.source)]},
                     result['protected_regions'],direction=self.direction)
        self.assertEqual(before,child.read_bytes())

    def test_corrupt_index_returns_controlled_error_without_touching_photos(self):
        row=self.accepted();import task_history as h
        before=self.output.read_bytes();(self.session/'tasks.sqlite3').write_bytes(b'invalid database')
        with self.assertRaises(ValueError):h.hints(self.session)
        self.assertEqual(before,self.output.read_bytes())
