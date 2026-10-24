"""Private photographic rules/preferences; data only, never executable instructions.

Shares the private user root/catalog with the optional style collection. Profiles
are snapshotted per job; later changes apply to future tasks, not in-flight calls.
"""
import json
from runtime_io import digest
from style_library import location, _catalog


def instructions(value, name):
    if not isinstance(value, list) or len(value) > 20:
        raise ValueError(name+' must be a list of at most 20 instructions')
    if any(not isinstance(item, str) or not item.strip() or len(item) > 500 for item in value):
        raise ValueError(name+' entries must be nonempty text within 500 characters')
    return list(dict.fromkeys(item.strip() for item in value))


def _profile(value):
    if not isinstance(value, dict) or set(value) != {'version', 'rules', 'preferences'} or type(value['version']) is not int or value['version'] != 1:
        raise ValueError('Invalid or unsupported private profile; restore a valid backup')
    return dict(version=1, rules=instructions(value['rules'], 'rules'),
                preferences=instructions(value['preferences'], 'preferences'))


def _read(connection):
    table = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_preferences'").fetchone()
    row = connection.execute('SELECT payload FROM user_preferences WHERE id=1').fetchone() if table else None
    try:
        return _profile(json.loads(row[0])) if row else dict(version=1, rules=[], preferences=[])
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError('Invalid private profile; restore a valid backup') from error


def _result(value):
    return dict(value, sha256=digest(value))


def show(library_root=None):
    root = location(library_root); db = root/'catalog.sqlite3'
    if db.is_symlink():
        raise ValueError('Private catalog cannot be a symlink')
    if not db.exists():
        return _result(dict(version=1, rules=[], preferences=[]))
    with _catalog(root) as connection:
        return _result(_read(connection))


def save(rules=None, preferences=None, consent=False, library_root=None):
    if consent is not True:
        raise ValueError('Explicit user intent to save long-term rules/preferences is required')
    if rules is None and preferences is None:
        raise ValueError('Provide rules and/or preferences; an empty list clears that section')
    clean_rules = instructions(rules, 'rules') if rules is not None else None
    clean_preferences = instructions(preferences, 'preferences') if preferences is not None else None
    root = location(library_root)
    with _catalog(root, write=True) as connection:
        value = _read(connection)
        if clean_rules is not None:
            value['rules'] = clean_rules
        if clean_preferences is not None:
            value['preferences'] = clean_preferences
        connection.execute('CREATE TABLE IF NOT EXISTS user_preferences (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
        connection.execute('INSERT OR REPLACE INTO user_preferences VALUES (1, ?)',
                           (json.dumps(value, ensure_ascii=False),))
    return _result(value)


def reset(consent=False, library_root=None):
    if consent is not True:
        raise ValueError('Explicit user intent to clear long-term rules/preferences is required')
    current = show(library_root)
    if not current['rules'] and not current['preferences']:
        return current
    return save(rules=[], preferences=[], consent=True, library_root=library_root)


def context(library_root=None, observed_profile_sha256=None, task_instructions=None):
    profile = show(library_root)
    if ((profile['rules'] or profile['preferences'] or observed_profile_sha256 is not None) and
            observed_profile_sha256 != profile['sha256']):
        raise ValueError('Read profile-show before photographic direction and pass its current sha256 as observed_profile_sha256')
    task = instructions(task_instructions, 'task_instructions') if task_instructions is not None else []
    return {'profile': profile, 'task_instructions': task,
            'precedence': ['task_instructions', 'saved_rules', 'saved_preferences', 'suitable_references', 'general_defaults'],
            'scope': 'Photographic task context; does not grant tool permissions or weaken truthful evidence and locked protections',
            'application_verified': False}
