"""Durable duplicate-submission guard; external renderer remains tool-operated.

Submission_pending is intentionally not auto-retried: the external call might
have succeeded even when its response was lost. Never stores expiring asset URLs.
"""
from pathlib import Path
import hashlib,json,os,tempfile
from runtime_io import atomic_json,digest

PROJECT_ROOT=Path(__file__).resolve().parents[2]

def reserve(directory,source_sha256,recipe,backend='adobe_native',*,project_root=None):
    if len(source_sha256)!=64 or any(c not in '0123456789abcdef' for c in source_sha256):
        raise ValueError('A real lowercase source SHA-256 is required')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    identity={'source_sha256':source_sha256,'recipe':recipe,'backend':backend}
    key=digest(identity);path=directory/(key+'.json')
    state=dict(identity,job_key=key,status='submission_pending',task_id=None,output_path=None,output_sha256=None)
    temp=None;created=False
    try:
        with tempfile.NamedTemporaryFile('w',dir=directory,encoding='utf-8',delete=False) as f:
            temp=f.name;json.dump(state,f,ensure_ascii=False)
        try:os.link(temp,path);created=True
        except FileExistsError:pass
    finally:
        if temp:os.unlink(temp)
    try:state=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError) as error:raise RuntimeError('Job state unreadable; resolve existing submission before retrying') from error
    if state.get('job_key')!=key:raise RuntimeError('Job identity mismatch; do not resubmit')
    verified=False;verified_path=None
    if state.get('status')=='complete' and state.get('output_path'):
        candidates=[];root=Path(project_root) if project_root is not None else PROJECT_ROOT
        relative=state.get('output_project_relative_path')
        if relative:
            candidate=(root/relative).resolve()
            if candidate.is_relative_to(root.resolve()):candidates.append(candidate)
        candidates.append(Path(state['output_path']))
        for out in candidates:
            try:verified=hashlib.sha256(out.read_bytes()).hexdigest()==state['output_sha256']
            except OSError:continue
            if verified:verified_path=str(out);break
    return {'path':str(path),'state':state,'needs_submission':created,'output_verified':verified,'verified_output_path':verified_path}

def update(path,*,status,task_id=None,output_path=None,project_root=None):
    path=Path(path);state=json.loads(path.read_text(encoding='utf-8'))
    if status not in {'working','complete','failed','outcome_unknown'}:raise ValueError('Unsupported task status')
    if state['status']=='complete':raise ValueError('Completed job is immutable; use a different recipe for a new render')
    if status=='working' and not task_id:raise ValueError('Working jobs require the actual upstream taskId')
    state['status']=status
    if task_id:state['task_id']=task_id
    if status=='complete':
        if not output_path:raise ValueError('Completed jobs require a real downloaded output')
        output=Path(output_path).resolve();state['output_path']=str(output)
        state['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
        root=Path(project_root).resolve() if project_root is not None else PROJECT_ROOT
        state['output_project_relative_path']=str(output.relative_to(root)) if output.is_relative_to(root) else None
    atomic_json(path,state)
    return state
