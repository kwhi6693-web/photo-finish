"""Real synthetic workflows for reference-before-direction and optional guidance."""
from pathlib import Path
import json, os, subprocess, sys, tempfile, unittest
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts'))
import photo_edit as edit
import user_preferences as profiles
import style_library as styles
import workflow_session as jobs
import delivery_automation as automation


class ReferenceFirstTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.private = self.base/'private'
        env = patch.dict(os.environ, {'PHOTO_FINISH_STYLE_LIBRARY':str(self.private)})
        env.start(); self.addCleanup(env.stop)
        self.source = self.base/'source.png'; Image.new('RGB',(24,32),(30,70,90)).save(self.source)
        self.job = self.base/'job.json'
        self.direction = dict(intent='Synthetic final direction',hierarchy='fixture subject',
            light_material='fixture light',output_use='screen',route='creative',qa_focus=['fixture'])
        self.protections = {'requirements':[],'reason':'Synthetic fixture has no protected targets'}
        self.fallback = {'branch':'PROFESSIONAL_FALLBACK','decisions':[],'reason':'No suitable reference'}

    def prepare(self, **extra):
        return edit.prepare(ROOT/'runtime',self.source,self.job,tags=[],evaluation_kind='synthetic',**extra)

    def submit(self, selection=None, **extra):
        return edit.submit(self.job,self.protections,selection or self.fallback,
                           'SYNTHETIC_TOOL',{'prompt':'Synthetic actual recipe'},{},**extra)

    def collect(self):
        image=self.base/'reference.png';Image.new('RGB',(32,24),(150,100,50)).save(image)
        saved=styles.add(image,'Synthetic wood light',tags=['A'],note='soft wood light',consent=True)
        styles.update(saved['reference_id'],use_for=['light','material'],consent=True)
        return saved

    def selected(self, rid, viewed=True):
        return {'branch':'PARTIAL','reason':'Borrow only suitable fixture light',
                'decisions':[{'reference_id':rid,'decision':'partial','viewed':viewed,
                              'scope':'fixture','reason':'Actual fixture observation','uses':['light']}]}

    def test_cli_prepare_returns_candidates_without_locking_direction(self):
        saved=self.collect()
        result=subprocess.run([sys.executable,str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts/photo_edit.py'),'prepare'],
            input=json.dumps({'project_root':str(ROOT/'runtime'),'source_path':str(self.source),
                              'path':str(self.job),'tags':['A'],'evaluation_kind':'synthetic'}),
            text=True,encoding='utf-8',capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        receipt=json.loads(result.stdout)
        self.assertEqual(receipt['candidates'][0]['reference_id'],saved['reference_id'])
        self.assertFalse(jobs._load(self.job).get('professional_direction'))
        self.assertEqual(receipt['next']['action'],'SELECT_REFERENCES_AND_DIRECTION')

    def test_final_direction_is_bound_after_viewed_partial_selection(self):
        saved=self.collect();before=self.source.read_bytes();self.prepare()
        self.submit(self.selected(saved['reference_id']),direction=self.direction)
        state=jobs._load(self.job)
        self.assertEqual(state['professional_direction']['intent'],'Synthetic final direction')
        self.assertEqual(state['professional_direction']['reference_branch'],'PARTIAL')
        self.assertEqual(state['reference_selection']['decisions'][0]['uses'],['light'])
        self.assertEqual(self.source.read_bytes(),before)

    def test_unviewed_selection_rolls_back_direction_and_submission(self):
        saved=self.collect();self.prepare();before=self.job.read_bytes()
        with self.assertRaisesRegex(ValueError,'visual inspection'):
            self.submit(self.selected(saved['reference_id'],False),direction=self.direction)
        self.assertEqual(self.job.read_bytes(),before)

    def test_missing_or_invalid_final_direction_can_be_corrected_without_partial_commit(self):
        self.prepare();before=self.job.read_bytes()
        for direction in (None,dict(self.direction,route='invalid')):
            with self.subTest(direction=direction),self.assertRaises(ValueError):
                self.submit(direction=direction)
            self.assertEqual(self.job.read_bytes(),before)
        self.submit(direction=self.direction)
        self.assertTrue(jobs._load(self.job)['render_result']['submission_id'])

    def test_legacy_prepare_direction_is_provisional_and_submit_can_replace_it(self):
        self.prepare(direction=dict(self.direction,intent='Earlier draft'))
        self.assertFalse(jobs._load(self.job).get('professional_direction'))
        self.submit(direction=self.direction)
        self.assertEqual(jobs._load(self.job)['professional_direction']['intent'],'Synthetic final direction')

    def test_legacy_prepare_draft_remains_usable_at_submit(self):
        self.prepare(direction=self.direction);self.submit()
        self.assertEqual(jobs._load(self.job)['professional_direction']['reference_branch'],'PROFESSIONAL_FALLBACK')

    def test_adopted_reference_needs_final_direction_instead_of_silent_draft_reuse(self):
        saved=self.collect();self.prepare(direction=self.direction);before=self.job.read_bytes()
        with self.assertRaisesRegex(ValueError,'final photographic direction'):
            self.submit(self.selected(saved['reference_id']))
        self.assertEqual(self.job.read_bytes(),before)

    def test_locked_direction_prevents_later_reference_replacement(self):
        self.prepare();self.submit(direction=self.direction);before=self.job.read_bytes()
        import photo_workflow
        with self.assertRaisesRegex(ValueError,'locked'):
            jobs.select_references(self.job,**self.fallback)
        with self.assertRaisesRegex(ValueError,'locked'):
            photo_workflow.candidates(self.job,ROOT/'runtime',[])
        self.assertEqual(self.job.read_bytes(),before)

    def test_explicit_corrupt_style_is_reported_without_publishing_a_fallback(self):
        saved=self.collect();Path(saved['path']).write_bytes(b'corrupt fixture')
        with self.assertRaisesRegex(ValueError,'requested personal style'):
            self.prepare(style_query='Synthetic wood')
        self.assertFalse(self.job.exists())

    def test_explicit_group_can_supply_cross_scene_partial_reference(self):
        saved=self.collect();styles.update(saved['reference_id'],group='Chosen group',consent=True)
        result=edit.prepare(ROOT/'runtime',self.source,self.job,tags=['B'],style_group='Chosen group')
        self.assertEqual([r['reference_id'] for r in result['candidates']],[saved['reference_id']])
        self.assertFalse(jobs._load(self.job).get('professional_direction'))
        self.submit(self.selected(saved['reference_id']),direction=self.direction)

    def test_low_level_direction_cannot_lock_before_reference_decision(self):
        self.prepare(direction=self.direction);before=self.job.read_bytes()
        with self.assertRaisesRegex(ValueError,'reference selection'):
            automation.direction(self.job,**self.direction)
        self.assertEqual(self.job.read_bytes(),before)

    def test_explicit_missing_style_query_and_group_do_not_publish_fallback_jobs(self):
        for selector in ({'style_query':'missing named style'},{'style_group':'missing group'}):
            with self.subTest(selector=selector),self.assertRaisesRegex(ValueError,'requested personal style'):
                self.prepare(direction=self.direction,**selector)
            self.assertFalse(self.job.exists())
        self.assertFalse(self.private.exists())

    def test_autonomous_and_guided_judgment_never_create_or_rewrite_saved_rules(self):
        result=self.prepare()
        self.assertEqual(result['customization']['professional_judgment']['mode'],'autonomous')
        self.assertFalse(self.private.exists())
        self.job=self.base/'guided.json'
        saved=profiles.save(rules=['Keep source lettering'],consent=True)
        result=self.prepare(observed_profile_sha256=saved['sha256'],
                            task_instructions=['Use professional judgment for all other photographic choices'])
        self.assertEqual(result['customization']['professional_judgment']['mode'],'guided')
        self.submit(direction=self.direction)
        self.assertEqual(profiles.show()['rules'],['Keep source lettering'])
        self.assertEqual(profiles.show()['sha256'],saved['sha256'])


if __name__=='__main__': unittest.main()
