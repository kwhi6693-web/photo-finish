"""Presentation protocol tests; synthetic states are not host/visual evidence."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))

class PresentationTests(unittest.TestCase):
    def view(self, action, **changes):
        import experience
        state={'status':'in_progress','reviews':[], 'render_result':None}
        state.update(changes)
        return experience.describe(state, action)

    def test_unknown_and_working_provide_safe_distinct_recovery(self):
        unknown=self.view('INVESTIGATE_RENDER')
        self.assertIn('不会重复生成',unknown['message'])
        self.assertEqual(unknown['recovery'],'查询原任务结果')
        self.assertFalse(unknown['render_retry_allowed'])
        working=self.view('POLL_RENDER')
        self.assertIn('仍在进行',working['message'])
        self.assertFalse(working['render_retry_allowed'])

    def test_unreviewed_file_is_not_claimed_visually_checked(self):
        view=self.view('REVIEW_OUTPUT',render_result={'acquired':{'path':'fixture.png'}})
        self.assertIn('等待检查',view['message'])
        self.assertFalse(view['quality_accepted'])

    def test_display_and_save_are_independent(self):
        state={'status':'accepted','platform_delivery':{'display':{'status':'observed'},'save':{'status':'pending_confirmation'}}}
        view=self.view('AWAIT_PLATFORM_SAVE_CONFIRMATION',**state)
        self.assertTrue(view['display_observed']);self.assertFalse(view['persistence_confirmed'])
        self.assertEqual(view['save_message'],'成片已生成，保存状态待确认。')
        state['delivery_receipt']={'file_id':'synthetic-receipt'}
        self.assertEqual(self.view('BUILD_RECORD',**state)['save_message'],'成片已保存。')

    def test_save_failure_is_not_a_render_action(self):
        view=self.view('INVESTIGATE_PHOTO_SAVE',status='accepted')
        self.assertIn('不需要重新修图',view['message'])
        self.assertEqual(view['recovery'],'核对原保存结果后重新保存')
        self.assertFalse(view['render_retry_allowed'])

    def test_hint_only_for_new_accepted_delivery_and_can_be_disabled(self):
        import experience
        state={'status':'accepted'}
        self.assertIn('更自然',experience.hint(state,new_delivery=True))
        self.assertEqual(experience.hint(state,new_delivery=False),'')
        self.assertEqual(experience.hint(state,new_delivery=True,enabled=False),'')
        self.assertEqual(experience.hint({'status':'in_progress'},new_delivery=True),'')

    def test_local_request_only_asks_region_and_goal(self):
        import experience
        self.assertEqual(experience.shortcut('局部修改')['action'],'clarify_local')
        self.assertEqual(experience.shortcut('看前后对比')['action'],'compare_existing')
        self.assertIn('真实材质',experience.shortcut('更自然')['instruction'])
        self.assertIn('构图',experience.shortcut('保持构图只调色')['protect'])

    def test_all_controller_actions_have_chinese_copy(self):
        import experience
        for action in experience.MESSAGES:
            value=self.view(action)
            self.assertNotIn(action,value['message'])
            self.assertTrue(value['recovery'])
