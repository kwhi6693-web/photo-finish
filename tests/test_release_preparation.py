"""Synthetic staged maintenance failures; no live install or remote writes."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_release as builder
import verify_release_preparation as preparation


class ReleasePreparationTests(unittest.TestCase):
    def fixture(self, root):
        config = root / 'runtime/10_SYSTEM_CONFIG'
        config.mkdir(parents=True)
        (root / 'SKILL.md').write_text('Synthetic skill\n', encoding='utf-8')
        (config / 'SESSION_BRIEF.json').write_text('{"runtime_version":"1.5.2"}', encoding='utf-8')
        (config / 'runtime_policy.json').write_text(json.dumps({
            'runtime_version': '1.5.2', 'distribution': {'version': '1.5.2'},
            'beautification_defaults': {'versions': {'runtime': '1.5.2'}}}), encoding='utf-8')
        output = root / 'dist/v1.5.2/photo-finish.zip'
        builder.build(output, root)
        return output

    def test_manifest_version_comes_from_source_not_old_release_constant(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self.fixture(Path(tmp))
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(json.loads(archive.read('photo-finish/release-manifest.json'))['version'], '1.5.2')

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
