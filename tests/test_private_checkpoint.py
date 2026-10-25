"""Private snapshot integrity/recovery using synthetic files, no host claims."""
from pathlib import Path
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile


class PrivateCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'private'
        self.root.mkdir()
        (self.root/'job.json').write_bytes(b'{"kind":"synthetic","status":"unknown"}')
        (self.root/'output.bin').write_bytes(b'synthetic-immutable-output')
        self.archive = self.base/'checkpoint.zip'

    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('private_checkpoint'),
                             'Private checkpoints must preserve explicitly selected task files')
        import private_checkpoint
        return private_checkpoint

    def export(self):
        return self.api().export(self.root, self.archive, ['job.json', 'output.bin'])

    def test_repeat_export_reuses_exact_bytes_without_claiming_remote_persistence(self):
        c = self.api()
        with patch.object(c.zipfile.time, 'localtime', return_value=(2020, 1, 1, 0, 0, 0, 2, 1, 0)):
            first = self.export()
        before = self.archive.read_bytes()
        with patch.object(c.zipfile.time, 'localtime', return_value=(2021, 1, 1, 0, 0, 0, 4, 1, 0)):
            again = self.export()
        self.assertEqual(self.archive.read_bytes(), before)
        self.assertEqual(first['sha256'], again['sha256'])
        self.assertTrue(again['reused'])
        self.assertFalse(again['persistent_save_confirmed'])

    def test_changed_source_cannot_overwrite_checkpoint_or_immutable_history(self):
        self.export()
        before = self.archive.read_bytes()
        (self.root/'job.json').write_bytes(b'{"changed":true}')
        with self.assertRaises(FileExistsError):
            self.export()
        self.assertEqual(self.archive.read_bytes(), before)

    def test_interrupted_restore_resumes_same_archive_and_preserves_old_bytes(self):
        c = self.api()
        receipt = self.export()
        dest = self.base/'restored'
        link = c.os.link
        def interrupt(source, target):
            if Path(target).name == 'output.bin':
                raise OSError('Synthetic interruption before second publication')
            return link(source, target)
        with patch.object(c.os, 'link', side_effect=interrupt):
            with self.assertRaises(OSError):
                c.restore(self.archive, dest, receipt['sha256'])
        original_job = (dest/'job.json').read_bytes()
        c.restore(self.archive, dest, receipt['sha256'])
        c.restore(self.archive, dest, receipt['sha256'])
        self.assertEqual((dest/'job.json').read_bytes(), original_job)
        self.assertEqual((dest/'output.bin').read_bytes(), b'synthetic-immutable-output')

    def test_restore_never_writes_into_an_unowned_existing_directory(self):
        c = self.api(); receipt = self.export()
        dest = self.base/'unrelated'; dest.mkdir()
        (dest/'job.json').write_bytes(b'previous-user-history')
        with self.assertRaises(FileExistsError):
            c.restore(self.archive, dest, receipt['sha256'])
        self.assertEqual((dest/'job.json').read_bytes(), b'previous-user-history')

    def test_changed_existing_restored_file_is_not_silently_overwritten(self):
        c = self.api(); receipt = self.export(); dest = self.base/'restored'
        c.restore(self.archive, dest, receipt['sha256'])
        (dest/'job.json').write_bytes(b'new-user-work')
        with self.assertRaises(ValueError):
            c.restore(self.archive, dest, receipt['sha256'])
        self.assertEqual((dest/'job.json').read_bytes(), b'new-user-work')

    def test_sqlite_wal_rows_are_in_snapshot_without_rewriting_source(self):
        c = self.api(); db = self.root/'tasks.sqlite3'
        connection = sqlite3.connect(db); self.addCleanup(connection.close)
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('CREATE TABLE tasks (label TEXT)')
        connection.execute("INSERT INTO tasks VALUES ('SYNTHETIC_V1')"); connection.commit()
        result = c.export(self.root, self.archive, ['tasks.sqlite3'])
        dest = self.base/'restored'; c.restore(self.archive, dest, result['sha256'])
        with sqlite3.connect(dest/'tasks.sqlite3') as restored:
            self.assertEqual(restored.execute('SELECT label FROM tasks').fetchall(), [('SYNTHETIC_V1',)])
        self.assertEqual(connection.execute('SELECT label FROM tasks').fetchall(), [('SYNTHETIC_V1',)])

    def test_archive_traversal_rejected_before_destination_is_created(self):
        c = self.api(); dest = self.base/'restored'
        with zipfile.ZipFile(self.archive, 'w') as z:
            z.writestr('../escape', b'bad')
            z.writestr('manifest.json', '{}')
        with self.assertRaises(ValueError):
            c.restore(self.archive, dest)
        self.assertFalse(dest.exists())
        self.assertFalse((self.base/'escape').exists())

    def test_symlink_sources_cannot_enter_a_private_checkpoint(self):
        c = self.api()
        try:
            (self.root/'link').symlink_to(self.root/'job.json')
        except OSError as error:
            self.skipTest('Host does not permit creating test symlinks: '+str(error))
        with self.assertRaises(ValueError):
            c.export(self.root, self.archive, ['link'])

    def test_git_sources_cannot_enter_a_private_checkpoint(self):
        self.api()
        (self.root/'.git').mkdir()
        with self.assertRaises(ValueError):
            self.export()

    def test_archive_changed_after_validation_cannot_publish_unverified_bytes(self):
        c = self.api(); self.export(); inspect = c.inspect
        def changed_archive(*args, **kwargs):
            proof = inspect(*args, **kwargs)
            with zipfile.ZipFile(self.archive) as z:
                members = {name: z.read(name) for name in z.namelist()}
            members['output.bin'] = b'changed-after-validation'
            with zipfile.ZipFile(self.archive, 'w') as z:
                for name, data in members.items():
                    z.writestr(name, data)
            return proof
        dest = self.base/'restored'
        with patch.object(c, 'inspect', side_effect=changed_archive):
            with self.assertRaises(ValueError):
                c.restore(self.archive, dest)
        self.assertFalse((dest/'output.bin').exists())
