"""A legitimate narrow continuous gradient must use its own numerical budget."""
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
from pixel_mask_qa import inspect_mask, graded_alpha


class GradientWidthTests(unittest.TestCase):
    def test_valid_wide_and_narrow_edges_are_not_measured_by_one_fixed_step(self):
        mask=Image.new('L',(1024,1024));ImageDraw.Draw(mask).rectangle((256,256,768,768),fill=255)
        core=Image.new('L',mask.size);ImageDraw.Draw(core).rectangle((480,480,540,540),fill=255)
        allowed=Image.new('L',mask.size,255);protected=Image.new('L',mask.size)
        audit=inspect_mask(mask,target_core=core,allowed_zone=allowed,protected=protected)
        steps=[]
        for sigma in (4,8,24,60):
            with self.subTest(sigma=sigma):
                receipt=graded_alpha(mask,audit=audit,target_core=core,allowed_zone=allowed,protected=protected,sigma_px=sigma)
                self.assertEqual(receipt.alpha.getpixel((510,510)),255)
                self.assertEqual(receipt.alpha.getpixel((0,0)),0)
                steps.append(receipt.max_neighbor_step)
        self.assertEqual(len(steps),4)
        self.assertGreater(steps[0],steps[-1])
