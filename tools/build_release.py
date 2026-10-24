"""Deterministic, source-only skill archive; no private workspace history."""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile
from check_publication import scan,inspect_archive
ROOT=Path(__file__).resolve().parents[1]
TOP={'SKILL.md','LICENSE','THIRD_PARTY_NOTICES.md','requirements.txt','requirements-analysis.txt'}
TOOLS={'tools/doctor.py','tools/sync_public.py','tools/check_publication.py'}
DIRS={'agents','assets','references','scripts','runtime'}
def build(destination,root=ROOT):
    root=Path(root);destination=Path(destination).resolve()
    if destination.suffix!='.zip':raise ValueError('Release destination must be a ZIP')
    if destination.is_relative_to(root) and any(v in DIRS for v in destination.relative_to(root).parts[:-1]):
        raise ValueError('Archive must not be inside the skill runtime')
    result=scan(root)
    if result['status']!='passed':raise ValueError('Publication scan failed; run check_publication.py for locations')
    files=[]
    for p in sorted(root.rglob('*'), key=lambda value:value.relative_to(root).as_posix()):
        rel=p.relative_to(root)
        if '__pycache__' in rel.parts or p.suffix in {'.pyc','.pyo'}:continue
        if p.is_file() and (rel.as_posix() in TOP|TOOLS or rel.parts[0] in DIRS):
            if p.is_symlink():raise ValueError('Symlink not allowed')
            files.append((rel.as_posix(),p.read_bytes()))
    manifest={'name':'photo-finish','version':'1.0.2','files':{n:hashlib.sha256(b).hexdigest() for n,b in files}}
    files.append(('release-manifest.json',(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()))
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix('.tmp')
    try:
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name,data in files:
                info=zipfile.ZipInfo('photo-finish/'+name,date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                info.create_system=3;info.external_attr=0o100644<<16;z.writestr(info,data)
        data=temporary.read_bytes()
        if inspect_archive(data):raise ValueError('Archive security check failed')
        temporary.replace(destination)
    finally:temporary.unlink(missing_ok=True)
    checksum=hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(destination.suffix+'.sha256').write_text(checksum+'  '+destination.name+'\n', encoding='utf-8', newline='\n')
    return {'status':'passed','archive':destination.name,'files':len(files),'sha256':checksum,'bytes':destination.stat().st_size}
if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT / 'dist/photo-finish.zip')
    a = p.parse_args()
    print(json.dumps(build(a.output), indent=2))
