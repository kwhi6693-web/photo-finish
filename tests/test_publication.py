"""Adversarial publication checks; all values are synthetic and never credentials."""
from pathlib import Path
import io,json,subprocess,tempfile,unittest,warnings,zipfile
from check_publication import findings_for,inspect_archive,scan,_historical_zip_findings,KNOWN_MALFORMED_HISTORY_ZIPS
from doctor import check
from build_release import build

class PublicationTests(unittest.TestCase):
    def test_nested_private_profile_cannot_enter_public_policy_or_archive(self):
        value={'nested':{'distribution_scope':'private','fixture_preference':'synthetic'}}
        body=json.dumps(value).encode()
        self.assertTrue(any(f['rule']=='private-profile-policy' for f in findings_for('runtime_policy.json',body)))
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as z:z.writestr('runtime/policy.json',body)
        self.assertTrue(any(f['rule']=='private-profile-policy' for f in inspect_archive(data.getvalue())))
    def test_public_policy_scope_is_explicit(self):
        root=Path(__file__).resolve().parents[1]
        policy=json.loads((root/'runtime/10_SYSTEM_CONFIG/runtime_policy.json').read_text(encoding='utf-8'))
        self.assertEqual(policy['distribution_scope'],'public')
        self.assertFalse(policy['personal_preferences_included'])
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
        for name in ('private.jpeg','.env.production','outputs/job.json', 'catalog.sqlite3',
                     'backup.db', 'style-library/catalog.txt'):
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
    def test_exact_historical_malformed_zip_is_bounded_and_read_only(self):
        root=Path(__file__).resolve().parents[1]
        oid='9a957a58986ad5599801b0b71fdf6eb160336769'
        name='dist/v2.0.0/photo-finish.zip'
        blob=subprocess.run(['git','cat-file','blob',oid],cwd=root,
                            check=True,capture_output=True).stdout
        self.assertEqual(len(blob),90060)
        with self.assertRaises(zipfile.BadZipFile):
            inspect_archive(blob)
        findings,waived=_historical_zip_findings(oid,name,blob)
        self.assertTrue(waived)
        self.assertIsInstance(findings,list)
        for identity in ((('0'*40),name,blob),
                         (oid,'dist/v2.0.0/different.zip',blob),
                         (oid,name,blob[:-1])):
            with self.assertRaisesRegex(zipfile.BadZipFile,'unknown invalid historical ZIP'):
                _historical_zip_findings(*identity)

    def test_known_malformed_zip_raw_credentials_still_trigger_findings(self):
        from unittest.mock import patch
        oid='a'*40
        name='dist/v2.0.0/test-bad.zip'
        # Build the test marker without placing a literal credential in source.
        marker=('gh'+'p_'+'X'*36).encode('ascii')
        data=b'corrupt-zip '+marker
        with patch.object(__import__('check_publication'),'KNOWN_MALFORMED_HISTORY_ZIPS',
                          {(oid,name,len(data))}):
            findings,waived=_historical_zip_findings(oid,name,data)
        self.assertTrue(waived)
        self.assertTrue(any(f['rule']=='github-credential' for f in findings))
        self.assertNotIn(marker.decode(),json.dumps(findings))

    def test_valid_but_unsafe_zip_never_gets_a_corrupt_history_waiver(self):
        from unittest.mock import patch
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            z.writestr('../escaped.txt',b'synthetic')
        data=stream.getvalue();oid='b'*40
        name='dist/v2.0.0/test-unsafe.zip'
        with patch.object(__import__('check_publication'),'KNOWN_MALFORMED_HISTORY_ZIPS',
                          {(oid,name,len(data))}):
            findings,waived=_historical_zip_findings(oid,name,data)
        self.assertFalse(waived)
        self.assertTrue(any(f['rule']=='unsafe-archive-entry' for f in findings))

    def test_public_tree_has_no_private_data_or_missing_policy(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(scan(root)['status'],'passed')
        self.assertEqual(check(root)['public_reference_count'],0)

if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    unittest.main()
