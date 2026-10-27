"""Anonymous packaging adversaries; no release creation or remote writes."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_release as b


class PackagePolicyTests(unittest.TestCase):
    @contextmanager
    def project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'project'
            (root / 'runtime/10_SYSTEM_CONFIG').mkdir(parents=True)
            (root / 'SKILL.md').write_text('Synthetic public skill\n', encoding='utf-8')
            (root / 'runtime/fixture.py').write_text('value = 1\n', encoding='utf-8')
            (root / 'runtime/10_SYSTEM_CONFIG/SESSION_BRIEF.json').write_text(
                '{"runtime_version":"1.5.0"}', encoding='utf-8')
            yield root

    def test_candidate_is_distinct_and_rejects_repository_destination(self):
        with self.project() as root, tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'candidate.zip'
            try:
                b.build(dest, root, candidate=True)
            except TypeError:
                self.fail('Builder lacks an explicit candidate mode')
            with zipfile.ZipFile(dest) as z:
                manifest = json.loads(z.read('photo-finish/release-manifest.json'))
            self.assertEqual(manifest['version'], '0+candidate')
            self.assertEqual(manifest['distribution_channel'], 'candidate')
            with self.assertRaises(ValueError):
                b.build(root / 'dist/photo-finish.zip', root, candidate=True)
            self.assertFalse((root / 'dist').exists())

    def test_real_source_change_is_valid_candidate_without_touching_stable(self):
        import verify_packages as v
        with self.project() as root, tempfile.TemporaryDirectory() as tmp:
            dest = root / 'dist/photo-finish.zip'
            b.build(dest, root)
            before = dest.read_bytes()
            (root / 'runtime/fixture.py').write_text('value = 2\n', encoding='utf-8')
            result = v.candidate(root)
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(dest.read_bytes(), before)

    def test_valid_payload_with_nondeterministic_zip_metadata_fails(self):
        import verify_packages as v
        with self.project() as root:
            original = b.build
            calls = []
            def altered(destination, *args, **kwargs):
                result = original(destination, *args, **kwargs)
                calls.append(destination)
                if len(calls) == 2:
                    with zipfile.ZipFile(destination) as z:
                        entries = [(n, z.read(n)) for n in z.namelist()]
                    with zipfile.ZipFile(destination, 'w') as z:
                        for name, body in entries:
                            info = zipfile.ZipInfo(name, date_time=(2025, 1, 1, 0, 0, 0))
                            z.writestr(info, body)
                    destination.with_suffix('.zip.sha256').write_bytes(
                        (hashlib.sha256(destination.read_bytes()).hexdigest() + '  candidate.zip\n').encode())
                return result
            with patch.object(b, 'build', side_effect=altered), self.assertRaisesRegex(ValueError, 'deterministic'):
                v.candidate(root)

    def test_stable_zip_or_checksum_tampering_fails_even_if_both_updated(self):
        import verify_packages as v
        actual = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'dist').mkdir()
            for name in ('photo-finish.zip', 'photo-finish.zip.sha256'):
                shutil.copyfile(actual / 'dist' / name, root / 'dist' / name)
            for name in ('photo-finish.zip', 'photo-finish.zip.sha256'):
                original = (root / 'dist' / name).read_bytes()
                (root / 'dist' / name).write_bytes(original + b'tamper')
                with self.assertRaises(ValueError):
                    v.check_frozen_files(root)
                (root / 'dist' / name).write_bytes(original)
            changed = b'changed synthetic artifact'
            (root / 'dist/photo-finish.zip').write_bytes(changed)
            (root / 'dist/photo-finish.zip.sha256').write_text(
                hashlib.sha256(changed).hexdigest() + '  photo-finish.zip\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                v.check_frozen_files(root)

    def test_archive_mapping_manifest_payload_and_candidate_identity_are_checked(self):
        import verify_packages as v
        with self.project() as root, tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'candidate.zip'
            b.build(dest, root, candidate=True)
            expected = v.source_files(root)
            data = dest.read_bytes()
            v.check_archive(data, expected, candidate=True)
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                entries = {n: z.read(n) for n in z.namelist()}
            variants = []
            missing = dict(entries); missing.pop('photo-finish/runtime/fixture.py'); variants.append(missing)
            extra = dict(entries); extra['photo-finish/extra.txt'] = b'extra'; variants.append(extra)
            changed = dict(entries); changed['photo-finish/runtime/fixture.py'] = b'changed'; variants.append(changed)
            for key, value in [('files', {}), ('version', '1.5.0'), ('distribution_channel', 'release')]:
                bad = dict(entries)
                manifest = json.loads(bad['photo-finish/release-manifest.json'])
                manifest[key] = value
                bad['photo-finish/release-manifest.json'] = json.dumps(manifest).encode()
                variants.append(bad)
            for bad in variants:
                out = io.BytesIO()
                with zipfile.ZipFile(out, 'w') as z:
                    for name, body in bad.items(): z.writestr(name, body)
                with self.assertRaises(ValueError):
                    v.check_archive(out.getvalue(), expected, candidate=True)

    def test_private_data_in_source_and_unsafe_archive_are_rejected(self):
        import verify_packages as v
        with self.project() as root:
            (root / 'runtime/private.jpeg').write_bytes(b'synthetic')
            with self.assertRaises(ValueError): v.candidate(root)
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w') as z: z.writestr('../escape', b'synthetic')
        with self.assertRaises(ValueError): v.check_archive(out.getvalue(), {}, candidate=True)

    def test_formal_release_requires_source_manifest_and_exact_attachments(self):
        import verify_packages as v
        with self.project() as root, tempfile.TemporaryDirectory() as tmp:
            files = v.source_files(root)
            archive = Path(tmp) / 'photo-finish.zip'; b.build(archive, root)
            checksum = archive.with_suffix('.zip.sha256')
            assets = Path(tmp) / 'assets'; assets.mkdir()
            for f in (archive, checksum): shutil.copyfile(f, assets / f.name)
            v.check_release_bytes(archive.read_bytes(), checksum.read_bytes(), files, '1.5.0', assets)
            (assets / archive.name).write_bytes(b'changed attachment')
            with self.assertRaises(ValueError):
                v.check_release_bytes(archive.read_bytes(), checksum.read_bytes(), files, '1.5.0', assets)
            with self.assertRaises(ValueError):
                v.check_release_bytes(archive.read_bytes(), checksum.read_bytes(), files, '1.6.0', assets)
