"""User-facing library and scene-rule behavior on synthetic fixtures."""
from pathlib import Path
import hashlib, importlib, os, sys, tempfile, unittest
from unittest.mock import patch
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts'))

class PersonalManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.root = self.base/'private'
        env = patch.dict(os.environ, {'PHOTO_FINISH_STYLE_LIBRARY': str(self.root)})
        env.start(); self.addCleanup(env.stop)
        self.photo = self.base/'source.png'; Image.new('RGB', (24, 32), (70, 90, 100)).save(self.photo)

    def test_style_partial_edit_group_pin_and_purpose_preserve_bytes(self):
        import style_library as s
        self.assertTrue(hasattr(s, 'update'), 'Style metadata editing is missing')
        saved = s.add(self.photo, 'Old name', labels=['old'], consent=True)
        changed = s.update(saved['reference_id'], title='New name', group='Travel', pinned=True,
                           use_for=['light', 'material'], note='Synthetic texture', consent=True)
        self.assertEqual(changed['title'], 'New name'); self.assertEqual(changed['labels'], ['old'])
        self.assertEqual(changed['group'], 'Travel'); self.assertTrue(changed['pinned'])
        self.assertEqual(changed['use_for'], ['light', 'material'])
        self.assertEqual(Path(changed['path']).read_bytes(), self.photo.read_bytes())
        self.assertEqual(changed['sha256'], saved['sha256'])
        self.assertEqual(s.list_references(group='Travel')['total'], 1)
        self.assertEqual(s.list_references(group='Other')['total'], 0)
        s.update(saved['reference_id'], group='', pinned=False, use_for=[], consent=True)
        self.assertEqual(s.list_references(pinned_only=True)['total'], 0)

    def test_style_edits_reject_invalid_fields_and_stale_metadata(self):
        import style_library as s
        self.assertTrue(hasattr(s, 'update'), 'Style metadata editing is missing')
        saved = s.add(self.photo, 'Original', consent=True)
        with self.assertRaises(ValueError): s.update(saved['reference_id'], title='New')
        for values in ({'pinned':'yes'}, {'use_for':['execute']}, {'title':''}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                s.update(saved['reference_id'], consent=True, **values)
        s.update(saved['reference_id'], title='Changed', consent=True)
        with self.assertRaises(ValueError):
            s.update(saved['reference_id'], title='Stale', consent=True, expected_metadata_sha256=saved['metadata_sha256'])
        with self.assertRaises(ValueError): s.records(query='Changed', style_ids=[saved['reference_id']])
        with self.assertRaises(ValueError): s.records(group='Travel', style_ids=[saved['reference_id']])
        self.assertEqual(s.list_references()['references'][0]['title'], 'Changed')

    def test_group_and_reference_purposes_reach_main_prepare(self):
        import style_library as s, photo_edit as e
        self.assertTrue(hasattr(s, 'update'), 'Style metadata editing is missing')
        saved=s.add(self.photo, 'Synthetic reference', consent=True)
        s.update(saved['reference_id'], group='Travel', use_for=['light'], consent=True)
        direction=dict(intent='Synthetic scene',hierarchy='flat field',light_material='synthetic RGB',
                       output_use='screen',route='creative',qa_focus=['fixture'])
        result=e.prepare(ROOT/'runtime',self.photo,self.base/'job.json',direction,[],style_group='Travel')
        self.assertEqual(result['candidates'][0]['group'], 'Travel')
        self.assertEqual(result['candidates'][0]['use_for'], ['light'])

    def test_scoped_rule_enable_edit_and_undo(self):
        import user_preferences as p
        self.assertTrue(hasattr(p, 'add_rule'), 'Scoped rules are missing')
        p.save(rules=['Global rule'], preferences=['Global preference'], consent=True)
        result=p.add_rule('Night rule', scenes=['F'], consent=True); rid=result['created_rule_id']
        night=p.show(scenes=['F']); day=p.show(scenes=['A'])
        self.assertEqual(night['active_rules'], ['Global rule', 'Night rule'])
        self.assertEqual(day['active_rules'], ['Global rule'])
        p.update_rule(rid, enabled=False, consent=True)
        self.assertEqual(p.show(scenes=['F'])['active_rules'], ['Global rule'])
        p.undo(consent=True)
        self.assertEqual(p.show(scenes=['F'])['active_rules'], ['Global rule', 'Night rule'])
        p.update_rule(rid, text='Updated rule', scenes=['product'], consent=True)
        self.assertEqual(p.show(scenes=['product'])['active_rules'], ['Global rule', 'Updated rule'])
        p.remove_rule(rid, consent=True)
        self.assertEqual(p.show(scenes=['product'])['active_rules'], ['Global rule'])

    def test_scene_acknowledgment_and_structured_conflicts(self):
        import user_preferences as p, photo_edit as e
        self.assertTrue(hasattr(p, 'add_rule'), 'Scoped rules are missing')
        p.add_rule('Warm direction', scenes=['F'], setting='palette', value='warm', consent=True)
        p.add_rule('Cool direction', scenes=['F'], setting='palette', value='cool', consent=True)
        profile=p.show(scenes=['F'])
        self.assertEqual(profile['conflicts'][0]['setting'], 'palette')
        direction=dict(intent='Synthetic scene',hierarchy='flat field',light_material='synthetic RGB',
                       output_use='screen',route='creative',qa_focus=['fixture'])
        with self.assertRaises(ValueError):
            e.prepare(ROOT/'runtime',self.photo,self.base/'blocked.json',direction,['F'],observed_profile_sha256=profile['sha256'])
        self.assertFalse((self.base/'blocked.json').exists())
        result=e.prepare(ROOT/'runtime',self.photo,self.base/'resolved.json',direction,['F'],
                         observed_profile_sha256=profile['sha256'],task_settings={'palette':'cool'})
        self.assertEqual(result['customization']['task_settings'], {'palette':'cool'})
        wrong=p.show(scenes=['A'])
        with self.assertRaises(ValueError):
            e.prepare(ROOT/'runtime',self.photo,self.base/'wrong.json',direction,['F'],observed_profile_sha256=wrong['sha256'])

    def test_profile_reset_clears_scoped_rules_and_undo_history(self):
        import user_preferences as p, style_library as s
        self.assertTrue(hasattr(p, 'add_rule'), 'Scoped rules are missing')
        photo=s.add(self.photo, 'Synthetic photo', consent=True)
        p.add_rule('Synthetic private scoped instruction', scenes=['F'], consent=True)
        self.assertTrue(p.history()['revisions'])
        p.reset(consent=True)
        self.assertEqual(p.show()['scoped_rules'], [])
        self.assertEqual(p.history()['revisions'], [])
        with self.assertRaises(ValueError): p.undo(consent=True)
        self.assertTrue(Path(photo['path']).is_file())

    def test_saved_reference_purpose_limits_selected_components(self):
        import style_library as s,photo_edit as e
        saved=s.add(self.photo,'Light only',consent=True)
        s.update(saved['reference_id'],use_for=['light'],consent=True)
        direction=dict(intent='Synthetic scene',hierarchy='flat field',light_material='synthetic RGB',
                       output_use='screen',route='creative',qa_focus=['fixture'])
        job=self.base/'purpose.json';e.prepare(ROOT/'runtime',self.photo,job,direction,[])
        before=job.read_bytes()
        decision=dict(reference_id=saved['reference_id'],decision='partial',viewed=True,scope='Synthetic light scope',reason='Synthetic observation',uses=['color'])
        def submit(): return e.submit(job,{'requirements':[],'reason':'Synthetic blank'},
            {'branch':'PARTIAL','decisions':[decision],'reason':'Synthetic selection'},'SYNTHETIC_TOOL',{'prompt':'fixture'},{})
        with self.assertRaises(ValueError):submit()
        self.assertEqual(job.read_bytes(),before)
        decision['uses']=['light'];self.assertTrue(submit()['call_actual_tool_once'])

if __name__=='__main__': unittest.main()
