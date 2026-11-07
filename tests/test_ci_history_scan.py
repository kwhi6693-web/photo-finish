"""CI history scanner regressions: known corrupt blob never silences other risks."""
from pathlib import Path
from unittest.mock import patch
import io
import json
import subprocess
import tempfile
import unittest
import zipfile
import ci_history_scan as gate
from check_publication import scan


class HistoryZipGateTests(unittest.TestCase):
    def test_actual_pinned_blob_is_malformed_and_exception_is_exact(self):
        root=Path(__file__).resolve().parents[1]
        oid,name,n=gate.KNOWN_INCOMPLETE_HISTORICAL_ZIP
        data=subprocess.run(['git','cat-file','blob',oid],cwd=root,
                            capture_output=True,check=True).stdout
        self.assertEqual(len(data),n)
        with self.assertRaises(zipfile.BadZipFile):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                archive.infolist()
        findings,waiver=gate.inspect_history_blob(oid,name,data)
        self.assertIsNotNone(waiver)
        self.assertEqual(waiver['blob_sha'],oid)
        self.assertIsInstance(findings,list)
        for args in ((('0'*40),name,data),
                     (oid,name+'-different.zip',data),
                     (oid,name,data[:-1])):
            findings,waiver=gate.inspect_history_blob(*args)
            self.assertIsNone(waiver)
            self.assertTrue(any(f['rule']=='invalid-unknown-historical-zip' for f in findings))

    def test_exact_exception_still_scans_raw_credentials(self):
        oid='a'*40
        name='dist/v2.0.0/old.zip'
        token=('gh'+'p_'+'X'*36).encode()
        data=b'invalid archive '+token
        with patch.object(gate,'KNOWN_INCOMPLETE_HISTORICAL_ZIP',(oid,name,len(data))):
            findings,waiver=gate.inspect_history_blob(oid,name,data)
        self.assertIsNotNone(waiver)
        self.assertTrue(any(f['rule']=='github-credential' for f in findings))
        self.assertNotIn(token.decode(),json.dumps(findings))

    def test_valid_traversal_or_private_zip_is_not_waived(self):
        for path,payload in (('../escape.txt',b'fixture'),
                             ('runtime/private.json',b'{"distribution_scope":"private"}')):
            data=io.BytesIO()
            with zipfile.ZipFile(data,'w') as archive:
                archive.writestr(path,payload)
            oid='b'*40;name='dist/v2.0.0/unsafe.zip';body=data.getvalue()
            with patch.object(gate,'KNOWN_INCOMPLETE_HISTORICAL_ZIP',
                              (oid,name,len(body))):
                findings,waiver=gate.inspect_history_blob(oid,name,body)
            self.assertIsNone(waiver)
            self.assertTrue(findings)

    def test_worktree_malformed_zip_still_raises(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'bad.zip').write_bytes(b'corrupt')
            with self.assertRaises(zipfile.BadZipFile):
                scan(root,history=False)

    def test_unrecognized_historical_zip_fails_in_real_git_history(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def git(*args):
                return subprocess.run(['git',*args],cwd=root,check=True,
                                      capture_output=True,text=True,encoding='utf-8').stdout
            git('init');git('config','user.name','Fixture')
            git('config','user.email','fixture@example.com')
            (root/'legacy.zip').write_bytes(b'not a zip')
            git('add','legacy.zip');git('commit','-m','malformed test object')
            (root/'legacy.zip').unlink()
            git('add','-u');git('commit','-m','remove malformed test object')
            report=gate.audit(root)
            self.assertEqual(report['status'],'failed')
            self.assertTrue(any(f['rule']=='invalid-unknown-historical-zip'
                                for f in report['findings']))

    def test_deleted_historical_secret_remains_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def git(*args):
                return subprocess.run(['git',*args],cwd=root,check=True,
                                      capture_output=True,text=True,encoding='utf-8').stdout
            git('init');git('config','user.name','Fixture')
            git('config','user.email','fixture@example.com')
            secret='gh'+'p_'+'Y'*36
            (root/'notes.txt').write_text(secret)
            git('add','notes.txt');git('commit','-m','fixture')
            (root/'notes.txt').unlink()
            git('add','-u');git('commit','-m','delete fixture')
            report=gate.audit(root)
            self.assertEqual(report['status'],'failed')
            self.assertTrue(any(f['rule']=='github-credential' for f in report['findings']))
            self.assertNotIn(secret,json.dumps(report))


if __name__=='__main__':
    unittest.main()
