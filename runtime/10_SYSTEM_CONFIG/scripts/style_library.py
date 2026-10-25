"""Private, opt-in photograph collection. No service, rendering or aesthetic verdict.

A catalog belongs to its filesystem user/root. Multi-user hosts must provide a
trusted, separate root per user; this module does not implement authentication.
"""
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from functools import lru_cache
from copy import deepcopy
import time
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

from PIL import Image
from style_match import features
from runtime_io import digest as metadata_digest

FORMATS = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp', 'TIFF': '.tiff'}
PURPOSES = {'light', 'color', 'material', 'composition', 'atmosphere'}


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
            'path': str(_asset(root, entry['private_relative_path'])),
            'group': entry.get('group', ''), 'pinned': entry.get('pinned', False),
            'use_for': entry.get('use_for', []), 'metadata_sha256': metadata_digest(_metadata(entry))}


def _metadata(entry):
    return {key:entry.get(key, default) for key,default in
            [('subject',''),('labels',[]),('tags',[]),('individual_note',''),
             ('group',''),('pinned',False),('use_for',[])]}


def _changes(title=None, labels=None, tags=None, note=None, group=None, pinned=None, use_for=None):
    clean = {}
    if title is not None: clean['subject'] = _text(title, 'title', 200)
    if labels is not None:
        clean['labels'] = _labels(labels, 'labels'); clean['scene_description'] = ' '.join(clean['labels'])
    if tags is not None:
        clean['tags'] = _labels(tags, 'tags')
        if set(clean['tags'])-set('ABCDEFGHIJKL'): raise ValueError('Scene tags must be A through L')
    for name,value,maximum in [('individual_note',note,2000),('group',group,80)]:
        if value is not None:
            if not isinstance(value,str) or len(value)>maximum: raise ValueError('Invalid '+name)
            clean[name] = value.strip()
    if pinned is not None:
        if type(pinned) is not bool: raise ValueError('pinned must be a boolean')
        clean['pinned'] = pinned
    if use_for is not None:
        clean['use_for'] = _labels(use_for, 'use_for')
        if set(clean['use_for'])-PURPOSES: raise ValueError('Unsupported reference purpose')
    return clean


def normalize_entry(entry):
    """Validate portable metadata without trusting an archive's paths or features."""
    allowed={'id','sha256','subject','labels','tags','individual_note','scene_description','original_filename',
             'private_relative_path','include_in_dna','style_weight','measured_full','origin','group','pinned','use_for','path'}
    if not isinstance(entry,dict) or set(entry)-allowed: raise ValueError('Invalid or unsupported private style record')
    try:
        if (not isinstance(entry['subject'],str) or not isinstance(entry['labels'],list) or
                not isinstance(entry['tags'],list) or not isinstance(entry['individual_note'],str) or
                not isinstance(entry.get('group',''),str) or type(entry.get('pinned',False)) is not bool or
                not isinstance(entry.get('use_for',[]),list)):
            raise ValueError('Invalid private style metadata types')
        sha = entry['sha256']
        if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{64}',sha) or entry['id']!='personal_'+sha:
            raise ValueError('Invalid private style identity')
        relative=entry['private_relative_path']
        if not isinstance(relative,str) or not re.fullmatch(r'images/'+sha+r'\.(jpg|png|webp|tiff)',relative):
            raise ValueError('Invalid private style image path')
        clean=dict(entry);clean.pop('path',None)
        clean.update(_changes(entry['subject'],entry['labels'],entry['tags'],entry['individual_note'],
                              entry.get('group',''),entry.get('pinned',False),entry.get('use_for',[])))
        clean.update(origin='personal',include_in_dna=True,style_weight=1,
                     original_filename=Path(relative).name)
        return clean
    except (KeyError,TypeError) as error:
        raise ValueError('Invalid private style record') from error


# Exact serialized-row keys: a modified/deleted row cannot return old metadata.
# Reads still query SQLite; no timestamp-based database freshness assumption.
@lru_cache(maxsize=2048)
def _decoded(serialized):
    return normalize_entry(json.loads(serialized))


SYNONYMS=(('安静','宁静','克制','quiet'),('柔和','柔光','低对比','soft'),
          ('旅行','旅游','旅途','travel'))


def _matches(query, text):
    text=text.casefold();query=query.casefold()
    # Small documented vocabulary expansion, not vector or model retrieval.
    for filler in ('找那种','帮我找','适合','的参考','的风格','参考照片'):
        query=query.replace(filler,' ')
    groups=[]
    for aliases in SYNONYMS:
        found=False
        for word in sorted(aliases,key=len,reverse=True):
            if word in query:query=query.replace(word,' ');found=True
        if found:groups.append(aliases)
    groups.extend((word,) for word in re.split(r'[\s、，,。；;！？]+',query) if word)
    return bool(groups) and all(any(word in text for word in aliases) for aliases in groups)


def _entries(connection):
    try:
        tables={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not tables: return []
        if 'styles' not in tables: raise ValueError('Missing private style catalog schema')
        return [deepcopy(_decoded(row[0])) for row in
                connection.execute('SELECT entry FROM styles ORDER BY id').fetchall()]
    except (json.JSONDecodeError,TypeError) as error:
        raise ValueError('Invalid private style catalog') from error


def update(reference_id, title=None, labels=None, tags=None, note=None, group=None,
           pinned=None, use_for=None, consent=False, library_root=None, expected_metadata_sha256=None):
    if consent is not True: raise ValueError('Explicit intent to modify the saved style is required')
    changes=_changes(title,labels,tags,note,group,pinned,use_for)
    if not changes: raise ValueError('Provide at least one metadata field to update')
    root=location(library_root)
    if not (root/'catalog.sqlite3').exists(): raise ValueError('Unknown personal style reference ID')
    with _catalog(root,write=True) as connection:
        row=connection.execute('SELECT entry FROM styles WHERE id=?',(reference_id,)).fetchone()
        if row is None: raise ValueError('Unknown personal style reference ID')
        entry=normalize_entry(json.loads(row[0]));current=_public(root,entry)
        if expected_metadata_sha256 is not None and expected_metadata_sha256!=current['metadata_sha256']:
            raise ValueError('Style metadata changed; list the current record before updating')
        verify(current);entry.update(changes)
        connection.execute('UPDATE styles SET entry=? WHERE id=?',(json.dumps(entry,ensure_ascii=False),reference_id))
    return _public(root,entry)


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


def records(library_root=None, query=None, style_ids=None, group=None):
    """Read metadata only. Never decode or scan every photograph during an edit."""
    root = location(library_root)
    if style_ids is not None and (query is not None or group is not None):
        raise ValueError('Explicit style_ids cannot be combined with query/group filters')
    if group is not None:
        if not isinstance(group,str) or len(group)>80: raise ValueError('Invalid style group')
        group=group.strip()
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
        entries = ([deepcopy(_decoded(row[0])) for row in catalog.execute(
            'SELECT entry FROM styles WHERE id IN ('+','.join('?' for _ in style_ids)+') ORDER BY id',style_ids)]
            if style_ids else _entries(catalog))
    try:
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
                (group is None or entry['group']==group) and
                (query is None or _matches(query,' '.join([entry['subject'], entry['individual_note'], entry['group'], *entry['labels']])))]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError('Invalid private style catalog; restore a valid backup') from error


def list_references(library_root=None, query=None, limit=50, group=None, pinned_only=False, offset=0, sort='default'):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be 1 through 100')
    if type(pinned_only) is not bool or type(offset) is not int or offset<0:
        raise ValueError('Invalid pinned_only or offset')
    if sort not in ('default','recent','frequent'):raise ValueError('sort must be default/recent/frequent')
    root = location(library_root); entries = records(root, query, group=group)
    usage={}
    if (root/'catalog.sqlite3').exists():
        with _catalog(root) as catalog:
            if catalog.execute("SELECT 1 FROM sqlite_master WHERE name='style_usage'").fetchone():
                usage={r[0]:(r[1],r[2]) for r in catalog.execute('SELECT id,COUNT(*),MAX(used_ns) FROM style_usage GROUP BY id')}
    entries=[r for r in entries if not pinned_only or r['pinned']]
    entries.sort(key=lambda r:(-(usage.get(r['id'],(0,0))[1 if sort=='recent' else 0]) if sort!='default' else 0,not r['pinned'],r['subject'].casefold(),r['id']))
    return {'library_root': str(root), 'total': len(entries),
            'offset':offset,'next_offset':offset+limit if offset+limit<len(entries) else None,
            'search_method':'expanded_keywords','sort':sort,
            'references': [dict(_public(root, entry),use_count=usage.get(entry['id'],(0,None))[0],
                                last_used_unix_ns=usage.get(entry['id'],(0,None))[1]) for entry in entries[offset:offset+limit]]}


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
        if catalog.execute("SELECT 1 FROM sqlite_master WHERE name='style_usage'").fetchone():
            catalog.execute('DELETE FROM style_usage WHERE id=?',(reference_id,))
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


def record_use(library_root, reference_id, event_id, observed_unix_ns=None):
    """Record an actual adopted/partial use once. Not a collection or taste inference."""
    root=location(library_root);event_id=_text(event_id,'event_id',500)
    observed=time.time_ns() if observed_unix_ns is None else observed_unix_ns
    if type(observed) is not int or observed<0:raise ValueError('Invalid observed use timestamp')
    if not (root/'catalog.sqlite3').exists():raise ValueError('Unknown personal style reference ID')
    with _catalog(root,write=True) as catalog:
        row=catalog.execute('SELECT entry FROM styles WHERE id=?',(reference_id,)).fetchone()
        if row is None:raise ValueError('Unknown personal style reference ID')
        verify(_public(root,normalize_entry(json.loads(row[0]))))
        catalog.execute('CREATE TABLE IF NOT EXISTS style_usage (id TEXT, event TEXT, used_ns INTEGER, PRIMARY KEY(id,event))')
        catalog.execute('INSERT OR IGNORE INTO style_usage VALUES(?,?,?)',(reference_id,event_id,observed))
    return {'reference_id':reference_id,'event_id':event_id}


def record_accepted_use(state):
    if state['status']!='accepted':return
    selection=state.get('reference_selection') or {};query=selection.get('query') or {}
    root=(query.get('personal_library') or {}).get('root')
    if not root:return
    personal={x['reference_id'] for x in query.get('candidates',[]) if x.get('origin')=='personal'}
    event=(state.get('render_result') or {}).get('submission_id')
    if not event:return
    for item in selection.get('decisions',[]):
        if item['reference_id'] in personal and item['decision'] in ('adopt','partial'):
            record_use(root,item['reference_id'],event)
