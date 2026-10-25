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
