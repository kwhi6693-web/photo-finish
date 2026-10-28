"""Isolated recovery of synthetic saved versions; no actual host calls."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/10_SYSTEM_CONFIG/scripts'))
from tests import test_recovery_archive as fixtures
import recovery_archive as archive
import workflow_session as workflow


class VersionRecoveryTests(unittest.TestCase):
    setUp = fixtures.RecoveryArchiveTests.setUp
    accept = fixtures.RecoveryArchiveTests.accept
    save_fixture = fixtures.RecoveryArchiveTests.save_fixture
    ready = fixtures.RecoveryArchiveTests.ready
    materialization = fixtures.RecoveryArchiveTests.materialization
    prepare = fixtures.RecoveryArchiveTests.prepare

    def inputs(self):
        self.ready()
        state = self.prepare()
        folder = self.d / 'new-host'
        folder.mkdir()
        package = folder / 'archive.zip'
        shutil.copyfile(state['archive']['path'], package)
        transfer = folder / 'archive-transfer.json'
        self.materialization(transfer, package, 'SYNTHETIC_ARCHIVE')
        cloud = []
        for source, identity in [(self.s, 'SYNTHETIC_SOURCE'), (self.o, 'SYNTHETIC_OUTPUT'),
                                 (self.rec, 'SYNTHETIC_RECORD')]:
            local = folder / source.name
            shutil.copyfile(source, local)
            result = folder / (source.stem + '-transfer.json')
            self.materialization(result, local, identity)
            cloud.append({'path': str(local), 'result_path': str(result)})
        return dict(archive_path=str(package), expected_sha256=state['archive']['sha256'],
                    archive_library_file_id='SYNTHETIC_ARCHIVE', result_path=str(transfer),
                    cloud_files=cloud, destination=str(self.d / 'restored-private'))

    def module(self):
        import version_recovery
        return version_recovery

    def test_restore_after_old_state_loss_keeps_identity_and_exact_pixels_without_render(self):
        args = self.inputs()
        expected = self.o.read_bytes()
        shutil.rmtree(self.session)
        for p in [self.j, self.s, self.o, self.rec, self.receipt]:
            p.unlink()
        module = self.module()
        with patch.object(workflow, '_load', side_effect=AssertionError('old ledger accessed')):
            result = module.restore(**args)
            current = module.status(args['destination'])
        self.assertEqual(result['status'], 'restored_read_only')
        self.assertEqual(current['series'], self.item['series'])
        self.assertEqual(current['label'], 'V1')
        self.assertIsNone(current['parent_version'])
        self.assertEqual(Path(current['output']['path']).read_bytes(), expected)
        self.assertEqual(current['source']['sha256'], self.item['source']['sha256'])
        self.assertEqual(current['renderer_calls'], 0)
        self.assertFalse(current['write_allowed'])
        self.assertFalse((Path(args['destination']) / 'tasks.sqlite3').exists())

    def test_repeat_reuses_target_but_conflicting_target_is_never_changed(self):
        args = self.inputs()
        module = self.module()
        module.restore(**args)
        target = Path(args['destination'])
        before = {str(p.relative_to(target)): p.read_bytes() for p in target.rglob('*') if p.is_file()}
        self.assertEqual(module.restore(**args)['status'], 'restored_read_only')
        self.assertEqual(before, {str(p.relative_to(target)): p.read_bytes() for p in target.rglob('*') if p.is_file()})
        occupied = self.d / 'existing'
        occupied.mkdir()
        (occupied / 'sentinel').write_bytes(b'original')
        args['destination'] = str(occupied)
        with self.assertRaises((ValueError, FileExistsError)):
            module.restore(**args)
        self.assertEqual(list(occupied.iterdir()), [occupied / 'sentinel'])
        self.assertEqual((occupied / 'sentinel').read_bytes(), b'original')

    def test_cloud_identity_or_bytes_conflict_is_rejected_before_destination_write(self):
        args = self.inputs()
        module = self.module()
        transfer = Path(args['cloud_files'][1]['result_path'])
        self.materialization(transfer, Path(args['cloud_files'][1]['path']), 'WRONG_CLOUD_ID')
        with self.assertRaisesRegex(ValueError, 'identity'):
            module.restore(**args)
        self.assertFalse(Path(args['destination']).exists())
        self.materialization(transfer, Path(args['cloud_files'][1]['path']), 'SYNTHETIC_OUTPUT')
        Path(args['cloud_files'][1]['path']).write_bytes(b'wrong bytes')
        with self.assertRaises(ValueError):
            module.restore(**args)
        self.assertFalse(Path(args['destination']).exists())

    def test_interruption_is_incomplete_then_resumes_without_changing_originals(self):
        args = self.inputs()
        module = self.module()
        protected = [self.j, self.s, self.o, self.rec, self.session / 'tasks.sqlite3']
        before = [p.read_bytes() for p in protected]
        publish = archive._publish
        def interrupt(path, data):
            if Path(path).parent.name == 'assets':
                raise OSError('Synthetic interrupted copy')
            return publish(path, data)
        with patch.object(archive, '_publish', side_effect=interrupt), self.assertRaises(OSError):
            module.restore(**args)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            module.status(args['destination'])
        self.assertEqual(module.restore(**args)['status'], 'restored_read_only')
        self.assertEqual(before, [p.read_bytes() for p in protected])

    def test_tampered_restored_file_or_cursor_cannot_be_used_as_verified_version(self):
        args = self.inputs()
        module = self.module()
        result = module.restore(**args)
        Path(result['output']['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            module.status(args['destination'])

    def test_interrupted_restore_resumes_after_archive_readback_path_changes(self):
        args = self.inputs()
        module = self.module()
        with patch.object(archive, '_publish', side_effect=OSError('Synthetic interruption')):
            with self.assertRaises(OSError):
                module.restore(**args)
        # Use a second clean target to interrupt after the immutable owner exists.
        args['destination'] += '-owned'
        publish = archive._publish
        def interrupt(path, data):
            if Path(path).parent.name == 'assets':
                raise OSError('Synthetic interruption')
            return publish(path, data)
        with patch.object(archive, '_publish', side_effect=interrupt), self.assertRaises(OSError):
            module.restore(**args)
        moved = Path(args['archive_path']).with_name('relocated-readback.zip')
        shutil.copyfile(args['archive_path'], moved)
        args['archive_path'] = str(moved)
        proof = moved.with_suffix('.json')
        self.materialization(proof, moved, 'SYNTHETIC_ARCHIVE')
        args['result_path'] = str(proof)
        self.assertEqual(module.restore(**args)['status'], 'restored_read_only')

    def test_missing_host_proofs_or_changed_archive_id_block_status(self):
        args = self.inputs()
        module = self.module()
        module.restore(**args)
        root = Path(args['destination'])
        owner = root / 'identity.json'
        value = json.loads(owner.read_text())
        value['archive_library_file_id'] = 'WRONG_CLOUD_ID'
        owner.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            module.status(root)

    def test_restored_assets_parent_symlink_is_rejected(self):
        args = self.inputs()
        module = self.module()
        module.restore(**args)
        root = Path(args['destination'])
        assets = root / 'assets'
        moved = root.parent / 'external-assets'
        assets.rename(moved)
        try:
            assets.symlink_to(moved, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not allow directory symlinks')
        with self.assertRaises(ValueError):
            module.status(root)


if __name__ == '__main__':
    unittest.main()
