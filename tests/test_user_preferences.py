"""Private user customization and source-bound main-flow regressions."""
from pathlib import Path
from contextlib import closing
import importlib, json, os, sqlite3, subprocess, sys, tempfile, time, unittest
from unittest.mock import patch
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts'))

class UserPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.private = self.base/'个人配置'
        self.env = patch.dict(os.environ, {'PHOTO_FINISH_STYLE_LIBRARY': str(self.private)})
        self.env.start(); self.addCleanup(self.env.stop)
        self.source = self.base/'source.png'; Image.new('RGB', (24, 32), (70, 90, 100)).save(self.source)
        self.direction = dict(intent='Synthetic task intent', hierarchy='flat field', light_material='synthetic RGB',
                              output_use='screen', route='creative', qa_focus=['fixture'])

    def module(self):
        try: return importlib.import_module('user_preferences')
        except ImportError: self.fail('Custom user instructions are not implemented')

    def test_empty_profile_is_read_only_and_isolated(self):
        p = self.module(); profile = p.show()
        self.assertEqual(profile['rules'], []); self.assertEqual(profile['preferences'], [])
        self.assertFalse(self.private.exists())
        p.save(rules=['Synthetic output rule'], consent=True)
        self.assertEqual(p.show(library_root=self.base/'other')['rules'], [])
        self.assertFalse((self.base/'other').exists())

    def test_partial_update_survives_restart_with_unicode_and_deduplication(self):
        p = self.module(); first = p.save(rules=['  保留原始文字  ', '保留原始文字'], consent=True)
        second = p.save(preferences=['柔光', '木质层次'], consent=True)
        self.assertEqual(second['rules'], ['保留原始文字']); self.assertNotEqual(first['sha256'], second['sha256'])
        result = subprocess.run([sys.executable, str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts/photo_edit.py'), 'profile-show'],
                                input=b'{}', capture_output=True, env=dict(os.environ, PYTHONIOENCODING='ascii'))
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
        restored = json.loads(result.stdout.decode('utf-8'))
        self.assertEqual(restored['rules'], ['保留原始文字']); self.assertEqual(restored['preferences'], ['柔光', '木质层次'])
        self.assertEqual(restored['sha256'], second['sha256'])

    def test_save_and_reset_require_explicit_consent_and_valid_lists(self):
        p = self.module()
        for consent in (False, 'yes', 1, None):
            with self.subTest(consent=consent), self.assertRaises(ValueError):
                p.save(rules=['Synthetic rule'], consent=consent)
        for rules in ('not a list', [''], [7], ['x'*501], ['x']*21):
            with self.subTest(rules=rules), self.assertRaises(ValueError):
                p.save(rules=rules, consent=True)
        with self.assertRaises(ValueError): p.save(consent=True)
        with self.assertRaises(ValueError): p.reset()
        with self.assertRaises(ValueError): p.save(rules=['rule'], consent=True, library_root=ROOT/'work/profile')
        self.assertFalse(self.private.exists())

    def test_clear_and_reset_preserve_the_photo_collection(self):
        p = self.module(); import style_library
        photo = style_library.add(self.source, 'Synthetic reference', consent=True)
        p.save(rules=['rule'], preferences=['preference'], consent=True)
        cleared = p.save(rules=[], consent=True)
        self.assertEqual(cleared['rules'], []); self.assertEqual(cleared['preferences'], ['preference'])
        reset = p.reset(consent=True)
        self.assertEqual(reset['rules'], []); self.assertEqual(reset['preferences'], [])
        self.assertEqual(Path(photo['path']).read_bytes(), self.source.read_bytes())
        self.assertEqual(len(style_library.list_references()['references']), 1)

    def test_corrupt_or_unsupported_profiles_are_not_overwritten_or_hidden(self):
        p = self.module(); p.save(rules=['Original rule'], consent=True)
        db = self.private/'catalog.sqlite3'
        with closing(sqlite3.connect(db)) as connection, connection:
            connection.execute("UPDATE user_preferences SET payload=? WHERE id=1", (json.dumps({'version': 99}),))
        with self.assertRaises(ValueError): p.show()
        before = db.read_bytes()
        with self.assertRaises(ValueError): p.save(preferences=['new preference'], consent=True)
        self.assertEqual(db.read_bytes(), before)

    def test_prepare_requires_current_profile_before_direction_is_locked(self):
        p = self.module(); import photo_edit
        first = p.save(rules=['Original rule'], consent=True); job = self.base/'job.json'
        with self.assertRaisesRegex(ValueError, 'profile-show'):
            photo_edit.prepare(ROOT/'runtime', self.source, job, self.direction, [])
        self.assertFalse(job.exists())
        p.save(rules=['Updated rule'], consent=True)
        with self.assertRaisesRegex(ValueError, 'profile-show'):
            photo_edit.prepare(ROOT/'runtime', self.source, job, self.direction, [], observed_profile_sha256=first['sha256'])
        self.assertFalse(job.exists())

    def test_task_instructions_and_profile_snapshot_survive_later_changes(self):
        p = self.module(); import photo_edit, workflow_session
        profile = p.save(rules=['Synthetic saved rule'], preferences=['Synthetic saved preference'], consent=True)
        job = self.base/'prepared.json'
        prepared = photo_edit.prepare(ROOT/'runtime', self.source, job, self.direction, [],
            observed_profile_sha256=profile['sha256'], task_instructions=['This task uses a different expression'])
        context = prepared['customization']
        self.assertEqual(context['profile']['rules'], ['Synthetic saved rule'])
        self.assertEqual(context['task_instructions'], ['This task uses a different expression'])
        p.reset(consent=True)
        self.assertEqual(workflow_session._load(job)['user_customization'], context)
        ticket = photo_edit.submit(job, {'requirements': [], 'reason': 'Synthetic blank'},
            {'branch': 'PROFESSIONAL_FALLBACK', 'decisions': [], 'reason': 'No style images'},
            'SYNTHETIC_TOOL', {'prompt': 'Synthetic actual arguments'}, {})
        now = time.time_ns()
        photo_edit.returned(job, ticket['submission_id'], 'working', now, now+1, task_id='synthetic')
        self.assertEqual(workflow_session._load(job)['user_customization'], context)
        self.assertEqual(p.show()['preferences'], [])

    def test_one_time_instructions_do_not_become_saved_preferences(self):
        p = self.module(); import photo_edit
        result = photo_edit.prepare(ROOT/'runtime', self.source, self.base/'once.json', self.direction, [],
                                    task_instructions=['Synthetic one-time instruction'])
        self.assertEqual(result['customization']['task_instructions'], ['Synthetic one-time instruction'])
        self.assertEqual(p.show()['rules'], []); self.assertFalse(self.private.exists())
        with self.assertRaises(ValueError):
            photo_edit.prepare(ROOT/'runtime', self.source, self.base/'bad.json', self.direction, [], task_instructions='invalid')
        self.assertFalse((self.base/'bad.json').exists())

    def test_reset_does_not_leave_old_profile_text_in_current_database_pages(self):
        p = self.module(); text = 'SyntheticPrivatePreferenceToClear_'*10
        p.save(preferences=[text], consent=True)
        p.reset(consent=True)
        self.assertEqual(p.show()['preferences'], [])
        self.assertFalse(text[:80].encode() in (self.private/'catalog.sqlite3').read_bytes(),
                         'Reset retained old profile text in current SQLite pages')

if __name__ == '__main__': unittest.main()
