"""Synthetic regressions for experimental Pillow-only color curve; no user photos."""
import sys
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'/'v2_global_curve'))
from bounded_global_curve_pillow_only import (
    pchip_dense, plan_from_stats, apply_curve, CurveParameters, frame_stats, rgb_gap_report)


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

    def test_triangular_dither_is_deterministic_and_neutral(self):
        gray=Image.new('RGB',(256,72))
        gray.putdata([(x,x,x) for y in range(72) for x in range(256)])
        params=CurveParameters((0,55,140,255),(0,48,220,255),1.3,.7)
        a,_=apply_curve(gray,params)
        b,_=apply_curve(gray,params)
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertTrue(all(r==g==b for r,g,b in a.get_flattened_data()))

    def test_dither_added_at_quantization_not_unbounded(self):
        img=Image.new('RGB',(256,64))
        img.putdata([(max(0,min(254,int(48+x*.46))),)*3
                     for y in range(64) for x in range(256)])
        base=CurveParameters((0,55,140,255),(0,48,220,255),1.3,0.)
        tpdf=CurveParameters((0,55,140,255),(0,48,220,255),1.3,.7)
        a,_=apply_curve(img,base)
        b,_=apply_curve(img,tpdf)
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertLessEqual(max(abs(i-j) for i,j in zip(a.tobytes(),b.tobytes())),1)
        self.assertLess(max(b.tobytes()),255)

    def test_three_channel_gap_report_detects_red_only_damage(self):
        src=Image.new('RGB',(256,72))
        src.putdata([(x,x,x) for y in range(72) for x in range(256)])
        damaged=Image.new('RGB',src.size)
        damaged.putdata([((r//8)*8,g,b) for r,g,b in src.get_flattened_data()])
        report=rgb_gap_report(src,damaged)['channels']
        self.assertEqual(set(report),{'R','G','B'})
        self.assertGreater(report['R']['new_gap_fraction'],.8)
        self.assertEqual(report['G']['new_gap_fraction'],0.)
        self.assertEqual(report['B']['new_gap_fraction'],0.)

    def test_synthetic_smooth_ramp_gap_reduction_all_channels(self):
        img=Image.new('RGB',(256,96))
        img.putdata([(max(0,min(254,int(48+x*.46))),)*3
                     for y in range(96) for x in range(256)])
        base=CurveParameters((0,55,140,255),(0,48,220,255),1.3,0.)
        tpdf=CurveParameters((0,55,140,255),(0,48,220,255),1.3,.7)
        a,_=apply_curve(img,base)
        b,_=apply_curve(img,tpdf)
        x=rgb_gap_report(img,a)
        y=rgb_gap_report(img,b)
        for channel in ('R','G','B'):
            self.assertLess(y['channels'][channel]['candidate']['interior_gap_fraction'],
                            x['channels'][channel]['candidate']['interior_gap_fraction'])
        self.assertLess(y['max_new_gap_fraction'],x['max_new_gap_fraction'])

    def test_rgb_gap_invalid_roi_fails_closed(self):
        with self.assertRaises(ValueError):
            rgb_gap_report(self.src,self.src,(0,0,100000,22))
        with self.assertRaises(ValueError):
            rgb_gap_report(self.src,Image.new('RGB',(3,3)))

