"""Read-only actual capability and same-source diagnostics, no aesthetic scoring."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
from tests import test_v2_packaged_native_entry as cli
import local_edit_qa as qa


class DiagnosticTests(unittest.TestCase):
    def test_distribution_has_actual_percentiles_not_quality_score(self):
        from PIL import Image
        im=Image.new('RGB',(5,1));im.putdata([(v,)*3 for v in (0,20,100,200,255)])
        r=qa.tonal_distribution(im)
        self.assertEqual(r['P50'],100)
        self.assertEqual(r['P05'],0)
        self.assertEqual(r['P95'],255)
        self.assertNotIn('quality_score',r)

    def test_real_capability_probe_and_nonmutating_quality_cli(self):
        h=cli.PackagedNativeEntryTests();h.setUp();self.addCleanup(h.doCleanups);h.fixture()
        result=h.invoke('capabilities')
        self.assertEqual(result.returncode,0,result.stderr)
        info=json.loads(result.stdout)
        self.assertTrue(info['native_selftest_passed'])
        self.assertFalse(info['semantic_segmentation_verified'])
        self.assertEqual(h.invoke('render',h.original,h.lineage,h.plan,h.zones,h.result,h.receipt).returncode,0)
        before={p.name:cli.digest(p) for p in h.root.iterdir() if p.is_file()}
        report=h.root/'quality.json'
        result=h.invoke('quality-report',h.original,h.lineage,h.result,h.receipt,report)
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(report.read_text())
        self.assertEqual(data['photographic_quality'],'PENDING_USER_REVIEW')
        self.assertEqual(data['candidate']['sha256'],cli.digest(h.result))
        after={p.name:cli.digest(p) for p in h.root.iterdir() if p.is_file() and p!=report}
        self.assertEqual(before,after)
