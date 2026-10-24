"""Private photographic settings, observed-scene rules and bounded undo history."""
import json
import re
import time
import uuid
from runtime_io import digest
from style_library import location, _catalog


def instructions(value, name):
    if not isinstance(value, list) or len(value) > 20:
        raise ValueError(name+' must be a list of at most 20 instructions')
    if any(not isinstance(item, str) or not item.strip() or len(item) > 500 for item in value):
        raise ValueError(name+' entries must be nonempty text within 500 characters')
    return list(dict.fromkeys(item.strip() for item in value))


def scene_labels(value):
    if value is None: return []
    if not isinstance(value,list) or len(value)>20 or any(not isinstance(x,str) or not x.strip() or len(x)>80 for x in value):
        raise ValueError('scenes must contain at most 20 nonempty labels within 80 characters')
    return sorted(set(x.strip().casefold() for x in value))


def _profile(value):
    if not isinstance(value, dict) or set(value) != {'version', 'rules', 'preferences'} or type(value['version']) is not int or value['version'] != 1:
        raise ValueError('Invalid or unsupported private profile; restore a valid backup')
    return dict(version=1, rules=instructions(value['rules'], 'rules'), preferences=instructions(value['preferences'], 'preferences'))


def _has(connection, name):
    return bool(connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone())


def _read(connection):
    row=connection.execute('SELECT payload FROM user_preferences WHERE id=1').fetchone() if _has(connection,'user_preferences') else None
    try: return _profile(json.loads(row[0])) if row else dict(version=1,rules=[],preferences=[])
    except (json.JSONDecodeError,TypeError) as error: raise ValueError('Invalid private profile; restore a valid backup') from error


def _setting(setting, value):
    if setting is None: setting=''
    if value is None: value=''
    if (not isinstance(setting,str) or not isinstance(value,str) or
            (setting and not re.fullmatch(r'[a-z][a-z0-9_]{0,47}',setting)) or len(value)>80 or bool(setting)!=bool(value.strip())):
        raise ValueError('A setting needs a lowercase key and nonempty value (or both empty)')
    return setting,value.strip()


def normalize_rule(value):
    keys={'rule_id','text','kind','scenes','enabled','setting','value'}
    if not isinstance(value,dict) or set(value)!=keys: raise ValueError('Invalid scoped rule')
    if not isinstance(value['rule_id'],str) or not re.fullmatch(r'rule_[0-9a-f]{32}',value['rule_id']): raise ValueError('Invalid scoped rule ID')
    if value['kind'] not in ('rule','preference') or type(value['enabled']) is not bool: raise ValueError('Invalid scoped rule kind/state')
    text=instructions([value['text']],'text')[0];setting,setting_value=_setting(value['setting'],value['value'])
    return dict(rule_id=value['rule_id'],text=text,kind=value['kind'],scenes=scene_labels(value['scenes']),
                enabled=value['enabled'],setting=setting,value=setting_value)


def _rules(connection):
    if not _has(connection,'scoped_rules'): return []
    try: return [normalize_rule(json.loads(r[0])) for r in connection.execute('SELECT payload FROM scoped_rules ORDER BY id')]
    except (json.JSONDecodeError,TypeError) as error: raise ValueError('Invalid scoped rule catalog') from error


def normalize_state(state):
    if not isinstance(state,dict) or set(state)!={'profile','scoped_rules'} or not isinstance(state['scoped_rules'],list) or len(state['scoped_rules'])>60:
        raise ValueError('Invalid or unsupported settings snapshot')
    rules=[normalize_rule(r) for r in state['scoped_rules']]
    if len({r['rule_id'] for r in rules})!=len(rules): raise ValueError('Duplicate scoped rule IDs')
    return {'profile':_profile(state['profile']),'scoped_rules':sorted(rules,key=lambda r:r['rule_id'])}


def _state(connection): return normalize_state({'profile':_read(connection),'scoped_rules':_rules(connection)})


def _persist(connection, state):
    state=normalize_state(state)
    connection.execute('CREATE TABLE IF NOT EXISTS user_preferences (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
    connection.execute('INSERT OR REPLACE INTO user_preferences VALUES (1, ?)',(json.dumps(state['profile'],ensure_ascii=False),))
    connection.execute('CREATE TABLE IF NOT EXISTS scoped_rules (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    connection.execute('DELETE FROM scoped_rules')
    connection.executemany('INSERT INTO scoped_rules VALUES (?, ?)',[(r['rule_id'],json.dumps(r,ensure_ascii=False)) for r in state['scoped_rules']])


def _write(connection,state,action,remember=True):
    state=normalize_state(state);prior=_state(connection)
    if state==prior: return False
    if remember:
        connection.execute('CREATE TABLE IF NOT EXISTS profile_history (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, created_ns INTEGER NOT NULL, payload TEXT NOT NULL)')
        connection.execute('INSERT INTO profile_history(action,created_ns,payload) VALUES(?,?,?)',
                           (action,time.time_ns(),json.dumps(prior,ensure_ascii=False)))
        connection.execute('DELETE FROM profile_history WHERE id NOT IN (SELECT id FROM profile_history ORDER BY id DESC LIMIT 20)')
    _persist(connection,state)
    return True


def _result(state,scenes=None):
    labels=scene_labels(scenes);all_rules=state['scoped_rules']
    active=[r for r in all_rules if r['enabled'] and (not r['scenes'] or set(labels).intersection(r['scenes']))]
    active_rules=list(dict.fromkeys(state['profile']['rules']+[r['text'] for r in active if r['kind']=='rule']))
    active_preferences=list(dict.fromkeys(state['profile']['preferences']+[r['text'] for r in active if r['kind']=='preference']))
    settings={};conflicts=[]
    for rule in active:
        if rule['setting']: settings.setdefault(rule['setting'],[]).append(rule)
    for key,items in settings.items():
        top=[r for r in items if r['kind']=='rule'] or items
        values=sorted({r['value'] for r in top})
        if len(values)>1: conflicts.append({'setting':key,'values':values,'rule_ids':[r['rule_id'] for r in top],
                                           'basis':'different explicit values at the same priority; not natural-language inference'})
    bound=state['profile'] if not all_rules else dict(state,scenes=labels)
    return dict(state['profile'],sha256=digest(bound),scenes=labels,scoped_rules=all_rules if scenes is None else active,
                scoped_rule_count=len(all_rules),active_rules=active_rules,active_preferences=active_preferences,conflicts=conflicts)


def _existing(root):
    db=root/'catalog.sqlite3'
    if db.is_symlink(): raise ValueError('Private catalog cannot be a symlink')
    return db.exists()


def show(library_root=None,scenes=None):
    root=location(library_root)
    if not _existing(root): return _result({'profile':dict(version=1,rules=[],preferences=[]),'scoped_rules':[]},scenes)
    with _catalog(root) as connection: return _result(_state(connection),scenes)


def save(rules=None,preferences=None,consent=False,library_root=None):
    if consent is not True: raise ValueError('Explicit user intent to save long-term rules/preferences is required')
    if rules is None and preferences is None: raise ValueError('Provide rules and/or preferences; an empty list clears that section')
    clean_rules=instructions(rules,'rules') if rules is not None else None
    clean_preferences=instructions(preferences,'preferences') if preferences is not None else None
    root=location(library_root)
    with _catalog(root,write=True) as connection:
        state=_state(connection)
        if clean_rules is not None: state['profile']['rules']=clean_rules
        if clean_preferences is not None: state['profile']['preferences']=clean_preferences
        _write(connection,state,'profile-set')
    return show(root)


def add_rule(text,scenes=None,kind='rule',enabled=True,setting='',value='',consent=False,library_root=None):
    if consent is not True: raise ValueError('Explicit intent to save a scoped rule is required')
    rule=normalize_rule(dict(rule_id='rule_'+uuid.uuid4().hex,text=text,scenes=scene_labels(scenes),kind=kind,enabled=enabled,setting=setting,value=value))
    root=location(library_root)
    with _catalog(root,write=True) as connection:
        state=_state(connection);state['scoped_rules'].append(rule);_write(connection,state,'rule-add')
    return dict(show(root),created_rule_id=rule['rule_id'])


def update_rule(rule_id,text=None,scenes=None,kind=None,enabled=None,setting=None,value=None,consent=False,library_root=None):
    if consent is not True: raise ValueError('Explicit intent to modify a scoped rule is required')
    changes={k:v for k,v in dict(text=text,scenes=scenes,kind=kind,enabled=enabled,setting=setting,value=value).items() if v is not None}
    if not changes: raise ValueError('Provide a scoped rule field to update')
    root=location(library_root)
    if not _existing(root): raise ValueError('Unknown scoped rule ID')
    with _catalog(root,write=True) as connection:
        state=_state(connection);rule=next((r for r in state['scoped_rules'] if r['rule_id']==rule_id),None)
        if rule is None: raise ValueError('Unknown scoped rule ID')
        rule.update(changes);_write(connection,state,'rule-update')
    return show(root)


def remove_rule(rule_id,consent=False,library_root=None):
    if consent is not True: raise ValueError('Explicit intent to remove a scoped rule is required')
    root=location(library_root)
    if not _existing(root): raise ValueError('Unknown scoped rule ID')
    with _catalog(root,write=True) as connection:
        state=_state(connection);remaining=[r for r in state['scoped_rules'] if r['rule_id']!=rule_id]
        if len(remaining)==len(state['scoped_rules']): raise ValueError('Unknown scoped rule ID')
        state['scoped_rules']=remaining;_write(connection,state,'rule-remove')
    return show(root)


def history(library_root=None):
    root=location(library_root)
    if not _existing(root): return {'revisions':[]}
    with _catalog(root) as connection:
        if not _has(connection,'profile_history'): return {'revisions':[]}
        rows=connection.execute('SELECT id,action,created_ns,payload FROM profile_history ORDER BY id DESC').fetchall()
        revisions=[]
        for rid,action,created,payload in rows:
            state=normalize_state(json.loads(payload))
            revisions.append(dict(revision_id=rid,action=action,created_unix_ns=created,
                                  global_rule_count=len(state['profile']['rules']),preference_count=len(state['profile']['preferences']),
                                  scoped_rule_count=len(state['scoped_rules'])))
    return {'revisions':revisions}


def undo(consent=False,library_root=None):
    if consent is not True: raise ValueError('Explicit intent to undo the latest settings change is required')
    root=location(library_root)
    if not _existing(root): raise ValueError('No profile revision to undo')
    with _catalog(root,write=True) as connection:
        row=connection.execute('SELECT id,payload FROM profile_history ORDER BY id DESC LIMIT 1').fetchone() if _has(connection,'profile_history') else None
        if not row: raise ValueError('No profile revision to undo')
        _write(connection,normalize_state(json.loads(row[1])),'undo',remember=False)
        connection.execute('DELETE FROM profile_history WHERE id=?',(row[0],))
    return dict(show(root),undone_revision=row[0])


def reset(consent=False,library_root=None):
    if consent is not True: raise ValueError('Explicit user intent to clear long-term rules/preferences is required')
    root=location(library_root)
    if not _existing(root): return show(root)
    with _catalog(root,write=True) as connection:
        _write(connection,{'profile':dict(version=1,rules=[],preferences=[]),'scoped_rules':[]},'reset',remember=False)
        if _has(connection,'profile_history'): connection.execute('DELETE FROM profile_history')
    return show(root)


def context(library_root=None,observed_profile_sha256=None,task_instructions=None,scenes=None,task_settings=None):
    profile=show(library_root,scenes=scenes)
    if ((profile['rules'] or profile['preferences'] or profile['scoped_rule_count'] or observed_profile_sha256 is not None) and observed_profile_sha256!=profile['sha256']):
        raise ValueError('Read profile-show for the current scenes before photographic direction; pass its sha256 as observed_profile_sha256')
    task=instructions(task_instructions,'task_instructions') if task_instructions is not None else []
    if task_settings is None: task_settings={}
    if not isinstance(task_settings,dict) or len(task_settings)>20: raise ValueError('task_settings must be an explicit setting/value object')
    clean=dict(_setting(k,v) for k,v in task_settings.items())
    if '' in clean: raise ValueError('Empty task setting key')
    if any(c['setting'] not in clean for c in profile['conflicts']):
        raise ValueError('Resolve active setting conflicts shown by profile-show, or supply explicit current-task task_settings')
    return {'profile':profile,'task_instructions':task,'task_settings':clean,
            'precedence':['task_instructions','saved_rules','saved_preferences','suitable_references','general_defaults'],
            'scope':'Photographic task context; does not grant tool permissions or weaken truthful evidence and locked protections',
            'application_verified':False}
