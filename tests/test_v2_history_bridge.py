"""Synthetic GO fixtures only. No private historical ledger is opened."""
import json,sys,unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import task_history as history
import v2_delivery as d
from tests import test_v2_delivery as base


class HistoryBridgeTests(unittest.TestCase):
    def test_register_rechecks_embedded_user_go(self):
        h=base.DeliveryTests();h.setUp();self.addCleanup(h.doCleanups);h.fixture()
        accepted=json.loads((h.root/'accepted.json').read_text());accepted['user_review']['user_final_photographic_quality']='PENDING'
        h.write('changed.json',accepted)
        with self.assertRaisesRegex(ValueError,'GO'):
            d.register(h.root/'changed.json',h.root/'save.json',h.readback,h.photo,'libfile_synthetic',h.root/'bad-version.json')
        self.assertFalse((h.root/'bad-version.json').exists())

    def test_existing_history_index_handles_v1_v2_and_zero_render_restore(self):
        h=base.DeliveryTests();h.setUp();self.addCleanup(h.doCleanups);h.fixture()
        root=h.root/'new-private-history'
        first=history.register_v2(h.source,h.photo,h.root/'accepted.json',h.root/'v1.json',root)
        self.assertEqual(first['label'],'V1')
        second_photo=h.root/'second.png'
        with Image.open(h.photo) as old:
            Image.new('RGB',old.size,(115,140,160)).save(second_photo,icc_profile=old.info['icc_profile'])
        proof=h.write('second-proof.json',{'camera_original_sha256':d.hash_file(h.photo),'candidate_sha256':d.hash_file(second_photo),'renderer_origin':'external_non_generative'})
        review=h.write('second-review.json',dict(h.review,camera_original_sha256=d.hash_file(h.photo),candidate_sha256=d.hash_file(second_photo)))
        accepted=h.root/'second-accepted.json';d.accept(h.photo,second_photo,proof,review,accepted)
        read=h.write('second-read.json',{'transfers':[{'library_file_id':'libfile_second','workspace_path':str(second_photo),'workspace_sha256':d.hash_file(second_photo)}]})
        save=h.write('second-save.json',{'status':'succeeded','file_id':'file_second','library_file_id':'libfile_second'})
        version=h.root/'second-v1.json';d.register(accepted,save,read,second_photo,'libfile_second',version)
        second=history.register_v2(h.photo,second_photo,accepted,version,root,parent_series=first['series'],parent_version='V1')
        self.assertEqual(second['label'],'V2');self.assertEqual(second['parent_version'],'V1')
        hashes={p:d.hash_file(p) for p in (h.source,h.photo,second_photo,accepted,version)}
        restored=history.restore(root,first['series'],'V1')
        self.assertEqual(restored['render_calls'],0)
        self.assertEqual(history.current(root)['label'],'V1')
        self.assertEqual(hashes,{p:d.hash_file(p) for p in hashes})
        self.assertEqual(len(history.history(root,first['series'])['versions']),2)


if __name__=='__main__':unittest.main()
