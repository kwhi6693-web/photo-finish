"""Synthetic contract tests only: no photographic improvement or host edit is certified."""
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/10_SYSTEM_CONFIG/scripts'))
import photo_edit as edit
import workflow_session as ledger
import verify_photo_edit as fixtures


AXES = ('composition', 'light', 'color', 'material')


def example_plan():
    return {
        axis: {
            'source_observation': 'Observed synthetic source ' + axis,
            'decision': 'improve' if axis == 'light' else 'preserve',
            'planned_action': 'Change light hierarchy with supported tool' if axis == 'light'
                              else 'Keep useful original ' + axis,
            'success_signal': 'Visible source-to-output ' + axis + ' comparison'
        } for axis in AXES
    }


def example_assessment(plan):
    return {axis: {
        'outcome': 'improved' if plan[axis]['decision'] == 'improve' else 'preserved',
        'source_comparison': 'Synthetic source ' + axis + ' baseline explicitly examined',
        'observed_result': 'Synthetic result ' + axis + ' inspected separately',
        'actual_action': 'Synthetic source-bound tool edit or preservation of ' + axis
    } for axis in AXES}


class ExpressionAcceptanceTests(unittest.TestCase):
    setUp = fixtures.LeanEditTests.setUp

    def live_job(self):
        path = self.base / 'live-expression-job.json'
        response = edit.prepare(self.root, self.source, path, tags=[],
                                evaluation_kind='live')
        self.assertTrue(response['direction_status']['expression_plan_required'])
        return path

    def directed(self, plan):
        return dict(self.direction, expression_plan=plan)

    def submit_live(self, path, plan):
        return edit.submit(
            path,
            {'requirements': [], 'reason': 'No protected targets in synthetic fixture'},
            {'branch': 'PROFESSIONAL_FALLBACK', 'decisions': [], 'reason': 'Synthetic no reference'},
            'SYNTHETIC_TOOL', {'prompt': 'No actual photograph editing was performed'}, {},
            direction=self.directed(plan))

    def ready_live(self, path, plan):
        ticket = self.submit_live(path, plan)
        now = time.time_ns()
        edit.returned(path, ticket['submission_id'], 'ready', now, now + 10,
                      output_path=self.output, presented=False)

    def review_events(self, plan, assessment):
        return [{'action': 'review', 'arguments': {
            'output_path': str(self.output),
            'input_sha256': ledger._file(self.source)['sha256'],
            'visual_passed': True, 'profile_passed': False,
            'color_scope': 'screen_srgb_assumed',
            'color_assumption_reason': 'Synthetic screen-only color fixture',
            'note': 'Synthetic workflow judgment, not an actual photographic assessment',
            'expression_assessment': assessment}}]

    def test_live_missing_plan_rejected_before_tool_reservation(self):
        path = self.live_job()
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'expression_plan'):
            self.submit_live(path, None)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse(ledger._load(path).get('render_result'))

    def test_plan_requires_four_explicit_dimensions_and_an_improvement(self):
        plan = example_plan()
        for bad in ({'light': plan['light']},
                    {key: dict(value, decision='preserve') for key, value in plan.items()},
                    {**plan, 'light': dict(plan['light'], success_signal='')}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ledger.validate_expression_plan(bad)
        self.assertEqual(set(ledger.validate_expression_plan(plan)), set(AXES))

    def test_live_missing_or_failed_evidence_never_accepts_v1(self):
        plan = example_plan()
        path = self.live_job()
        self.ready_live(path, plan)
        valid = example_assessment(plan)
        for payload in (None, {**valid, 'light': dict(valid['light'], outcome='unverified')},
                        {**valid, 'light': dict(valid['light'], outcome='preserved')},
                        {**valid, 'color': dict(valid['color'], observed_result='')}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                edit.review(path, self.review_events(plan, payload), self.output)
            self.assertEqual(ledger._load(path)['status'], 'in_progress')
            self.assertFalse(ledger._load(path)['reviews'])

    def test_live_complete_human_claim_is_hash_bound_but_not_quality_certification(self):
        plan = example_plan()
        path = self.live_job()
        self.ready_live(path, plan)
        response = edit.review(path, self.review_events(plan, example_assessment(plan)), self.output)
        state = ledger._load(path)
        self.assertEqual(state['status'], 'accepted')
        self.assertEqual(set(state['reviews'][-1]['expression_assessment']), set(AXES))
        self.assertFalse(state['professional_direction']['quality_certified'])
        self.assertEqual(state['output']['sha256'], ledger._file(self.output)['sha256'])
        self.assertIn('quality_observation', response)

    def test_legacy_synthetic_tasks_remain_compatible(self):
        ticket = fixtures.LeanEditTests.submit(self)
        fixtures.LeanEditTests.returned(self, ticket, presented=False)
        edit.review(self.job, fixtures.LeanEditTests.events(self), self.output)
        self.assertEqual(ledger._load(self.job)['status'], 'accepted')
        self.assertNotIn('expression_protocol', ledger._load(self.job))


if __name__ == '__main__':
    unittest.main()
