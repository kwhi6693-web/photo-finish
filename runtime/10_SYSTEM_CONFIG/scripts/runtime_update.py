"""Apply a checked small runtime update, preserving style and rollback bytes."""
from pathlib import Path
import hashlib,json,os,shutil,tempfile,uuid
from runtime_io import atomic_json

def checksum(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe_path(root,relative):
    root=Path(root).resolve();relative=Path(relative)
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe update path')
    path=(root/relative).resolve()
    if not path.is_relative_to(root):raise ValueError('Unsafe update path')
    return path

def apply(package_root,project_root):
    package=Path(package_root);project=Path(project_root).resolve();manifest=json.loads((package/'PATCH_MANIFEST.json').read_text())
    protected=manifest['protected_base_hashes']
    for rel,expected in protected.items():
        path=safe_path(project,rel)
        if not path.is_file() or checksum(path)!=expected:raise ValueError('Base style or reference library differs; do not overwrite a newer user project')
    prepared=[]
    for item in manifest['files']:
        rel=item['path']
        if rel in protected:raise ValueError('Runtime update cannot replace protected style files')
        source=safe_path(package/'PERSONAL_COLOR_SYSTEM',rel);target=safe_path(project,rel)
        if checksum(source)!=item['sha256']:raise ValueError('Update file checksum mismatch: '+rel)
        if not target.is_file() or checksum(target)!=item['sha256']:prepared.append((rel,source,target))
    backup=project/'09_VERSION_HISTORY'/('applied_runtime_v1.5_'+uuid.uuid4().hex[:12]) if prepared else None
    for rel,source,target in prepared:
        if target.exists():
            old=backup/rel;old.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,old)
        target.parent.mkdir(parents=True,exist_ok=True);temporary=None
        try:
            with tempfile.NamedTemporaryFile('wb',dir=target.parent,delete=False) as f:temporary=Path(f.name);f.write(source.read_bytes())
            os.replace(temporary,target)
        finally:
            if temporary and temporary.exists():temporary.unlink()
    result={'runtime_version':manifest['runtime_version'],'applied_files':len(prepared),'backup_directory':str(backup) if backup else None,'protected_style_unchanged':True}
    if backup:atomic_json(backup/'APPLY_RECEIPT.json',result)
    return result
