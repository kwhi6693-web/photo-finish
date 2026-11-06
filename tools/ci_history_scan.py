"""CI-only full-history publication scan with one immutable damaged-ZIP exception.

The packaged tools/check_publication.py remains unchanged and fail-closed. This
script duplicates only its Git traversal to make an exact public historical ZIP
exception while preserving every other history finding and current-tree check.
It is not a Skill payload or a release/installation operation.
"""
from pathlib import Path
import json
import subprocess
import sys
import zipfile
from check_publication import ROOT, scan, inspect_archive, findings_for

# Independently confirmed by GitHub Actions: this blob is not a readable ZIP.
# The exact public Git object ID + pathname + size are required together.
KNOWN_INCOMPLETE_HISTORICAL_ZIP=(
    '9a957a58986ad5599801b0b71fdf6eb160336769',
    'dist/v2.0.0/photo-finish.zip',
    90060,
)


def _git(root,*args,binary=False):
    value=subprocess.run(['git',*args],cwd=root,capture_output=True,
                         check=True,**({} if binary else {'text':True,'encoding':'utf-8'}))
    return value.stdout


def inspect_history_blob(oid,name,data):
    """Return (security findings, scoped audit exception). Unknown damage fails."""
    if not name.endswith('.zip'):
        return findings_for(name,data),None
    try:
        return inspect_archive(data),None
    except zipfile.BadZipFile:
        if (oid,name,len(data))!=KNOWN_INCOMPLETE_HISTORICAL_ZIP:
            return [{'rule':'invalid-unknown-historical-zip','line':None}],None
        # This legacy object cannot be fully unpacked. Preserve regex and
        # private-data screening over its raw bytes; report the limitation.
        return findings_for('known-incomplete-historical-zip.raw',data),{
            'blob_sha':oid,'path':name,'size_bytes':len(data),
            'limitation':'compressed members cannot be fully inspected',
        }


def audit(root=ROOT):
    root=Path(root)
    current=scan(root,history=False)
    found=list(current['findings'])
    waivers=[]
    blobs=0
    for line in _git(root,'rev-list','--objects','--all').splitlines():
        oid,_,name=line.partition(' ')
        if _git(root,'cat-file','-t',oid).strip()!='blob':
            continue
        blobs+=1
        data=_git(root,'cat-file','blob',oid,binary=True)
        issues,waiver=inspect_history_blob(oid,name,data)
        for issue in issues:
            found.append(dict(issue,file='git-blob:'+oid[:12]))
        if waiver is not None:
            # Git log --find-object finds commits that added/removed this blob.
            transitions=_git(root,'log','--all','--format=%H',
                             '--find-object='+oid,'--',name).splitlines()
            waiver['commits_changing_blob_occurrences']=transitions
            waivers.append(waiver)
    return {
        'status':'passed' if not found else 'failed',
        'files_scanned':current['files_scanned'],
        'historical_blobs_scanned':blobs,
        'known_incomplete_archive_exceptions':waivers,
        'findings':found,
        'scope':'original current-tree gate; all Git blobs; exact historical exception uses raw-byte screening only',
    }


def main():
    for stream in (sys.stdin,sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    result=audit()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='passed' else 1


if __name__=='__main__':
    sys.exit(main())
