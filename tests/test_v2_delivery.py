"""Synthetic evidence-binding regressions; never host/aesthetic certification."""
from pathlib import Path
import tempfile,json,sys,unittest
from PIL import Image,ImageCms
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import v2_delivery as d

class DeliveryTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name).resolve()
        self.source=self.root/'source.jpg';self.photo=self.root/'photo.png'
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        for p in (self.source,self.photo):Image.new('RGB',(12,16),(100,130,150)).save(p,icc_profile=icc)
        self.proof={'camera_original_sha256':d.hash_file(self.source),'candidate_sha256':d.hash_file(self.photo),'renderer_origin':'external_non_generative'}
        self.review={'reviewer_role':'end_user_final_editorial_authority','user_final_photographic_quality':'GO','candidate_sha256':d.hash_file(self.photo),'camera_original_sha256':d.hash_file(self.source),'decision_reference':'caller supplied user reference; synthetic fixture'}
        self.write('proof.json',self.proof);self.write('review.json',self.review)
    def write(self,name,data):
        p=self.root/name;p.write_text(json.dumps(data));return p
    def accept(self):
        return d.accept(self.source,self.photo,self.root/'proof.json',self.root/'review.json',self.root/'accepted.json')
    def fixture(self):
        self.accept();lib='libfile_synthetic'
        self.save=self.write('save.json',{'structuredContent':{'library_file_id':lib,'file_id':'file_synthetic','status':'succeeded'}})
        self.readback=self.write('readback.json',{'transfers':[{'library_file_id':lib,'workspace_path':str(self.photo),'workspace_sha256':d.hash_file(self.photo)}]})
        return d.register(self.root/'accepted.json',self.save,self.readback,self.photo,lib,self.root/'v1.json')
    def test_external_acceptance_keeps_origin(self):
        r=self.accept();self.assertFalse(r['native_controller_e2e']);self.assertFalse(r['third_party_independent_review']);self.assertFalse(r['formal_V1_registered'])
    def test_no_overwrite(self):
        self.accept()
        with self.assertRaises(FileExistsError):self.accept()
    def test_wrong_review_hash_and_role_refused(self):
        for field,value in [('candidate_sha256','0'*64),('camera_original_sha256','0'*64),('reviewer_role','assistant'),('user_final_photographic_quality','PENDING')]:
            with self.subTest(field=field):
                self.write('review.json',dict(self.review,**{field:value}))
                with self.assertRaises(ValueError):self.accept()
                self.assertFalse((self.root/'accepted.json').exists())
    def test_native_receipt_cannot_be_missing(self):
        self.write('proof.json',dict(self.proof,renderer_origin='pr47_native_controller',controller_receipt_path=str(self.root/'missing.json')))
        with self.assertRaises(FileNotFoundError):self.accept()
    def test_register_and_restore_preserve_bytes(self):
        v=self.fixture();before={p:p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        r=d.restore(self.root/'v1.json',d.hash_file(self.root/'v1.json'),self.readback,self.photo)
        self.assertEqual(r['render_calls'],0);self.assertEqual(r['ledger_writes'],0)
        self.assertFalse(v['cross_conversation_restore_verified'])
        self.assertEqual(before,{p:p.read_bytes() for p in self.root.iterdir() if p.is_file()})
    def test_restore_wrong_version_hash_refused(self):
        self.fixture()
        with self.assertRaises(ValueError):d.restore(self.root/'v1.json','0'*64,self.readback,self.photo)
    def test_readback_wrong_identity_or_hash_refused(self):
        self.accept();save=self.write('save.json',{'file_id':'file_synthetic','library_file_id':'libfile_synthetic'})
        for identity,sha in [('libfile_other',d.hash_file(self.photo)),('libfile_synthetic','0'*64)]:
            read=self.write('read.json',{'transfers':[{'library_file_id':identity,'workspace_path':str(self.photo),'workspace_sha256':sha}]})
            with self.assertRaises(ValueError):d.register(self.root/'accepted.json',save,read,self.photo,'libfile_synthetic',self.root/'v1.json')
            self.assertFalse((self.root/'v1.json').exists())
    def test_missing_save_receipt_refused(self):
        self.fixture();self.write('bad.json',{'status':'failed'})
        with self.assertRaises(ValueError):d.register(self.root/'accepted.json',self.root/'bad.json',self.readback,self.photo,'libfile_synthetic',self.root/'another.json')
    def test_official_partial_binding_shape_is_supported(self):
        self.accept();lib='libfile_synthetic'
        save=self.write('save.json',{'results':[{'status':'succeeded','file_id':'file_synthetic','library_file_id':lib}]})
        read=self.write('bound.json',{'structuredContent':{'transfers':[{'transfer_id':'t1','library_file_id':lib,'workspace_path':str(self.photo)}],'partial_bindings':{'selected_refs':{'t1':{'library_file_id':lib,'workspace_sha256':d.hash_file(self.photo)}}}}})
        r=d.register(self.root/'accepted.json',save,read,self.photo,lib,self.root/'v1.json')
        self.assertTrue(r['formal_V1_registered'])
    def test_failed_save_with_id_and_binding_conflict_refused(self):
        lib='libfile_synthetic';self.accept()
        save=self.write('save.json',{'results':[{'status':'failed','file_id':'file_synthetic','library_file_id':lib}]})
        read=self.write('read.json',{'transfers':[{'library_file_id':lib,'workspace_path':str(self.photo),'workspace_sha256':d.hash_file(self.photo)}]})
        with self.assertRaises(ValueError):d.register(self.root/'accepted.json',save,read,self.photo,lib,self.root/'v1.json')
        self.write('save.json',{'results':[{'status':'succeeded','file_id':'file_synthetic','library_file_id':lib}]})
        self.write('read.json',{'transfers':[{'transfer_id':'t1','library_file_id':lib,'workspace_path':str(self.photo)}],'partial_bindings':{'selected_refs':{'t1':{'library_file_id':'libfile_wrong','workspace_sha256':d.hash_file(self.photo)}}}})
        with self.assertRaises(ValueError):d.register(self.root/'accepted.json',save,read,self.photo,lib,self.root/'v1.json')
