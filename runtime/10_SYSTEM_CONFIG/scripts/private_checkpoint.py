"""Explicit private task checkpoints; no image editing, upload or remote save claim."""
from pathlib import Path, PurePosixPath
from contextlib import closing
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import tempfile
import zipfile
from runtime_io import atomic_json
from style_library import location

FORMAT = 'photo-finish-task-checkpoint'
JOURNAL = '.photo-finish-checkpoint.json'
MAX_FILE = 256 * 1024**2
MAX_TOTAL = 2 * 1024**3


def _name(value):
    if (not isinstance(value, str) or not value or '\\' in value or
            PurePosixPath(value).is_absolute() or
            any(x in ('', '.', '..') for x in value.split('/')) or
            value in ('manifest.json', JOURNAL)):
        raise ValueError('Unsafe or reserved checkpoint member')
    return value


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def _directory_sync(path):
    if os.name == 'nt':
        return  # Directory fsync is not provided by this Windows interface.
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _durable_json(path, value):
    atomic_json(path, value)
    # Windows file flushing requires write access; r+b preserves existing bytes.
    with Path(path).open('r+b') as stream:
        os.fsync(stream.fileno())
    _directory_sync(Path(path).parent)


def _member(root, name):
    path = root / _name(name)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(root):
        raise ValueError('Checkpoint paths cannot traverse symlinks or leave the private root')
    return path


def _snapshot(source, target):
    if not source.is_file() or source.stat().st_size > MAX_FILE:
        raise ValueError('Checkpoint source missing or exceeds size limit')
    if source.suffix in ('.sqlite3', '.sqlite', '.db'):
        # Online backup includes committed WAL rows; copying the main file alone does not.
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro', uri=True, timeout=10)) as incoming:
            with closing(sqlite3.connect(target)) as outgoing:
                incoming.backup(outgoing)
        return 'sqlite_online_backup'
    shutil.copyfile(source, target)
    if _sha(source) != _sha(target):
        raise ValueError('Source changed during checkpoint; quiesce the task and retry')
    return 'exact_bytes'


def export(root, destination, files):
    root = location(root)
    target = Path(destination).expanduser()
    if target.is_symlink():
        raise ValueError('Checkpoint destination cannot be a symlink')
    target = location(target.parent) / target.name
    if target.suffix != '.zip' or target.is_relative_to(root):
        raise ValueError('Use a checkpoint ZIP outside the private working root')
    if not isinstance(files, list) or not files or len(files) > 1000 or len(set(files)) != len(files):
        raise ValueError('Explicit unique file list required, at most 1000 files')
    names = sorted(_name(name) for name in files)
    sources = {name: _member(root, name) for name in names}
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        stage = Path(temporary)
        manifest = {'format': FORMAT, 'version': 1, 'scope': 'private',
                    'original_root': str(root), 'files': {}, 'ledger_paths_rewritten': False}
        total = 0
        for i, name in enumerate(names):
            snap = stage / str(i)
            method = _snapshot(sources[name], snap)
            size = snap.stat().st_size
            total += size
            if size > MAX_FILE or total > MAX_TOTAL:
                raise ValueError('Checkpoint exceeds bounded size')
            manifest['files'][name] = {'sha256': _sha(snap), 'bytes': size, 'method': method}
        archive = stage/'checkpoint.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for i, name in enumerate(names):
                info = zipfile.ZipInfo(name); info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3; info.external_attr = 0o100600 << 16
                with (stage/str(i)).open('rb') as incoming, z.open(info, 'w') as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
            info = zipfile.ZipInfo('manifest.json'); info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3; info.external_attr = 0o100600 << 16
            z.writestr(info, json.dumps(manifest, ensure_ascii=False, sort_keys=True))
        # Keep a writable, non-truncating handle for Windows _commit/FlushFileBuffers.
        with archive.open('r+b') as stream:
            os.fsync(stream.fileno())
        digest = _sha(archive)
        reused = False
        try:
            os.link(archive, target)
            target.chmod(0o600)
            _directory_sync(target.parent)
        except FileExistsError:
            if target.is_symlink() or not target.is_file() or _sha(target) != digest:
                raise FileExistsError('Existing checkpoint differs; use a new destination')
            reused = True
    return {'path': str(target), 'sha256': digest, 'files': len(names), 'reused': reused,
            'persistent_save_confirmed': False,
            'next': 'Persist with an actual private-store receipt, re-read and verify this archive hash'}


def inspect(archive_path, expected_sha256=None):
    path = Path(archive_path)
    if path.is_symlink():
        raise ValueError('Checkpoint archive cannot be a symlink')
    digest = _sha(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError('Checkpoint archive hash mismatch')
    with zipfile.ZipFile(path) as z:
        infos = z.infolist(); names = [i.filename for i in infos]
        if len(names) > 1001 or len(names) != len(set(names)) or 'manifest.json' not in names:
            raise ValueError('Invalid checkpoint member list')
        for item in infos:
            if item.filename != 'manifest.json':
                _name(item.filename)
            if (item.is_dir() or item.flag_bits & 1 or
                    stat.S_IFMT(item.external_attr >> 16) not in (0, stat.S_IFREG) or
                    item.file_size > (4*1024**2 if item.filename == 'manifest.json' else MAX_FILE)):
                raise ValueError('Unsafe checkpoint member')
        if sum(i.file_size for i in infos) > MAX_TOTAL:
            raise ValueError('Checkpoint exceeds bounded size')
        manifest = json.loads(z.read('manifest.json'))
        if (not isinstance(manifest, dict) or manifest.get('format') != FORMAT or
                not isinstance(manifest.get('original_root'), str) or manifest.get('scope') != 'private' or
                manifest.get('ledger_paths_rewritten') is not False or type(manifest.get('version')) is not int or
                manifest['version'] != 1 or not isinstance(manifest.get('files'), dict) or
                set(manifest['files']) != set(names)-{'manifest.json'}):
            raise ValueError('Invalid checkpoint manifest')
        for name, item in manifest['files'].items():
            data = z.read(name)
            if (not isinstance(item, dict) or type(item.get('bytes')) is not int or
                    len(data) != item.get('bytes') or hashlib.sha256(data).hexdigest() != item.get('sha256')):
                raise ValueError('Checkpoint member checksum mismatch')
    return {'sha256': digest, 'manifest': manifest, 'persistent_save_confirmed': False}


def restore(archive_path, destination, expected_sha256=None):
    proof = inspect(archive_path, expected_sha256)
    dest = location(destination); manifest = proof['manifest']; journal = dest/JOURNAL
    if dest.exists():
        if journal.is_symlink() or not journal.is_file():
            raise FileExistsError('Existing destination has no matching restore journal')
        state = json.loads(journal.read_text(encoding='utf-8'))
        if state.get('archive_sha256') != proof['sha256']:
            raise ValueError('Another checkpoint owns this restore destination')
    else:
        dest.mkdir(parents=True, mode=0o700)
        _durable_json(journal, {'archive_sha256': proof['sha256'], 'status': 'in_progress'})
    # Preflight all existing files before publishing any new files.
    for name, item in manifest['files'].items():
        target = _member(dest, name)
        if os.path.lexists(target) and (not target.is_file() or _sha(target) != item['sha256']):
            raise ValueError('Existing restored bytes differ; never overwrite history')
    with zipfile.ZipFile(archive_path) as z:
        for name, item in manifest['files'].items():
            target = _member(dest, name)
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as outgoing:
                    temporary = Path(outgoing.name)
                    with z.open(name) as incoming:
                        shutil.copyfileobj(incoming, outgoing)
                    outgoing.flush(); os.fsync(outgoing.fileno())
                if temporary.stat().st_size != item['bytes'] or _sha(temporary) != item['sha256']:
                    raise ValueError('Checkpoint changed after validation; no unverified bytes published')
                os.link(temporary, target)
                _directory_sync(target.parent)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
    _durable_json(journal, {'archive_sha256': proof['sha256'], 'status': 'complete'})
    return {'path': str(dest), 'sha256': proof['sha256'], 'files': len(manifest['files']),
            'historical_paths_match': str(dest) == manifest['original_root'],
            'ledger_paths_rewritten': False, 'persistent_save_confirmed': False}
