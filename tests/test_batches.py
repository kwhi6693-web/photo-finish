"""Batch protocol regressions. Fixtures do not represent actual image service calls."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import verify_photo_edit as fixtures
import photo_edit as e,workflow_session as w

class BatchTests(unittest.TestCase):
    setUp=fixtures.LeanEditTests.setUp
    submit=fixtures.LeanEditTests.submit
    returned=fixtures.LeanEditTests.returned
    events=fixtures.LeanEditTests.events

    def batch(self):
        self.returned(self.submit());e.review(self.job,self.events(),self.output)
        self.session=self.base/'session';jobs=[]
        for i in range(9):
            path=self.base/('done-'+str(i)+'.json');path.write_bytes(self.job.read_bytes());jobs.append(str(path))
        failed=self.base/'failed.json';e.prepare(self.root,self.source,failed,self.direction,[])
        w.finish_job(failed,'failed','Synthetic failure before any submission')
        jobs.append(str(failed));self.jobs=jobs
        import batch_workflow as b
        return b.create(self.session,jobs)

    def test_ten_photo_batch_one_failure_preserves_nine_completed(self):
        batch=self.batch();import batch_workflow as b
        before={x:Path(x).read_bytes() for x in self.jobs}
        result=b.summary(self.session,batch['batch_id'])
        self.assertEqual(result['counts']['已完成'],9);self.assertEqual(result['counts']['失败'],1)
        self.assertEqual(result['total'],10)
        self.assertEqual(before,{x:Path(x).read_bytes() for x in self.jobs})

    def test_retry_prepares_only_failed_item_and_never_calls_renderer(self):
        batch=self.batch();import batch_workflow as b
        before={x:Path(x).read_bytes() for x in self.jobs[:9]}
        with patch.object(e,'submit',side_effect=AssertionError('batch rendered without executor')):
            result=b.retry_failed(self.session,batch['batch_id'],consent=True)
        self.assertEqual(len(result['prepared']),1)
        self.assertEqual(w._load(result['prepared'][0]['path'])['status'],'in_progress')
        self.assertEqual(before,{x:Path(x).read_bytes() for x in self.jobs[:9]})
        self.assertEqual(b.retry_failed(self.session,batch['batch_id'],consent=True)['prepared'],[])

    def test_unknown_is_needs_confirmation_and_never_retryable(self):
        ticket=self.submit();import batch_workflow as b
        batch=b.create(self.base/'session',[str(self.job)])
        result=b.summary(self.base/'session',batch['batch_id'])
        self.assertEqual(result['counts']['需确认'],1)
        self.assertFalse(result['items'][0]['retryable'])
        self.assertEqual(b.retry_failed(self.base/'session',batch['batch_id'],consent=True)['prepared'],[])

    def test_batch_hint_only_once_at_end(self):
        batch=self.batch();import batch_workflow as b
        first=b.completed(self.session,batch['batch_id'])
        self.assertIn('更自然',first['hint'])
        self.assertEqual(b.completed(self.session,batch['batch_id'])['hint'],'')

    def test_retry_preserves_unchanged_profile_and_task_settings(self):
        import user_preferences as p,batch_workflow as b
        private=self.base/'styles'
        p.save(rules=['保留颗粒'],consent=True,library_root=private)
        profile=p.show(private,scenes=[])
        path=self.base/'profile-failed.json'
        e.prepare(self.root,self.source,path,self.direction,[],style_library_root=private,
                  observed_profile_sha256=profile['sha256'],task_settings={'grain':'retain'})
        w.finish_job(path,'failed','Synthetic failure before submission')
        batch=b.create(self.base/'session',[str(path)])
        result=b.retry_failed(self.base/'session',batch['batch_id'],consent=True)
        self.assertEqual(result['errors'],[]);self.assertEqual(len(result['prepared']),1)
        self.assertEqual(w._load(result['prepared'][0]['path'])['user_customization']['task_settings'],{'grain':'retain'})

    def test_failed_local_revision_retry_cannot_drop_protections(self):
        self.returned(self.submit());e.review(self.job,self.events(),self.output)
        import task_history as h,batch_workflow as b
        session=self.base/'session';row=h.register(self.job,session)
        child=self.base/'child.json';h.revise(session,row['series'],'V1',child,'只改天空',local=True)
        w.finish_job(child,'failed','Synthetic pre-submission failure')
        batch=b.create(session,[str(child)]);result=b.retry_failed(session,batch['batch_id'],consent=True)
        replacement=result['prepared'][0]['path']
        self.assertIn('revision',w._load(replacement))
        with self.assertRaises(ValueError):w.set_protections(replacement,[],'drop requirements')

    def test_pending_only_batch_does_not_consume_future_completion_hint(self):
        import batch_workflow as b
        session=self.base/'session';batch=b.create(session,[str(self.job)])
        self.assertEqual(b.completed(session,batch['batch_id'])['hint'],'')
        self.returned(self.submit());e.review(self.job,self.events(),self.output)
        self.assertIn('更自然',b.completed(session,batch['batch_id'])['hint'])

    def test_all_failed_summary_does_not_consume_first_actual_delivery_hint(self):
        import batch_workflow as b
        failed=self.base/'failed.json';e.prepare(self.root,self.source,failed,self.direction,[])
        w.finish_job(failed,'failed','Synthetic no-submit failure')
        session=self.base/'session';batch=b.create(session,[str(failed)])
        self.assertEqual(b.completed(session,batch['batch_id'])['hint'],'')
        replacement=b.retry_failed(session,batch['batch_id'],consent=True)['prepared'][0]['path']
        # Attach a synthetic accepted-state fixture without claiming a live tool call.
        self.returned(self.submit());e.review(self.job,self.events(),self.output)
        Path(replacement).write_bytes(self.job.read_bytes())
        self.assertIn('更自然',b.completed(session,batch['batch_id'])['hint'])

    def test_batch_rechecks_accepted_revision_original_provenance(self):
        self.returned(self.submit());e.review(self.job,self.events(),self.output)
        import batch_workflow as b
        # Use real revision metadata binding an additional original fixture.
        original=self.base/'original.png';original.write_bytes(self.source.read_bytes())
        state=w._load(self.job);state['revision']={'original_source':w._file(original),'parent_output':w._file(self.source),
              'parent_job':str(self.job),'parent_protection_sha256':'synthetic'}
        w._save(self.job,state)
        batch=b.create(self.base/'session',[str(self.job)]);original.write_bytes(b'changed')
        self.assertEqual(b.summary(self.base/'session',batch['batch_id'])['counts']['需确认'],1)
