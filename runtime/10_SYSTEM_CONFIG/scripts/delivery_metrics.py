"""Read-only observed quality statistics, separated from synthetic/replay evidence.

Snapshots carry one compact observation automatically. Aggregate only explicitly
provided jobs/records; do not scan photos or reinterpret old jobs as new tests.
"""
from pathlib import Path
import argparse,json,statistics,sys
import workflow_session as w

KINDS=('live','replay','synthetic','unclassified')

def observe(state,sidecar=None):
    evaluation=state.get('evaluation',{});kind=evaluation.get('kind','unclassified')
    if kind not in KINDS:kind='unclassified'
    receipts=state.get('external_call_receipts',[])
    submissions={x['submission_id'] for x in receipts}
    reviews=state.get('reviews',[]);accepted=state['status']=='accepted'
    history=state.get('render_history',[])
    protection_failed=any(r.get('status')=='failed' for target in (state.get('protection_plan') or {}).get('targets',{}).values() for r in target.get('reviews',[]))
    first_pass=(len(submissions)==1 and not history and not protection_failed and bool(reviews) and all(r.get('visual_passed') is True and w.review_color_ready(state,r) for r in reviews)) if accepted and submissions else None
    if state['status'] in ('failed','cancelled') and submissions and any(r.get('visual_passed') is False for r in reviews):first_pass=False
    events=state.get('stages',[])+(sidecar or {}).get('events',[])
    validation_errors=sum(x.get('status')=='error' and x.get('stage') in ('review_receipt','ledger_transaction','acceptance') for x in events)
    # Failed nested operations can overlap. Count outer intervals, never pretend
    # this is an image-quality failure or a cloud retry.
    spans=[(x['start_unix_ns'],x['end_unix_ns']) for x in events if x.get('status')=='error' and x.get('stage') in ('review_receipt','ledger_transaction','acceptance')]
    validation_errors=len(w._merged_intervals(spans))
    render_intervals=[(x['start_unix_ns'],x['end_unix_ns']) for x in receipts]
    render_seconds=sum(b-a for a,b in w._merged_intervals(render_intervals))/1e9 if receipts else None
    started=state['milestones']['job_started'];saved=state['milestones'].get('save_completed') if state.get('delivery_receipt') else None
    return {'schema':1,'kind':kind,'scenario':evaluation.get('scenario','unclassified'),
      'workflow_revision':state['workflow_revision'],'source_sha256':state['source']['sha256'],
      'job_started_unix_ns':started,'output_sha256':(state.get('output') or {}).get('sha256'),
      'quality_status':state['status'],'acceptance_scope':state.get('acceptance_scope'),
      'first_output_accepted':first_pass,'render_submissions_observed':len(submissions),
      'image_revision_count':len(history),'validation_failure_count':validation_errors,
      'render_call_seconds_union':render_seconds,
      'photo_save_elapsed_seconds':(saved-started)/1e9 if saved is not None else None,
      'persistence_confirmed':saved is not None and bool(state.get('delivery_receipt')),
      'note':'Caller-declared live/synthetic/replay scope; quality is recorded actual visual judgment, not an independent aesthetic score. Missing timing remains null.'}

def sample(path):
    value=json.loads(Path(path).read_text());state=value.get('ledger',value)
    if 'ledger' in value:
        return value.get('quality_observation') or observe(state,{'events':(value.get('timing') or {}).get('stage_events',[])})
    return observe(state,w._stage_sidecar(path,state))

def report(paths):
    by_task={};duplicates=0
    for path in paths:
        item=sample(path);key=(item['source_sha256'],item['job_started_unix_ns'],item['workflow_revision'])
        if key in by_task:
            duplicates+=1
            if by_task[key]!=item:raise ValueError('Conflicting snapshots of the same task; choose one explicit current observation')
        else:by_task[key]=item
    rows=list(by_task.values());groups={}
    for kind in KINDS:
        items=[x for x in rows if x['kind']==kind];judged=[x for x in items if x['first_output_accepted'] is not None]
        rendered=[x for x in items if x['render_submissions_observed']>0]
        durations=[x['render_call_seconds_union'] for x in items if x['render_call_seconds_union'] is not None]
        saves=[x['photo_save_elapsed_seconds'] for x in items if x['photo_save_elapsed_seconds'] is not None]
        groups[kind]={'tasks':len(items),'unique_sources':len({x['source_sha256'] for x in items}),
          'scenarios':sorted({x['scenario'] for x in items}),
          'quality_accepted':sum(x['quality_status']=='accepted' for x in items),
          'first_output_acceptance':{'numerator':sum(x['first_output_accepted'] is True for x in judged),'denominator':len(judged),
            'rate':sum(x['first_output_accepted'] is True for x in judged)/len(judged) if judged else None},
          'image_revision':{'tasks':sum(x['image_revision_count']>0 for x in rendered),'denominator':len(rendered),
            'rate':sum(x['image_revision_count']>0 for x in rendered)/len(rendered) if rendered else None},
          'validation_failure_count':sum(x['validation_failure_count'] for x in items),
          'render_call_median_seconds':statistics.median(durations) if durations else None,
          'confirmed_photo_save_samples':len(saves),'photo_save_median_seconds':statistics.median(saves) if saves else None}
    return {'schema':1,'groups':groups,'duplicate_records_omitted':duplicates,'samples':rows,
      'measurement_scope':{'render_call_median_seconds':'Median across tasks of each task\'s union of observed external-call intervals; not a median of individual calls or end-to-end delivery latency',
        'validation_failure_count':'Recorded review_receipt/ledger_transaction/acceptance failures only; unrecorded submit/save errors are not inferred',
        'artifact_status':'Historical recorded judgments and receipts; report does not re-inspect photographs or certify current file availability'},
      'limitations':['No inferred missing timing or platform save','No automatic declaration of stable quality from a small sample','Synthetic and replay counts excluded from live rates','Same-source repetitions are not independent scene coverage']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('sample','report'));args=parser.parse_args()
    try:
        value=json.load(sys.stdin);result=sample(value['path']) if args.action=='sample' else report(value['paths'])
        print(json.dumps(result,ensure_ascii=False,allow_nan=False));return 0
    except (OSError,ValueError,TypeError,KeyError) as error:print(json.dumps({'error':str(error),'type':type(error).__name__}),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
