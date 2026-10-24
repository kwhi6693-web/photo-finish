"""Portable private backup/merge and hostile-archive boundaries."""
from pathlib import Path
from contextlib import closing
import importlib, json, os, sqlite3, sys, tempfile, unittest, zipfile
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts'))

class PersonalBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'source-store';self.target=self.base/'restored'
        env=patch.dict(os.environ,{'PHOTO_FINISH_STYLE_LIBRARY':str(self.root)});env.start();self.addCleanup(env.stop)
        self.photo=self.base/'source.png';Image.new('RGB',(24,32),(70,90,100)).save(self.photo)

    def module(self):
        try:return importlib.import_module('personal_backup')
        except ImportError:self.fail('Private backup support is missing')

    def fixture(self):
        import style_library as s,user_preferences as p
        saved=s.add(self.photo,'Backup title',consent=True)
        s.update(saved['reference_id'],group='Travel',pinned=True,use_for=['light'],consent=True)
        p.save(rules=['Saved global rule'],consent=True)
        p.add_rule('Saved night rule',scenes=['F'],consent=True)
        return saved

    def test_empty_target_roundtrip_preserves_photos_metadata_rules_and_history(self):
        b=self.module();saved=self.fixture();archive=self.base/'backup.zip'
        (self.root/'unindexed.txt').write_text('Not part of the backup')
        result=b.export_backup(archive)
        self.assertEqual(result['style_count'],1)
        with zipfile.ZipFile(archive) as z:
            self.assertNotIn('unindexed.txt',z.namelist())
            self.assertNotIn(str(self.root).encode(),z.read('catalog.json'))
        plan=b.inspect_backup(archive,library_root=self.target)
        self.assertFalse(self.target.exists());self.assertEqual(plan['new_styles'],1)
        restored=b.import_backup(archive,consent=True,library_root=self.target)
        self.assertEqual(restored['imported_styles'],1)
        import style_library as s,user_preferences as p
        photo=s.list_references(library_root=self.target)['references'][0]
        self.assertEqual(Path(photo['path']).read_bytes(),self.photo.read_bytes())
        self.assertEqual(photo['group'],'Travel');self.assertEqual(photo['use_for'],['light'])
        self.assertEqual(p.show(library_root=self.target,scenes=['F'])['active_rules'],['Saved global rule','Saved night rule'])
        self.assertTrue(p.history(library_root=self.target)['revisions'])
        self.assertEqual(photo['reference_id'],saved['reference_id'])

    def test_merge_preserves_existing_values_and_explicit_backup_policy_can_replace_metadata(self):
        b=self.module();saved=self.fixture();archive=self.base/'backup.zip';b.export_backup(archive)
        import style_library as s,user_preferences as p
        s.add(self.photo,'Local title',consent=True,library_root=self.target)
        p.save(rules=['Local rule'],consent=True,library_root=self.target)
        plan=b.inspect_backup(archive,library_root=self.target)
        self.assertTrue(plan['conflicts'])
        b.import_backup(archive,consent=True,library_root=self.target)
        self.assertEqual(s.list_references(library_root=self.target)['references'][0]['title'],'Local title')
        self.assertEqual(p.show(library_root=self.target)['rules'],['Local rule'])
        b.import_backup(archive,consent=True,library_root=self.target,style_policy='use_backup',settings_policy='use_backup')
        self.assertEqual(s.list_references(library_root=self.target)['references'][0]['title'],'Backup title')
        self.assertEqual(p.show(library_root=self.target)['rules'],['Saved global rule'])
        p.undo(consent=True,library_root=self.target)
        self.assertEqual(p.show(library_root=self.target)['rules'],['Local rule'])
        self.assertEqual(Path(s.list_references(library_root=self.target)['references'][0]['path']).read_bytes(),self.photo.read_bytes())

    def test_changed_image_hash_fails_before_any_target_write(self):
        b=self.module();self.fixture();archive=self.base/'backup.zip';b.export_backup(archive)
        changed=self.base/'changed.zip'
        with zipfile.ZipFile(archive) as source,zipfile.ZipFile(changed,'w') as dest:
            for info in source.infolist():
                data=source.read(info)
                dest.writestr(info,b'changed bytes' if info.filename.startswith('images/') else data)
        with self.assertRaises(ValueError):b.import_backup(changed,consent=True,library_root=self.target)
        self.assertFalse(self.target.exists())

    def test_unlisted_traversal_symlink_duplicate_and_future_format_are_rejected(self):
        b=self.module();self.fixture();archive=self.base/'backup.zip';b.export_backup(archive)
        for kind in ('traversal','symlink','duplicate','future'):
            bad=self.base/(kind+'.zip')
            with zipfile.ZipFile(archive) as source,zipfile.ZipFile(bad,'w') as dest:
                for info in source.infolist():
                    data=source.read(info)
                    if kind=='future' and info.filename=='manifest.json':
                        value=json.loads(data);value['version']=999;data=json.dumps(value).encode()
                    dest.writestr(info,data)
                if kind=='traversal':dest.writestr('../escape.txt','escape')
                if kind=='symlink':
                    info=zipfile.ZipInfo('images/link.png');info.create_system=3;info.external_attr=0o120777<<16;dest.writestr(info,'outside')
                if kind=='duplicate':
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore',UserWarning);dest.writestr('catalog.json',b'{}')
            with self.subTest(kind=kind),self.assertRaises(ValueError):b.import_backup(bad,consent=True,library_root=self.target)
            self.assertFalse(self.target.exists())
        self.assertFalse((self.base/'escape.txt').exists())

    def test_export_does_not_overwrite_or_use_git_and_import_requires_consent(self):
        b=self.module();self.fixture();archive=self.base/'backup.zip';b.export_backup(archive);before=archive.read_bytes()
        with self.assertRaises(FileExistsError):b.export_backup(archive)
        self.assertEqual(archive.read_bytes(),before)
        with self.assertRaises(ValueError):b.export_backup(ROOT/'backup.zip')
        with self.assertRaises(ValueError):b.export_backup(self.root/'inside.zip')
        with self.assertRaises(ValueError):b.import_backup(archive,library_root=self.target)
        self.assertFalse(self.target.exists())
        empty=self.base/'empty-store';b.export_backup(self.base/'empty.zip',library_root=empty)
        self.assertFalse(empty.exists())

    def test_failed_catalog_write_rolls_back_new_image_copies(self):
        b=self.module();import style_library as s
        s.add(self.photo,'Large metadata',labels=[str(i)+'x'*75 for i in range(32)],note='x'*2000,consent=True)
        archive=self.base/'backup.zip';b.export_backup(archive)
        connect=sqlite3.connect
        def limited(*args,**kwargs):
            conn=connect(*args,**kwargs);conn.execute('PRAGMA max_page_count=3');return conn
        with patch.object(s.sqlite3,'connect',limited),self.assertRaises(ValueError):
            b.import_backup(archive,consent=True,library_root=self.target)
        self.assertEqual(list((self.target/'images').glob('*')) if (self.target/'images').exists() else [],[])

    def test_export_size_limit_includes_catalog_and_manifest(self):
        b=self.module();destination=self.base/'too-small.zip'
        with patch.object(b,'MAX_TOTAL',64),self.assertRaises(ValueError):b.export_backup(destination)
        self.assertFalse(destination.exists())

    def test_import_binds_the_inspected_archive_identity(self):
        b=self.module();self.fixture();archive=self.base/'backup.zip';b.export_backup(archive)
        with self.assertRaises(ValueError):
            b.import_backup(archive,consent=True,library_root=self.target,expected_archive_sha256='0'*64)
        self.assertFalse(self.target.exists())

    def test_null_style_metadata_is_rejected_before_target_writes(self):
        import hashlib
        b=self.module();self.fixture();archive=self.base/'backup.zip';b.export_backup(archive)
        for field in ('subject','labels','tags','individual_note','group','pinned','use_for'):
            bad=self.base/('null-'+field+'.zip')
            with zipfile.ZipFile(archive) as source:
                data={n:source.read(n) for n in source.namelist()}
            catalog=json.loads(data['catalog.json']);catalog['styles'][0][field]=None
            data['catalog.json']=json.dumps(catalog,ensure_ascii=False).encode()
            manifest=json.loads(data['manifest.json']);manifest['files']['catalog.json']={
                'sha256':hashlib.sha256(data['catalog.json']).hexdigest(),'bytes':len(data['catalog.json'])}
            data['manifest.json']=json.dumps(manifest).encode()
            with zipfile.ZipFile(bad,'w') as dest:
                for name,content in data.items():dest.writestr(name,content)
            with self.subTest(field=field),self.assertRaises(ValueError):
                b.import_backup(bad,consent=True,library_root=self.target)
            self.assertFalse(self.target.exists())

    def test_backup_validation_handles_temporary_directory_alias(self):
        b=self.module();self.fixture();archive=self.base/'backup.zip';b.export_backup(archive)
        real=self.base/'real-temp';real.mkdir();alias=self.base/'temp-alias'
        try:alias.symlink_to(real,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('Directory symlinks unavailable; native platform paths remain covered by roundtrip tests')
        original=tempfile.TemporaryDirectory
        def aliased(*args,**kwargs):
            kwargs['dir']=alias
            return original(*args,**kwargs)
        with patch.object(b.tempfile,'TemporaryDirectory',aliased):
            result=b.inspect_backup(archive,library_root=self.target)
        self.assertEqual(result['new_styles'],1)
        self.assertFalse(self.target.exists())

if __name__=='__main__':unittest.main()
