import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime" / "10_SYSTEM_CONFIG" / "scripts"))
from PIL import Image,ImageDraw
import render_defect_qa as qa

class PostrenderDefectTests(unittest.TestCase):
    def test_same_source_geometry_required(self):
        with self.assertRaisesRegex(ValueError, 'same-geometry'):
            qa.postrender_defect_report(Image.new('RGB',(20,20)),Image.new('RGB',(21,20)))
    def test_new_halo_detected_without_depending_on_alpha_flag(self):
        before=Image.new('RGB',(160,90));d=ImageDraw.Draw(before)
        d.rectangle((0,0,80,89),fill=(42,42,42))
        d.rectangle((81,0,159,89),fill=(125,125,125))
        after=before.copy();ImageDraw.Draw(after).line((80,5,80,84),fill=(225,225,225),width=1)
        result=qa.strong_edge_overshoot(before,after)
        self.assertTrue(result['strong_edge_overshoot_warning'],result)
        self.assertGreater(result['candidate_rim_hits'],3)
        self.assertFalse(qa.strong_edge_overshoot(before,before)['strong_edge_overshoot_warning'])
    def test_new_dark_banding_detected_and_existing_steps_not_false_positive(self):
        before=Image.new('RGB',(320,96));before.putdata([((14+x//4),)*3 for y in range(96) for x in range(320)])
        # 80 encoded tonal values, reduced to 10 -> visible regular quantization.
        after=Image.new('RGB',before.size)
        after.putdata([((14+x//4)//8*8,)*3 for y in range(96) for x in range(320)])
        r=qa.new_dark_gradient_banding(before,after)
        self.assertTrue(r['new_dark_banding_warning'],r)
        self.assertFalse(qa.new_dark_gradient_banding(before,before)['new_dark_banding_warning'])
    def test_chromatic_only_banding_detected_in_dark_gradient(self):
        before=Image.new('RGB',(320,100))
        before.putdata([(28+x//4,35,58-x//4) for y in range(100) for x in range(320)])
        after=Image.new('RGB',(320,100))
        after.putdata([((28+x//4)//8*8,35,58-x//4) for y in range(100) for x in range(320)])
        result=qa.new_dark_gradient_banding(before,after)
        self.assertTrue(result['new_dark_banding_warning'],result)
    def test_legitimate_natural_edge_and_gradient_not_warned(self):
        source=Image.new('RGB',(160,90))
        source.putdata([((45 if x<81 else 125),)*3 for y in range(90) for x in range(160)])
        out=source.copy();ImageDraw.Draw(out).rectangle((0,0,75,89),fill=(65,65,65))
        self.assertFalse(qa.strong_edge_overshoot(source,out)['strong_edge_overshoot_warning'])
    def test_warning_is_never_photographic_GO(self):
        im=Image.new('RGB',(30,20),(55,65,75))
        report=qa.postrender_defect_report(im,im)
        self.assertEqual(report['photographic_quality'],'NOT_INFERRED')
        self.assertIn('ADVISORY',report['decision'])

if __name__=='__main__':unittest.main()
