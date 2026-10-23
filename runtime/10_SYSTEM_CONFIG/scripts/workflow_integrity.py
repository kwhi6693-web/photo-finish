"""System-update validation only: current entry points, anchors and JSON pointers."""
from pathlib import Path
import hashlib, json, re
import session_brief

def validate(root, skill=None):
    root=Path(root); cfg=root/'10_SYSTEM_CONFIG'
    policy=json.loads((cfg/'runtime_policy.json').read_text())
    defaults=json.loads((cfg/'BEAUTIFICATION_POLICY.json').read_text())
    fast=json.loads((cfg/'FAST_EDIT_WORKFLOW.json').read_text())
    if policy['beautification_defaults'] != defaults or policy['fast_edit_workflow'] != fast:
        raise ValueError('Current policy/default/workflow drift')
    session_brief.validate_policy_copies(policy)
    development=cfg/'DEVELOPMENT_WORKFLOW.json'
    if not development.is_file() or json.loads(development.read_text())!=policy['development_workflow']:
        raise ValueError('DEVELOPMENT_WORKFLOW standalone drift')
    brief=session_brief.load(cfg/'SESSION_BRIEF.json',root)
    if brief['runtime_policy'] != policy:
        raise ValueError('Brief runtime drift')
    revision=fast['revision']
    master=root/'我的照片美化偏好与修图标准.md'
    if '现行总规范｜'+revision not in master.read_text():
        raise ValueError('Master revision differs from canonical workflow revision')
    docs=[root/'我的照片美化偏好与修图标准.md']+[cfg/n for n in
          ('QUICK_START.md','NEW_PHOTO_WORKFLOW.md','FAST_EDIT_WORKFLOW.md','DEVELOPMENT_WORKFLOW.md')]
    if skill:
        skill=Path(skill); docs += [skill/'SKILL.md']+list((skill/'references').glob('*.md'))
        entry=policy.get('entrypoint_skill')
        if entry:
            if entry['revision']!=revision:
                raise ValueError('Skill entrypoint revision drift')
            for name,expected in entry['files'].items():
                target=skill/name
                if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
                    raise ValueError('Skill entrypoint hash drift: '+name)
            if '当前编排'+revision not in (skill/'SKILL.md').read_text():
                raise ValueError('Skill revision differs from current workflow')
    count=0
    for doc in docs:
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if '://' in link or link.startswith(('mailto:','sandbox:')): continue
            name,_,anchor=link.partition('#'); target=(doc.parent/name).resolve() if name else doc
            if not target.is_file(): raise ValueError(f'Missing link: {doc.name}: {link}')
            if anchor:
                headings=re.findall(r'^#+\s+(.+)$',target.read_text(),re.M)
                slugs=[re.sub(r'[^\w\-\s]','',x.strip()).lower().replace(' ','-') for x in headings]
                if anchor not in slugs: raise ValueError(f'Missing anchor: {doc.name}: {link}')
            count+=1
    pointers=0
    for match in re.finditer(r'([\w./-]+\.json)#(/[\w~/-]+)',json.dumps(policy,ensure_ascii=False)):
        name,pointer=match.groups(); target=root/name
        if not target.is_file(): target=cfg/name
        if not target.is_file(): raise ValueError('Missing pointer file: '+name)
        value=json.loads(target.read_text())
        try:
            for key in pointer[1:].split('/'):
                key=key.replace('~1','/').replace('~0','~')
                value=value[int(key)] if isinstance(value,list) else value[key]
        except (KeyError,IndexError,TypeError,ValueError) as e:
            raise ValueError('Invalid policy pointer: '+name+'#'+pointer) from e
        pointers+=1
    return {'status':'passed','local_links':count,'policy_pointers':pointers,
            'workflow_revision':policy['fast_edit_workflow']['revision']}
