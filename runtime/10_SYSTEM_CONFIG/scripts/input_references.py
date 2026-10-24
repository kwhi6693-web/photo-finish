"""Bind actual local tool inputs; never infer reference roles from image appearance."""
from pathlib import Path

ROLES={'edit_target','style_reference','composition_reference','identity_reference','supporting_reference'}

def capture(arguments,identify,source_path,prior_path=None,roles=None):
    paths=arguments.get('referenced_image_paths') or []
    if not isinstance(paths,list) or any(not isinstance(p,str) or not p.strip() for p in paths):
        raise ValueError('referenced_image_paths must contain local path strings')
    attached=[(str(Path(p).absolute()),str(Path(p).resolve(strict=True))) for p in paths]
    resolved=[target for _,target in attached]
    explicit={}
    if roles is not None:
        if not isinstance(roles,list):raise ValueError('input_references must be a list of path/role objects')
        for item in roles:
            if not isinstance(item,dict) or set(item)!={'path','role'} or item['role'] not in ROLES:
                raise ValueError('Each input reference needs one supported path/role pair')
            path=str(Path(item['path']).resolve(strict=True))
            if path not in resolved:raise ValueError('Explicit reference path is not an actual referenced_image_paths input')
            if path in explicit and explicit[path]!=item['role']:raise ValueError('Conflicting input reference roles')
            explicit[path]=item['role']
    targets={str(Path(source_path).resolve())}
    if prior_path:targets.add(str(Path(prior_path).resolve()))
    files=[];seen=set()
    for argument_path,path in attached:
        if argument_path in seen:continue
        seen.add(argument_path)
        role=explicit.get(path,'edit_target' if path in targets else 'supporting_reference')
        files.append(dict(identify(argument_path),argument_path=argument_path,role=role))
    return {'version':1,'files':files,'scope':'Actual local referenced_image_paths; conversation/remote image bytes are not claimed locally verified',
            'conversation_image_count':arguments.get('num_last_images_to_include')}

def verify(manifest,identify):
    if manifest is None:return
    if not isinstance(manifest,dict) or manifest.get('version')!=1 or not isinstance(manifest.get('files'),list):
        raise ValueError('Invalid input reference manifest')
    for item in manifest['files']:
        if not isinstance(item,dict) or item.get('role') not in ROLES or not isinstance(item.get('path'),str):
            raise ValueError('Invalid input reference identity')
        current=identify(item.get('argument_path',item['path']))
        if current!={key:item.get(key) for key in ('path','sha256')}:
            raise ValueError('Input reference changed; investigate the existing submission without repeating the tool call')
