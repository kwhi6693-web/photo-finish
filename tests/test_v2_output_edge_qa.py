"""Output checks must examine rendered pixels, independently of caller flags."""
import sys
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import local_edit_qa as qa
from tests import test_v2_packaged_native_entry as base


class OutputEdgeTests(unittest.TestCase):
    def test_controller_receipt_separates_preflight_from_actual_output(self):
        h=base.PackagedNativeEntryTests();h.setUp();self.addCleanup(h.doCleanups)
        h.fixture()
        result=h.invoke('render',h.original,h.lineage,h.plan,h.zones,h.result,h.receipt)
        self.assertEqual(result.returncode,0,result.stderr)
        import json
        receipt=json.loads(h.receipt.read_text())['technical_receipt']
        self.assertTrue(receipt['mask_boundary_preflight_verified'])
        self.assertTrue(receipt['output_edge_qa_passed'])
        self.assertEqual(receipt['visual_edge_review'],'PENDING')
        self.assertGreater(receipt['zones'][0]['actual_region_change']['max_abs_channel_delta'],0)

    def fixture(self):
        before=Image.new('RGB',(8,4),(40,80,120))
        graded=Image.new('RGB',before.size,(80,100,140))
        alpha=Image.new('L',before.size)
        alpha.putdata([v for _ in range(4) for v in (0,0,32,96,160,224,255,255)])
        return before,graded,alpha,Image.composite(graded,before,alpha)

    def test_real_output_matches_bounded_edge_budget(self):
        before,graded,alpha,after=self.fixture()
        result=qa.inspect_output_edges(before,after,graded,alpha)
        self.assertTrue(result['output_edge_qa_passed'])
        self.assertEqual(result['visual_edge_review'],'PENDING')
        self.assertGreater(result['boundary_neighbor_pairs'],0)

    def test_injected_halo_is_rejected_even_with_smooth_alpha(self):
        before,graded,alpha,after=self.fixture()
        after.putpixel((2,2),(200,200,200))
        with self.assertRaisesRegex(ValueError,'output edge'):
            qa.inspect_output_edges(before,after,graded,alpha)

    def test_identity_roi_and_background_metrics_are_actual_pixels(self):
        before=Image.new('RGB',(4,1),(100,100,100))
        after=before.copy();after.putpixel((0,0),(120,120,120))
        roi=Image.new('L',(4,1));roi.putpixel((0,0),255)
        result=qa.measure_pixel_change(before,after,roi)
        self.assertEqual(result['max_abs_channel_delta'],20)
        self.assertEqual(result['mean_abs_channel_delta'],20)
        self.assertEqual(result['changed_pixel_fraction'],1)
        self.assertAlmostEqual(result['subject_relative_background_luma_delta'],20)
        self.assertEqual(result['under_powered_calibration'],'PENDING_REAL_MULTI_CATEGORY_CALIBRATION')
        self.assertIsNone(result['under_powered'])


if __name__=='__main__': unittest.main()
