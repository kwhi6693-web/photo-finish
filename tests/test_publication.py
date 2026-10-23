"""Adversarial publication checks; all values are synthetic and never credentials."""
from pathlib import Path
import io,json,subprocess,tempfile,unittest,warnings,zipfile
from check_publication import findings_for,inspect_archive,scan
from doctor import check
from build_release import build

class PublicationTests(unittest.TestCase):
    def test_known_credentials_are_rejected_without_echoing_value(self):
        value='gh'+'p_'+'X'*36
        findings=findings_for('fixture.txt',value.encode())
        self.assertTrue(any(x['rule']=='github-credential' for x in findings))
        self.assertNotIn(value,json.dumps(findings))
    def test_paths_and_library_identifiers_are_rejected(self):
        for value in ('/work'+'space/private/file','lib'+'file_'+'b'*32):
            self.assertTrue(findings_for('fixture.txt',value.encode()))
    def test_signed_urls_and_private_keys_are_rejected(self):
        for value in ('https://example.com/image?'+'sig='+'private-value', '-----BE'+'GIN PRIVATE KEY-----'):
            self.assertTrue(findings_for('fixture.txt',value.encode()))
    def test_photographs_and_environment_files_are_rejected(self):
        for name in ('private.jpeg','.env.production','outputs/job.json'):
            self.assertTrue(findings_for(name,b'{}'))
    def test_archive_traversal_duplicates_and_symlinks_are_rejected(self):
        for name,mode in (('../escape.txt',0o100644),('safe.txt',0o120777)):
            data=io.BytesIO()
            with zipfile.ZipFile(data,'w') as z:
                info=zipfile.ZipInfo(name);info.external_attr=mode<<16;z.writestr(info,b'fixture')
            self.assertTrue(inspect_archive(data.getvalue()))
    def test_safe_schema_names_and_example_urls_are_allowed(self):
        self.assertEqual(findings_for('fixture.json',b'{"library_file_id":null,"url":"https://example.com/image"}'),[])
    def test_duplicate_archive_entry_is_rejected(self):
        data=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(data,'w') as archive:
                archive.writestr('same.txt','first');archive.writestr('same.txt','second')
        self.assertTrue(any(f['rule']=='unsafe-archive-entry' for f in inspect_archive(data.getvalue())))
    def test_deleted_secret_is_still_detected_in_history(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def git(*args):return subprocess.run(['git',*args],cwd=root,capture_output=True,check=True)
            git('init');git('config','user.name','Synthetic Fixture');git('config','user.email','fixture@example.com')
            secret='gh'+'p_'+'Y'*36
            path=root/'fixture.txt';path.write_text(secret, encoding='utf-8', newline='\n');git('add','fixture.txt');git('commit','-m','synthetic fixture')
            path.unlink();git('add','-u');git('commit','-m','remove fixture')
            result=scan(root,history=True)
            self.assertEqual(result['status'],'failed');self.assertNotIn(secret,json.dumps(result))
    def test_public_tree_has_no_private_data_or_missing_policy(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(scan(root)['status'],'passed')
        self.assertEqual(check(root)['public_reference_count'],0)

if __name__=='__main__':unittest.main()
