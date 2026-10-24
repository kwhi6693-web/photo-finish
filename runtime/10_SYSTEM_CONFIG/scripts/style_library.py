"""Private, opt-in photograph collection. No service, rendering or aesthetic verdict.

A catalog belongs to its filesystem user/root. Multi-user hosts must provide a
trusted, separate root per user; this module does not implement authentication.
"""
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

from PIL import Image
from style_match import features

FORMATS = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp', 'TIFF': '.tiff'}


def location(library_root=None):
    value = library_root if library_root is not None else os.environ.get('PHOTO_FINISH_STYLE_LIBRARY')
    if value is None:
        if sys.platform == 'win32':
            base = Path(os.environ.get('LOCALAPPDATA') or Path.home()/'AppData'/'Local')
        elif sys.platform == 'darwin':
            base = Path.home()/'Library'/'Application Support'
        else:
            base = Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local'/'share')
        value = base/'photo-finish'/'style-library'
    if not str(value).strip():
        raise ValueError('Style library root cannot be empty')
    root = Path(value).expanduser().resolve()
    # Includes an extracted, non-Git installation. No writes inside a skill.
    runtime = Path(__file__).resolve().parents[2]
    skill = runtime.parent if (runtime.parent/'SKILL.md').is_file() else runtime
    if root.is_relative_to(skill) or any((parent/'.git').exists() for parent in (root, *root.parents)):
        raise ValueError('Choose a private style library outside the skill and Git checkouts')
    return root


def _text(value, name, maximum=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(name+' must be nonempty text within '+str(maximum)+' characters')
    return value.strip()


def _labels(value, name):
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 32:
        raise ValueError(name+' must be a list of at most 32 labels')
    return list(dict.fromkeys(_text(item, name, 80) for item in value))


def _asset(root, relative):
    path = root/relative
    if (not isinstance(relative, str) or
            not re.fullmatch(r'images/[0-9a-f]{64}\.(?:jpg|png|webp|tiff)', relative) or
            path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(root)):
        raise ValueError('Invalid private style image path')
    return path


@contextmanager
def _catalog(root, write=False, rollback_assets=None):
    db = root/'catalog.sqlite3'
    if db.is_symlink():
        raise ValueError('Style catalog cannot be a symlink')
    connection = None
    try:
        if write:
            root.mkdir(parents=True, exist_ok=True, mode=0o700)
            connection = sqlite3.connect(db, timeout=10)
            db.chmod(0o600)
            connection.execute('PRAGMA secure_delete=ON')
            connection.execute('BEGIN IMMEDIATE')
            connection.execute('CREATE TABLE IF NOT EXISTS styles (id TEXT PRIMARY KEY, entry TEXT NOT NULL)')
        else:
            connection = sqlite3.connect(db.as_uri()+'?mode=ro', uri=True, timeout=10)
        yield connection
        if write:
            connection.commit()
    except BaseException as error:
        if connection is not None and rollback_assets:
            # A failed statement can automatically release SQLite's transaction.
            # Reacquire the writer lock, and preserve any copy another writer
            # has since committed. Only our newly created copies are eligible.
            try:
                connection.rollback()
                connection.execute('BEGIN IMMEDIATE')
                exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='styles'").fetchone()
                for rid, path in rollback_assets:
                    row = connection.execute('SELECT entry FROM styles WHERE id=?', (rid,)).fetchone() if exists else None
                    if row is None or _asset(root, json.loads(row[0])['private_relative_path']) != path:
                        path.unlink(missing_ok=True)
                connection.rollback()
            except (sqlite3.Error, OSError, ValueError, KeyError, TypeError) as cleanup_error:
                raise ValueError('Style collection failed and cleanup could not be confirmed; inspect the private library') from cleanup_error
        if isinstance(error, sqlite3.Error):
            raise ValueError('Private style catalog could not be read or written; check its path, permissions and backup') from error
        raise
    finally:
        if connection is not None:
            connection.close()


def _public(root, entry):
    return {'reference_id': entry['id'], 'title': entry['subject'], 'labels': entry['labels'],
            'tags': entry['tags'], 'note': entry['individual_note'], 'sha256': entry['sha256'],
            'path': str(_asset(root, entry['private_relative_path']))}


def add(source_path, title, consent=False, labels=None, tags=None, note='', library_root=None):
    if consent is not True:
        raise ValueError('Explicit user intent to save this photograph as a style reference is required')
    root = location(library_root)
    title = _text(title, 'title', 200)
    labels = _labels(labels, 'labels'); tags = _labels(tags, 'tags')
    if set(tags)-set('ABCDEFGHIJKL'):
        raise ValueError('Scene tags must use existing A through L scene codes; use labels for free-form styles')
    if not isinstance(note, str) or len(note) > 2000:
        raise ValueError('note must be text within 2000 characters')
    data = Path(source_path).read_bytes()
    # Validate before creating anything. Preserve exact file bytes, including ICC/EXIF.
    with Image.open(BytesIO(data)) as image:
        image.load()
        extension = FORMATS.get(image.format)
        if extension is None:
            raise ValueError('Style collection supports JPEG, PNG, WebP and TIFF photographs')
    digest = hashlib.sha256(data).hexdigest(); rid = 'personal_'+digest
    # Finish fallible analysis before creating a catalog or permanent image copy.
    measured = features(source_path, digest)
    if hashlib.sha256(Path(source_path).read_bytes()).hexdigest() != digest:
        raise ValueError('Style source changed during collection')
    relative = 'images/'+digest+extension
    destination = _asset(root, relative)
    rollback_assets = []
    with _catalog(root, write=True, rollback_assets=rollback_assets) as catalog:
        row = catalog.execute('SELECT entry FROM styles WHERE id=?', (rid,)).fetchone()
        if row:
            entry = json.loads(row[0])
            verify(_public(root, entry))
            return dict(_public(root, entry), duplicate=True)
        destination.parent.mkdir(mode=0o700, exist_ok=True)
        if destination.parent.is_symlink():
            raise ValueError('Style image directory cannot be a symlink')
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name); stream.write(data)
            try:
                os.link(temporary, destination)
                rollback_assets.append((rid, destination))
            except FileExistsError:
                if destination.is_symlink() or hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
                    raise ValueError('Existing private style bytes changed')
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        entry = dict(id=rid, sha256=digest, subject=title, labels=labels, tags=tags,
                     individual_note=note.strip(), scene_description=' '.join(labels),
                     original_filename=destination.name, private_relative_path=relative,
                     include_in_dna=True, style_weight=1, measured_full=measured, origin='personal')
        catalog.execute('INSERT INTO styles VALUES (?, ?)', (rid, json.dumps(entry, ensure_ascii=False)))
    return dict(_public(root, entry), duplicate=False)


def records(library_root=None, query=None, style_ids=None):
    """Read metadata only. Never decode or scan every photograph during an edit."""
    root = location(library_root)
    if query is not None and style_ids is not None:
        raise ValueError('Use either style_query or style_ids, not both')
    if query is not None:
        query = _text(query, 'query', 200).casefold()
    if style_ids is not None and (not isinstance(style_ids, list) or not 1 <= len(style_ids) <= 3 or
                                 any(not isinstance(i, str) for i in style_ids) or len(set(style_ids)) != len(style_ids)):
        raise ValueError('style_ids must contain one through three distinct reference IDs')
    if (root/'catalog.sqlite3').is_symlink():
        raise ValueError('Style catalog cannot be a symlink')
    if not (root/'catalog.sqlite3').exists():
        if style_ids:
            raise ValueError('Unknown personal style reference ID')
        return []
    with _catalog(root) as catalog:
        rows = catalog.execute('SELECT entry FROM styles ORDER BY id').fetchall()
    try:
        entries = [json.loads(row[0]) for row in rows]
        for entry in entries:
            if (not re.fullmatch(r'[0-9a-f]{64}', entry['sha256']) or entry['id'] != 'personal_'+entry['sha256'] or
                    not isinstance(entry['tags'], list) or not isinstance(entry['labels'], list)):
                raise ValueError('Invalid private style record')
            entry['path'] = str(_asset(root, entry['private_relative_path']))
        known = {entry['id'] for entry in entries}
        if style_ids and set(style_ids)-known:
            raise ValueError('Unknown personal style reference ID')
        return [entry for entry in entries if
                (style_ids is None or entry['id'] in style_ids) and
                (query is None or all(word in ' '.join([entry['subject'], entry['individual_note'], *entry['labels']]).casefold()
                                      for word in query.split()))]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError('Invalid private style catalog; restore a valid backup') from error


def list_references(library_root=None, query=None, limit=50):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be 1 through 100')
    root = location(library_root); entries = records(root, query)
    return {'library_root': str(root), 'total': len(entries),
            'references': [_public(root, entry) for entry in entries[:limit]]}


def remove(reference_id, library_root=None):
    root = location(library_root)
    if (root/'catalog.sqlite3').is_symlink():
        raise ValueError('Style catalog cannot be a symlink')
    if not (root/'catalog.sqlite3').exists():
        raise ValueError('Unknown personal style reference ID')
    with _catalog(root, write=True) as catalog:
        row = catalog.execute('SELECT entry FROM styles WHERE id=?', (reference_id,)).fetchone()
        if row is None:
            raise ValueError('Unknown personal style reference ID')
        path = _asset(root, json.loads(row[0])['private_relative_path'])
        path.unlink(missing_ok=True)
        catalog.execute('DELETE FROM styles WHERE id=?', (reference_id,))
    return {'removed': reference_id}


def verify(candidate):
    path = Path(candidate['path'])
    if (path.is_symlink() or path.parent.is_symlink() or not path.is_file() or
            hashlib.sha256(path.read_bytes()).hexdigest() != candidate['sha256']):
        raise ValueError('Personal style reference changed or is missing; retrieve and inspect it again')


def verify_selection(state):
    """Selection evidence is separate from actual image-tool input evidence."""
    selection = state.get('reference_selection') or {}
    selected = {item['reference_id'] for item in selection.get('decisions', [])
                if item['decision'] in ('adopt', 'partial')}
    for candidate in (selection.get('query') or {}).get('candidates', []):
        if candidate.get('origin') == 'personal' and candidate['reference_id'] in selected:
            verify(candidate)
