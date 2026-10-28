"""Private recovery credentials and a fail-closed Work-host storage handshake.

No network client, credentials, renderer, version registration or background hook.
Library calls and truthful evidence capture belong to the authenticated host.
"""
from contextlib import contextmanager, closing
from pathlib import Path
import json
import hashlib
import os
import re
import sqlite3
import tempfile

import delivery_automation as delivery
import private_checkpoint as checkpoint
import task_history as history
import workflow_session as workflow
from runtime_io import digest
from style_library import location


def _json(path):
    if Path(path).is_symlink():
        raise ValueError('Recovery evidence cannot be a symlink')
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _root(session_root):
    raw = Path(session_root).expanduser()
    if any(p.is_symlink() for p in (raw, *raw.parents)):
        raise ValueError('Recovery root cannot traverse symlinks')
    root = location(raw) / 'recovery-archives'
    if root.is_symlink():
        raise ValueError('Recovery root cannot be a symlink')
    return root


@contextmanager
def _locked(session_root):
    root = _root(session_root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = root / 'writer.lock'
    # A process loss leaves the lock for investigation, never an automatic retry.
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.close(fd)
        yield root
    finally:
        lock.unlink()


def _publish(path, data):
    """Exclusive, durable publication; same bytes may be reused after interruption."""
    path = Path(path)
    if any(p.is_symlink() for p in path.parents):
        raise ValueError('Recovery publication cannot traverse symlinks')
    if os.path.lexists(path):
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ValueError('Recovery conflict; existing evidence cannot be overwritten')
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        try:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.link(temporary, path)
        checkpoint._directory_sync(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                       allow_nan=False) + '\n').encode('utf-8')


def _body(value):
    # Native tool result or its unchanged structuredContent may be retained.
    value = value.get('structuredContent', value)
    return value.get('result', value)


def _transfer(result_path, local_path):
    result = _body(_json(result_path))
    matches = [t for t in result.get('transfers', [])
               if t.get('workspace_path') and Path(t['workspace_path']).resolve() == Path(local_path).resolve()]
    if len(matches) != 1 or not matches[0].get('library_file_id'):
        raise ValueError('One actual Library materialization transfer matching the local bytes is required')
    return matches[0]


def _rows(session_root, series, number):
    # Online backup includes committed WAL data. The source index is only read.
    with history._index(session_root) as incoming, closing(sqlite3.connect(':memory:')) as snap:
        incoming.backup(snap)
        if snap.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Version snapshot is damaged')
        return snap.execute('SELECT series,number,job,data,delivered FROM versions '
                            'WHERE series=? AND number<=? ORDER BY number', (series, number)).fetchall()


def prepare(path, session_root, directory_id, cloud_files):
    """Freeze saved, delivered versions; return a host request, never upload.

    cloud_files: actual materializations [{path, result_path}], covering each
    source/original_source/output/parent_output hash in this series prefix.
    Host authorization and account isolation are not inferred by this module.
    """
    if not isinstance(directory_id, str) or not directory_id.strip():
        raise ValueError('Host-resolved owner-private Library directory ID required')
    if not isinstance(cloud_files, list):
        raise ValueError('Actual dependency materializations required')
    with _locked(session_root) as root:
        job = str(Path(path).resolve())
        with history._index(session_root) as db:
            row = db.execute('SELECT series,number FROM versions WHERE job=?', (job,)).fetchone()
        if row is None:
            raise ValueError('Use the existing delivered version; recovery never registers a version')
        series, number = row
        if not re.fullmatch('[0-9a-f]{32}', series):
            raise ValueError('Invalid series identity')
        rows = _rows(session_root, series, number)
        required = {}
        payload = {}
        versions = []
        for sid, num, old_job, data, delivered in rows:
            item = json.loads(data)
            state = history._verify(item)
            if delivered != 1 or delivery.plan(old_job)['action'] != 'DELIVER':
                raise ValueError('Every included version needs actual delivery and both confirmed saves')
            if sid != item['series'] or item['label'] != 'V' + str(num) or old_job != item['job']:
                raise ValueError('Version row conflicts with its recorded identity')
            if num == 1:
                if item['parent_version'] is not None or item['parent_output'] is not None:
                    raise ValueError('First version has a conflicting parent')
            else:
                parent = next((v for v in versions if v['version']['label'] == item['parent_version']), None)
                if parent is None or parent['version']['output'] != item['parent_output'] or item['source'] != item['parent_output']:
                    raise ValueError('Parent relation is missing or conflicts with the selected source')
            prefix = 'evidence/V' + str(num)
            bindings = {'job': workflow._file(old_job), 'record': state['final_record'],
                        'photo_receipt': state['delivery_receipt']['result'],
                        'record_receipt': state['record_delivery']['result']}
            for name, identity in bindings.items():
                if workflow._file(identity['path']) != identity:
                    raise ValueError('Saved recovery evidence changed')
                payload[prefix + '/' + name + '.json'] = Path(identity['path']).read_bytes()
            record = _json(state['final_record']['path'])
            if (record.get('record_status') != 'final' or record['ledger']['source'] != state['source'] or
                    record['ledger']['output'] != state['output'] or
                    record['ledger']['delivery_receipt'] != state['delivery_receipt'] or
                    state['record_delivery']['record_sha256'] != state['final_record']['sha256']):
                raise ValueError('Formal record does not match the saved job')
            saved_record = delivery._receipt(state['record_delivery']['result']['path'], state['final_record']['path'])
            if saved_record.get('library_file_id') != state['record_delivery']['file_id']:
                raise ValueError('Record cloud identity conflicts with original save receipt')
            if state.get('platform_delivery'):
                proof = _json(state['delivery_receipt']['result']['path'])
                if (proof.get('source') != 'platform_save_receipt' or proof.get('status') != 'succeeded' or
                        proof.get('library_file_id') != state['delivery_receipt']['file_id'] or
                        proof.get('output_sha256') != state['output']['sha256']):
                    raise ValueError('Platform photo receipt conflicts with saved identity')
            else:
                saved_photo = delivery._receipt(state['delivery_receipt']['result']['path'], state['output']['path'])
                if saved_photo.get('library_file_id') != state['delivery_receipt']['file_id']:
                    raise ValueError('Photo cloud identity conflicts with original save receipt')
            # Never leak other tasks from a shared batch receipt into a per-series archive.
            allowed = {json.loads(r[3])['output']['path'] for r in rows}
            allowed.update(workflow._load(r[2])['final_record']['path'] for r in rows)
            for kind in ('photo_receipt', 'record_receipt'):
                receipt = json.loads(payload[prefix + '/' + kind + '.json'])
                if 'results' in receipt and any(x.get('local_path') not in allowed for x in receipt['results']):
                    raise ValueError('Shared receipt includes unrelated tasks; require a scoped host archive')
            for key in ('source', 'original_source', 'output', 'parent_output'):
                identity = item.get(key)
                if identity:
                    required.setdefault(identity['sha256'], []).append(identity)
            versions.append({'version': item, 'number': num, 'delivered': delivered,
                             'members': {k: prefix + '/' + k + '.json' for k in bindings},
                             'submission_id': (state.get('execution_adapter') or {}).get('submission_id'),
                             'output_library_file_id': state['delivery_receipt']['file_id'],
                             'output_storage_version': state['delivery_receipt'].get('version_id'),
                             'record_library_file_id': state['record_delivery']['file_id']})
        dependencies = {}
        for entry in cloud_files:
            identity = workflow._file(entry['path'])
            if identity['sha256'] not in required:
                raise ValueError('Unrelated dependency materialization refused')
            transfer = _transfer(entry['result_path'], entry['path'])
            value = {'library_file_id': transfer['library_file_id'],
                     'storage_version': transfer.get('current_version_number'),
                     'sha256': identity['sha256'], 'bytes': Path(entry['path']).stat().st_size}
            old = dependencies.get(identity['sha256'])
            if old and old != value:
                raise ValueError('Conflicting cloud identities for the same dependency')
            dependencies[identity['sha256']] = value
        if set(dependencies) != set(required):
            raise ValueError('Missing independently materialized cloud dependencies; no complete archive claim')
        for version in versions:
            if dependencies[version['version']['output']['sha256']]['library_file_id'] != version['output_library_file_id']:
                raise ValueError('Output cloud identity conflicts with its original save receipt')
        descriptor = {'format': 'photo-finish-version-recovery', 'version': 1,
                      'classification': 'new_recovery_credentials_not_historical_ledger',
                      'series': series, 'label': 'V' + str(number), 'versions': versions,
                      'dependencies': dependencies, 'directory_id': directory_id,
                      'evidence_sha256': {k: hashlib.sha256(v).hexdigest() for k, v in payload.items()},
                      'sqlite_kind': 'derived_series_prefix_from_online_backup',
                      'sqlite_rows_sha256': digest(rows), 'historical_paths_rewritten': False,
                      'atomic_cross_service_transaction': False}
        operation = digest(descriptor)
        descriptor['operation_id'] = operation
        slot = root / (series + '-V' + str(number))
        if slot.is_symlink():
            raise ValueError('Recovery slot cannot be a symlink')
        slot.mkdir(exist_ok=True, mode=0o700)
        if (slot / 'identity.json').exists() and not (slot / 'state.json').exists():
            raise ValueError('Recovery state lost or capture interrupted; host reconciliation required, never recreate pending')
        _publish(slot / 'identity.json', _bytes(descriptor))
        if (slot / 'state.json').exists():
            return _status(slot)
        payload['recovery.json'] = _bytes(descriptor)
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            stage = Path(temporary) / 'payload'
            stage.mkdir()
            # Keep exact row JSON; scope the derived SQLite and omit session cursors.
            with closing(sqlite3.connect(stage / 'versions.sqlite3')) as db:
                db.execute('CREATE TABLE versions (series TEXT, number INTEGER, job TEXT UNIQUE, data TEXT, delivered INTEGER, PRIMARY KEY(series,number))')
                db.executemany('INSERT INTO versions VALUES(?,?,?,?,?)', rows)
                db.commit()
            for name, content in payload.items():
                dest = stage / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(content)
            # A fixed origin makes the existing checkpoint format portable/deterministic.
            frozen = slot / 'payload'
            for member in stage.rglob('*'):
                if member.is_file():
                    _publish(frozen / member.relative_to(stage), member.read_bytes())
        if rows != _rows(session_root, series, number):
            raise ValueError('Selected versions changed during capture; investigate, do not publish')
        for version in versions:
            history._verify(version['version'])
            state = workflow._load(version['version']['job'])
            for name, identity in [('job', workflow._file(version['version']['job'])),
                                   ('record', state['final_record']),
                                   ('photo_receipt', state['delivery_receipt']['result']),
                                   ('record_receipt', state['record_delivery']['result'])]:
                if Path(identity['path']).read_bytes() != payload[version['members'][name]]:
                    raise ValueError('Evidence changed during capture; investigate before saving')
        archive = slot / ('PF-Version-' + operation + '.zip')
        checkpoint.export(frozen, archive,
                                   [str(p.relative_to(frozen)).replace(os.sep, '/') for p in frozen.rglob('*') if p.is_file()])
        state = {'operation_id': operation, 'status': 'credentials_pending',
                 'archive': workflow._file(archive), 'bytes': archive.stat().st_size,
                 'library_file_id': None, 'events': []}
        checkpoint._durable_json(slot / 'state.json', state)
        return _status(slot)


def _slot(session_root, series, version):
    if not re.fullmatch('[0-9a-f]{32}', series) or not re.fullmatch('V[1-9][0-9]*', version):
        raise ValueError('Invalid series/version selector')
    slot = _root(session_root) / (series + '-' + version)
    if slot.is_symlink():
        raise ValueError('Recovery slot cannot be a symlink')
    return slot


def _status(slot):
    state = _json(slot / 'state.json')
    if workflow._file(state['archive']['path']) != state['archive']:
        raise ValueError('Frozen recovery archive changed')
    descriptor = _json(slot / 'identity.json')
    if state['operation_id'] != descriptor['operation_id']:
        raise ValueError('Operation identity conflict')
    if state['status'] == 'credentials_pending' and (slot / 'claim.json').exists():
        state['status'] = 'result_unknown'
    action = {'credentials_pending': 'HOST_SAVE_ONCE', 'result_unknown': 'HOST_QUERY_EXISTING',
              'uploaded_unverified': 'HOST_MATERIALIZE_EXISTING', 'archive_confirmed': 'DONE'}[state['status']]
    return dict(state, photo_saved=True, archive_confirmed=state['status'] == 'archive_confirmed',
                host_action=action, directory_id=descriptor['directory_id'],
                query_name=Path(state['archive']['path']).name, renderer_calls=0,
                host_required=True, background_automation_installed=False)


def status(session_root, series, version):
    return _status(_slot(session_root, series, version))


def claim(session_root, series, version):
    """Durably mark unknown BEFORE the host's sole create attempt."""
    with _locked(session_root):
        slot = _slot(session_root, series, version)
        current = _status(slot)
        if current['status'] != 'credentials_pending':
            return dict(current, write_allowed=False)
        state = _json(slot / 'state.json')
        if (slot / 'claim.json').exists():
            return dict(current, status='result_unknown', host_action='HOST_QUERY_EXISTING', write_allowed=False)
        _publish(slot / 'claim.json', _bytes({'operation_id':state['operation_id']}))
        state['status'] = 'result_unknown'
        checkpoint._durable_json(slot / 'state.json', state)
        return dict(_status(slot), write_allowed=True)


def _event(slot, state, kind, path):
    content = Path(path).read_bytes()
    name = 'events/' + kind + '-' + digest({'bytes': content.hex()}) + '.json'
    _publish(slot / name, content)
    event = {'kind': kind, 'member': name, 'file': workflow._file(slot / name)}
    if event not in state['events']:
        state['events'].append(event)


def observe(session_root, series, version, result_path):
    """Consume existing normalized Library helper results; never retry a create.

    The helper's local_path/hash association is host evidence, not a signed
    server content hash. Full materialization remains mandatory.
    """
    with _locked(session_root):
        slot = _slot(session_root, series, version)
        current = _status(slot)
        if current['status'] == 'credentials_pending':
            raise ValueError('Claim the operation before the actual host call')
        state = _json(slot / 'state.json')
        _event(slot, state, 'save', result_path)
        # Keep even failed/partial/unknown results before examining them.
        checkpoint._durable_json(slot / 'state.json', state)
        try:
            saved = delivery._receipt(result_path, state['archive']['path'])
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return _status(slot)
        identity = saved.get('library_file_id')
        if not identity:
            raise ValueError('Stable Library identity required, not a backing file ID')
        if state['library_file_id'] not in (None, identity):
            raise ValueError('Conflicting save identity; never overwrite the first confirmation')
        state['library_file_id'] = identity
        if state['status'] != 'archive_confirmed':
            state['status'] = 'uploaded_unverified'
        checkpoint._durable_json(slot / 'state.json', state)
        return _status(slot)


def confirm(session_root, series, version, result_path, materialized_path):
    """Resolve success or unknown by actual Library readback, never metadata alone."""
    with _locked(session_root):
        slot = _slot(session_root, series, version)
        current = _status(slot)
        if current['status'] == 'credentials_pending':
            raise ValueError('No actual save attempt to reconcile')
        state = _json(slot / 'state.json')
        transfer = _transfer(result_path, materialized_path)
        identity = transfer['library_file_id']
        if state['library_file_id'] not in (None, identity):
            raise ValueError('Readback cloud identity conflict')
        if (Path(materialized_path).stat().st_size != state['bytes'] or
                workflow._file(materialized_path)['sha256'] != state['archive']['sha256']):
            raise ValueError('Readback bytes conflict; do not resave or overwrite')
        checkpoint.inspect(materialized_path, state['archive']['sha256'])
        _event(slot, state, 'materialize', result_path)
        state['library_file_id'] = identity
        state['status'] = 'archive_confirmed'
        checkpoint._durable_json(slot / 'state.json', state)
        return _status(slot)
