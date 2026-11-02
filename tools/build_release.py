"""Deterministic, source-only skill archive; no private workspace history."""
from pathlib import Path
import argparse,hashlib,io,json,sys,zipfile
from check_publication import scan,inspect_archive
ROOT=Path(__file__).resolve().parents[1]
TOP={'SKILL.md','LICENSE','THIRD_PARTY_NOTICES.md','requirements.txt','requirements-analysis.txt'}
TOOLS={'tools/doctor.py','tools/sync_public.py','tools/check_publication.py'}
DIRS={'agents','assets','references','scripts','runtime'}
def build(destination,root=ROOT,*,candidate=False):
    root=Path(root).resolve()
    destination=Path(destination)
    destination=destination.parent.resolve()/destination.name
    checksum_path=destination.with_suffix(destination.suffix+'.sha256')
    if candidate and destination.is_relative_to(root):
        raise ValueError('Candidate archive must be outside the repository')
    if destination.suffix!='.zip':raise ValueError('Release destination must be a ZIP')
    if any(p.exists() or p.is_symlink() for p in (destination,checksum_path)):
        raise ValueError('Release outputs already exist; use a fresh destination')
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
    version=json.loads(dict(files)['runtime/10_SYSTEM_CONFIG/SESSION_BRIEF.json'])['runtime_version']
    if destination.is_relative_to(root/'dist'):
        relative=destination.relative_to(root/'dist')
        if len(relative.parts)!=2 or relative.parts[0]!='v'+version:
            raise ValueError('Repository release output must use dist/v'+version+'/; historical paths are read-only')
    manifest={'name':'photo-finish','version':version,'files':{n:hashlib.sha256(b).hexdigest() for n,b in files}}
    if candidate:
        manifest.update(version='0+candidate',distribution_channel='candidate')
    files.append(('release-manifest.json',(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()))
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in files:
            info=zipfile.ZipInfo('photo-finish/'+name,date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3;info.external_attr=0o100644<<16;z.writestr(info,data)
    data=buffer.getvalue()
    if inspect_archive(data):raise ValueError('Archive security check failed')
    checksum=hashlib.sha256(data).hexdigest()
    destination.parent.mkdir(parents=True,exist_ok=True)
    created=[]
    try:
        # Exclusive creation also protects a target that appears after preflight.
        with destination.open('xb') as archive_output:
            created.append(destination)
            with checksum_path.open('xb') as checksum_output:
                created.append(checksum_path)
                archive_output.write(data)
                checksum_output.write((checksum+'  '+destination.name+'\n').encode('utf-8'))
    except BaseException:
        for path in reversed(created):path.unlink(missing_ok=True)
        raise
    return {'status':'passed','archive':destination.name,'files':len(files),'sha256':checksum,'bytes':len(data)}
if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True, help='Fresh ZIP path; existing outputs are never replaced')
    p.add_argument('--candidate', action='store_true', help='Non-release build; output must be outside the repository')
    a = p.parse_args()
    print(json.dumps(build(a.output,candidate=a.candidate), indent=2))
