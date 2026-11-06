"""Public-tree and reachable-file-history leak gate; Git metadata is excluded.

Never print matched values. Commit and annotated-tag messages are not scanned."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, io, json, re, subprocess, sys, zipfile

ROOT=Path(__file__).resolve().parents[1]
# One audited historic 90,060-byte malformed PR47 candidate; Git OID, path and
# exact size are all required. No malformed current-tree ZIP can use this waiver.
KNOWN_MALFORMED_HISTORY_ZIPS={
    ('9a957a58986ad5599801b0b71fdf6eb160336769','dist/v2.0.0/photo-finish.zip',90060),
}
SKIP={'.git','.venv','__pycache__','.pytest_cache'}
MEDIA={'.jpg','.jpeg','.png','.webp','.gif','.heic','.tif','.tiff','.dng','.cr2','.nef','.psd','.pdf'}
FORBIDDEN_PARTS={'uploads','generated_images','records','outputs','runtime_cache','09_VERSION_HISTORY','01_STYLE_REFERENCES','02_EDIT_TARGETS','07_ANALYSIS_REPORTS','08_EDIT_OUTPUTS'}
PATTERNS={
 'private-library-id':r'\blibfile_[0-9a-f]{16,}\b|\bfile_00000000[0-9a-f]{16,}\b',
 'machine-path':r'(?:/work'+r'space/|/ro'+r'ot/|/Us'+r'ers/|/ho'+r'me/[A-Za-z0-9_-]+/|[A-Za-z]:\\(?:Users|workspace)\\)',
 'github-credential':r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',
 'api-credential':r'\bsk-[A-Za-z0-9_-]{24,}\b|\bAKIA[0-9A-Z]{16}\b|\bxox[baprs]-[A-Za-z0-9-]{20,}',
 'private-key':r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'credential-in-url':r'https?://[^\s/<>:@]+:[^\s/<>@]+@',
 'signed-url':r'https?://[^\s<>"\x27]+[?&](?:sig|token|access_token|X-Amz-Signature|X-Goog-Signature|se)=[^\s<>"\x27]+',
 'private-email':r'\b[A-Z0-9._%+-]+@(?!users\.noreply\.github\.com\b|example\.(?:com|org)\b)[A-Z0-9.-]+\.[A-Z]{2,}\b',
}
RULES={k:re.compile(v,re.I) for k,v in PATTERNS.items()}

def findings_for(name,data):
    """Return only rule/line; input values are deliberately omitted."""
    found=[];text=data.decode('utf-8','replace')
    for rule,regex in RULES.items():
        for match in regex.finditer(text):found.append({'rule':rule,'line':text.count('\n',0,match.start())+1})
    suffix=PurePosixPath(name).suffix.lower()
    if suffix=='.json':
        try:value=json.loads(text)
        except (ValueError,TypeError):value=None
        def private_scope(item):
            if isinstance(item,dict):
                return item.get('distribution_scope')=='private' or any(private_scope(v) for v in item.values())
            return isinstance(item,list) and any(private_scope(v) for v in item)
        if private_scope(value):found.append({'rule':'private-profile-policy','line':None})
    parts=PurePosixPath(name).parts
    if suffix in MEDIA|{'.sqlite', '.sqlite3', '.db'} or any(p in FORBIDDEN_PARTS|{'style-library'} for p in parts):found.append({'rule':'private-media-or-work-record','line':None})
    if any(p=='.env' or p.startswith('.env.') for p in parts) or suffix in {'.pem','.key','.p12','.pfx'}:
        found.append({'rule':'credential-file','line':None})
    return found

def safe_name(name):
    p=PurePosixPath(name)
    return bool(name) and '\\' not in name and not p.is_absolute() and '..' not in p.parts

def inspect_archive(data):
    findings=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        seen=set();total=0
        for info in z.infolist():
            name=info.filename;total+=info.file_size
            if not safe_name(name) or name in seen or (info.external_attr>>16)&0o170000==0o120000:
                findings.append({'file':'archive-entry','rule':'unsafe-archive-entry','line':None});continue
            seen.add(name)
            if total>32*1024*1024 or info.file_size>8*1024*1024:raise ValueError('Release archive exceeds bounded public source size')
            for f in findings_for(name,z.read(info)):findings.append(dict(file=name,**f))
    return findings

def _historical_zip_findings(oid,name,data):
    """Return (findings, waived). Unknown corrupt ZIPs still raise BadZipFile."""
    try:
        return inspect_archive(data),False
    except zipfile.BadZipFile as error:
        if (oid,name,len(data)) not in KNOWN_MALFORMED_HISTORY_ZIPS:
            raise zipfile.BadZipFile(
                'unknown invalid historical ZIP blob %s path %s size %d' %
                (oid,name,len(data))
            ) from error
        # Still search raw archive bytes for public-data leaks. Compressed
        # entries of this malformed historic artifact cannot be certified.
        return findings_for('known-legacy-archive.raw',data),True


def scan(root=ROOT,history=False):
    root=Path(root);found=[];count=0
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if any(v in SKIP for v in rel.parts):continue
        name=rel.as_posix()
        if p.is_symlink():found.append({'file':name,'rule':'symlink','line':None});continue
        if not p.is_file():continue
        count+=1
        if p.stat().st_size>8*1024*1024:
            found.append({'file':name,'rule':'oversize-public-file','line':None});continue
        data=p.read_bytes()
        if p.suffix=='.zip':found.extend(inspect_archive(data))
        else:
            for f in findings_for(name,data):found.append(dict(file=name,**f))
    blobs=0;legacy_zip_exceptions=[]
    if history:
        output=subprocess.run(['git','rev-list','--objects','--all'],cwd=root,check=True,capture_output=True,text=True, encoding='utf-8').stdout
        for line in output.splitlines():
            oid,_,name=line.partition(' ')
            kind=subprocess.run(['git','cat-file','-t',oid],cwd=root,check=True,capture_output=True,text=True, encoding='utf-8').stdout.strip()
            if kind!='blob':continue
            blobs+=1;data=subprocess.run(['git','cat-file','blob',oid],cwd=root,check=True,capture_output=True).stdout
            if name.endswith('.zip'):
                archive_findings,waived=_historical_zip_findings(oid,name,data)
                if waived:
                    # Git --find-object identifies commits adding/removing this exact blob.
                    changes=subprocess.run(
                        ['git','log','--all','--format=%H','--find-object='+oid,'--',name],
                        cwd=root,check=True,capture_output=True,text=True,encoding='utf-8'
                    ).stdout.splitlines()
                    legacy_zip_exceptions.append({
                        'blob_sha':oid,'path':name,'size_bytes':len(data),
                        'commits_changing_blob_occurrences':changes,
                        'limitation':'malformed ZIP compressed members cannot be fully audited',
                    })
            else:
                archive_findings=findings_for(name,data)
            for f in archive_findings:
                found.append(dict(f,file='git-blob:'+oid[:12]))
    return {'status':'passed' if not found else 'failed','files_scanned':count,'historical_blobs_scanned':blobs,'known_malformed_historical_zip_exceptions':legacy_zip_exceptions,'findings':found,
       'scope':'Known patterns, private media/work classes, paths and ZIP safety; no universal absence guarantee'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--history',action='store_true');args=parser.parse_args()
    result=scan(args.root,args.history);print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='passed' else 1
if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    sys.exit(main())
