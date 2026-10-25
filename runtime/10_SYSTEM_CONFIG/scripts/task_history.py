"""Private conversation index. Ledgers and exact file bytes remain authoritative.

No rendering, implicit visual acceptance, personal-preference writes or host saving.
Each host conversation must supply its own private session_root.
"""
from contextlib import contextmanager
from pathlib import Path
import json, os, sqlite3, tempfile, uuid
import workflow_session as w
import experience
from runtime_io import digest
from style_library import location


@contextmanager
def _index(session_root, write=False):
    root=location(session_root);db=root/'tasks.sqlite3'
    if db.is_symlink():raise ValueError('Task index cannot be a symlink')
    if not write and not db.exists():raise ValueError('No conversation history at this location')
    if write:root.mkdir(parents=True,exist_ok=True,mode=0o700)
    connection=sqlite3.connect(db if write else db.as_uri()+'?mode=ro',uri=not write,timeout=10)
    try:
        if write:
            db.chmod(0o600);connection.execute('BEGIN IMMEDIATE')
            connection.execute('CREATE TABLE IF NOT EXISTS versions (series TEXT, number INTEGER, job TEXT UNIQUE, data TEXT, delivered INTEGER DEFAULT 0, PRIMARY KEY(series,number))')
            connection.execute('CREATE TABLE IF NOT EXISTS session (key TEXT PRIMARY KEY, value TEXT)')
        yield connection
        if write:connection.commit()
    finally:connection.close()


def _row(row):
    if row is None:raise ValueError('Version not found in this conversation')
    return json.loads(row[0])


def _number(version):
    if not isinstance(version,str) or not version.startswith('V') or not version[1:].isdigit() or int(version[1:])<1:
        raise ValueError('Select a version label such as V1')
    return int(version[1:])


def _contract(state):
    return digest({key:state.get(key) for key in ('source','output','protection_plan','professional_direction',
                   'reference_selection','render_result','render_history','revision')})


def _verify(item):
    state=w._load(item['job'])
    if state['status']!='accepted' or state.get('output')!=item['output'] or state.get('source')!=item['source']:
        raise ValueError('Version no longer matches its accepted ledger')
    if item.get('accepted_contract_sha256')!=_contract(state):raise ValueError('Historical photographic contract changed')
    for identity in (item['output'],item['source'],item['original_source']):
        if w._file(identity['path'])!=identity:raise ValueError('Historical file changed or is missing; do not rerender')
    return state


def register(path, session_root):
    state=w._load(path)
    if state['status']!='accepted':raise ValueError('Only accepted formal outputs receive a version')
    job=str(Path(path).resolve());revision=state.get('revision') or {}
    with _index(session_root,True) as db:
        old=db.execute('SELECT data FROM versions WHERE job=?',(job,)).fetchone()
        if old:
            item=_row(old);_verify(item);return item
        series=revision.get('series') or uuid.uuid4().hex
        if revision and location(session_root)!=Path(revision['session_root']):raise ValueError('Revision belongs to a different conversation')
        number=db.execute('SELECT COALESCE(MAX(number),0)+1 FROM versions WHERE series=?',(series,)).fetchone()[0]
        item={'series':series,'label':'V'+str(number),'job':job,'output':state['output'],'source':state['source'],
              'original_source':revision.get('original_source',state['source']),
              'parent_version':revision.get('parent_version'),'parent_output':revision.get('parent_output'),
              'revision_request':revision.get('request'),'accepted_contract_sha256':_contract(state)}
        _verify(item)
        db.execute('INSERT INTO versions(series,number,job,data) VALUES(?,?,?,?)',(series,number,job,json.dumps(item,ensure_ascii=False)))
        db.execute('INSERT OR REPLACE INTO session VALUES(?,?)',('current',json.dumps([series,item['label']])))
    return item


def get(session_root, series, version):
    with _index(session_root) as db:
        item=_row(db.execute('SELECT data FROM versions WHERE series=? AND number=?',(series,_number(version))).fetchone())
    _verify(item);return item


def history(session_root, series):
    with _index(session_root) as db:
        items=[_row(row) for row in db.execute('SELECT data FROM versions WHERE series=? ORDER BY number',(series,))]
    return {'versions':items,'scope':'Metadata index; selecting a version verifies ledger and file hashes'}


def current(session_root):
    with _index(session_root) as db:
        value=db.execute('SELECT value FROM session WHERE key=?',('current',)).fetchone()
    if value is None:raise ValueError('No selected version in this conversation')
    series,version=json.loads(value[0]);return get(session_root,series,version)


def restore(session_root, series, version):
    item=get(session_root,series,version)
    # Only the conversation cursor changes; no accepted ledger or image is written.
    with _index(session_root,True) as db:
        db.execute('INSERT OR REPLACE INTO session VALUES(?,?)',('current',json.dumps([series,version])))
    return dict(item,render_calls=0,message='已取回'+version+'，沿用已有成片。')


def compare(session_root, series, version):
    item=get(session_root,series,version)
    return {'label':version,'before':item['source'],'after':item['output'],
            'original_source':item['original_source'],'render_calls':0}


def hints(session_root, enabled=None):
    if enabled is not None and type(enabled) is not bool:raise ValueError('enabled must be boolean')
    with _index(session_root,True) as db:
        if enabled is not None:db.execute('INSERT OR REPLACE INTO session VALUES(?,?)',('hints',json.dumps(enabled)))
        row=db.execute('SELECT value FROM session WHERE key=?',('hints',)).fetchone()
    return {'enabled':json.loads(row[0]) if row else True,'scope':'conversation_only'}


def delivered(path, session_root, presented):
    if presented is not True:raise ValueError('Delivery requires an actually observed presentation')
    item=register(path,session_root);state=_verify(item)
    with _index(session_root,True) as db:
        setting=db.execute('SELECT value FROM session WHERE key=?',('hints',)).fetchone()
        enabled=json.loads(setting[0]) if setting else True
        changed=db.execute('UPDATE versions SET delivered=1 WHERE job=? AND delivered=0',(item['job'],)).rowcount
    return {'version':item,'hint':experience.hint(state,new_delivery=bool(changed),enabled=enabled),
            'experience':experience.describe(state,__import__('delivery_automation').plan(path)['action'])}


def _requirements(state):
    return [{'target':key,'level':value['level'],'requirement':value['requirement']}
            for key,value in (state.get('protection_plan') or {}).get('targets',{}).items()]


def validate_protections(state, requirements):
    inherited=(state.get('revision') or {}).get('requirements',[])+(state.get('recovery_contract') or {}).get('requirements',[])
    for locked in inherited:
        supplied=next((x for x in requirements if x.get('target')==locked['target']),None)
        if supplied is None or supplied.get('requirement')!=locked['requirement'] or (
                supplied.get('level')!=locked['level'] and supplied.get('level')!='exact_content'):
            raise ValueError('Inherited protection cannot be removed or weakened: '+locked['target'])


def verify_revision(state):
    revision=state.get('revision')
    if not revision:return
    for identity in (revision['original_source'],revision['parent_output']):
        if w._file(identity['path'])!=identity:raise ValueError('Revision provenance changed')
    parent=w._load(revision['parent_job'])
    if parent['status']!='accepted' or parent['output']!=revision['parent_output']:
        raise ValueError('Revision parent must remain an accepted formal output')
    if state['source']!=revision['parent_output']:raise ValueError('Revision must edit the selected version')
    if digest(_requirements(parent))!=revision['parent_protection_sha256']:
        raise ValueError('Parent protection contract changed')
    if state.get('protection_plan') is not None:validate_protections(state,_requirements(state))
    if state.get('execution_adapter'):validate_regions(state,state['execution_adapter']['protected_regions'])


def revise(session_root, series, version, path, request, local=False, **prepare_options):
    import photo_edit
    item=get(session_root,series,version);parent=_verify(item)
    request=w._text(request,'revision request')
    if type(local) is not bool:raise ValueError('local must be boolean')
    requirements=_requirements(parent);targets={x['target'] for x in requirements}
    if local or request=='保持构图只调色':
        for target,requirement in [('composition','保留选定版本构图和画幅'),('people','保留人物身份与非目标人物区域'),
                                   ('approved_direction','继承已认可的整体审美方向，只修改指定目标')]:
            if target not in targets:requirements.append({'target':target,'level':'semantic_identity','requirement':requirement})
    revision={'series':series,'session_root':str(location(session_root)),'parent_job':item['job'],
              'parent_version':version,'parent_output':item['output'],'original_source':item['original_source'],
              'root_started_unix_ns':(parent.get('revision') or {}).get('root_started_unix_ns',parent['milestones']['job_started']),
              'parent_protection_sha256':digest(_requirements(parent)),'requirements':requirements,
              'inherited_direction':parent.get('professional_direction'),
              'protected_regions':(parent.get('execution_adapter') or {}).get('protected_regions',{}),'request':request,'local':local}
    target=Path(path).resolve()
    if os.path.lexists(target):raise FileExistsError('Revision destination exists')
    target.parent.mkdir(parents=True,exist_ok=True)
    forbidden={'project_root','source_path','path','task_instructions'} & set(prepare_options)
    if forbidden:raise ValueError('Revision provenance fields cannot be overridden')
    # Publish only after provenance and preparation both succeed; no old task writes.
    with tempfile.TemporaryDirectory(dir=target.parent) as folder:
        temporary=Path(folder)/'revision.json'
        photo_edit.prepare(parent['context']['project_root'],item['output']['path'],temporary,
                           task_instructions=[request],**prepare_options)
        child=w._load(temporary);child['revision']=revision;w._save(temporary,child)
        verify_revision(child);os.link(temporary,target)
    regions=(parent.get('execution_adapter') or {}).get('protected_regions',{}).copy()
    for req in requirements:regions.setdefault(req['target'],[req['requirement']])
    return {'path':str(target),'parent_version':version,'input':item['output'],'original_source':item['original_source'],
            'protections':{'requirements':requirements,'reason':'继承选定版本保护契约及本次修改范围'},
            'protected_regions':regions,'inherited_direction':revision['inherited_direction'],
            'shortcut':experience.shortcut(request),'next':'View applicable references and submit the new revision once'}


def validate_regions(state, regions):
    for inherited in (state.get('revision') or {},state.get('recovery_contract') or {}):
        for target,planned in inherited.get('protected_regions',{}).items():
            if not set(planned).issubset(regions.get(target,[])):
                raise ValueError('Inherited comparison regions cannot be removed: '+target)


def verify_recovery(state):
    retry=state.get('retry_of')
    if not retry:return
    old=w._load(retry['path'])
    if old['status']!='failed' or old.get('render_result') or old['source']!=retry['source'] or state['source']!=old['source']:
        raise ValueError('Recovery requires the same confirmed never-submitted failed task')
    if w._file(old['source']['path'])!=old['source']:raise ValueError('Recovery source changed')
    if state.get('protection_plan') is not None:validate_protections(state,_requirements(state))
    if state.get('execution_adapter'):validate_regions(state,state['execution_adapter']['protected_regions'])
