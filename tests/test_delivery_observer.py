"""Synthetic clock/sidecar tests; no image, host or external-service evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import observe_delivery as o

class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name)/'trace.json';o.create(self.p)
    def clock(self,n):return {'wall_ns':n*10**9,'mono_ns':n*10**9}
    def test_unknown_open_span_does_not_certify_completion(self):
        o.mark(self.p,'edit_call','external_tool');r=o.summary(self.p)
        self.assertEqual(r['open_spans'],1);self.assertIsNone(r['coverage_fraction']);self.assertFalse(r['quality_or_save_certification'])
    def test_nested_intervals_are_not_double_counted(self):
        with patch.object(o,'_clock',side_effect=[self.clock(n) for n in [0,0,1,2,3,3]]):
            a=o.mark(self.p,'task_received','caller_activity');b=o.mark(self.p,'edit_call','external_tool');o.mark(self.p,'task_received','caller_activity',a,'ok');o.mark(self.p,'edit_call','external_tool',b,'timeout');c=o.mark(self.p,'delivery_observed','caller_activity');o.mark(self.p,'delivery_observed','caller_activity',c,'ok')
        r=o.summary(self.p);self.assertEqual(r['recorded_interval_union_seconds'],2);self.assertAlmostEqual(r['coverage_fraction'],2/3);self.assertIsNone(r['model_compute_seconds'])
    def test_duplicate_end_and_payload_labels_rejected(self):
        a=o.mark(self.p,'photo_save_call','external_tool');o.mark(self.p,'photo_save_call','external_tool',a,'unknown');before=self.p.read_bytes()
        with self.assertRaises(ValueError):o.mark(self.p,'photo_save_call','external_tool',a,'ok')
        with self.assertRaises(ValueError):o.mark(self.p,'https://private.invalid','external_tool')
        self.assertEqual(before,self.p.read_bytes())
    def test_exclusive_lock_and_git_guard(self):
        lock=self.p.with_name(self.p.name+'.lock');lock.touch()
        with self.assertRaises(FileExistsError):o.mark(self.p,'context_read','local_controller')
        lock.unlink();(self.p.parent/'.git').mkdir()
        with self.assertRaises(ValueError):o.summary(self.p)

    def test_endpoint_span_does_not_inflate_coverage(self):
        with patch.object(o,'_clock',side_effect=[self.clock(n) for n in [0,10,10,10]]):
            a=o.mark(self.p,'task_received','caller_activity');o.mark(self.p,'task_received','caller_activity',a,'ok');b=o.mark(self.p,'delivery_observed','caller_activity');o.mark(self.p,'delivery_observed','caller_activity',b,'ok')
        self.assertEqual(o.summary(self.p)['coverage_fraction'],0)
    def test_clock_disagreement_disables_coverage(self):
        with patch.object(o,'_clock',side_effect=[self.clock(0),{'wall_ns':10**9,'mono_ns':4*10**9}]):
            a=o.mark(self.p,'edit_call','external_tool');o.mark(self.p,'edit_call','external_tool',a,'unknown')
        self.assertTrue(o.summary(self.p)['warnings'])
