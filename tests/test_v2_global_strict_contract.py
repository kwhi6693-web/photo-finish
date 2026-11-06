"""Unknown global controls must not be acknowledged without execution."""
import json
import unittest
from tests import test_v2_global_operation as base


class GlobalStrictTests(unittest.TestCase):
    def test_unknown_global_control_stops_without_candidate(self):
        host = base.SourceBoundGlobalTests()
        host.setUp()
        self.addCleanup(host.doCleanups)
        host.op['temperature_kelvin'] = 12000
        host.save_op()
        result = host.render()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('unknown global operation fields',result.stderr)
        self.assertFalse(host.output.exists())
        self.assertFalse(host.receipt.exists())
