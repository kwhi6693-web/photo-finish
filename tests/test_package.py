"""Exercise deterministic packaging and a clean, relocated runtime."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,unittest,zipfile
from build_release import build

class PackageTests(unittest.TestCase):
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
            result=subprocess.run([sys.executable,str(relocated/'tools/doctor.py')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)['public_reference_count'],0)

if __name__=='__main__':unittest.main()
