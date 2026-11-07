"""Synthetic regressions for experimental Pillow-only color curve; no user photos."""
import sys
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'/'v2_global_curve'))
from bounded_global_curve_pillow_only import (
    pchip_dense, plan_from_stats, apply_curve, CurveParameters, frame_stats)


class ExperimentalCurveTests(unittest.TestCase):
    def setUp(self):
        self.src=Image.new('RGB',(120,64))
        self.src.putdata([((58+x*2+y//3)%170,(72+x*2+y//3)%170,
                           (89+x*2+y//3)%170) for y in range(64) for x in range(120)])
        self.params=CurveParameters((0,75,140,255),(0,70,210,255),1.3)

    def test_monotone_endpoints(self):
        c,s=pchip_dense((0,40,80,140,190,255),(0,36,70,218,247,255))
        self.assertEqual(c[0],0)
        self.assertEqual(c[-1],255)
        self.assertTrue(all(b>=a for a,b in zip(c,c[1:])))

    def test_invalid_knots_fail_closed(self):
        with self.assertRaises(ValueError):
            pchip_dense((0,70,60,255),(0,30,80,255))

    def test_strength_out_of_bounds_fail_closed(self):
        with self.assertRaises(ValueError):
            apply_curve(self.src,CurveParameters((0,75,140,255),(0,70,210,255),1.61))

    def test_no_new_rgb_255(self):
        out,_=apply_curve(self.src,self.params)
        self.assertLess(max(max(q) for q in out.get_flattened_data()),255)

    def test_deterministic_pixels(self):
        a,_=apply_curve(self.src,self.params)
        b,_=apply_curve(self.src,self.params)
        self.assertEqual(a.tobytes(),b.tobytes())

    def test_geometry_unchanged(self):
        out,_=apply_curve(self.src,self.params)
        self.assertEqual(out.size,self.src.size)

    def test_source_unmodified(self):
        original=self.src.tobytes()
        apply_curve(self.src,self.params)
        self.assertEqual(original,self.src.tobytes())

    def test_out_of_domain_refuses(self):
        with self.assertRaises(ValueError):
            plan_from_stats(20,50,240)

    def test_malformed_parameters_rejected(self):
        with self.assertRaises(ValueError):
            apply_curve(self.src,CurveParameters((0,70,255),(0,255,255),1.3))

    def test_source_stats_available(self):
        stats=frame_stats(self.src)
        self.assertLess(stats['p01'],stats['p99'])
