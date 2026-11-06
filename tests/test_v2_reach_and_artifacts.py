"""Source-guided reach and actual execution artifacts, not semantic segmentation."""
import json,sys,unittest
from pathlib import Path
from dataclasses import replace
from PIL import Image,ImageDraw,ImageChops
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import pixel_mask_qa as q
from tests import test_v2_packaged_native_entry as cli
from tests import test_v2_multizone_editor as legacy


class ReachTests(unittest.TestCase):
    def test_luma_reach_preserves_continuous_weights_and_never_grows_support(self):
        source=Image.new('RGB',(16,4));source.putdata([(x*16,)*3 for y in range(4) for x in range(16)])
        alpha=Image.new('L',source.size,190)
        core=Image.new('L',source.size);ImageDraw.Draw(core).rectangle((3,0,5,3),fill=255)
        refined,receipt=q.refine_graded_alpha(source,alpha,core,luma_range=(0,0,96,224))
        self.assertEqual(refined.getpixel((3,1)),190)
        self.assertEqual(refined.getpixel((15,1)),0)
        self.assertGreater(refined.getpixel((9,1)),0)
        self.assertLess(refined.getpixel((9,1)),190)
        self.assertFalse(ImageChops.subtract(refined,alpha).getbbox())
        self.assertTrue(receipt['support_not_expanded'])

    def test_invalid_range_gradient_and_core_loss_stop(self):
        for kw in ({'luma_range':(0,90,20,255)}, {'luma_range':(0,True,20,255)},
                   {'linear_gradient':(0,0,float('nan'),1)}, {'linear_gradient':(0,0,0,0)}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):q.validate_reach(**kw)
        source=Image.new('RGB',(16,16),(220,220,220));a=Image.new('L',source.size,255)
        with self.assertRaisesRegex(ValueError,'core'):
            q.refine_graded_alpha(source,a,a,luma_range=(0,0,20,80))

    def test_gradient_uses_source_geometry_and_keeps_fractional_alpha(self):
        s=Image.new('RGB',(32,8),(100,100,100));a=Image.new('L',s.size,255)
        core=Image.new('L',s.size);ImageDraw.Draw(core).rectangle((26,0,31,7),fill=255)
        out,_=q.refine_graded_alpha(s,a,core,linear_gradient=(0,0,1,0))
        self.assertEqual(out.getpixel((0,4)),0)
        self.assertEqual(out.getpixel((31,4)),255)
        self.assertGreater(out.getpixel((16,4)),100)
        self.assertLess(out.getpixel((16,4)),200)

    def test_legacy_output_unchanged_when_reach_is_absent(self):
        h=legacy.MultiZoneTests();h.setUp();before,_=h.trial()
        images=[]
        after,_=h.trial(artifact_sink=lambda name,alpha,image:images.append((name,alpha.copy(),image.copy())))
        self.assertEqual(before.tobytes(),after.tobytes())
        self.assertEqual(len(images),2)
        self.assertEqual(after.tobytes(),images[-1][2].tobytes())

    def test_cli_captures_actual_alpha_without_an_extra_render(self):
        h=cli.PackagedNativeEntryTests();h.setUp();self.addCleanup(h.doCleanups);h.fixture()
        folder=h.root/'actual'
        result=h.invoke('render',h.original,h.lineage,h.plan,h.zones,h.result,h.receipt,'--artifacts-dir',folder)
        self.assertEqual(result.returncode,0,result.stderr)
        proof=json.loads(h.receipt.read_text())
        self.assertEqual(proof['execution_artifacts']['render_calls'],1)
        self.assertEqual(len(proof['execution_artifacts']['zones']),2)
        with Image.open(folder/'zone_2_output.png') as image,Image.open(h.result) as candidate:
            self.assertEqual(image.tobytes(),candidate.tobytes())
        self.assertTrue((folder/'zone_1_alpha.png').is_file())

    def test_bad_reach_or_occupied_artifact_directory_leaves_no_candidate(self):
        h=cli.PackagedNativeEntryTests();h.setUp();self.addCleanup(h.doCleanups);h.fixture()
        folder=h.root/'occupied';folder.mkdir()
        result=h.invoke('render',h.original,h.lineage,h.plan,h.zones,h.result,h.receipt,'--artifacts-dir',folder)
        self.assertNotEqual(result.returncode,0);self.assertFalse(h.result.exists())
        record=json.loads(h.zones.read_text());record['zones'][0]['luma_range']=[0,10,40,255]
        h.zones.write_text(json.dumps(record))
        result=h.invoke('render',h.original,h.lineage,h.plan,h.zones,h.result,h.receipt)
        self.assertEqual(json.loads(result.stdout)['stage'],'STOP')
        self.assertFalse(h.result.exists())

    def test_capture_write_failure_cleans_staging_without_candidate(self):
        from unittest.mock import patch
        from execution_artifacts import ExecutionArtifacts
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();target=root/'actual'
            with self.assertRaisesRegex(OSError,'injected'),ExecutionArtifacts(target) as capture:
                with patch.object(Image.Image,'save',side_effect=OSError('injected artifact write failure')):
                    capture.capture('zone',Image.new('L',(8,8)),Image.new('RGB',(8,8)))
            self.assertEqual(list(root.iterdir()),[])


if __name__=='__main__':unittest.main()
