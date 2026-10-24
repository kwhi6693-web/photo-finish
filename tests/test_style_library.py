"""Private collection and main-flow behavior, using generated fixtures only."""
from pathlib import Path
import hashlib, importlib, json, os, sqlite3, subprocess, sys, tempfile, unittest
from unittest.mock import patch
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts'))

class StyleLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.library = self.base/'private'
        self.source = self.base/'样片.png'
        Image.new('RGB', (24, 32), (70, 90, 100)).save(self.source)
        self.env = patch.dict(os.environ, {'PHOTO_FINISH_STYLE_LIBRARY': str(self.library)})
        self.env.start(); self.addCleanup(self.env.stop)

    def module(self):
        try: return importlib.import_module('style_library')
        except ImportError: self.fail('Personal style library is not implemented')

    def collect(self, **kwargs):
        return self.module().add(source_path=self.source, title='柔光咖啡馆',
                                 labels=['柔光', '木质'], note='喜欢安静光影', consent=True, **kwargs)

    def test_collection_survives_restart_preserves_bytes_and_deduplicates(self):
        s = self.module(); first = self.collect(); again = self.collect()
        self.assertEqual(first['reference_id'], again['reference_id'])
        self.assertTrue(again['duplicate'])
        result = subprocess.run([sys.executable, str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts/photo_edit.py'), 'style-list'],
            input=b'{}', capture_output=True, env=dict(os.environ, PYTHONIOENCODING='ascii'))
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8'))
        found = json.loads(result.stdout)['references']; self.assertEqual(len(found), 1)
        stored = Path(found[0]['path']); self.assertEqual(stored.read_bytes(), self.source.read_bytes())
        self.assertEqual(found[0]['sha256'], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(found[0]['labels'], ['柔光', '木质'])
        self.assertEqual(s.list_references(library_root=self.base/'other')['references'], [])
        self.assertFalse((self.base/'other').exists())

    def test_empty_lookup_does_not_create_files(self):
        self.assertEqual(self.module().list_references()['references'], [])
        self.assertFalse(self.library.exists())

    def test_collection_requires_consent_valid_image_and_private_location(self):
        s = self.module()
        for consent in (False, 'yes', 1, None):
            with self.subTest(consent=consent), self.assertRaises(ValueError):
                s.add(self.source, 'sample', consent=consent)
        bad = self.base/'invalid.png'; bad.write_text('not a photograph')
        with self.assertRaises((ValueError, OSError)): s.add(bad, 'bad', consent=True)
        for root in (ROOT/'work/styles', ROOT/'runtime/styles'):
            with self.subTest(root=root), self.assertRaises(ValueError):
                s.add(self.source, 'bad root', consent=True, library_root=root)
        self.assertFalse(self.library.exists())

    def test_keyword_explicit_ids_removal_and_isolation(self):
        s = self.module(); first = self.collect()
        other = self.base/'night.png'; Image.new('RGB', (20, 20), (10, 15, 25)).save(other)
        second = s.add(other, '夜景霓虹', labels=['夜景'], consent=True)
        found = s.list_references(query='木质')['references']
        self.assertEqual([r['reference_id'] for r in found], [first['reference_id']])
        self.assertEqual([r['id'] for r in s.records(style_ids=[second['reference_id']])], [second['reference_id']])
        with self.assertRaises(ValueError): s.records(style_ids=['unknown'])
        s.remove(first['reference_id'])
        self.assertFalse(Path(first['path']).exists())
        self.assertEqual(len(s.list_references()['references']), 1)
        with self.assertRaises(ValueError): s.remove(first['reference_id'])

    def test_prepare_automatically_retrieves_and_submit_rejects_changed_style(self):
        import photo_edit as e
        self.module(); collected = self.collect()
        job = self.base/'job.json'
        direction = dict(intent='Synthetic scene', hierarchy='flat field', light_material='synthetic RGB',
                         output_use='screen', route='creative', qa_focus=['fixture'])
        prepared = e.prepare(ROOT/'runtime', self.source, job, direction, [], style_query='木质')
        self.assertEqual([r['reference_id'] for r in prepared['candidates']], [collected['reference_id']])
        self.assertEqual(prepared['candidates'][0]['path'], collected['path'])
        before = job.read_bytes()
        Image.new('RGB', (24, 32), (200, 30, 10)).save(collected['path'])
        with self.assertRaisesRegex(ValueError, 'changed'):
            e.submit(job, {'requirements': [], 'reason': 'Synthetic blank'},
                {'branch': 'MATCHED', 'decisions': [dict(reference_id=collected['reference_id'], decision='adopt',
                    viewed=True, scope='light', reason='Synthetic inspection')], 'reason': 'Synthetic selection'},
                'SYNTHETIC_TOOL', {'prompt': 'synthetic'}, {})
        self.assertEqual(job.read_bytes(), before)

    def test_default_prepare_does_not_collect_the_edit_target(self):
        import photo_edit as e
        self.module()
        direction = dict(intent='Synthetic scene', hierarchy='flat field', light_material='synthetic RGB',
                         output_use='screen', route='creative', qa_focus=['fixture'])
        result = e.prepare(ROOT/'runtime', self.source, self.base/'empty.json', direction, [])
        self.assertEqual(result['candidates'], [])
        self.assertFalse(self.library.exists())

    def test_selected_style_remains_bound_after_submission(self):
        import photo_edit as e
        import time
        self.module(); collected = self.collect(); job = self.base/'bound.json'
        direction = dict(intent='Synthetic scene', hierarchy='flat field', light_material='synthetic RGB',
                         output_use='screen', route='creative', qa_focus=['fixture'])
        e.prepare(ROOT/'runtime', self.source, job, direction, [], style_ids=[collected['reference_id']])
        ticket = e.submit(job, {'requirements': [], 'reason': 'Synthetic blank'},
            {'branch': 'MATCHED', 'decisions': [dict(reference_id=collected['reference_id'], decision='adopt',
                viewed=True, scope='light', reason='Synthetic inspection')], 'reason': 'Synthetic selection'},
            'SYNTHETIC_TOOL', {'prompt': 'synthetic'}, {}, direction=direction)
        before = job.read_bytes()
        Path(collected['path']).unlink()
        now = time.time_ns()
        with self.assertRaisesRegex(ValueError, 'changed'):
            e.returned(job, ticket['submission_id'], 'working', now, now+1, task_id='synthetic')
        self.assertEqual(job.read_bytes(), before)

    def test_corrupt_catalog_is_reported_instead_of_empty_fallback(self):
        self.module(); self.library.mkdir(); (self.library/'catalog.sqlite3').write_bytes(b'invalid catalog')
        with self.assertRaisesRegex(ValueError, 'catalog'):
            self.module().list_references()

    def test_scene_hints_can_be_overridden_with_explicit_style_ids(self):
        import photo_edit as e
        s = self.module()
        first = s.add(self.source, 'Synthetic tagged style', tags=['A'], consent=True)
        direction = dict(intent='Synthetic scene', hierarchy='flat field', light_material='synthetic RGB',
                         output_use='screen', route='creative', qa_focus=['fixture'])
        automatic = e.prepare(ROOT/'runtime', self.source, self.base/'auto.json', direction, ['B'])
        self.assertEqual(automatic['candidates'], [])
        explicit = e.prepare(ROOT/'runtime', self.source, self.base/'explicit.json', direction, ['B'],
                             style_ids=[first['reference_id']])
        self.assertEqual([r['reference_id'] for r in explicit['candidates']], [first['reference_id']])

    def test_adopted_style_completes_existing_review_protocol(self):
        import photo_edit as e
        import time
        self.module(); collected = self.collect(); job = self.base/'complete.json'
        direction = dict(intent='Synthetic scene', hierarchy='flat field', light_material='synthetic RGB',
                         output_use='screen', route='creative', qa_focus=['fixture'])
        e.prepare(ROOT/'runtime', self.source, job, direction, [])
        ticket = e.submit(job, {'requirements': [], 'reason': 'Synthetic blank'},
            {'branch': 'PARTIAL', 'decisions': [dict(reference_id=collected['reference_id'], decision='partial',
                viewed=True, scope='light', reason='Synthetic inspection')], 'reason': 'Synthetic selection'},
            'SYNTHETIC_TOOL', {'prompt': 'synthetic', 'referenced_image_paths': [str(self.source), collected['path']]}, {},
            input_references=[{'path': collected['path'], 'role': 'style_reference'}], direction=direction)
        output = self.base/'result.png'; Image.new('RGB', (24, 32), (80, 100, 110)).save(output)
        now = time.time_ns()
        e.returned(job, ticket['submission_id'], 'ready', now, now+1, output_path=output, presented=True)
        events = [{'action': 'review', 'arguments': dict(output_path=str(output),
            input_sha256=hashlib.sha256(self.source.read_bytes()).hexdigest(), visual_passed=True,
            profile_passed=False, color_scope='screen_srgb_assumed',
            color_assumption_reason='Synthetic ordinary screen fixture; not calibration',
            note='Synthetic protocol review, not actual photographic quality evidence')}]
        result = e.review(job, events, output)
        self.assertEqual(result['next']['action'], 'AWAIT_PLATFORM_SAVE_CONFIRMATION')

    def test_profiled_non_rgb_image_uses_its_original_color_mode(self):
        s = self.module(); source = self.base/'lab.tiff'
        profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('LAB')).tobytes()
        Image.new('LAB', (24, 32), (140, 130, 125)).save(source, icc_profile=profile)
        saved = s.add(source, 'Synthetic Lab reference', consent=True)
        self.assertEqual(Path(saved['path']).read_bytes(), source.read_bytes())
        self.assertEqual(len(s.list_references()['references']), 1)

    def test_failed_color_measurement_does_not_leave_unindexed_photographs(self):
        s = self.module(); source = self.base/'invalid-profile.png'
        Image.new('RGB', (24, 32), (70, 90, 100)).save(source, icc_profile=b'invalid ICC')
        with self.assertRaises(ValueError): s.add(source, 'Invalid profile', consent=True)
        self.assertFalse(self.library.exists())

    def test_explicit_ids_and_keyword_require_one_unambiguous_selector(self):
        s = self.module(); saved = self.collect()
        with self.assertRaises(ValueError):
            s.records(query='nonmatching keyword', style_ids=[saved['reference_id']])

    def test_full_catalog_rolls_back_new_copy_but_preserves_preexisting_bytes(self):
        s = self.module(); connect = sqlite3.connect
        def limited(*args, **kwargs):
            connection = connect(*args, **kwargs)
            connection.execute('PRAGMA max_page_count=3')
            return connection
        # Three pages fit the schema but cannot fit this valid catalog entry.
        for preexisting in (False, True):
            root = self.base/('preexisting' if preexisting else 'new-copy')
            digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
            target = root/'images'/(digest+'.png')
            if preexisting:
                target.parent.mkdir(parents=True); target.write_bytes(self.source.read_bytes())
            with self.subTest(preexisting=preexisting), patch.object(s.sqlite3, 'connect', limited):
                with self.assertRaisesRegex(ValueError, 'catalog'):
                    s.add(self.source, 'Synthetic quota fixture', consent=True, library_root=root,
                          labels=[str(i)+'x'*75 for i in range(32)], note='x'*2000)
            self.assertEqual(target.exists(), preexisting)
            if preexisting: self.assertEqual(target.read_bytes(), self.source.read_bytes())

if __name__ == '__main__': unittest.main()
