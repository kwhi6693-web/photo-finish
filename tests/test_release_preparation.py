"""Synthetic staged maintenance failures; no live install or remote writes."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_release as builder
import verify_release_preparation as preparation
import verify_packages as packages


class ReleasePreparationTests(unittest.TestCase):
    def fixture(self, root):
        config = root / 'runtime/10_SYSTEM_CONFIG'
        config.mkdir(parents=True)
        (root / 'SKILL.md').write_text('Synthetic skill\n', encoding='utf-8')
        (config / 'SESSION_BRIEF.json').write_text('{"runtime_version":"1.5.3"}', encoding='utf-8')
        (config / 'runtime_policy.json').write_text(json.dumps({
            'runtime_version': '1.5.3', 'distribution': {'version': '1.5.3'},
            'beautification_defaults': {'versions': {'runtime': '1.5.3'}}}), encoding='utf-8')
        output = root / 'dist/v1.5.3/photo-finish.zip'
        builder.build(output, root)
        return output

    def test_manifest_version_comes_from_source_not_old_release_constant(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self.fixture(Path(tmp))
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(json.loads(archive.read('photo-finish/release-manifest.json'))['version'], '1.5.3')

    def test_tampered_staged_archive_fails_before_installed_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = self.fixture(root)
            output.write_bytes(b'corrupt synthetic archive')
            with patch.object(preparation.subprocess, 'run') as child:
                with self.assertRaises((ValueError, zipfile.BadZipFile)):
                    preparation.verify(root)
                child.assert_not_called()

    def test_mismatched_installation_version_fails_before_build_or_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            brief = root / 'runtime/10_SYSTEM_CONFIG/SESSION_BRIEF.json'
            brief.write_text('{"runtime_version":"1.5.0"}', encoding='utf-8')
            with patch.object(preparation.subprocess, 'run') as child:
                with self.assertRaisesRegex(ValueError, 'versions differ'):
                    preparation.verify(root)
                child.assert_not_called()

    def committed_fixture(self, root, *, versioned):
        output = self.fixture(root)
        if versioned:
            # The historical canonical archive must not be selected for this tag.
            (root / 'dist/photo-finish.zip').write_bytes(b'SYNTHETIC historical canonical bytes')
        else:
            shutil.copy2(output, root / 'dist/photo-finish.zip')
            shutil.copy2(output.with_suffix('.zip.sha256'), root / 'dist/photo-finish.zip.sha256')
            shutil.rmtree(output.parent)
        # Local anonymous Git fixture only; no repository/remote tag is created.
        for args in (('init', '-q'), ('add', '.'),
                     ('-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@example.com',
                      'commit', '-qm', 'Synthetic package fixture'), ('tag', 'v1.5.3')):
            subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
        assets = root / 'attachments'
        assets.mkdir()
        source = output.parent if versioned else root / 'dist'
        for name in (packages.ARCHIVE, packages.CHECKSUM):
            shutil.copy2(source / name, assets / name)
        return assets

    def test_tagged_release_uses_exact_versioned_package_and_keeps_legacy_layout(self):
        for versioned in (True, False):
            with self.subTest(versioned=versioned), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                assets = self.committed_fixture(root, versioned=versioned)
                result = packages.release(root, 'v1.5.3', assets)
                self.assertEqual(result['status'], 'passed')
                self.assertEqual(result['sha256'], packages.digest((assets / packages.ARCHIVE).read_bytes()))

    def test_versioned_release_rejects_replaced_attachment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = self.committed_fixture(root, versioned=True)
            (assets / packages.ARCHIVE).write_bytes(b'SYNTHETIC replaced attachment')
            with self.assertRaisesRegex(ValueError, 'attachment differs'):
                packages.release(root, 'v1.5.3', assets)
