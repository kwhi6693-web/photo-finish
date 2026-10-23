"""Exercise deterministic packaging and a clean, relocated runtime."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile,unittest,zipfile
from build_release import build

class PackageTests(unittest.TestCase):
    def test_json_cli_preserves_unicode_paths_with_ascii_stdio_default(self):
        from PIL import Image
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);source=folder/'源图.png';job=folder/'任务.json'
            Image.new('RGB',(12,16),(70,90,100)).save(source)
            payload={'project_root':str(root/'runtime'),'source_path':str(source),'path':str(job),'tags':[],
                'evaluation_kind':'synthetic','scenario':'unicode-protocol-fixture',
                'direction':{'intent':'Synthetic fixture','hierarchy':'flat field','light_material':'synthetic RGB',
                             'output_use':'screen','route':'creative','qa_focus':['fixture']}}
            env=dict(os.environ,PYTHONIOENCODING='ascii')
            result=subprocess.run([sys.executable,str(root/'runtime/10_SYSTEM_CONFIG/scripts/photo_edit.py'),'prepare'],
                input=json.dumps(payload,ensure_ascii=False).encode('utf-8'),capture_output=True,env=env)
            self.assertEqual(result.returncode,0,result.stderr.decode('utf-8'))
            self.assertEqual(json.loads(result.stdout.decode('utf-8'))['path'],str(job.resolve()))
            self.assertTrue(job.is_file())
    def test_two_builds_match_and_clean_extraction_bootstraps(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);a=folder/'one.zip';b=folder/'two.zip'
            build(a,root);build(b,root);self.assertEqual(a.read_bytes(),b.read_bytes())
            with zipfile.ZipFile(a) as z:
                manifest=json.loads(z.read('photo-finish/release-manifest.json'))
                for name,digest in manifest['files'].items():
                    self.assertEqual(hashlib.sha256(z.read('photo-finish/'+name)).hexdigest(),digest)
                self.assertNotIn('photo-finish/tests/test_package.py',z.namelist())
                z.extractall(folder/'extract')
            relocated=folder/'extract/photo-finish'
            result=subprocess.run([sys.executable,str(relocated/'tools/doctor.py')],capture_output=True,text=True, encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)['public_reference_count'],0)

if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    unittest.main()
