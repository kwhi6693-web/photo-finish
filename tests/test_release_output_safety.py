"""Release builds must not replace historical or concurrently created outputs."""
from contextlib import contextmanager
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_release as builder


class ReleaseOutputSafetyTests(unittest.TestCase):
    @contextmanager
    def project(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            root = base / 'project'
            config = root / 'runtime/10_SYSTEM_CONFIG'
            config.mkdir(parents=True)
            (root / 'SKILL.md').write_text('Synthetic public skill\n', encoding='utf-8')
            (config / 'SESSION_BRIEF.json').write_text(
                '{"runtime_version":"1.5.5"}', encoding='utf-8')
            yield root, base

    def test_existing_archive_and_checksum_are_not_replaced(self):
        with self.project() as (root, base):
            output = base / 'release.zip'
            builder.build(output, root)
            checksum = output.with_suffix('.zip.sha256')
            before = output.read_bytes(), checksum.read_bytes()
            (root / 'SKILL.md').write_text('Changed public source\n', encoding='utf-8')
            with self.assertRaises((ValueError, FileExistsError)):
                builder.build(output, root)
            self.assertEqual((output.read_bytes(), checksum.read_bytes()), before)

    def test_orphan_checksum_is_preserved_without_creating_archive(self):
        with self.project() as (root, base):
            output = base / 'release.zip'
            checksum = output.with_suffix('.zip.sha256')
            checksum.write_bytes(b'Existing checksum evidence\n')
            with self.assertRaises((ValueError, FileExistsError)):
                builder.build(output, root)
            self.assertEqual(checksum.read_bytes(), b'Existing checksum evidence\n')
            self.assertFalse(output.exists())

    def test_historical_canonical_path_is_rejected_even_when_missing(self):
        with self.project() as (root, _):
            with self.assertRaises(ValueError):
                builder.build(root / 'dist/photo-finish.zip', root)
            self.assertFalse((root / 'dist').exists())

    def test_wrong_version_directory_is_rejected_before_writing(self):
        with self.project() as (root, _):
            with self.assertRaises(ValueError):
                builder.build(root / 'dist/v1.5.4/photo-finish.zip', root)
            self.assertFalse((root / 'dist').exists())

    def test_matching_new_version_directory_can_be_staged(self):
        with self.project() as (root, _):
            output = root / 'dist/v1.5.5/photo-finish.zip'
            builder.build(output, root)
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read('photo-finish/release-manifest.json'))
            self.assertEqual(manifest['version'], '1.5.5')
            self.assertTrue(output.with_suffix('.zip.sha256').is_file())

    def test_concurrent_output_creation_cannot_be_overwritten(self):
        for suffix in ('.zip', '.zip.sha256'):
            with self.subTest(suffix=suffix), self.project() as (root, base):
                output = base / 'release.zip'
                occupied = output.with_suffix(suffix)
                inspect = builder.inspect_archive

                def concurrent_writer(data):
                    result = inspect(data)
                    occupied.write_bytes(b'Another writer owns this file\n')
                    return result

                with patch.object(builder, 'inspect_archive', side_effect=concurrent_writer):
                    with self.assertRaises((ValueError, FileExistsError)):
                        builder.build(output, root)
                self.assertEqual(occupied.read_bytes(), b'Another writer owns this file\n')
                other = output.with_suffix('.zip.sha256') if suffix == '.zip' else output
                self.assertFalse(other.exists())

    def test_dangling_output_symlink_is_preserved(self):
        with self.project() as (root, base):
            output = base / 'release.zip'
            target = base / 'missing.zip'
            try:
                output.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest('Host cannot create a symlink')
            with self.assertRaises((ValueError, FileExistsError)):
                builder.build(output, root)
            self.assertTrue(output.is_symlink())
            self.assertFalse(target.exists())

    def test_cli_requires_output_without_touching_canonical_archive(self):
        with self.project() as (root, _):
            tools = root / 'tools'
            tools.mkdir()
            for name in ('build_release.py', 'check_publication.py'):
                shutil.copyfile(builder.ROOT / 'tools' / name, tools / name)
            result = subprocess.run([sys.executable, '-B', str(tools / 'build_release.py')],
                                    cwd=root, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('--output', result.stderr)
            self.assertFalse((root / 'dist').exists())
