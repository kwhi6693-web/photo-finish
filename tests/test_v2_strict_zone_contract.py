"""CLI regressions: ignored requests must never produce a pending photo."""
import json
import unittest
from tests import test_v2_packaged_native_entry as base


class StrictZoneContractTests(unittest.TestCase):
    def setUp(self):
        self.host = base.PackagedNativeEntryTests()
        self.host.setUp()
        self.addCleanup(self.host.doCleanups)
        self.host.fixture()
        self.initial = json.loads(self.host.zones.read_text())

    def refuse(self, data):
        h = self.host
        h.result.unlink(missing_ok=True)
        h.receipt.unlink(missing_ok=True)
        h.zones.write_text(json.dumps(data), encoding='utf-8')
        before = {p.name: base.digest(p) for p in h.root.iterdir() if p.is_file()}
        result = h.invoke('render', h.original, h.lineage, h.plan, h.zones, h.result, h.receipt)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['stage'], 'STOP')
        self.assertFalse(h.result.exists())
        receipt = json.loads(h.receipt.read_text())
        self.assertEqual(receipt['status'], 'STOP')
        self.assertIsNone(receipt['candidate_sha256'])
        self.assertFalse(receipt['formal_V1_registered'])
        after = {p.name: base.digest(p) for p in h.root.iterdir() if p.is_file() and p != h.receipt}
        self.assertEqual(before, after)
        h.receipt.unlink()

    def test_unknown_nested_and_top_level_operations_stop(self):
        for key in ('temperature_kelvin', 'hue_shift_deg', 'exposure_ev', 'split_tone', 'typo'):
            for level in ('zone', 'root'):
                with self.subTest(key=key, level=level):
                    data = json.loads(json.dumps(self.initial))
                    target = data['zones'][0] if level == 'zone' else data
                    target[key] = 2
                    self.refuse(data)

    def test_nonfinite_numeric_wrong_types_and_flags_stop(self):
        cases = [('gamma',float('nan')), ('gamma',float('inf')), ('gamma',True),
                 ('saturation','1'), ('saturation',False), ('sigma_px',False),
                 ('edge_mode',[]), ('chroma_shift',[0,True]),
                 ('boundary_visually_inspected','yes')]
        for key,value in cases:
            with self.subTest(key=key,value=value):
                data = json.loads(json.dumps(self.initial))
                data['zones'][0][key] = value
                self.refuse(data)

    def test_wrong_source_cannot_leave_png_or_version(self):
        h = self.host
        data = json.loads(json.dumps(self.initial))
        data['source_sha256'] = '0'*64
        h.zones.write_text(json.dumps(data))
        result = h.invoke('render', h.original, h.lineage, h.plan, h.zones, h.result, h.receipt)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(h.result.exists())
        self.assertFalse(h.receipt.exists())


if __name__ == '__main__':
    unittest.main()
