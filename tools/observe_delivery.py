"""Opt-in private caller timing sidecar. Never invokes or resumes workflow/tools.
No payloads, URLs, provider task IDs, prompts, receipts or automatic quality claims.
Use on the next naturally authorized task; not shipped in the stable skill ZIP.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager

STAGES=('task_received','context_read','reference_view','professional_decision',
        'edit_call','poll_call','caller_wait','formal_download','visual_review',
        'photo_save_call','final_record','record_save_call','version_register',
        'delivery_observed')
KINDS=('local_controller','caller_activity','external_tool','caller_wait')
STATUS=('ok','failed','timeout','unknown')


def _private(path):
    p=Path(path).expanduser().absolute()
    if any(x.is_symlink() for x in (p,*p.parents)):
        raise ValueError('Trace cannot traverse symlinks')
    if any((x/'.git').exists() for x in p.parents):
        raise ValueError('Trace must be outside Git')
    return p


@contextmanager
def _locked(path):
    p=_private(path);p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=p.with_name(p.name+'.lock')
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        yield p
    finally:
        os.close(fd);lock.unlink()


def _write(p,state):
    name=None
    try:
        with tempfile.NamedTemporaryFile('w',dir=p.parent,delete=False,encoding='utf-8') as f:
            name=f.name;json.dump(state,f,allow_nan=False);f.flush();os.fsync(f.fileno())
        os.replace(name,p)
    finally:
        if name and os.path.exists(name):os.unlink(name)


def create(path):
    with _locked(path) as p:
        if p.exists():raise FileExistsError('Trace already exists')
        state={'schema':1,'anonymous_task':uuid.uuid4().hex,'events':[]}
        _write(p,state)
    return state['anonymous_task']


def _clock():
    return {'wall_ns':time.time_ns(),'mono_ns':time.monotonic_ns()}


def mark(path,stage,kind,call=None,status='unknown'):
    if stage not in STAGES or kind not in KINDS or status not in STATUS:
        raise ValueError('Only fixed stage/kind/status labels allowed')
    with _locked(path) as p:
        state=json.loads(p.read_text());events=state['events']
        if call is None:
            call=uuid.uuid4().hex;event=dict(call=call,stage=stage,kind=kind,start=_clock(),end=None,status='unknown')
            events.append(event)
        else:
            event=next((e for e in events if e['call']==call),None)
            if event is None or event['stage']!=stage or event['kind']!=kind:
                raise ValueError('End must identify original anonymous span')
            if event['end'] is not None:raise ValueError('Span already ended; do not invent a retry')
            event.update(end=_clock(),status=status)
        _write(p,state)
    return call


def summary(path):
    state=json.loads(_private(path).read_text());events=state['events'];totals={};intervals=[];warnings=[]
    for e in events:
        if e['end'] is None:continue
        a=e['start']['mono_ns'];b=e['end']['mono_ns']
        if b<a:
            warnings.append('monotonic reversal: do not combine sessions/clocks');continue
        if e['end']['wall_ns']<e['start']['wall_ns']:warnings.append('wall clock reversed')
        if abs((e['end']['wall_ns']-e['start']['wall_ns'])-(b-a))>10**9:
            warnings.append('wall/monotonic disagreement; clock domain uncertain')
        totals[e['stage']]=totals.get(e['stage'],0)+(b-a)/1e9
        if e['stage'] not in ('task_received','delivery_observed'):intervals.append((a,b))
    total=0;last=None
    for a,b in sorted(intervals):
        total+=max(0,b-max(a,last if last is not None else a));last=max(b,last if last is not None else b)
    starts=[e['start']['mono_ns'] for e in events if e['stage']=='task_received']
    ends=[e['end']['mono_ns'] for e in events if e['stage']=='delivery_observed' and e['end']]
    envelope=(max(ends)-min(starts)) if starts and ends and max(ends)>=min(starts) else None
    clipped=[]
    if envelope is not None:
        lo=min(starts);hi=max(ends)
        clipped=[(max(a,lo),min(b,hi)) for a,b in intervals if b>=lo and a<=hi]
    covered=0;last=None
    for a,b in sorted(clipped):
        covered+=max(0,b-max(a,last if last is not None else a));last=max(b,last if last is not None else b)
    return dict(anonymous_task=state['anonymous_task'],stage_seconds=totals,
        open_spans=sum(e['end'] is None for e in events),
        missing_stages=[s for s in STAGES if s not in totals],
        recorded_interval_union_seconds=total/1e9,
        caller_received_to_observed_delivery_seconds=envelope/1e9 if envelope is not None else None,
        coverage_fraction=covered/envelope if envelope and not warnings else None,
        coverage_basis='union of completed caller spans, not independently certified attribution',
        model_compute_seconds=None,pure_host_seconds=None,pure_service_compute_seconds=None,
        warnings=warnings,quality_or_save_certification=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['create','start','end','summary']);p.add_argument('path');p.add_argument('--stage',choices=STAGES);p.add_argument('--kind',choices=KINDS);p.add_argument('--call');p.add_argument('--status',choices=STATUS,default='unknown');a=p.parse_args()
    if a.action=='create':r=create(a.path)
    elif a.action=='summary':r=summary(a.path)
    elif a.action=='start':r=mark(a.path,a.stage,a.kind)
    else:
        if not a.call:p.error('end requires --call')
        r=mark(a.path,a.stage,a.kind,a.call,a.status)
    print(json.dumps(r,allow_nan=False))
