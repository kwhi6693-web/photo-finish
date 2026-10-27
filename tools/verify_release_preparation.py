"""Verify staged maintenance bytes and isolated installation; never publish/install live."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile

import build_release as builder
import verify_packages as packages

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.5.1'


def verify(root=ROOT, *, canonical=False):
    root = Path(root)
    expected = packages.source_files(root)
    brief = json.loads(expected['runtime/10_SYSTEM_CONFIG/SESSION_BRIEF.json'])
    policy = json.loads(expected['runtime/10_SYSTEM_CONFIG/runtime_policy.json'])
    if not (brief['runtime_version'] == policy['runtime_version'] ==
            policy['distribution']['version'] ==
            policy['beautification_defaults']['versions']['runtime'] == VERSION):
        raise ValueError('Maintenance installation versions differ')
    if canonical:
        packages.canonical(root)
    staged = root / 'dist' if canonical else root / 'dist' / ('v' + VERSION)
    if staged.is_symlink() or any((staged / n).is_symlink() for n in (packages.ARCHIVE, packages.CHECKSUM)):
        raise ValueError('Staged artifacts cannot be symlinks')
    data = (staged / packages.ARCHIVE).read_bytes()
    checksum = (staged / packages.CHECKSUM).read_bytes()
    count = packages.check_release_bytes(data, checksum, expected, VERSION, staged)
    with tempfile.TemporaryDirectory(prefix='photo-finish-maintenance-') as tmp:
        base = Path(tmp)
        for name in ('first', 'second'):
            output = base / name / packages.ARCHIVE
            builder.build(output, root)
            if output.read_bytes() != data or output.with_suffix('.zip.sha256').read_bytes() != checksum:
                raise ValueError('Staged maintenance build is not reproducible')
        install = base / 'skills'
        with zipfile.ZipFile(staged / packages.ARCHIVE) as archive:
            archive.extractall(install)  # check_release_bytes already rejects unsafe entries.
        skill = install / 'photo-finish'
        for name, body in expected.items():
            if (skill / name).read_bytes() != body:
                raise ValueError('Installed file differs from verified archive')
        environment = dict(os.environ, PHOTO_FINISH_STYLE_LIBRARY=str(base / 'anonymous-styles'),
                           PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
        # -I excludes user site/PYTHONPATH/cwd. Dependencies are provided by the CI environment.
        result = subprocess.run([sys.executable, '-I', str(root / 'tools/verify_installed_maintenance.py'),
                                 str(skill), str(root / 'tests')], cwd=base, env=environment,
                                check=True, capture_output=True, text=True, encoding='utf-8')
        installed = json.loads(result.stdout)
    return {'status': 'passed', 'version': VERSION,
            'scope': 'canonical_release_ready_not_published' if canonical else 'staged_unpublished_maintenance',
            'sha256': packages.digest(data), 'bytes': len(data), 'payload_files': count,
            'deterministic_builds': 2, 'isolated_install': installed}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--canonical', action='store_true', help='Verify/install the canonical release-ready artifact')
    args = parser.parse_args()
    print(json.dumps(verify(args.root, canonical=args.canonical), ensure_ascii=False))
