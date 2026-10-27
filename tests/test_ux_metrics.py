"""Observational UX metrics use only explicit synthetic receipts in this suite."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import delivery_metrics as m

class UXMetricTests(unittest.TestCase):
    def state(self):
        return {'status':'accepted','workflow_revision':'fixture','source':{'sha256':'a'*64},
                'milestones':{'job_started':100,'local_final_ready':300,'visual_accepted':400},
                'reviews':[],'render_history':[], 'render_result':{'submission_id':'one','input_sha256':'a'*64,'recipe':{'arguments_sha256':'b'*64}},
                'external_call_receipts':[{'submission_id':'one','start_unix_ns':200,'end_unix_ns':250},
                                           {'submission_id':'one','start_unix_ns':260,'end_unix_ns':270}]}

    def test_polls_are_not_duplicate_renders_and_save_absence_remains_unknown(self):
        item=m.observe(self.state())
        self.assertEqual(item['duplicate_render_count'],0)
        self.assertEqual(item['accepted_output_elapsed_seconds'],300/1e9)
        self.assertIsNone(item['photo_save_elapsed_seconds'])
        self.assertFalse(item['persistence_confirmed'])

    def test_distinct_submissions_with_same_input_and_arguments_count_as_duplicate(self):
        state=self.state();state['render_history']=[dict(state['render_result'],submission_id='earlier')]
        state['external_call_receipts'].append({'submission_id':'earlier','start_unix_ns':120,'end_unix_ns':150})
        self.assertEqual(m.observe(state)['duplicate_render_count'],1)

    def test_missing_readiness_or_acceptance_is_not_measured_as_success(self):
        state=self.state();state['status']='in_progress';state['milestones']={'job_started':100}
        self.assertIsNone(m.observe(state)['accepted_output_elapsed_seconds'])
