"""Failure injection, overlap order, and deterministic property regressions."""
from dataclasses import replace
import random
import unittest
from unittest.mock import patch
from PIL import Image, ImageChops
from tests import test_v2_native_candidate_export as export_base
from tests import test_v2_multizone_editor as zone_base


class RenderFailureGateTests(unittest.TestCase):
    def test_overlap_is_ordered_and_all_protection_is_union(self):
        h=zone_base.MultiZoneTests();h.setUp()
        a=replace(h.zoneA,chroma_shift=(-5,5))
        b=replace(h.zoneB,mask=a.mask,core=a.core,allowed=a.allowed,chroma_shift=(3,-2))
        forward,receipt=h.trial([a,b]);reverse,_=h.trial([b,a])
        self.assertNotEqual(forward.tobytes(),reverse.tobytes())
        self.assertEqual(receipt['overlap_order'],[a.name,b.name])
        self.assertTrue(receipt['protected_pixel_check'])

    def test_export_rejects_missing_preflight_or_output_check(self):
        h=export_base.NativePNGHandoffTests();h.setUp();self.addCleanup(h.doCleanups)
        for key in ('mask_boundary_preflight_verified','output_edge_qa_passed'):
            with self.subTest(key=key):
                h.output_path.unlink(missing_ok=True)
                receipt=dict(h.trial.technical_receipt);receipt.pop(key,None)
                trial=replace(h.trial,technical_receipt=receipt)
                with self.assertRaises(ValueError):
                    export_base.export_pending_png(trial,working_source_path=h.source_path,destination=h.output_path)
                self.assertFalse(h.output_path.exists())

    def test_bad_second_mask_stops_before_any_grade(self):
        h=zone_base.MultiZoneTests();h.setUp()
        bad=replace(h.zoneB,core=Image.new('L',h.source.size,255))
        with patch.object(zone_base.sys.modules['multizone_editor'],'_grade',side_effect=AssertionError('render began before preflight')):
            with self.assertRaises(ValueError): h.trial([h.zoneA,bad])

    def test_seeded_tones_keep_protection_support_source_and_determinism(self):
        h=zone_base.MultiZoneTests();h.setUp()
        rng=random.Random(61547)
        source=h.source.tobytes()
        for _ in range(12):
            zones=[replace(h.zoneA,gamma=rng.uniform(1.05,1.5)),replace(h.zoneB,gamma=rng.uniform(.68,.95))]
            first,receipt=h.trial(zones)
            second,_=h.trial(zones)
            self.assertEqual(first.tobytes(),second.tobytes())
            self.assertEqual(source,h.source.tobytes())
            self.assertTrue(receipt['protected_pixel_check'])
            self.assertTrue(receipt['output_edge_qa_passed'])


if __name__=='__main__': unittest.main()
