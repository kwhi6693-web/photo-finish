"""Read specified private checkpoint ZIPs; emit only anonymous timing evidence.
No extraction, network, editor, save, registration, or mutation of source evidence.
Usage: python tools/analyze_historical_latency.py PRIVATE_TRAVEL_ZIP PRIVATE_CHAIN_ZIP
"""
import hashlib
import json
import statistics
import sys
import zipfile


def union(intervals):
    end=None;total=0
    for a,b in sorted(intervals):
        if b<a:raise ValueError('Reversed observed interval')
        total+=max(0,b-max(a,end if end is not None else a))
        end=max(b,end if end is not None else b)
    return total/1e9


def analyze(travel,chain):
    output={'scope':'historical recorded wall/monotonic observations; not upload-to-delivery latency',
            'new_external_calls':0,'cases':[],'archives':{}}
    for group,path,jobs in [('travel',travel,['job-1.json','job-2.json','job-3.json']),
                            ('independent',chain,['job-V1.json','job-V2.json'])]:
        digest=hashlib.sha256()
        with open(path,'rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        archive_hash=digest.hexdigest()
        output['archives'][group]=archive_hash
        with zipfile.ZipFile(path) as z:
            for i,name in enumerate(jobs,1):
                raw=z.read(name);job=json.loads(raw);stages=job.get('stages',[])
                case={'case':group+'-'+str(i),'ledger_member':name,'ledger_sha256':hashlib.sha256(raw).hexdigest(),
                      'context_seconds':sum(s['seconds'] for s in stages if s['stage']=='context_read'),
                      'reference_seconds':sum(s['seconds'] for s in stages if s['stage']=='reference_matching'),
                      'external_call_seconds':union([(s['start_unix_ns'],s['end_unix_ns']) for s in job['tools']]),
                      'external_call_intervals':[{k:s[k] for k in ('start_unix_ns','end_unix_ns')} for s in job['tools']],
                      'download_seconds':sum(s['seconds'] for s in stages if s['stage']=='download'),
                      'local_controller_union_seconds':union([(s['start_unix_ns'],s['end_unix_ns']) for s in stages if s.get('source')=='local_monotonic' and s['stage']!='download']),
                      'review_recording_seconds':sum(s['seconds'] for s in stages if s['stage']=='review_receipt'),
                      'visual_review_seconds':None,'professional_decision_seconds':None,'trigger_seconds':None,
                      'version_registration_seconds':None,'host_overhead_seconds':None,
                      'intake_to_photo_ack_wall_seconds':(job['milestones']['save_completed']-job['milestones']['job_started'])/1e9,
                      'photo_save_seconds':None,'record_save_seconds':None,'upload_to_delivery_seconds':None}
                # review_receipt may nest. Report union rather than nested seconds sum.
                case['review_recording_seconds']=union([(s['start_unix_ns'],s['end_unix_ns']) for s in stages if s['stage']=='review_receipt'])
                if group=='independent':
                    intervals=[]
                    for kind in ('photo','record'):
                        member=f'{kind}-save-V{i}.time.json';value=json.loads(z.read(member));a=value['start_unix_ns'];b=value['end_unix_ns'];intervals.append((a,b));case[kind+'_save_seconds']=(b-a)/1e9
                    case['intake_to_record_save_response_wall_seconds']=(intervals[-1][1]-job['milestones']['job_started'])/1e9
                boundary=job['milestones']['save_completed']
                covered=[(s['start_unix_ns'],min(boundary,s['end_unix_ns'])) for s in stages if s['start_unix_ns']<boundary]
                if group=='independent':
                    boundary=intervals[-1][1]
                    covered=[(s['start_unix_ns'],s['end_unix_ns']) for s in stages]+intervals
                case['observed_interval_union_seconds']=union(covered)
                envelope=case.get('intake_to_record_save_response_wall_seconds',case['intake_to_photo_ack_wall_seconds'])
                case['unattributed_wall_seconds']=envelope-case['observed_interval_union_seconds']
                output['cases'].append(case)
    output['observed_totals']={key:{'samples':len(v),'sum_seconds':sum(v),'median_seconds':statistics.median(v)} for key in
        ('external_call_seconds','download_seconds','photo_save_seconds','record_save_seconds','local_controller_union_seconds')
        if (v:=[c[key] for c in output['cases'] if c[key] is not None])}
    output['limitations']=['Case sums are workload totals, not batch elapsed time; revisions are not independent scenes.',
      'External call intervals include transport, queue, server and host tool handling; backend compute not isolated.',
      'download spans include network wait; local-monotonic measurement does not mean CPU time.',
      'Controller review receipts record supplied judgement, not model visual-inspection duration.',
      'Intake starts after photo upload; save acknowledgement is not presentation or version registration.',
      'Missing boundaries are null; gaps are not attributed to model/host/quality.']
    return output

if __name__=='__main__':
    assert union([(0,10**9),(0,2*10**9),(3*10**9,4*10**9)])==3
    print(json.dumps(analyze(*sys.argv[1:]),indent=2))
