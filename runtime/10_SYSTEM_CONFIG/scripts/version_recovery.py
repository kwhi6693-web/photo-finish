"""Explicit recovery into a NEW private target, preserving historical bytes.

This is a recovered version view, not a migrated task ledger. It grants neither
upload permission nor revision/registration capability. No host SDK or renderer.
"""
from contextlib import closing
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import re
import sqlite3
import tempfile
import zipfile

from PIL import Image
import recovery_archive as archive
from runtime_io import digest
from style_library import location


def _private(path):
    raw = Path(path).expanduser()
    if any(p.is_symlink() for p in (raw, *raw.parents)):
        raise ValueError('Recovery target cannot traverse symlinks')
    return location(raw)


def _member(root, relative):
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(root):
        raise ValueError('Recovered paths cannot traverse symlinks or leave the private target')
    return path


def _proof(result_path, transfer, sha):
    return {'sha256': sha, 'workspace_path': transfer['workspace_path'],
            'result': archive._json(result_path)}


def _bundle(path, expected_sha256):
    if not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ValueError('An independently retained full archive SHA-256 is required')
    archive.checkpoint.inspect(path, expected_sha256)
    with zipfile.ZipFile(path) as z:
        payload = {n: z.read(n) for n in z.namelist()}
    r = json.loads(payload['recovery.json'])
    identity = dict(r)
    operation = identity.pop('operation_id')
    if (r.get('format') != 'photo-finish-version-recovery' or r.get('version') != 1 or
            digest(identity) != operation or not re.fullmatch('[0-9a-f]{32}', r['series'])):
        raise ValueError('Invalid recovery operation identity')
    expected_members = {'manifest.json', 'recovery.json', 'versions.sqlite3'}
    with tempfile.TemporaryDirectory() as folder:
        dbpath = Path(folder) / 'scoped.sqlite3'
        dbpath.write_bytes(payload['versions.sqlite3'])
        with closing(sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True)) as db:
            db.execute('PRAGMA query_only=ON')
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Recovery index is damaged')
            rows = db.execute('SELECT series,number,job,data,delivered FROM versions ORDER BY number').fetchall()
    if digest(rows) != r['sqlite_rows_sha256'] or len(rows) != len(r['versions']) or not rows:
        raise ValueError('Recovery row fingerprint mismatch')
    required = set()
    previous = None
    validated = {}
    for number, (row, v) in enumerate(zip(rows, r['versions']), 1):
        item = v['version']
        if (row[0] != r['series'] or row[1] != number or row[2] != item['job'] or
                json.loads(row[3]) != item or row[4] != 1 or v['delivered'] != 1 or
                v['number'] != number or item['series'] != r['series'] or item['label'] != 'V' + str(number)):
            raise ValueError('Recovery series/version identity conflict')
        if previous is None:
            if item['parent_version'] is not None or item['parent_output'] is not None:
                raise ValueError('Recovery first parent conflicts')
        else:
            parent = validated.get(item['parent_version'])
            if (parent is None or item['parent_output'] != parent['output'] or
                    item['source'] != parent['output'] or item['original_source'] != parent['original_source']):
                raise ValueError('Recovery parent/source conflict')
        prefix = 'evidence/V' + str(number) + '/'
        if v['members'] != {k: prefix + k + '.json' for k in ('job', 'record', 'photo_receipt', 'record_receipt')}:
            raise ValueError('Recovery evidence member identity conflict')
        for name in v['members'].values():
            expected_members.add(name)
            if hashlib.sha256(payload[name]).hexdigest() != r['evidence_sha256'][name]:
                raise ValueError('Recovery evidence hash conflict')
        job = json.loads(payload[v['members']['job']])
        record = json.loads(payload[v['members']['record']])
        record_hash = hashlib.sha256(payload[v['members']['record']]).hexdigest()
        if (job['status'] != 'accepted' or job['source'] != item['source'] or job['output'] != item['output'] or
                archive.history._contract(job) != item['accepted_contract_sha256'] or
                record['record_status'] != 'final' or record['ledger']['source'] != item['source'] or
                record['ledger']['output'] != item['output'] or
                record['ledger']['delivery_receipt'] != job['delivery_receipt'] or
                job['final_record']['sha256'] != record_hash or job['record_delivery']['record_sha256'] != record_hash):
            raise ValueError('Recovery formal record/contract conflict')
        for kind, field, idfield in [('record_receipt', 'record_delivery', 'record_library_file_id'),
                                     ('photo_receipt', 'delivery_receipt', 'output_library_file_id')]:
            receipt_bytes = payload[v['members'][kind]]
            if hashlib.sha256(receipt_bytes).hexdigest() != job[field]['result']['sha256']:
                raise ValueError('Recovery saved receipt hash conflict')
            receipt = json.loads(receipt_bytes)
            if kind == 'photo_receipt' and job.get('platform_delivery'):
                matches = [receipt] if (receipt.get('source') == 'platform_save_receipt' and
                           receipt.get('output_sha256') == item['output']['sha256']) else []
            else:
                old_path = job['final_record']['path'] if kind == 'record_receipt' else item['output']['path']
                matches = [x for x in receipt.get('results', []) if x.get('local_path') == old_path]
            if (len(matches) != 1 or matches[0].get('status') != 'succeeded' or
                    matches[0].get('library_file_id') != v[idfield] or job[field]['file_id'] != v[idfield]):
                raise ValueError('Recovery save receipt cloud identity conflict')
        for key in ('source', 'original_source', 'output', 'parent_output'):
            if item.get(key):
                required.add(item[key]['sha256'])
        dependency = r['dependencies'][item['output']['sha256']]
        if dependency['library_file_id'] != v['output_library_file_id']:
            raise ValueError('Recovery output cloud identity conflict')
        previous = item
        validated[item['label']] = item
    if (r['label'] != previous['label'] or set(payload) != expected_members or
            set(r['dependencies']) != required or set(r['evidence_sha256']) != expected_members -
            {'manifest.json', 'recovery.json', 'versions.sqlite3'}):
        raise ValueError('Recovery inventory conflict')
    return r, payload


def _views(root, recovery):
    def mapped(identity):
        if identity is None:
            return None
        return {'path': str(root / 'assets' / identity['sha256']), 'sha256': identity['sha256']}
    views = []
    for v in recovery['versions']:
        old = v['version']
        view = dict(old, historical_version=old, job=str(root / 'evidence' / v['members']['job']),
                    record=str(root / 'evidence' / v['members']['record']))
        for key in ('source', 'original_source', 'output', 'parent_output'):
            view[key] = mapped(old.get(key))
        views.append(view)
    return views


def restore(archive_path, expected_sha256, archive_library_file_id, result_path, cloud_files, destination):
    """Preflight actual readbacks, then resume exclusive copies into a new target.

    All inputs must be current host materializations. An unknown old upload never
    becomes a new upload. Interruption leaves an incomplete owned target; only an
    identical handoff can resume. Existing unowned targets are never adopted.
    """
    root = _private(destination)
    transfer = archive._transfer(result_path, archive_path)
    if not archive_library_file_id or transfer['library_file_id'] != archive_library_file_id:
        raise ValueError('Archive cloud identity conflicts with retained handoff')
    r, payload = _bundle(archive_path, expected_sha256)
    needed = dict(r['dependencies'])
    for v in r['versions']:
        name = v['members']['record']
        sha = hashlib.sha256(payload[name]).hexdigest()
        needed[sha] = {'sha256': sha, 'bytes': len(payload[name]),
                       'library_file_id': v['record_library_file_id']}
    verified = {}
    proofs = [_proof(result_path, transfer, expected_sha256)]
    for entry in cloud_files:
        path = Path(entry['path'])
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha not in needed:
            raise ValueError('Missing or unrelated recovery bytes')
        t = archive._transfer(entry['result_path'], path)
        expected = needed[sha]
        if (t['library_file_id'] != expected['library_file_id'] or len(data) != expected['bytes'] or
                ('storage_version' in expected and t.get('current_version_number') != expected['storage_version'])):
            raise ValueError('Recovery cloud identity/storage version conflict')
        if sha in verified:
            raise ValueError('Duplicate recovery dependency')
        verified[sha] = data
        proofs.append(_proof(entry['result_path'], t, sha))
    if set(verified) != set(needed):
        raise ValueError('Missing independently retrieved recovery dependencies or records')
    for sha in r['dependencies']:
        with Image.open(BytesIO(verified[sha])) as image:
            image.load()  # Complete decoding, no saving or rendering.
    owner = {'archive_sha256': expected_sha256, 'archive_library_file_id': archive_library_file_id,
             'operation_id': r['operation_id'], 'series': r['series'], 'label': r['label']}
    if root.exists():
        if not (root / 'identity.json').is_file():
            raise FileExistsError('Existing target has no recovery ownership; never adopt it')
        if archive._json(root / 'identity.json') != owner:
            raise ValueError('Another recovery owns this target')
    else:
        root.mkdir(parents=True, mode=0o700)
        archive._publish(root / 'identity.json', archive._bytes(owner))
    lock = root / 'writer.lock'
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    try:
        if (root / 'state.json').exists() and archive._json(root / 'state.json')['status'] == 'complete':
            return status(root)
        archive.checkpoint._durable_json(root / 'state.json', {'status': 'incomplete'})
        archive._publish(root / 'archive.zip', Path(archive_path).read_bytes())
        # Later continuation paths may differ. Retain every actual transfer as an
        # immutable event rather than overwrite the initial path-bearing proof.
        for proof in proofs:
            archive._publish(root / 'transfers' / (digest(proof) + '.json'), archive._bytes(proof))
        for name, data in payload.items():
            archive._publish(root / 'evidence' / name, data)
        for sha, data in verified.items():
            archive._publish(root / 'assets' / sha, data)
        views = _views(root, r)
        mapping = {'historical_paths_rewritten': False, 'versions': views,
                   'rollback': 'Only this new target is disposable; originals and old indexes are never written'}
        archive._publish(root / 'path-map.json', archive._bytes(mapping))
        with tempfile.TemporaryDirectory(dir=root) as folder:
            index = Path(folder) / 'recovered.sqlite3'
            with closing(sqlite3.connect(index)) as db:
                db.execute('CREATE TABLE versions (series TEXT, number INTEGER, data TEXT, PRIMARY KEY(series,number))')
                db.execute('CREATE TABLE session (key TEXT PRIMARY KEY, value TEXT)')
                for number, view in enumerate(views, 1):
                    db.execute('INSERT INTO versions VALUES(?,?,?)', (r['series'], number, json.dumps(view)))
                db.execute('INSERT INTO session VALUES(?,?)', ('current', json.dumps([r['series'], r['label']])))
                db.commit()
            archive._publish(root / 'recovered.sqlite3', index.read_bytes())
        # All publication uses exclusive links. No historical path is a write target.
        archive.checkpoint._durable_json(root / 'state.json',
            {'status': 'complete', 'index_sha256': archive.checkpoint._sha(root / 'recovered.sqlite3'),
             'proofs': sorted(p.name for p in (root / 'transfers').iterdir())})
        return status(root)
    finally:
        lock.unlink()


def status(destination):
    """Verify the recovered cursor, view, records and every exact byte again."""
    root = _private(destination)
    state = archive._json(root / 'state.json')
    if state['status'] != 'complete':
        raise ValueError('Recovery target is incomplete; no usable cursor')
    owner = archive._json(root / 'identity.json')
    r, payload = _bundle(root / 'archive.zip', owner['archive_sha256'])
    if (r['operation_id'], r['series'], r['label']) != (owner['operation_id'], owner['series'], owner['label']):
        raise ValueError('Recovered identity conflict')
    for name, data in payload.items():
        path = _member(root, 'evidence/' + name)
        if path.is_symlink() or path.read_bytes() != data:
            raise ValueError('Recovered evidence changed')
    for sha, item in r['dependencies'].items():
        path = _member(root, 'assets/' + sha)
        if path.is_symlink() or path.stat().st_size != item['bytes'] or archive.checkpoint._sha(path) != sha:
            raise ValueError('Recovered image bytes changed')
    for v in r['versions']:
        data = payload[v['members']['record']]
        sha = hashlib.sha256(data).hexdigest()
        path = _member(root, 'assets/' + sha)
        if path.is_symlink() or path.read_bytes() != data:
            raise ValueError('Recovered formal record changed')
    index = _member(root, 'recovered.sqlite3')
    if index.is_symlink() or archive.checkpoint._sha(index) != state['index_sha256']:
        raise ValueError('Recovered cursor/index changed')
    views = _views(root, r)
    if archive._json(root / 'path-map.json')['versions'] != views:
        raise ValueError('Recovered path map changed')
    with closing(sqlite3.connect(index.as_uri() + '?mode=ro', uri=True)) as db:
        rows = db.execute('SELECT series,number,data FROM versions ORDER BY number').fetchall()
        cursor = db.execute('SELECT key,value FROM session').fetchall()
        if ([(s, n, json.loads(d)) for s, n, d in rows] !=
                [(r['series'], n, v) for n, v in enumerate(views, 1)] or
                cursor != [('current', json.dumps([r['series'], r['label']]))] or
                db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok'):
            raise ValueError('Recovered version/cursor conflict')
    expected = dict(r['dependencies'])
    expected[owner['archive_sha256']] = {'library_file_id': owner['archive_library_file_id']}
    for v in r['versions']:
        sha = hashlib.sha256(payload[v['members']['record']]).hexdigest()
        expected[sha] = {'library_file_id': v['record_library_file_id']}
    seen = set()
    if not state.get('proofs'):
        raise ValueError('Missing actual host readback proofs')
    for name in state['proofs']:
        if not re.fullmatch('[0-9a-f]{64}\\.json', name):
            raise ValueError('Invalid host proof member')
        proof = archive._json(_member(root, 'transfers/' + name))
        if digest(proof) + '.json' != name or proof['sha256'] not in expected:
            raise ValueError('Host readback proof changed')
        matches = [t for t in archive._body(proof['result']).get('transfers', [])
                   if t.get('workspace_path') == proof['workspace_path']]
        item = expected[proof['sha256']]
        if (len(matches) != 1 or matches[0].get('library_file_id') != item['library_file_id'] or
                ('storage_version' in item and matches[0].get('current_version_number') != item['storage_version'])):
            raise ValueError('Retained host readback cloud identity conflict')
        seen.add(proof['sha256'])
    if seen != set(expected):
        raise ValueError('Missing actual host readback identities')
    return dict(views[-1], status='restored_read_only', archive_library_file_id=owner['archive_library_file_id'],
                operation_id=r['operation_id'], renderer_calls=0, write_allowed=False,
                historical_paths_rewritten=False, original_ledger_migrated=False,
                scope='Private recovered view; no task registration, revision or host upload authority')
