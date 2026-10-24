"""Versioned private data backups. Never publish these archives as skill releases."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import tempfile
import zipfile
from PIL import Image
import style_library as s
import user_preferences as p
from style_match import features

MAX_TOTAL=2*1024**3
MAX_FILE=256*1024**2
MAX_CATALOG=16*1024**2
MAX_MANIFEST=4*1024**2
IMAGE_NAME=re.compile(r'images/[0-9a-f]{64}\.(jpg|png|webp|tiff)')


def _json(value): return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')


def _load_json(data):
    def bad(value): raise ValueError('Nonfinite JSON number')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('Duplicate backup JSON key')
            result[key]=value
        return result
    try: return json.loads(data.decode('utf-8'),parse_constant=bad,object_pairs_hook=pairs)
    except (UnicodeError,json.JSONDecodeError,RecursionError) as error: raise ValueError('Invalid backup JSON') from error


def _hash(stream):
    result=hashlib.sha256()
    while True:
        chunk=stream.read(1024*1024)
        if not chunk: return result.hexdigest()
        result.update(chunk)


def _history(connection):
    if not p._has(connection,'profile_history'): return []
    return [_history_row(dict(revision_id=rid,action=action,created_ns=created,state=_load_json(payload.encode())))
            for rid,action,created,payload in connection.execute('SELECT id,action,created_ns,payload FROM profile_history ORDER BY id')]


def _history_row(row):
    if not isinstance(row,dict) or set(row)!={'revision_id','action','created_ns','state'}: raise ValueError('Invalid backup history')
    if (type(row['revision_id']) is not int or row['revision_id']<1 or type(row['created_ns']) is not int or
            not 0<=row['created_ns']<2**63 or not isinstance(row['action'],str) or not row['action'] or len(row['action'])>80):
        raise ValueError('Invalid backup revision metadata')
    return dict(row,state=p.normalize_state(row['state']))


def _settings_present(connection):
    return bool((p._has(connection,'user_preferences') and connection.execute('SELECT 1 FROM user_preferences WHERE id=1').fetchone()) or p._rules(connection))


def _snapshot(connection):
    if connection is None:
        return {'version':1,'styles':[],'settings':{'profile':dict(version=1,rules=[],preferences=[]),'scoped_rules':[]},'settings_present':False,'history':[]}
    return dict(version=1,styles=s._entries(connection),settings=p._state(connection),settings_present=_settings_present(connection),history=_history(connection))


def _validate_catalog(value):
    if not isinstance(value,dict) or set(value)!={'version','styles','settings','settings_present','history'} or type(value['version']) is not int or value['version']!=1:
        raise ValueError('Unsupported backup catalog version')
    if not isinstance(value['styles'],list) or len(value['styles'])>10000 or type(value['settings_present']) is not bool:
        raise ValueError('Invalid backup catalog')
    styles=[s.normalize_entry(entry) for entry in value['styles']]
    if len({r['id'] for r in styles})!=len(styles): raise ValueError('Duplicate backup style IDs')
    if not isinstance(value['history'],list) or len(value['history'])>20: raise ValueError('Invalid backup history size')
    history=[_history_row(r) for r in value['history']]
    if len({r['revision_id'] for r in history})!=len(history): raise ValueError('Duplicate backup history IDs')
    settings=p.normalize_state(value['settings'])
    if not value['settings_present'] and (settings['profile']['rules'] or settings['profile']['preferences'] or settings['scoped_rules'] or history):
        raise ValueError('Backup settings presence contradicts its contents')
    return dict(value,styles=styles,settings=settings,history=sorted(history,key=lambda r:r['revision_id']))


def _zip_info(name):
    info=zipfile.ZipInfo(name);info.compress_type=zipfile.ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100600<<16
    return info


def export_backup(destination,library_root=None):
    root=s.location(library_root);raw=Path(destination).expanduser()
    if raw.is_symlink(): raise ValueError('Backup destination cannot be a symlink')
    target=raw.resolve()
    if target.suffix.lower()!='.zip' or target.is_relative_to(root): raise ValueError('Use a new ZIP outside the private store')
    s.location(target.parent)  # Also forbids a Git checkout or skill installation.
    if target.exists(): raise FileExistsError('Backup destination already exists')
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    def write(connection):
        catalog=_validate_catalog(_snapshot(connection));manifest={};total=0
        catalog_bytes=_json(catalog)
        total=len(catalog_bytes)
        if total>MAX_CATALOG or total>MAX_TOTAL: raise ValueError('Backup catalog exceeds its bounded size')
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(_zip_info('catalog.json'),catalog_bytes)
            manifest['catalog.json']={'sha256':hashlib.sha256(catalog_bytes).hexdigest(),'bytes':len(catalog_bytes)}
            for entry in catalog['styles']:
                source=s._asset(root,entry['private_relative_path']);s.verify(s._public(root,entry))
                size=source.stat().st_size;total+=size
                if size>MAX_FILE or total>MAX_TOTAL: raise ValueError('Private backup exceeds its bounded image size')
                digest=hashlib.sha256();count=0
                with source.open('rb') as incoming,archive.open(_zip_info(entry['private_relative_path']),'w') as outgoing:
                    while True:
                        chunk=incoming.read(1024*1024)
                        if not chunk: break
                        count+=len(chunk)
                        if count>MAX_FILE or total-size+count>MAX_TOTAL: raise ValueError('Image grew beyond backup bounds')
                        digest.update(chunk);outgoing.write(chunk)
                if digest.hexdigest()!=entry['sha256'] or count!=size: raise ValueError('Style bytes changed during backup')
                manifest[entry['private_relative_path']]={'sha256':digest.hexdigest(),'bytes':count}
            manifest_bytes=_json({'format':'photo-finish-private-backup','version':1,'distribution_scope':'private','files':manifest})
            if len(manifest_bytes)>MAX_MANIFEST or total+len(manifest_bytes)>MAX_TOTAL: raise ValueError('Backup manifest exceeds bounded size')
            archive.writestr(_zip_info('manifest.json'),manifest_bytes)
        return catalog
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as stream: temporary=Path(stream.name)
        if p._existing(root):
            # The reserved writer lock prevents metadata updates and library-file deletion.
            with s._catalog(root,write=True) as connection: catalog=write(connection)
        else: catalog=write(None)
        os.link(temporary,target)
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)
    with target.open('rb') as stream: sha=_hash(stream)
    return {'path':str(target),'sha256':sha,'style_count':len(catalog['styles']),'history_count':len(catalog['history']),'private':True,'format_version':1}


@contextmanager
def _validated(archive_path):
    path=Path(archive_path).expanduser()
    if path.is_symlink(): raise ValueError('Backup source cannot be a symlink')
    try:
        with path.open('rb') as stream,tempfile.TemporaryDirectory(prefix='photo-finish-import-') as folder:
            sha=_hash(stream);stream.seek(0);stage=Path(folder).resolve()
            with zipfile.ZipFile(stream) as archive:
                infos=archive.infolist();names=[i.filename for i in infos]
                if len(names)>10002 or len(set(names))!=len(names) or 'manifest.json' not in names or 'catalog.json' not in names:
                    raise ValueError('Missing or duplicate backup entries')
                total=0
                for info in infos:
                    mode=info.external_attr>>16
                    if (info.flag_bits&1 or info.is_dir() or stat.S_ISLNK(mode) or
                            stat.S_IFMT(mode) not in (0,stat.S_IFREG) or
                            (info.filename not in ('manifest.json','catalog.json') and not IMAGE_NAME.fullmatch(info.filename))):
                        raise ValueError('Unsafe or unsupported backup entry')
                    limit=MAX_MANIFEST if info.filename=='manifest.json' else MAX_CATALOG if info.filename=='catalog.json' else MAX_FILE
                    total+=info.file_size
                    if info.file_size>limit or total>MAX_TOTAL: raise ValueError('Backup exceeds bounded size')
                manifest=_load_json(archive.read('manifest.json'))
                if (not isinstance(manifest,dict) or set(manifest)!={'format','version','distribution_scope','files'} or
                        manifest['format']!='photo-finish-private-backup' or type(manifest['version']) is not int or manifest['version']!=1 or
                        manifest['distribution_scope']!='private' or not isinstance(manifest['files'],dict)):
                    raise ValueError('Unsupported private backup format')
                if set(manifest['files'])!=set(names)-{'manifest.json'}: raise ValueError('Backup member list differs from manifest')
                for info in infos:
                    if info.filename=='manifest.json': continue
                    expected=manifest['files'][info.filename]
                    if (not isinstance(expected,dict) or set(expected)!={'sha256','bytes'} or not isinstance(expected['sha256'],str) or
                            not re.fullmatch(r'[0-9a-f]{64}',expected['sha256']) or type(expected['bytes']) is not int or expected['bytes']!=info.file_size):
                        raise ValueError('Invalid backup member identity')
                    target=stage/info.filename;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                    digest=hashlib.sha256();count=0
                    with archive.open(info) as incoming,target.open('xb') as outgoing:
                        target.chmod(0o600)
                        while True:
                            chunk=incoming.read(1024*1024)
                            if not chunk: break
                            count+=len(chunk)
                            if count>expected['bytes']: raise ValueError('Backup member exceeded declared size')
                            digest.update(chunk);outgoing.write(chunk)
                    if count!=expected['bytes'] or digest.hexdigest()!=expected['sha256']: raise ValueError('Backup member checksum changed')
                catalog=_validate_catalog(_load_json((stage/'catalog.json').read_bytes()))
                expected_names={'catalog.json'}|{r['private_relative_path'] for r in catalog['styles']}
                if expected_names!=set(manifest['files']): raise ValueError('Backup contains unindexed or missing image files')
                for entry in catalog['styles']:
                    photo=s._asset(stage,entry['private_relative_path'])
                    if manifest['files'][entry['private_relative_path']]['sha256']!=entry['sha256']: raise ValueError('Catalog/image identity mismatch')
                    with Image.open(photo) as image:
                        image.load()
                        if s.FORMATS.get(image.format)!=photo.suffix: raise ValueError('Backup image format does not match filename')
                    entry['measured_full']=features(photo,entry['sha256'])
            stream.seek(0)
            if _hash(stream)!=sha: raise ValueError('Backup changed during validation')
            yield catalog,stage,sha
    except (zipfile.BadZipFile,zipfile.LargeZipFile,RuntimeError) as error:
        raise ValueError('Invalid or unsupported private backup archive') from error


def _current(root,connection=None):
    if connection is not None: return _snapshot(connection)
    if not p._existing(root): return _snapshot(None)
    with s._catalog(root) as local: return _snapshot(local)


def _plan(current,incoming):
    known={r['id']:r for r in current['styles']};conflicts=[];new=0;duplicates=0
    for entry in incoming['styles']:
        if entry['id'] not in known: new+=1
        else:
            duplicates+=1
            if s._metadata(entry)!=s._metadata(known[entry['id']]): conflicts.append({'kind':'style_metadata','reference_id':entry['id']})
    settings_conflict=current['settings_present'] and incoming['settings_present'] and current['settings']!=incoming['settings']
    if settings_conflict: conflicts.append({'kind':'settings'})
    return {'new_styles':new,'duplicate_styles':duplicates,'conflicts':conflicts,'settings_conflict':settings_conflict,
            'incoming_history_count':len(incoming['history']),'default_policy':'keep_existing'}


def inspect_backup(archive_path,library_root=None):
    root=s.location(library_root)
    with _validated(archive_path) as (incoming,stage,sha):
        return dict(_plan(_current(root),incoming),archive_sha256=sha,format_version=1)


def import_backup(archive_path,consent=False,library_root=None,style_policy='keep_existing',settings_policy='keep_existing',expected_archive_sha256=None):
    if consent is not True: raise ValueError('Explicit intent to import private data is required')
    if style_policy not in ('keep_existing','use_backup') or settings_policy not in ('keep_existing','use_backup'):
        raise ValueError('Import policies must be keep_existing or use_backup')
    root=s.location(library_root);rollback_assets=[];imported=0;updated=0;settings_applied=False;history_restored=False
    with _validated(archive_path) as (incoming,stage,sha):
        if expected_archive_sha256 is not None and sha!=expected_archive_sha256: raise ValueError('Backup differs from the inspected archive')
        with s._catalog(root,write=True,rollback_assets=rollback_assets) as connection:
            current=_current(root,connection);plan=_plan(current,incoming);known={r['id']:r for r in current['styles']}
            # Check all existing indexed photographs before publishing any new copy.
            for entry in current['styles']: s.verify(s._public(root,entry))
            for entry in incoming['styles']:
                if entry['id'] in known:
                    if style_policy=='use_backup' and s._metadata(entry)!=s._metadata(known[entry['id']]):
                        connection.execute('UPDATE styles SET entry=? WHERE id=?',(_json(entry).decode(),entry['id']));updated+=1
                    continue
                target=s._asset(root,entry['private_relative_path']);target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                s._asset(root,entry['private_relative_path'])
                # Cross-filesystem safe copy, then no-overwrite link in the target directory.
                temporary=None
                try:
                    with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as outgoing,(stage/entry['private_relative_path']).open('rb') as source:
                        temporary=Path(outgoing.name)
                        while True:
                            chunk=source.read(1024*1024)
                            if not chunk: break
                            outgoing.write(chunk)
                    try:
                        os.link(temporary,target);rollback_assets.append((entry['id'],target))
                    except FileExistsError: s.verify(dict(path=str(target),sha256=entry['sha256']))
                finally:
                    if temporary is not None: temporary.unlink(missing_ok=True)
                connection.execute('INSERT INTO styles VALUES(?,?)',(entry['id'],_json(entry).decode()));imported+=1
            if (incoming['settings_present'] and not current['settings_present']) or settings_policy=='use_backup':
                if not current['settings_present']:
                    p._persist(connection,incoming['settings'])
                    if incoming['history']:
                        connection.execute('CREATE TABLE IF NOT EXISTS profile_history (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, created_ns INTEGER NOT NULL, payload TEXT NOT NULL)')
                        connection.executemany('INSERT INTO profile_history(id,action,created_ns,payload) VALUES(?,?,?,?)',
                            [(r['revision_id'],r['action'],r['created_ns'],_json(r['state']).decode()) for r in incoming['history']])
                        history_restored=True
                else: p._write(connection,incoming['settings'],'backup-import')
                settings_applied=True
    return dict(plan,archive_sha256=sha,imported_styles=imported,updated_styles=updated,settings_applied=settings_applied,history_restored=history_restored)
