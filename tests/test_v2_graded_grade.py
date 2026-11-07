"""Synthetic tests for graded (large-scale continuous) alpha, bounded chroma
shift and the split-tone global operation. No aesthetic claims.

These cover what the original 37 tests did not: a continuous alpha with no
0/255 jump, protected pixels that fade instead of cutting a step, tail
containment on the real alpha, an explicit boundary-review gate for graded
zones, and that `strong` or out-of-range grades still cannot pass.
"""
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / 'experiments' / 'v2_local_light'
RUNTIME = ROOT / 'runtime' / '10_SYSTEM_CONFIG' / 'scripts'
sys.path.insert(0, str(EXPERIMENTS))
from pixel_mask_qa import (inspect_mask, feather_mask, graded_alpha,  # noqa: E402
                           compose_only_tonal_output, verify_protected_pixels,
                           GradedAlphaReceipt, FeatherReceipt)
from multizone_editor import ToneZone, composite_zones, _sha_pixels  # noqa: E402

import tests.test_v2_global_operation as base_global  # noqa: E402

SIZE = (256, 256)


def rect(box=None, size=SIZE):
    image = Image.new('L', size, 0)
    if box:
        ImageDraw.Draw(image).rectangle(box, fill=255)
    return image


def alpha_row(image, y, x0, x1):
    return [image.getpixel((x, y)) for x in range(x0, x1)]


def max_step(image):
    w, h = image.size
    horizontal = ImageChops.difference(image.crop((1, 0, w, h)), image.crop((0, 0, w - 1, h))).getextrema()[1]
    vertical = ImageChops.difference(image.crop((0, 1, w, h)), image.crop((0, 0, w, h - 1))).getextrema()[1]
    return max(horizontal, vertical)


def fixture(protected_box=(206, 104, 214, 150)):
    subject = rect((100, 100, 156, 156))
    core = rect((110, 110, 146, 146))
    allowed = rect((8, 8, 248, 248))
    protected = rect(protected_box) if protected_box else rect()
    return subject, core, allowed, protected


class GradedAlphaTests(unittest.TestCase):
    def audit(self, **kw):
        s, c, a, p = fixture(**kw)
        return s, c, a, p, inspect_mask(s, target_core=c, allowed_zone=a, protected=p)

    def test_transition_is_wide_and_has_no_jump(self):
        s, c, a, p, audit = self.audit()
        graded = graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=p, sigma_px=24)
        self.assertIsInstance(graded, GradedAlphaReceipt)
        row = alpha_row(graded.alpha, 128, 20, 100)
        partial = [v for v in row if 0 < v < 255]
        narrow = feather_mask(s, audit=audit, allowed_zone=a, protected=p, radius_px=10)
        narrow_partial = [v for v in alpha_row(narrow.alpha, 128, 20, 100) if 0 < v < 255]
        self.assertGreater(len(partial), 2 * len(narrow_partial))
        self.assertLessEqual(max_step(graded.alpha), 12)
        self.assertEqual(graded.max_neighbor_step, max_step(graded.alpha))
        self.assertEqual(graded.alpha.getpixel((128, 128)), 255)
        self.assertEqual(graded.alpha.getpixel((2, 2)), 0)

    def test_alpha_decreases_monotonically_away_from_the_selection(self):
        s, c, a, p, audit = self.audit()
        graded = graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=p, sigma_px=24)
        row = alpha_row(graded.alpha, 128, 20, 101)
        self.assertEqual(row, sorted(row))

    def test_protected_pixels_are_exactly_zero_and_fade_without_a_step(self):
        s, c, a, p, audit = self.audit()
        graded = graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=p, sigma_px=24)
        # protected block
        for x in range(206, 215):
            for y in range(104, 151, 6):
                self.assertEqual(graded.alpha.getpixel((x, y)), 0)
        self.assertLessEqual(max_step(graded.alpha), 12)
        # Without any protection the same point would carry visible alpha.
        free = graded_alpha(s, audit=inspect_mask(s, target_core=c, allowed_zone=a, protected=rect()),
                            target_core=c, allowed_zone=a, protected=rect(), sigma_px=24)
        self.assertGreater(free.alpha.getpixel((190, 128)), graded.alpha.getpixel((190, 128)))
        self.assertGreater(graded.protected_pixel_count, 8 * 46)

    def test_tail_that_would_escape_allowed_zone_stops(self):
        s, c, a, p, audit = self.audit()
        tight = rect((70, 70, 186, 186))
        tight_audit = inspect_mask(s, target_core=c, allowed_zone=tight, protected=p)
        self.assertTrue(tight_audit.passed, tight_audit.reason)
        with self.assertRaisesRegex(ValueError, 'escape allowed region'):
            graded_alpha(s, audit=tight_audit, target_core=c, allowed_zone=tight, protected=p, sigma_px=24)

    def test_mask_audit_is_mandatory_and_bound_to_bytes(self):
        s, c, a, p, audit = self.audit()
        failed = inspect_mask(rect(), target_core=c, allowed_zone=a, protected=p)
        with self.assertRaisesRegex(ValueError, 'passing pixel mask audit'):
            graded_alpha(s, audit=failed, target_core=c, allowed_zone=a, protected=p, sigma_px=24)
        with self.assertRaisesRegex(ValueError, 'passing pixel mask audit'):
            graded_alpha(s, audit=None, target_core=c, allowed_zone=a, protected=p, sigma_px=24)
        mutated = s.copy()
        mutated.putpixel((2, 2), 255)
        with self.assertRaisesRegex(ValueError, 'changed since audit'):
            graded_alpha(mutated, audit=audit, target_core=c, allowed_zone=a, protected=p, sigma_px=24)
        other_protected = p.copy()
        other_protected.putpixel((60, 60), 255)
        with self.assertRaisesRegex(ValueError, 'changed since mask audit'):
            graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=other_protected, sigma_px=24)

    def test_parameters_are_strictly_validated(self):
        s, c, a, p, audit = self.audit()
        for sigma in (True, 3, 121, 24.0, '24', None):
            with self.subTest(sigma=sigma):
                with self.assertRaisesRegex(ValueError, 'sigma'):
                    graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=p, sigma_px=sigma)
        for kw in ({'protected_margin_px': 13}, {'protected_margin_px': True},
                   {'max_neighbor_step': 0}, {'max_neighbor_step': 65},
                   {'peak_normalize': 1}):
            with self.subTest(**kw):
                with self.assertRaises(ValueError):
                    graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=p, sigma_px=24, **kw)

    def test_too_steep_alpha_is_rejected(self):
        s, c, a, p, audit = self.audit()
        with self.assertRaisesRegex(ValueError, 'too steep'):
            graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=p, sigma_px=4,
                         max_neighbor_step=12)

    def test_selection_far_too_small_for_sigma_is_rejected(self):
        tiny = rect((126, 126, 129, 129))
        core = rect((126, 126, 129, 129))
        a, p = rect((8, 8, 248, 248)), rect()
        audit = inspect_mask(tiny, target_core=core, allowed_zone=a, protected=p)
        self.assertTrue(audit.passed, audit.reason)
        with self.assertRaisesRegex(ValueError, 'too small'):
            graded_alpha(tiny, audit=audit, target_core=core, allowed_zone=a, protected=p, sigma_px=60)

    def test_protected_content_that_quietly_suppresses_the_core_stops(self):
        # Selection sandwiched between two protected blocks 14 px away on each side.
        subject = rect((100, 50, 160, 206))
        core = rect((110, 60, 150, 196))
        allowed = rect((0, 0, 255, 255))  # whole frame, so only the core-weight rule can object
        sandwich = ImageChops.lighter(rect((76, 30, 86, 226)), rect((174, 30, 184, 226)))
        audit = inspect_mask(subject, target_core=core, allowed_zone=allowed, protected=sandwich)
        self.assertTrue(audit.passed, audit.reason)
        with self.assertRaisesRegex(ValueError, 'under-edited'):
            graded_alpha(subject, audit=audit, target_core=core, allowed_zone=allowed,
                         protected=sandwich, sigma_px=30)
        # Isolation: with the weight rule relaxed the same alpha is accepted and is smooth,
        # so the steepness rule was not what stopped it.
        relaxed = graded_alpha(subject, audit=audit, target_core=core, allowed_zone=allowed,
                               protected=sandwich, sigma_px=30, min_core_weight=0.01)
        self.assertLessEqual(relaxed.max_neighbor_step, 12)

    def test_core_must_match_the_audited_core_and_weight_bound_is_validated(self):
        s, c, a, p, audit = self.audit()
        other_core = c.copy()
        other_core.putpixel((120, 120), 0)
        with self.assertRaisesRegex(ValueError, 'target core changed'):
            graded_alpha(s, audit=audit, target_core=other_core, allowed_zone=a, protected=p, sigma_px=24)
        for weight in (0, -0.1, 1.5, True, float('nan'), '0.6', None):
            with self.subTest(weight=weight):
                with self.assertRaisesRegex(ValueError, 'min core weight'):
                    graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=p,
                                 sigma_px=24, min_core_weight=weight)

    def test_binary_feather_cap_is_unchanged(self):
        s, c, a, p, audit = self.audit()
        with self.assertRaisesRegex(ValueError, 'integer 1..10'):
            feather_mask(s, audit=audit, allowed_zone=a, protected=p, radius_px=11)

    def test_graded_receipt_composes_and_keeps_protected_pixels(self):
        s, c, a, p, audit = self.audit()
        receipt = graded_alpha(s, audit=audit, target_core=c, allowed_zone=a, protected=p, sigma_px=24)
        before = Image.new('RGB', SIZE, (30, 60, 100))
        candidate = Image.new('RGB', SIZE, (110, 90, 130))
        result = compose_only_tonal_output(before, candidate, receipt=receipt)
        self.assertTrue(verify_protected_pixels(before, result, protected=p))
        self.assertNotEqual(result.getpixel((128, 128)), before.getpixel((128, 128)))
        self.assertEqual(result.getpixel((2, 2)), before.getpixel((2, 2)))
        receipt.alpha.putpixel((128, 128), 3)
        with self.assertRaisesRegex(ValueError, 'changed after feather'):
            compose_only_tonal_output(before, candidate, receipt=receipt)

    def test_graded_receipt_is_a_feather_receipt(self):
        self.assertTrue(issubclass(GradedAlphaReceipt, FeatherReceipt))


class GradedZoneTests(unittest.TestCase):
    def setUp(self):
        self.source = Image.new('RGB', SIZE, (105, 130, 160))
        self.icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        self.source.info['icc_profile'] = self.icc
        protected = rect((232, 20, 242, 60))
        self.boat = ToneZone('boat light', rect((110, 150, 146, 186)), rect((116, 156, 140, 180)),
                             rect((40, 100, 216, 236)), protected, .80, 1.0,
                             'Lift the one lit subject so the eye lands on it first',
                             edge_mode='graded', boundary_visually_inspected=True,
                             sigma_px=12, chroma_shift=(-6.0, 6.0))
        self.bank = ToneZone('bank dark', rect((10, 120, 40, 240)), rect((14, 130, 34, 230)),
                             rect((0, 60, 100, 255)), protected, 1.25, 1.0,
                             'Quiet the heavy left bank so it frames rather than competes',
                             edge_mode='graded', boundary_visually_inspected=True,
                             sigma_px=16)
        self.args = dict(observed_source_pixel_sha256=_sha_pixels(self.source),
                         source_visually_inspected=True, masks_visually_inspected=True,
                         spatial_intent='Viewer enters past a quieter bank to the one lit boat on the water',
                         expected_icc_bytes=self.icc, geometry_id='source:G0')

    def run_zones(self, zones=None, **overrides):
        kwargs = dict(self.args)
        kwargs.update(overrides)
        return composite_zones(self.source, [self.boat, self.bank] if zones is None else zones, **kwargs)

    def test_graded_zones_edit_inside_and_leave_far_pixels_identical(self):
        out, receipt = self.run_zones()
        self.assertGreater(out.getpixel((128, 168))[1], self.source.getpixel((128, 168))[1])
        self.assertLess(out.getpixel((20, 180))[1], self.source.getpixel((20, 180))[1])
        self.assertEqual(out.getpixel((200, 20)), self.source.getpixel((200, 20)))
        self.assertEqual(out.getpixel((237, 40)), self.source.getpixel((237, 40)))
        self.assertFalse(receipt['photographic_quality_accepted'])
        by_name = {z['name']: z for z in receipt['zones']}
        self.assertEqual(by_name['boat light']['edge_mode'], 'graded')
        self.assertEqual(by_name['boat light']['sigma_px'], 12)
        self.assertLessEqual(by_name['boat light']['max_neighbor_step'], 12)
        self.assertEqual(by_name['boat light']['chroma_shift'], [-6.0, 6.0])
        self.assertNotIn('chroma_shift', by_name['bank dark'])

    def test_the_edit_has_no_hard_step_anywhere(self):
        out, _ = self.run_zones()
        diff = ImageChops.difference(out, self.source)
        for band in diff.split():
            self.assertLessEqual(max_step(band), 14)

    def test_warm_chroma_shift_moves_red_up_and_blue_down_only_in_zone(self):
        warm, _ = self.run_zones()
        neutral_boat = replace(self.boat, chroma_shift=(0.0, 0.0))
        plain, _ = self.run_zones([neutral_boat, self.bank])
        r_w, g_w, b_w = warm.getpixel((128, 168))
        r_n, g_n, b_n = plain.getpixel((128, 168))
        self.assertGreater(r_w, r_n)
        self.assertLess(b_w, b_n)
        self.assertEqual(warm.getpixel((20, 180)), plain.getpixel((20, 180)))

    def test_deterministic(self):
        first, _ = self.run_zones()
        second, _ = self.run_zones()
        self.assertEqual(_sha_pixels(first), _sha_pixels(second))

    def test_graded_zone_needs_real_boundary_inspection(self):
        with self.assertRaisesRegex(ValueError, 'mask-boundary inspection'):
            self.run_zones([replace(self.boat, boundary_visually_inspected=False), self.bank])
        with self.assertRaisesRegex(ValueError, 'mask-boundary inspection'):
            self.run_zones([replace(self.boat, boundary_visually_inspected='yes'), self.bank])

    def test_graded_zone_needs_a_valid_sigma(self):
        for sigma in (0, 3, 121, 12.0, True):
            with self.subTest(sigma=sigma):
                with self.assertRaisesRegex(ValueError, 'sigma'):
                    self.run_zones([replace(self.boat, sigma_px=sigma), self.bank])

    def test_sigma_is_rejected_on_non_graded_zones(self):
        with self.assertRaisesRegex(ValueError, 'sigma_px is only valid'):
            self.run_zones([replace(self.boat, edge_mode='soft', sigma_px=12), self.bank])

    def test_unbounded_or_malformed_chroma_shift_fails(self):
        for shift in ((13.0, 0.0), (0.0, -12.5), (float('nan'), 0.0), (1.0,), 'warm',
                      (1.0, 2.0, 3.0), (True, 0.0), None):
            with self.subTest(shift=shift):
                with self.assertRaisesRegex(ValueError, 'chroma shift'):
                    self.run_zones([replace(self.boat, chroma_shift=shift), self.bank])

    def test_grade_bounds_still_apply_to_graded_zones(self):
        with self.assertRaisesRegex(ValueError, 'grade strength'):
            self.run_zones([replace(self.boat, gamma=0.3), self.bank])

    def test_graded_tail_escaping_allowed_region_stops(self):
        tight = replace(self.boat, allowed=rect((100, 140, 156, 196)))
        with self.assertRaisesRegex(ValueError, 'escape allowed region|allowed'):
            self.run_zones([tight, self.bank])

    def test_new_white_clipping_is_still_blocked_with_a_warm_shift(self):
        self.source = Image.new('RGB', SIZE, (254, 254, 254))
        self.source.info['icc_profile'] = self.icc
        out, _ = self.run_zones(observed_source_pixel_sha256=_sha_pixels(self.source))
        self.assertNotIn(255, out.getpixel((128, 168)))

    def test_protected_pixels_survive_graded_zones(self):
        near = rect((182, 150, 192, 186))  # 36 px from the selection, inside its blur tail
        zone = replace(self.boat, protected=near, sigma_px=16,
                       allowed=rect((20, 80, 236, 255)))
        out, _ = self.run_zones([zone, replace(self.bank, protected=near)])
        for x in range(182, 193):
            for y in range(150, 187, 6):
                self.assertEqual(out.getpixel((x, y)), self.source.getpixel((x, y)))

    def test_protected_content_hugging_the_selection_stops_instead_of_stepping_or_fading_away(self):
        hugging = rect((150, 150, 160, 186))  # 4 px from the selection
        zone = replace(self.boat, protected=hugging, sigma_px=16,
                       allowed=rect((20, 80, 236, 255)))
        with self.assertRaisesRegex(ValueError, 'under-edited|too steep'):
            self.run_zones([zone, replace(self.bank, protected=hugging)])

    def test_selection_touching_the_border_needs_allowed_zone_to_reach_it(self):
        clipped = replace(self.bank, allowed=rect((8, 60, 100, 248)))
        with self.assertRaisesRegex(ValueError, 'escape allowed region'):
            self.run_zones([self.boat, clipped])


class SplitToneLutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(RUNTIME))
        import v2_global_operation
        cls.module = v2_global_operation

    def test_curves_are_bounded_monotonic_and_pin_black_and_white(self):
        for strength in ('subtle', 'moderate'):
            r, g, b = self.module._channel_luts('split_tone_warm_cool', strength)
            for lut in (r, g, b):
                self.assertEqual(len(lut), 256)
                self.assertEqual((lut[0], lut[255]), (0, 255))
                self.assertTrue(all(x <= y for x, y in zip(lut, lut[1:])))
                self.assertTrue(all(lut[i] <= 254 for i in range(255)))

    def test_highlights_go_warm_and_shadows_go_cool(self):
        r, g, b = self.module._channel_luts('split_tone_warm_cool', 'moderate')
        self.assertGreater(r[170], 170)
        self.assertLess(b[170], 170)
        self.assertLess(r[85], 85)
        self.assertGreater(b[85], 85)

    def test_moderate_is_stronger_than_subtle_and_neither_is_negligible(self):
        def peak(strength):
            r, _, b = self.module._channel_luts('split_tone_warm_cool', strength)
            return max(max(abs(r[i] - i) for i in range(256)), max(abs(b[i] - i) for i in range(256)))
        self.assertGreater(peak('moderate'), peak('subtle'))
        self.assertGreaterEqual(peak('subtle'), 6)

    def test_tonal_operations_still_use_one_shared_curve(self):
        for op in ('gentle_shadow_lift', 'restrain_bright_regions', 'mild_tonal_contrast'):
            r, g, b = self.module._channel_luts(op, 'subtle')
            self.assertEqual(r, g)
            self.assertEqual(g, b)
            self.assertEqual(r, self.module._lut(op, 'subtle'))


class SplitToneGlobalGateTests(base_global.SourceBoundGlobalTests):
    """Every fail-closed global gate must hold for the new operation too.

    This re-runs the nine original gate tests with operation=split_tone_warm_cool.
    """

    def setUp(self):
        super().setUp()
        self.op['operation'] = 'split_tone_warm_cool'
        self.save_op()

    def test_split_tone_output_is_warm_in_highlights_cool_in_shadows(self):
        self.assertEqual(self.render().returncode, 0)
        with Image.open(self.working) as before, Image.open(self.output) as after:
            before.load()
            after.load()
            b, a = before.convert('RGB'), after.convert('RGB')
            bright = shadow = None
            for y in range(b.height):
                for x in range(b.width):
                    px = b.getpixel((x, y))
                    if bright is None and all(150 <= v <= 190 for v in px):
                        bright = (x, y)
                    if shadow is None and all(60 <= v <= 110 for v in px):
                        shadow = (x, y)
            self.assertIsNotNone(bright, 'fixture has no highlight-range pixel')
            self.assertIsNotNone(shadow, 'fixture has no shadow-range pixel')
            hb, ha = b.getpixel(bright), a.getpixel(bright)
            sb, sa = b.getpixel(shadow), a.getpixel(shadow)
            self.assertGreaterEqual((ha[0] - ha[2]) - (hb[0] - hb[2]), 4)
            self.assertGreaterEqual((sa[2] - sa[0]) - (sb[2] - sb[0]), 4)

    def test_strong_split_tone_cannot_pass(self):
        self.op['strength'] = 'strong'
        self.save_op()
        self.assertNotEqual(self.render().returncode, 0)
        self.assertFalse(self.output.exists())


class RuntimeCopiesStayInSyncTests(unittest.TestCase):
    """The package keeps the same editor in two layouts. Drift is a real risk."""

    def test_experiments_and_runtime_copies_are_byte_identical(self):
        for name in ('pixel_mask_qa.py', 'multizone_editor.py'):
            with self.subTest(name=name):
                self.assertEqual((EXPERIMENTS / name).read_bytes(), (RUNTIME / name).read_bytes())


class ZoneIntentValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(RUNTIME))
        import v2_native_entry
        cls.entry = v2_native_entry

    def zones(self, **second):
        base = {'name': 'a', 'target_effect': 'brighten', 'gamma': 0.8}
        other = {'name': 'b', 'target_effect': 'darken', 'gamma': 1.25}
        other.update(second)
        return {'zones': [base, other]}

    def test_valid_graded_zone_with_chroma_passes(self):
        record = self.zones(edge_mode='graded', sigma_px=20, chroma_shift=[4.0, -3.0])
        self.assertIsNone(self.entry._verify_zone_intents(record))

    def test_graded_without_sigma_or_with_bad_sigma_is_refused(self):
        for extra in ({'edge_mode': 'graded'}, {'edge_mode': 'graded', 'sigma_px': 3},
                      {'edge_mode': 'graded', 'sigma_px': 121},
                      {'edge_mode': 'graded', 'sigma_px': 20.0},
                      {'edge_mode': 'graded', 'sigma_px': True}):
            with self.subTest(**extra):
                self.assertIn('sigma_px', self.entry._verify_zone_intents(self.zones(**extra)))

    def test_sigma_on_a_non_graded_zone_is_refused(self):
        self.assertIn('only valid', self.entry._verify_zone_intents(self.zones(sigma_px=20)))

    def test_unknown_edge_mode_and_bad_chroma_are_refused(self):
        self.assertIn('edge_mode', self.entry._verify_zone_intents(self.zones(edge_mode='blur')))
        for shift in ([20, 0], [0], 'warm', [float('inf'), 0]):
            with self.subTest(shift=shift):
                self.assertIn('chroma', self.entry._verify_zone_intents(self.zones(chroma_shift=shift)))

    def test_existing_direction_rules_still_apply(self):
        self.assertIn('disagree', self.entry._verify_zone_intents(
            self.zones(target_effect='brighten')))
        self.assertIn('target_effect', self.entry._verify_zone_intents(
            self.zones(target_effect='neutral')))


if __name__ == '__main__':
    unittest.main()
