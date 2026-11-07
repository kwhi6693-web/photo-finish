"""Resumable orchestration around actual render/review/save receipts.

No renderer, upload client, aesthetic judge or scheduler. The assistant calls
real tools and performs visual review. This controller chooses the next safe
step, retains render handles, avoids duplicate work and confirms both saves.
"""
from pathlib import Path
import argparse,json,sys,uuid
from urllib.parse import urlparse
import os
import workflow_session as w
from input_references import verify as verify_inputs


def entry(project_root, observed_skill_revision=None):
    ctx=w.bootstrap(project_root,observed_skill_revision=observed_skill_revision)
    return dict(ctx,effective_revision=ctx['workflow_revision'],provider_cache_repaired=False,
                execution_authority='Verified current master, runtime policy and source hashes; provider prose is a loader.',
                controller=str(Path(project_root).resolve()/'10_SYSTEM_CONFIG/scripts/delivery_automation.py'))


def _fresh(path, editable=False):
    state=w._load(path,editable=editable)
    if w._file(state['source']['path'])!=state['source']:raise ValueError('Source changed since intake')
    ctx=state.get('context') or {};current=w.bootstrap(ctx['project_root'])
    if any(ctx.get(k)!=current[k] for k in ('workflow_revision','source_hashes','document_hashes')):
        raise ValueError('Stale context requires a newly prepared task')
    verify_inputs(((state.get('render_result') or {}).get('recipe') or {}).get('input_references'),w._file)
    from style_library import verify_selection
    verify_selection(state)
    from task_history import verify_revision, verify_recovery
    verify_revision(state)
    verify_recovery(state)
    return state


def direction_details(intent,hierarchy,light_material,output_use,route,qa_focus):
    """Validate observed photographic choices without locking a task."""
    if output_use not in ('screen','print_proof_requested') or route not in ('native','creative','hybrid'):
        raise ValueError('Explicit supported output scope and route required')
    if not isinstance(qa_focus,list) or not qa_focus:raise ValueError('Actual affected detail areas required')
    return {'intent':w._text(intent,'intent'),
           'hierarchy':w._text(hierarchy,'hierarchy'),'light_material':w._text(light_material,'light_material'),
           'output_use':output_use,'route':route,'qa_focus':[w._text(x,'qa_focus') for x in qa_focus]}


def direction(path,intent,hierarchy,light_material,output_use,route,qa_focus):
    """Lock after reference decisions; never certify aesthetics or print color."""
    state=_fresh(path,editable=True)
    if state.get('direction_workflow')=='reference_first_v1' and state.get('reference_selection') is None:
        raise ValueError('Record actual reference selection before final photographic direction')
    if state['reviews'] or state.get('render_result') or state.get('professional_direction'):
        raise ValueError('Direction is locked before the first submission')
    value=dict(direction_details(intent,hierarchy,light_material,output_use,route,qa_focus),
               source_sha256=state['source']['sha256'],quality_certified=False,print_calibrated=False)
    if state.get('direction_workflow')=='reference_first_v1':
        value['reference_branch']=state['reference_selection']['branch']
    state['professional_direction']=value;w._save(path,state);return value


def next_render(path,tool_name,recipe):
    """Start a deliberate next edit, only from the actual reviewed prior output.

    This is not a retry path for working/unknown submissions or failed transfer.
    Prior issue/protection evidence is retained and must match the final output.
    """
    state=_fresh(path,editable=True);old=state.get('render_result') or {};prior=old.get('acquired')
    review=state['reviews'][-1] if state['reviews'] else {}
    if old.get('status')!='ready' or not prior or review.get('output')!=prior:
        raise ValueError('Next step requires the acquired latest reviewed output')
    if w._file(prior['path'])!=prior or not review.get('visual_passed') or not w.review_color_ready(state,review):
        raise ValueError('Prior bytes and actual visual/profile review must pass before another edit')
    tool_name=w._text(tool_name,'tool_name')
    if not isinstance(recipe,dict):raise ValueError('Next actual recipe must be an object')
    token=uuid.uuid4().hex
    state.setdefault('render_history',[]).append(old)
    state['render_result']={'tool_name':tool_name,'input_sha256':prior['sha256'],
        'job_source_sha256':state['source']['sha256'],'status':'unknown','output_url':None,
        'task_id':None,'request_id':None,'recipe':recipe,'submission_id':token,'acquired':None}
    w._save(path,state)
    return {'submission_id':token,'input':prior,'status':'unknown','step':len(state['render_history'])+1}


def begin_render(path,tool_name,input_sha256,recipe=None):
    """Persist a submission guard before a real tool call; interruption is unknown, not retryable."""
    state=_fresh(path,editable=True)
    if state.get('render_result') is not None:raise ValueError('A render already exists; resume or investigate it')
    render_result(path,tool_name,input_sha256,'unknown',recipe=recipe)
    state=w._load(path);token=uuid.uuid4().hex;state['render_result']['submission_id']=token;w._save(path,state)
    return {'submission_id':token,'status':'unknown','next':'Call the actual tool once, then register its actual result with this token'}


def render_result(path,tool_name,input_sha256,status,output_url=None,task_id=None,request_id=None,recipe=None,submission_id=None,output_path=None):
    """Register an actual tool result. A working/unknown submission is never reissued."""
    state=_fresh(path,editable=True)
    if state.get('protection_plan') is None or state.get('reference_selection') is None:
        raise ValueError('Reference choice and protection plan must precede rendering')
    if state.get('direction_workflow')=='reference_first_v1' and not state.get('professional_direction'):
        raise ValueError('Lock final photographic direction after reference selection before rendering')
    if status not in ('ready','working','unknown'):raise ValueError('Unsupported render status')
    input_sha=w._input_hash(state,input_sha256);tool_name=w._text(tool_name,'tool_name')
    acquired=None;inspection=None
    if output_path is not None:
        if status!='ready' or output_url is not None:raise ValueError('Local formal output is exclusive with URL and requires ready status')
        inspection=w._inspect_output(output_path);acquired={'path':inspection['path'],'sha256':inspection['sha256']}
        if acquired['path'] in (str(Path(path).resolve()),state['source']['path']):raise ValueError('Output cannot overwrite source or ledger')
    if status=='ready' and acquired is None and (not isinstance(output_url,str) or urlparse(output_url).scheme not in ('http','https')):
        raise ValueError('Ready render needs its actual output URL')
    if status=='working':w._text(task_id,'task_id')
    old=state.get('render_result')
    if old:
        previous_recipe=old.get('recipe') or {}
        if recipe is None:recipe=previous_recipe
        elif 'actual_arguments' in previous_recipe and recipe!=previous_recipe:
            raise ValueError('Bound submission arguments/references cannot be replaced during result registration')
        if old['tool_name']!=tool_name or old['input_sha256']!=input_sha:
            raise ValueError('Existing render must be resumed, never blindly resubmitted')
        if old.get('task_id') and task_id!=old['task_id']:raise ValueError('Resume the exact existing task ID')
        if old.get('submission_id') and submission_id!=old['submission_id']:
            raise ValueError('Result must resolve the exact recorded submission')
        resolving=old['status']=='unknown' and old.get('submission_id') and submission_id==old['submission_id']
        if old['status'] in ('ready','unknown') and not resolving:
            if (old['status'],old.get('output_url'),old.get('request_id'))==(status,output_url,request_id):return state
            raise ValueError('Existing ready/unknown result requires investigation or a new job')
    state['render_result']={'tool_name':tool_name,'input_sha256':input_sha,'job_source_sha256':state['source']['sha256'],
        'status':status,'output_url':output_url,'task_id':task_id,'request_id':request_id,'recipe':recipe or {},
        'submission_id':submission_id,'acquired':acquired,'inspection':inspection}
    return w._save(path,state)


@w.measured('download')
def fetch(path,destination,timeout=30):
    state=_fresh(path,editable=True);render=state.get('render_result') or {}
    if render.get('status')!='ready':raise ValueError('No completed render to fetch; poll or investigate first')
    raw_target=Path(destination);target=raw_target.resolve();acquired=render.get('acquired')
    if acquired:
        if acquired['path']!=str(target) or w._file(target)!=acquired:
            raise ValueError('Recorded output changed or another destination was requested')
        return {'reused':True,'output':acquired}
    if os.path.lexists(raw_target):raise ValueError('Untracked output destination exists; do not overwrite it')
    protected={Path(path).resolve(),Path(state['source']['path']).resolve()}
    if target in protected:raise ValueError('Output cannot overwrite source or ledger')
    w.download_image(render['output_url'],target,timeout=timeout)
    state['render_result']['acquired']=w._file(target);w._save(path,state)
    return {'reused':False,'output':state['render_result']['acquired']}


def _receipt(result_path,local_path):
    value=json.loads(Path(result_path).read_text(encoding='utf-8'))
    entries=value.get('results',[]) if isinstance(value,dict) else []
    matches=[x for x in entries if isinstance(x,dict) and x.get('local_path') and Path(x['local_path']).resolve()==Path(local_path).resolve()]
    if len(matches)!=1 or matches[0].get('status')!='succeeded' or matches[0].get('local_metadata_applied') is not True:
        raise ValueError('Exactly one matching successful save receipt is required')
    item=matches[0];w._text(item.get('library_file_id') or item.get('file_id'),'Saved identity')
    return item


def plan(path):
    """Read-only next step; it never generates reviews or replays external writes."""
    state=w._load(path)
    def result(action,reason):return {'action':action,'reason':reason,'workflow_revision':state['workflow_revision'],
        'terminal_for_turn':action in ('STOP','RESTART_CONTEXT','AWAIT_PLATFORM_SAVE_CONFIRMATION',
            'INVESTIGATE_RENDER','INVESTIGATE_PHOTO_SAVE','INVESTIGATE_RECORD_SAVE',
            'WAIT_TRANSFER_RECOVERY','FIX_REVIEW','DELIVER'),
        'resume_requires_new_evidence':action in ('AWAIT_PLATFORM_SAVE_CONFIRMATION',
            'INVESTIGATE_RENDER','INVESTIGATE_PHOTO_SAVE','INVESTIGATE_RECORD_SAVE','WAIT_TRANSFER_RECOVERY'),
        'automatic_visual_acceptance':False,'new_user_approval_gate':False,
        'display_needed':not (state.get('platform_delivery',{}).get('no_extra_upload_or_display') is True or
                             state.get('platform_delivery',{}).get('display',{}).get('status')=='observed')}
    if state['status'] in ('failed','cancelled'):return result('STOP','Terminal task is immutable; prepare a new task to continue')
    try:state=_fresh(path)
    except (OSError,ValueError,KeyError) as error:return result('RESTART_CONTEXT',str(error))
    if state['status']=='accepted':
        if w._file(state['output']['path'])!=state['output']:return result('STOP','Accepted output changed')
        platform=state.get('platform_delivery')
        if platform and platform.get('save',{}).get('status')!='confirmed':
            presentation='observed' if platform.get('display',{}).get('status')=='observed' else 'unobserved'
            return result('AWAIT_PLATFORM_SAVE_CONFIRMATION',f'Quality accepted for the recorded output use; tool presentation is {presentation}. Automatic persistence is expected after commit, not confirmed. Do not upload or independently redisplay the generated image.')
        if not state.get('delivery_receipt'):
            intent=state.get('save_intent')
            if not intent:return result('PREPARE_PHOTO_SAVE','Bind accepted bytes to a fresh result path')
            if not Path(intent['result_path']).exists():return result('SAVE_PHOTO','Existing intent retained; call the real save tool once')
            try:_receipt(intent['result_path'],state['output']['path'])
            except (OSError,ValueError,TypeError):return result('INVESTIGATE_PHOTO_SAVE','Existing result is failed, incomplete or unknown; do not repeat the write')
            return result('COMPLETE_PHOTO_SAVE','Consume observed successful receipt, then build the final record')
        record=state.get('final_record')
        if not record:return result('BUILD_RECORD','Photo acknowledged; build or verify one compact final record')
        if w._file(record['path'])!=record:return result('STOP','Final record changed after registration')
        confirmed=state.get('record_delivery')
        if confirmed:return result('DELIVER','Photo and final record have matching confirmed saves')
        intent=state.get('record_save_intent')
        if not intent:return result('PREPARE_RECORD_SAVE','Bind final record to a fresh save result path')
        if not Path(intent['result_path']).exists():return result('SAVE_RECORD','Save the final record with the actual file tool')
        try:_receipt(intent['result_path'],record['path'])
        except (OSError,ValueError,TypeError):return result('INVESTIGATE_RECORD_SAVE','Unknown/failed record save result must be investigated')
        return result('CONFIRM_RECORD_SAVE','Consume the actual successful record-save receipt')
    if state.get('direction_workflow')=='reference_first_v1' and not state.get('professional_direction'):
        return result('SELECT_REFERENCES_AND_DIRECTION','View suitable references or choose professional fallback, then submit final direction and protections together')
    if state.get('protection_plan') is None:return result('ASSESS_PROTECTION','Define source-information protection before rendering')
    if state.get('reference_query') is None:return result('MATCH_REFERENCES','Query source-conditioned reference candidates')
    if state.get('reference_selection') is None:return result('SELECT_REFERENCES','Actual viewed selection or professional fallback required')
    render=state.get('render_result')
    if not render:return result('RENDER','No registered submission exists')
    if render['status']=='working':return result('POLL_RENDER','Continue exact task_id; do not submit again')
    if render['status']=='unknown':return result('INVESTIGATE_RENDER','Submission status is unknown; do not submit again')
    acquired=render.get('acquired')
    if not acquired:
        errors=[e for e in w._stage_sidecar(path,state)['events'] if e['stage']=='download' and e['status']=='error']
        return result('WAIT_TRANSFER_RECOVERY' if len(errors)>=2 else 'FETCH_OUTPUT',
                      'Fetch completed render only; at most one bounded retry, never rerender for a transfer failure')
    if w._file(acquired['path'])!=acquired:return result('STOP','Downloaded output changed')
    reviews=state['reviews'];review=reviews[-1] if reviews else None
    if not review or review['output']!=acquired:return result('REVIEW_OUTPUT','Actual formal file/color inspection and whole/native-detail visual review required')
    if not review['visual_passed'] or not w.review_color_ready(state,review):return result('FIX_REVIEW','Unmet actual output review cannot be automatically passed')
    return result('VERIFY_AND_ACCEPT','Use existing accept/transact checks for every issue, protection, source and current context')


def native_status(original,candidate,receipt_json,accepted_json=None,
                  save_json=None,readback_json=None,readback_image=None,
                  library_file_id=None,version_json=None):
    """Read-only v2 next-action projection through the existing task orchestrator.

    It owns no new ledger, cannot infer a user GO, never renders or writes,
    and never converts a pending native receipt into a formal V1. Callers must
    supply trusted host receipts to the existing v2_delivery commands.
    """
    import v2_delivery as native
    source=native.inspect(original)
    output=native.inspect(candidate,png=True)
    pending=native.load(receipt_json)
    if (pending.get('camera_original_sha256')!=source['sha256'] or
            pending.get('candidate_sha256')!=output['sha256'] or
            not str(pending.get('status','')).startswith('PENDING') or
            pending.get('formal_V1_registered') is not False):
        raise ValueError('pending native candidate identity or stage mismatch')

    def result(action,reason,*,terminal,required=None,formal=False):
        return {'action':action,'reason':reason,
                'source_sha256':source['sha256'],
                'candidate_sha256':output['sha256'],
                'terminal_for_turn':terminal,
                'new_render_allowed':False,
                'user_photographic_GO':('RECORDED_FOR_EXACT_PNG' if accepted_json is not None
                                        else 'NOT_INFERRED_FROM_TECHNICAL_QA'),
                'formal_V1_registered':formal,
                'cross_conversation_restore_verified':False,
                'iphone_save_confirmed':False,
                'resume_requires':required or []}

    hosted=[save_json,readback_json,readback_image,library_file_id]
    if accepted_json is None:
        if any(x is not None for x in hosted) or version_json is not None:
            raise ValueError('official accepted evidence required before native save/version status')
        return result('WAITING_ACCEPTANCE_RECORD',
                      'Reuse an existing exact-PNG user GO if recorded; never re-request solely because a QA report is pending',
                      terminal=True,required=['source-bound accepted record or new user decision'])
    accepted=native.validate_accepted(native.load(accepted_json))
    if accepted['source']!=source or accepted['output']!=output:
        raise ValueError('accepted source/output differs from actual pending native bytes')
    if (accepted['renderer_origin']=='pr47_native_controller' and
            accepted['provenance'].get('controller_receipt_sha256')!=native.hash_file(receipt_json)):
        raise ValueError('accepted native controller receipt differs from current candidate')
    if not all(x is not None for x in hosted):
        if version_json is not None:
            raise ValueError('formal version status requires same-file host save/readback evidence')
        return result('WAITING_EXTERNAL',
                      'User GO recorded for exact PNG; only actual host save/readback evidence can advance to V1',
                      terminal=True,required=['genuine save receipt','same-ID and same-byte Library readback'])
    saved=native.saved_identity(save_json,readback_json,readback_image,library_file_id)
    if saved!=output:
        raise ValueError('host saved bytes differ from accepted PNG')
    if version_json is None:
        return result('REGISTER_V1',
                      'Host save/readback verified; register the existing exact PNG once, never rerender or resave',
                      terminal=False,required=['fresh official immutable V1 record'])
    version=native.load(version_json)
    if (version.get('schema')!='photo-finish-v2-version/1' or
            version.get('formal_V1_registered') is not True or
            version.get('label')!='V1' or
            version.get('acceptance_sha256')!=native.hash_file(accepted_json) or
            version.get('acceptance')!=accepted or
            version.get('source')!=source or version.get('output')!=output or
            version.get('library_file_id')!=library_file_id or
            version.get('save_receipt_sha256')!=native.hash_file(save_json) or
            version.get('readback_receipt_sha256')!=native.hash_file(readback_json)):
        raise ValueError('formal version record does not bind exact accepted/save/readback evidence')
    native.restore(version_json,native.hash_file(version_json),readback_json,readback_image)
    return result('FORMAL_V1_VERIFIED',
                  'Persisted V1 verified; actual host presentation and iPhone saving require separate observation',
                  terminal=True,formal=True)


def complete(path,result_path,record_destination,brief=None,recipe=None):
    """Idempotent local completion after actual photo save; never uploads a photograph."""
    state=_fresh(path)
    if state.get('platform_delivery',{}).get('save',{}).get('status')=='confirmed':
        if state['delivery_receipt']['result']!=w._file(result_path):raise ValueError('Platform save evidence differs from confirmed receipt')
    else:w.complete_save(path,result_path)
    state=w._load(path)
    target=Path(record_destination).resolve()
    if target.exists():
        record=json.loads(target.read_text(encoding='utf-8'));ledger=record.get('ledger',{})
        if (record.get('record_status')!='final' or ledger.get('output')!=state['output'] or
            ledger.get('delivery_receipt')!=state['delivery_receipt'] or record.get('actual_recipe')!=(recipe or {})):
            raise ValueError('Existing record is not the matching final snapshot')
    else:w.build_record(path,target,brief=brief,recipe=recipe)
    state['final_record']=w._file(target);w._save(path,state)
    return {'record':state['final_record'],'next':plan(path)}


def record_intent(path,record_path,result_path):
    state=_fresh(path)
    if not state.get('delivery_receipt') or state.get('final_record')!=w._file(record_path):
        raise ValueError('Matching final record after photo acknowledgment required')
    dest=str(Path(result_path).resolve());old=state.get('record_save_intent')
    if old:
        if old['result_path']==dest and old['record']==state['final_record']:return state
        raise ValueError('Resume or investigate the existing record save intent')
    if Path(dest).exists():raise ValueError('Use a fresh record save result path')
    state['record_save_intent']={'record':state['final_record'],'result_path':dest};return w._save(path,state)


def record_saved(path,result_path):
    state=_fresh(path);intent=state.get('record_save_intent') or {};record=state.get('final_record')
    if not record or intent.get('record')!=record or intent.get('result_path')!=str(Path(result_path).resolve()) or w._file(record['path'])!=record:
        raise ValueError('Record save intent/hash mismatch')
    item=_receipt(result_path,record['path']);identity=item.get('library_file_id') or item.get('file_id')
    receipt={'file_id':identity,'record_sha256':record['sha256'],'result':w._file(result_path)}
    if state.get('record_delivery') and state['record_delivery']!=receipt:raise ValueError('Different record save cannot replace confirmation')
    state['record_delivery']=receipt;w._save(path,state);return plan(path)


def main(argv=None):
    routes={'entry':entry,'plan':plan,'direction':direction,'next-render':next_render,'begin-render':begin_render,'render-result':render_result,'fetch':fetch,'complete':complete,
            'record-intent':record_intent,'record-saved':record_saved}
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=routes);args=parser.parse_args(argv)
    try:
        payload=json.load(sys.stdin)
        if not isinstance(payload,dict):raise ValueError('CLI stdin must be one JSON object')
        print(json.dumps(routes[args.action](**payload),ensure_ascii=False,allow_nan=False));return 0
    except (OSError,ValueError,TypeError,KeyError) as error:
        print(json.dumps({'error':str(error),'type':type(error).__name__}),file=sys.stderr);return 1


if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    sys.exit(main())
