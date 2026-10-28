"""Anonymous adversaries for independent historical and release-ready protection."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

import verify_packages as packages


class FinalizationPolicyTests(unittest.TestCase):
    @contextmanager
    def fixture(self):
        actual = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Exercise the frozen release fixture, independently of current development source.
            # canonical() must still reject later fixture/source/manifest disagreement.
            for name, body in packages.tagged_files(actual, 'v1.5.1').items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
            shutil.copytree(actual / 'dist', root / 'dist')
            yield root

    def test_canonical_requires_source_mapping_and_matching_staged_attachments(self):
        with self.fixture() as root:
            self.assertEqual(packages.canonical(root)['scope'], 'canonical_release_ready_not_published')
            staged = root / 'dist/v1.5.1/photo-finish.zip'
            before = staged.read_bytes()
            staged.write_bytes(b'changed synthetic staged attachment')
            with self.assertRaises(ValueError): packages.canonical(root)
            staged.write_bytes(before)
            (root / 'runtime/10_SYSTEM_CONFIG/scripts/experience.py').write_text(
                'SYNTHETIC = True\n', encoding='utf-8')
            with self.assertRaises(ValueError): packages.canonical(root)

    def test_coordinated_canonical_and_checksum_replacement_cannot_change_pinned_release(self):
        with self.fixture() as root:
            changed = b'coordinated synthetic replacement'
            for folder in (root / 'dist', root / 'dist/v1.5.1'):
                (folder / packages.ARCHIVE).write_bytes(changed)
                (folder / packages.CHECKSUM).write_bytes(
                    (hashlib.sha256(changed).hexdigest() + '  photo-finish.zip\n').encode())
            with self.assertRaisesRegex(ValueError, 'Pinned canonical'):
                packages.canonical(root)
            packages.check_frozen_files(root)  # Historical bytes are independently protected.

    def test_historical_tampering_and_tag_move_remain_blocked(self):
        with self.fixture() as root:
            frozen = root / packages.FROZEN_DIRECTORY / packages.ARCHIVE
            frozen.write_bytes(b'changed synthetic historical archive')
            with self.assertRaises(ValueError): packages.check_frozen_files(root)
            packages.canonical(root)
            with patch.object(packages, 'git', return_value=b'changed-tag\n'):
                with self.assertRaisesRegex(ValueError, 'tag moved'):
                    packages.stable(root)
