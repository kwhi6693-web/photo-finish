"""Synthetic adapter routing regressions; no actual mask/editor/visual pass is claimed."""
import time
import unittest
from PIL import Image

try:  # The installed smoke loader supplies this module without a repository on sys.path.
    import test_versions as version_fixtures
except ModuleNotFoundError:
    import tests.test_versions as version_fixtures
import photo_edit as e
import workflow_session as w
import delivery_adapter as adapter
import delivery_automation as automation
import task_history as history


class LocalRouteTests(unittest.TestCase):
    setUp = version_fixtures.VersionTests.setUp
    submit = version_fixtures.VersionTests.submit
    returned = version_fixtures.VersionTests.returned
    events = version_fixtures.VersionTests.events
    accepted = version_fixtures.VersionTests.accepted

    def child(self, name, local=True):
        if not hasattr(self, 'parent_row'):
            self.parent_row = self.accepted()
        path = self.base / (name + '.json')
        result = history.revise(self.session, self.parent_row['series'], 'V1', path,
                                'Synthetic sky-only request', local=local)
        direction = {k: result['inherited_direction'][k] for k in
                     ('intent', 'hierarchy', 'light_material', 'output_use', 'route', 'qa_focus')}
        fidelity = {target: {'strategy': 'local_excluded', 'capability_basis': 'Synthetic route fixture only',
                            'repair_route': 'Keep the accepted parent when unavailable'}
                    for target in result['protected_regions']}
        return path, result, direction, fidelity

    def send(self, path, result, direction, fidelity, name, arguments):
        return e.submit(path, result['protections'],
                        {'branch': 'PROFESSIONAL_FALLBACK', 'decisions': [], 'reason': 'Synthetic'},
                        name, arguments, result['protected_regions'], direction=direction, fidelity=fidelity)

    def test_local_native_missing_blank_nested_and_nontext_mask_rejected_atomically(self):
        for i, mask in enumerate((None, '', ' ', [], True, {'maskURI': 'synthetic'})):
            with self.subTest(mask=mask):
                path, result, direction, fidelity = self.child('mask-' + str(i))
                before = path.read_bytes(); parent = self.job.read_bytes(); photo = self.output.read_bytes()
                args = {'imageURIs': ['https://example.invalid/source.png'], 'options': {'highlights': -10}}
                if mask is not None: args['maskURI'] = mask
                with self.assertRaisesRegex(ValueError, 'region-mask'):
                    self.send(path, result, direction, fidelity, 'image_apply_adjustments', args)
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(self.job.read_bytes(), parent)
                self.assertEqual(self.output.read_bytes(), photo)

    def test_unknown_local_editor_cannot_claim_mask_support(self):
        path, result, direction, fidelity = self.child('unknown')
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'region-mask'):
            self.send(path, result, direction, fidelity, 'UNVERIFIED_EDITOR', {'maskURI': 'synthetic'})
        self.assertEqual(path.read_bytes(), before)

    def test_low_level_begin_cannot_bypass_local_full_frame_block(self):
        path, result, direction, _ = self.child('low-level')
        w.transact(path, [{'action': 'protect', 'arguments': result['protections']},
                          {'action': 'select', 'arguments': {'branch': 'PROFESSIONAL_FALLBACK',
                                                           'decisions': [], 'reason': 'Synthetic'}}])
        automation.direction(path, **direction)
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'region-mask'):
            adapter.begin(path, 'tools.image_gen__imagegen', {'prompt': 'Synthetic sky'},
                          protected_regions=result['protected_regions'])
        self.assertEqual(path.read_bytes(), before)

    def test_documented_namespaced_native_route_binds_mask_argument(self):
        for i, name in enumerate(('image_apply_adjustments', 'adobe.image_apply_adjustments',
                                  'mcp__codex_apps__adobe_image_apply_adjustments',
                                  'tools.mcp__codex_apps__adobe_image_apply_adjustments')):
            with self.subTest(name=name):
                path, result, direction, fidelity = self.child('valid-' + str(i))
                args = {'imageURIs': ['https://example.invalid/source.png'],
                        'maskURI': 'https://example.invalid/synthetic-mask.png',
                        'options': {'highlights': -10}, 'outputFileType': 'png'}
                token = self.send(path, result, direction, fidelity, name, args)
                state = w._load(path)
                self.assertEqual(state['render_result']['recipe']['actual_arguments'], args)
                self.assertEqual(state['render_result']['submission_id'], token['submission_id'])
                self.assertEqual(state['render_result']['status'], 'unknown')

    def test_local_next_step_cannot_switch_to_unmasked_or_full_frame_editor(self):
        path, result, direction, fidelity = self.child('next')
        token = self.send(path, result, direction, fidelity, 'image_apply_adjustments',
                          {'maskURI': 'https://example.invalid/synthetic-mask.png', 'options': {}})
        output = self.base / 'synthetic-next.png'
        Image.new('RGB', (32, 48), (80, 100, 110)).save(output)
        now = time.time_ns()
        e.returned(path, token['submission_id'], 'ready', now, now + 10, output_path=output)
        w.add_review(path, output_path=output, input_sha256=w._file(self.output)['sha256'],
                     visual_passed=True, profile_passed=False, color_scope='screen_srgb_assumed',
                     color_assumption_reason='Synthetic screen fixture', note='Synthetic protocol review')
        for name in ('image_apply_adjustments', 'image_gen.imagegen'):
            before = path.read_bytes()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'region-mask'):
                adapter.next_step(path, name, {'prompt': 'Synthetic unmasked next step'})
            self.assertEqual(path.read_bytes(), before)

    def test_nonlocal_native_full_frame_adjustment_still_allowed(self):
        path, result, direction, fidelity = self.child('global', local=False)
        token = self.send(path, result, direction, fidelity, 'image_apply_adjustments',
                          {'options': {'exposure': 0.2}})
        self.assertEqual(w._load(path)['render_result']['submission_id'], token['submission_id'])
