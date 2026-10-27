"""Read-only frozen release protection and isolated candidate/source verification."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile

import build_release as builder
from check_publication import inspect_archive, scan

ROOT = Path(__file__).resolve().parents[1]
STABLE_TAG = 'v1.5.0'
STABLE_COMMIT = '48b7e2bfcbd8a4b111ec3815186c96ef14c807fe'
STABLE_SHA256 = '84fbc42db21d2aa7dc8122152d4390a526761519eb58a212534f4266bd46fb9f'
FROZEN_DIRECTORY = 'dist/v1.5.0'
RELEASE_VERSION = '1.5.1'
RELEASE_SHA256 = '0d929e31f4cf132c9855b933771c0c8fc98ece4702f598aaca759b9444d70608'
ARCHIVE = 'photo-finish.zip'
CHECKSUM = ARCHIVE + '.sha256'
MANIFEST = 'photo-finish/release-manifest.json'
REPOSITORY = 'kwhi6693-web/photo-finish'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected(name):
    path = Path(name)
    return ('__pycache__' not in path.parts and path.suffix not in ('.pyc', '.pyo') and
            (name in builder.TOP | builder.TOOLS or path.parts[0] in builder.DIRS))


def source_files(root):
    root = Path(root)
    files = {}
    for path in root.rglob('*'):
        name = path.relative_to(root).as_posix()
        if selected(name) and path.is_file():
            if path.is_symlink(): raise ValueError('Symlink source is not a release payload')
            files[name] = path.read_bytes()
    return files


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def tagged_files(root, ref):
    """Read committed regular files without extracting or changing checkout."""
    files = {}
    data = git(root, 'archive', '--format=tar', ref)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for item in archive:
            if selected(item.name) and not item.isdir():
                if not item.isfile(): raise ValueError('Non-regular tagged payload')
                files[item.name] = archive.extractfile(item).read()
    return files


def check_archive(data, expected, *, candidate=False, version='1.5.0'):
    if inspect_archive(data): raise ValueError('Archive security/publication checks failed')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        want = {'photo-finish/' + name for name in expected} | {MANIFEST}
        if set(archive.namelist()) != want: raise ValueError('Archive file mapping differs from source')
        manifest = json.loads(archive.read(MANIFEST))
        if manifest.get('name') != 'photo-finish': raise ValueError('Manifest package identity differs')
        if candidate:
            if (manifest.get('version') != '0+candidate' or
                    manifest.get('distribution_channel') != 'candidate'):
                raise ValueError('Development artifact must explicitly identify as candidate')
        elif manifest.get('version') != version or 'distribution_channel' in manifest:
            raise ValueError('Formal manifest version/channel differs')
        if manifest.get('files') != {name: digest(body) for name, body in expected.items()}:
            raise ValueError('Manifest source hashes differ')
        for name, body in expected.items():
            if archive.read('photo-finish/' + name) != body:
                raise ValueError('Archive payload differs from exact source bytes')
    return len(expected)


def check_frozen_files(root):
    root = Path(root)
    folder = root / FROZEN_DIRECTORY
    if (root / 'dist').is_symlink() or folder.is_symlink() or any((folder / name).is_symlink() for name in (ARCHIVE, CHECKSUM)):
        raise ValueError('Frozen artifacts cannot be symlinks')
    data = (folder / ARCHIVE).read_bytes()
    checksum = (folder / CHECKSUM).read_bytes()
    if digest(data) != STABLE_SHA256 or checksum != (STABLE_SHA256 + '  ' + ARCHIVE + '\n').encode():
        raise ValueError('Frozen stable archive/checksum changed')
    return data


def stable(root=ROOT):
    root = Path(root)
    commit = git(root, 'rev-parse', 'refs/tags/' + STABLE_TAG + '^{commit}').decode().strip()
    if commit != STABLE_COMMIT: raise ValueError('Published stable tag moved')
    data = check_frozen_files(root)
    if data != git(root, 'show', STABLE_COMMIT + ':dist/' + ARCHIVE):
        raise ValueError('Stable checkout artifact differs from tagged artifact')
    if (Path(root) / FROZEN_DIRECTORY / CHECKSUM).read_bytes() != git(root, 'show', STABLE_COMMIT + ':dist/' + CHECKSUM):
        raise ValueError('Frozen checksum differs from tagged checksum')
    expected = tagged_files(root, STABLE_COMMIT)
    count = check_archive(data, expected)
    return {'status': 'passed', 'scope': 'frozen_stable', 'tag': STABLE_TAG,
            'sha256': STABLE_SHA256, 'payload_files': count}


def canonical(root=ROOT):
    """Pin release-ready canonical bytes without claiming the version is published."""
    root = Path(root)
    folder = root / 'dist'
    staged = folder / ('v' + RELEASE_VERSION)
    if folder.is_symlink() or staged.is_symlink() or any(
            (directory / name).is_symlink()
            for directory in (folder, staged) for name in (ARCHIVE, CHECKSUM)):
        raise ValueError('Canonical artifacts cannot be symlinks')
    data = (folder / ARCHIVE).read_bytes()
    checksum = (folder / CHECKSUM).read_bytes()
    if digest(data) != RELEASE_SHA256:
        raise ValueError('Pinned canonical release-ready archive changed')
    count = check_release_bytes(data, checksum, source_files(root), RELEASE_VERSION, staged)
    return {'status': 'passed', 'scope': 'canonical_release_ready_not_published',
            'version': RELEASE_VERSION, 'sha256': RELEASE_SHA256, 'payload_files': count}


def candidate(root=ROOT):
    root = Path(root)
    if scan(root)['status'] != 'passed': raise ValueError('Source publication scan failed')
    expected = source_files(root)
    # Independent builds in separate external directories; no artifact replaces dist.
    with tempfile.TemporaryDirectory(prefix='photo-finish-candidate-') as tmp:
        paths = [Path(tmp) / name / 'candidate.zip' for name in ('first', 'second')]
        for path in paths:
            builder.build(path, root, candidate=True)
            check_archive(path.read_bytes(), expected, candidate=True)
            if path.with_suffix('.zip.sha256').read_bytes() != (digest(path.read_bytes()) + '  candidate.zip\n').encode():
                raise ValueError('Candidate checksum differs')
        if paths[0].read_bytes() != paths[1].read_bytes():
            raise ValueError('Candidate build is not deterministic')
        checksum = digest(paths[0].read_bytes())
    return {'status': 'passed', 'scope': 'development_candidate_not_release',
            'payload_files': len(expected), 'sha256': checksum, 'deterministic_builds': 2}


def check_release_bytes(data, checksum, expected, version, attachments):
    """Formal source/manifest/installer AND actual attachment bytes must agree."""
    count = check_archive(data, expected, version=version)
    source_version = json.loads(expected['runtime/10_SYSTEM_CONFIG/SESSION_BRIEF.json'])['runtime_version']
    if source_version != version: raise ValueError('Source runtime version differs from release')
    if checksum != (digest(data) + '  ' + ARCHIVE + '\n').encode():
        raise ValueError('Formal checksum differs')
    for name, body in ((ARCHIVE, data), (CHECKSUM, checksum)):
        if (Path(attachments) / name).read_bytes() != body:
            raise ValueError('Published attachment differs from verified installer/checksum')
    return count


def release(root, tag, attachments):
    if not tag.startswith('v') or not all(x.isdigit() for x in tag[1:].split('.')) or len(tag[1:].split('.')) != 3:
        raise ValueError('Formal release requires a version tag')
    ref = 'refs/tags/' + tag
    git(root, 'rev-parse', '--verify', ref + '^{commit}')
    expected = tagged_files(root, ref)
    data = git(root, 'show', ref + ':dist/' + ARCHIVE)
    checksum = git(root, 'show', ref + ':dist/' + CHECKSUM)
    count = check_release_bytes(data, checksum, expected, tag[1:], attachments)
    return {'status': 'passed', 'scope': 'formal_source_manifest_installer_attachments',
            'tag': tag, 'sha256': digest(data), 'payload_files': count}


def published(root=ROOT, tag=STABLE_TAG):
    """Read-only audit of public Release attachments; never publishes anything."""
    base = 'https://api.github.com/repos/' + REPOSITORY + '/releases/tags/'
    def get(url, limit):
        request = urllib.request.Request(url, headers={'User-Agent': 'photo-finish-package-validator'})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(limit + 1)
        if len(data) > limit: raise ValueError('Release response exceeds bound')
        return data
    metadata = json.loads(get(base + urllib.parse.quote(tag, safe=''), 1024 * 1024))
    if metadata.get('tag_name') != tag or metadata.get('draft') or metadata.get('prerelease'):
        raise ValueError('Expected a published formal Release')
    names = [a['name'] for a in metadata['assets']]
    if names.count(ARCHIVE) != 1 or names.count(CHECKSUM) != 1:
        raise ValueError('Release installer/checksum assets missing or ambiguous')
    with tempfile.TemporaryDirectory(prefix='photo-finish-release-audit-') as tmp:
        for name in (ARCHIVE, CHECKSUM):
            url = 'https://github.com/' + REPOSITORY + '/releases/download/' + urllib.parse.quote(tag, safe='') + '/' + name
            (Path(tmp) / name).write_bytes(get(url, 32 * 1024 * 1024))
        return release(root, tag, tmp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['stable', 'canonical', 'candidate', 'release', 'published'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--tag', default=STABLE_TAG)
    parser.add_argument('--attachments', type=Path)
    args = parser.parse_args()
    try:
        if args.mode == 'release':
            if args.attachments is None: raise ValueError('Actual attachment directory required')
            result = release(args.root, args.tag, args.attachments)
        elif args.mode == 'published': result = published(args.root, args.tag)
        else: result = globals()[args.mode](args.root)
        print(json.dumps(result))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, type(error).__name__ + ': package verification failed\n')
