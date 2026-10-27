"""Actual-tool bridge: register once, attach returned local bytes, then reconcile evidence.

No tool client, image upload, automatic visual approval, scheduler or post-commit hook.
Caller invokes begin before the real tool and finish immediately after it. Platform
presentation, scoped quality acceptance and confirmed persistence remain distinct.
"""
from pathlib import Path
import argparse, hashlib, json, os, sys, tempfile, time
import delivery_automation as a
import workflow_session as w
from input_references import capture as capture_inputs


def _edit_route(state, tool_name, arguments):
    """Reject known incompatible fidelity/local routes before reserving a call.

    A mask parameter is necessary, never proof of a correct/feathered mask or
    non-target preservation. The caller still inspects the actual source/mask
    and final pixels under the existing quality/protection contract.
    """
    tool_name = w._text(tool_name, 'tool_name')
    generator = tool_name.removeprefix('tools.') in ('image_gen.imagegen', 'image_gen__imagegen')
    plans = (state.get('fidelity_plan') or {}).values()
    targets = ((state.get('protection_plan') or {}).get('targets') or {}).values()
    if generator and (any(p.get('strategy') in ('native_preserved', 'local_excluded') for p in plans) or
                      any(p.get('level') == 'exact_content' for p in targets)):
        raise ValueError('Full-frame generation cannot satisfy source-preserving fidelity or exact_content. '
                         'Use an actually compatible editor or keep the source/accepted version.')
    if (state.get('revision') or {}).get('local') is not True:
        return
    names = {'image_apply_adjustments', 'adobe.image_apply_adjustments',
             'mcp__codex_apps__adobe_image_apply_adjustments',
             'tools.mcp__codex_apps__adobe_image_apply_adjustments'}
    if tool_name not in names or not isinstance(arguments.get('maskURI'), str) or not arguments['maskURI'].strip():
        raise ValueError('Local-only revision requires a verified region-mask editor '
                         'and its actual top-level maskURI. Keep the accepted version.')


def _transaction(path, mutate):
    path=Path(path).resolve(strict=True);original=path.read_bytes();temporary=None
    try:
        with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False) as f:
            temporary=Path(f.name);f.write(original)
        result=mutate(temporary)
        if path.read_bytes()!=original:raise ValueError('Concurrent task change; do not repeat an external call')
        os.replace(temporary,path);temporary=None
        return result
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def begin(path,tool_name,arguments,display_mode='manual',protected_regions=None,input_references=None):
    """Persist exact source-bound arguments; never calls or retries an external service."""
    if not isinstance(arguments,dict):raise ValueError('Actual tool arguments must be an object')
    if display_mode not in ('manual','platform_auto'):raise ValueError('Unknown display mode')
    protected_regions=protected_regions or {}
    if not isinstance(protected_regions,dict):raise ValueError('Protected review regions must be an object')
    state=a._fresh(path,editable=True)
    _edit_route(state,tool_name,arguments)
    if not state.get('professional_direction'):raise ValueError('Set photographic direction/output use before tool submission')
    targets=set((state.get('protection_plan') or {}).get('targets',{}))
    if set(protected_regions)!=targets:raise ValueError('Each protected target requires a planned comparison scope')
    for regions in protected_regions.values():
        if not isinstance(regions,list) or not regions or any(not isinstance(x,str) or not x.strip() for x in regions):
            raise ValueError('Describe visible regions; no automatic per-stroke certification')
    from task_history import validate_regions
    validate_regions(state,protected_regions)
    encoded=json.dumps(arguments,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()
    inputs=capture_inputs(arguments,w._file,state['source']['path'],roles=input_references)
    if state.get('revision') and inputs['files'] and not any(
            x['path']==state['source']['path'] and x['sha256']==state['source']['sha256'] and x['role']=='edit_target' for x in inputs['files']):
        raise ValueError('Revision local inputs must include the selected version as edit_target')
    def apply(p):
        token=a.begin_render(p,tool_name,state['source']['sha256'],recipe={'actual_arguments':arguments,'arguments_sha256':hashlib.sha256(encoded).hexdigest(),'input_references':inputs})
        value=w._load(p);value['execution_adapter']={'version':1,'display_mode':display_mode,
            'protected_regions':protected_regions,'submission_id':token['submission_id']}
        w._save(p,value);return token
    return _transaction(path,apply)


def finish(path,submission_id,status,start_unix_ns,end_unix_ns,output_path=None,output_url=None,task_id=None,request_id=None,presented=False):
    """Record observed call boundaries from the caller, never time spent preparing arguments."""
    start=w._timestamp(start_unix_ns);end=w._timestamp(end_unix_ns)
    if end<start:raise ValueError('Call endpoint precedes start')
    w._boolean(presented,'presented')
    state=a._fresh(path);adapter=state.get('execution_adapter') or {};render=state.get('render_result') or {}
    if adapter.get('submission_id')!=submission_id:raise ValueError('Finish must match the registered actual invocation')
    if start<state['milestones']['job_started']:raise ValueError('Call precedes this task')
    if status not in ('ready','working','unknown','error'):raise ValueError('Unknown tool result state')
    if presented and (status!='ready' or adapter.get('display_mode')!='platform_auto' or not output_path):
        raise ValueError('Observed platform presentation requires its returned formal local file')
    payload={'submission_id':submission_id,'status':status,'start_unix_ns':start,'end_unix_ns':end,
             'output_path':str(Path(output_path).resolve()) if output_path else None,'output_url':output_url,
             'task_id':task_id,'request_id':request_id,'presented':presented}
    prior=next((x for x in reversed(state.get('external_call_receipts',[])) if x['submission_id']==submission_id),None)
    if payload in state.get('external_call_receipts',[]):
        if render.get('acquired') and w._file(render['acquired']['path'])!=render['acquired']:raise ValueError('Returned formal bytes changed')
        return {'reused':True,'next':a.plan(path)}
    if prior and not (render.get('status')=='working' and task_id==render.get('task_id') and start>=prior['end_unix_ns']):
        raise ValueError('Different result requires the exact working task poll or explicit investigation; never resubmit')
    if state['status']!='in_progress':raise ValueError('Cannot attach a new call to accepted/terminal output')
    def apply(p):
        if status!='error':
            a.render_result(p,render['tool_name'],render['input_sha256'],status,output_url,task_id,request_id,
                            render.get('recipe'),submission_id,output_path)
        w.record_tool(p,render['tool_name'],start,end,'error' if status=='error' else 'ok')
        w.record_stage(p,'render',start,end,'error' if status=='error' else 'ok',source='external_observation')
        value=w._load(p);value['external_call_receipt']=payload
        value.setdefault('external_call_receipts',[]).append(payload)
        if 'first_render' not in value['milestones']:value['milestones']['first_render']=start
        if adapter['display_mode']=='platform_auto' and status=='ready':
            value['platform_delivery']={'display':{'status':'observed' if presented else 'unobserved','output':value['render_result']['acquired'],'observed_unix_ns':end if presented else None},
              'save':{'status':'pending_confirmation','expected_after_turn_commit':True},
              'no_extra_upload_or_display':True,'background_reconciliation_installed':False}
        w._save(p,value)
    _transaction(path,apply)
    return {'reused':False,'next':a.plan(path)}


def next_step(path,tool_name,arguments,input_references=None):
    """Deliberate refinement of the reviewed latest bytes; never a retry of unknown work."""
    if not isinstance(arguments,dict):raise ValueError('Actual next-step arguments must be an object')
    state=a._fresh(path,editable=True)
    _edit_route(state,tool_name,arguments)
    if not state.get('execution_adapter'):raise ValueError('Use begin for the first actual invocation')
    encoded=json.dumps(arguments,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()
    prior=(state.get('render_result') or {}).get('acquired') or {}
    inputs=capture_inputs(arguments,w._file,state['source']['path'],prior.get('path'),input_references)
    if inputs['files'] and not any(x['path']==prior.get('path') and x['sha256']==prior.get('sha256') and x['role']=='edit_target' for x in inputs['files']):
        raise ValueError('Next-step local references must include the latest reviewed output as edit_target')
    def apply(p):
        token=a.next_render(p,tool_name,{'actual_arguments':arguments,'arguments_sha256':hashlib.sha256(encoded).hexdigest(),'input_references':inputs})
        value=w._load(p);value['execution_adapter']['submission_id']=token['submission_id'];w._save(p,value)
        return token
    return _transaction(path,apply)


def resolve_unknown(path,submission_id,evidence_path):
    """Attach a later actually observed result to the same unknown call, without resubmission.

    This reconciliation is not a second render and does not invent tool timing.
    Caller archives the real investigation result as evidence, not an expected output.
    """
    state=a._fresh(path);render=state.get('render_result') or {};adapter=state.get('execution_adapter') or {}
    evidence_file=w._file(evidence_path)
    prior=next((x for x in reversed(state.get('reconciliation_receipts',[])) if x['submission_id']==submission_id),None)
    if prior is None and (state.get('reconciliation_receipt') or {}).get('submission_id')==submission_id:
        prior=state['reconciliation_receipt']
    if prior:
        if prior=={'submission_id':submission_id,'evidence':evidence_file}:return {'reused':True,'next':a.plan(path)}
        raise ValueError('Different evidence cannot replace resolved submission')
    if state['status']!='in_progress' or render.get('status')!='unknown' or adapter.get('submission_id')!=submission_id:
        raise ValueError('Only the same unresolved invocation can be investigated')
    evidence=json.loads(Path(evidence_path).read_text(encoding='utf-8'))
    if (evidence.get('basis')!='observed_tool_result' or evidence.get('tool_name')!=render['tool_name'] or
            evidence.get('input_sha256')!=render['input_sha256'] or evidence.get('status') not in ('ready','working')):
        raise ValueError('Investigation requires a real source-bound result from the same tool')
    w._text(evidence.get('note'),'Actual investigation basis')
    presented=w._boolean(evidence.get('presented',False),'presented')
    if presented and (adapter['display_mode']!='platform_auto' or evidence['status']!='ready' or not evidence.get('output_path')):
        raise ValueError('Presented evidence requires the actual ready platform file')
    def apply(p):
        a.render_result(p,render['tool_name'],render['input_sha256'],evidence['status'],
            evidence.get('output_url'),evidence.get('task_id'),evidence.get('request_id'),render.get('recipe'),submission_id,evidence.get('output_path'))
        value=w._load(p);receipt={'submission_id':submission_id,'evidence':evidence_file}
        value['reconciliation_receipt']=receipt;value.setdefault('reconciliation_receipts',[]).append(receipt)
        if adapter['display_mode']=='platform_auto' and evidence['status']=='ready':
            value['platform_delivery']={'display':{'status':'observed' if presented else 'unobserved','output':value['render_result']['acquired'],
              'observed_unix_ns':time.time_ns() if presented else None},'save':{'status':'pending_confirmation','expected_after_turn_commit':True},
              'no_extra_upload_or_display':True,'background_reconciliation_installed':False}
        w._save(p,value)
    _transaction(path,apply)
    return {'reused':False,'next':a.plan(path)}


def status(path):
    state=w._load(path);platform=state.get('platform_delivery') or {};review=state['reviews'][-1] if state['reviews'] else {}
    return {'display':platform.get('display',{}).get('status','not_observed'),
      'quality':'accepted_'+state.get('acceptance_scope','') if state['status']=='accepted' else ('review_failed_or_limited' if review else 'review_required'),
      'profile_check_passed':review.get('profile_passed') is True,'professional_color_calibrated':False,
      'color_scope':review.get('color_scope'),'persistence':platform.get('save',{}).get('status','not_confirmed'),
      'controller_next':a.plan(path),'background_reconciliation_installed':False}


def confirm_platform_save(path,evidence_path,observed_unix_ns=None):
    """Consume a real platform receipt only when it explicitly binds saved identity to output SHA.

    An expected automatic save or an unrelated Library file id is insufficient.
    No lookup/download/upload is performed to manufacture this evidence.
    """
    state=a._fresh(path);platform=state.get('platform_delivery')
    if state['status']!='accepted' or not platform:raise ValueError('Scoped quality acceptance and platform result required')
    output=state['output']
    if w._file(output['path'])!=output:raise ValueError('Accepted bytes changed')
    evidence=json.loads(Path(evidence_path).read_text(encoding='utf-8'))
    if (evidence.get('status')!='succeeded' or evidence.get('output_sha256')!=output['sha256'] or
            evidence.get('submission_id') not in (None,state['execution_adapter']['submission_id']) or
            evidence.get('source')!='platform_save_receipt'):
        raise ValueError('Authoritative save evidence must bind exact output bytes; a supplied invocation ID must match')
    identity=w._text(evidence.get('library_file_id'),'Observed saved Library identity')
    receipt={'file_id':identity,'output_sha256':output['sha256'],'result':w._file(evidence_path),'kind':'platform_auto'}
    if state.get('delivery_receipt'):
        if state['delivery_receipt']!=receipt:raise ValueError('Conflicting persistence evidence')
        return status(path)
    observed=w._timestamp(time.time_ns() if observed_unix_ns is None else observed_unix_ns)
    if observed<max(state['milestones'].values()):raise ValueError('Save confirmation precedes quality/readiness observations')
    state['delivery_receipt']=receipt;state['milestones']['save_completed']=observed
    state['platform_delivery']['save']={'status':'confirmed','evidence':receipt}
    w._save(path,state);return status(path)


def snapshot(path,destination,brief=None):
    """Archive pending evidence honestly without presenting it as a completed final record."""
    state=w._load(path);target=Path(destination).resolve()
    if target.exists():raise FileExistsError('Snapshot already exists')
    if target in (Path(path).resolve(),Path(state['source']['path']).resolve()):raise ValueError('Snapshot cannot overwrite source/ledger')
    draft=state['status']!='accepted' or not state.get('delivery_receipt')
    w.build_record(path,target,brief=brief,recipe=(state.get('render_result') or {}).get('recipe'),draft=draft)
    if draft and state.get('platform_delivery'):
        value=json.loads(target.read_text(encoding='utf-8'));value['record_status']='pending_platform_confirmation'
        value['execution_status']=status(path)
        # The source-bound query is kept once in the local ledger, not duplicated in the archive.
        selection=value['ledger'].get('reference_selection') or {};selection.pop('query',None)
        features=(value['ledger'].get('reference_query') or {}).get('features')
        if isinstance(features,dict):
            value['ledger']['reference_query']['features']={k:features[k] for k in ('version','source_sha256','color_basis') if k in features}
        w.atomic_json(target,value)
    return {'path':str(target),'record_status':'pending_platform_confirmation' if draft and state.get('platform_delivery') else ('draft' if draft else 'final'),
            'execution':status(path)}


def main():
    routes={'begin':begin,'finish':finish,'next-step':next_step,'resolve-unknown':resolve_unknown,'status':status,'confirm-platform-save':confirm_platform_save,'snapshot':snapshot}
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=routes);args=parser.parse_args()
    try:print(json.dumps(routes[args.action](**json.load(sys.stdin)),ensure_ascii=False,allow_nan=False));return 0
    except (OSError,ValueError,TypeError,KeyError) as error:print(json.dumps({'error':str(error),'type':type(error).__name__}),file=sys.stderr);return 1

if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    sys.exit(main())
