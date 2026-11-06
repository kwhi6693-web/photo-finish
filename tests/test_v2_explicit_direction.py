import json,unittest
from tests import test_v2_photo_direction as base


class ExplicitDirectionTests(unittest.TestCase):
    def test_observed_light_color_and_intensity_survive_compilation(self):
        h=base.ObservedDirectionCLITests();h.setUp();self.addCleanup(h.doCleanups)
        h.data.update(intensity='moderate',lighting_direction='Lift the actual wooden boat, retaining deep original tree shadows',color_direction='Let original warm wood stand against the naturally cool river water')
        h.save();result=h.decide();self.assertEqual(result.returncode,0,result.stderr)
        plan=json.loads(h.plan.read_text())
        for key in ('lighting_direction','color_direction','intensity'):self.assertEqual(plan[key],h.data[key])
