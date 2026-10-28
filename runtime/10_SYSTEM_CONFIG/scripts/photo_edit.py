"""Compact daily entry points. No renderer and no automatic visual judgments.

prepare merges intake/candidate retrieval; submit binds viewed reference choices,
final direction and call parameters; returned attaches the real tool result and inspection;
review commits supplied actual judgments and creates one internal snapshot.
Full proof remains in the job, compact responses avoid dumping policy/histograms.
"""
from pathlib import Path
import argparse,json,os,sys,tempfile
import photo_workflow as p
import workflow_session as w
import delivery_adapter as d
import delivery_automation as a
import review_contract as c
import delivery_metrics as m
import style_library as styles
import user_preferences as preferences
import personal_backup as backup
import experience
import task_history as history
import batch_workflow as batches
import private_checkpoint as checkpoints
import recovery_archive as recovery
import version_recovery


def _response(path):
    state=w._load(path);render=state.get('render_result') or {};review=state['reviews'][-1] if state['reviews'] else {}
    inspection=render.get('inspection') or review.get('inspection') or state.get('source_inspection') or {}
    next_step=a.plan(path)
    return {'path':str(Path(path).resolve()),'workflow_revision':state['workflow_revision'],
            'source_sha256':state['source']['sha256'],'output':render.get('acquired'),
            'dimensions':inspection.get('dimensions'),'color':inspection.get('color'),
            'next':next_step,'experience':experience.describe(state,next_step['action'])}


def prepare(project_root,source_path,path,direction=None,tags=None,intent=None,started_unix_ns=None,observed_skill_revision=None,evaluation_kind='unclassified',scenario=None,
            style_library_root=None,style_query=None,style_ids=None,style_group=None,
            observed_profile_sha256=None,task_instructions=None,profile_scenes=None,task_settings=None):
    """Retrieve before final direction; a legacy direction is only a provisional draft."""
    if direction is not None and (not isinstance(direction,dict) or 'path' in direction):raise ValueError('Photographic direction draft must be an object')
    draft=a.direction_details(**direction) if direction is not None else None
    tags=[] if tags is None else tags
    if evaluation_kind not in m.KINDS:raise ValueError('evaluation_kind must be live/replay/synthetic/unclassified')
    if scenario is not None:w._text(scenario,'scenario')
    customization=preferences.context(style_library_root,observed_profile_sha256,task_instructions,
                                      scenes=tags if profile_scenes is None else profile_scenes,task_settings=task_settings)
    target=Path(path).resolve()
    if target.exists():raise FileExistsError('Job already exists')
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as folder:
        temporary=Path(folder)/'job.json'
        p.prepare(project_root,source_path,temporary,started_unix_ns=started_unix_ns,observed_skill_revision=observed_skill_revision)
        candidates=p.candidates(temporary,project_root,tags,intent=intent,
                                style_library_root=style_library_root,style_query=style_query,style_ids=style_ids,style_group=style_group)
        state=w._load(temporary);state['evaluation']={'kind':evaluation_kind,'scenario':scenario or ('/'.join(tags) if tags else 'unclassified')}
        state['user_customization']=customization
        state['direction_workflow']='reference_first_v1'
        if draft is not None:state['direction_proposal']=draft
        w._save(temporary,state)
        # Atomic no-overwrite publication after every preparation step succeeds.
        os.link(temporary,target)
    value=_response(path)
    value['master_sha256']=w._load(path)['context']['document_hashes']['我的照片美化偏好与修图标准.md']
    value['candidates']=[{key:item.get(key) for key in ('reference_id','relative_path','library_file_id','path','sha256','origin','labels','group','pinned','use_for','subject','note','semantic_evidence')} for item in candidates['candidates']]
    value['personal_library']=candidates['personal_library']
    value['reference_limits']=candidates['limitations']
    value['customization']=customization
    value['direction_status']={'final_locked':False,'draft_available':draft is not None,
                               'next':'View suitable candidates, then supply final direction with submit'}
    return value


def submit(path,protections,selection,tool_name,arguments,protected_regions,issues=None,display_mode='platform_auto',fidelity=None,input_references=None,direction=None):
    """Atomic source-bound decision and submission reservation, before the actual tool call."""
    if not isinstance(protections,dict) or not isinstance(selection,dict):raise ValueError('Explicit protection and reference decisions required')
    plan=c.fidelity_plan(protections,protected_regions,fidelity)
    events=[{'action':'protect','arguments':protections},{'action':'select','arguments':selection}]
    for issue in issues or []:events.append({'action':'issue','arguments':issue})
    def apply(temporary):
        w.transact(temporary,events)
        state=w._load(temporary);state['fidelity_plan']=plan;state['fidelity_source_sha256']=state['source']['sha256'];w._save(temporary,state)
        if state.get('direction_workflow')=='reference_first_v1':
            if direction is None and state['reference_selection']['branch']!='PROFESSIONAL_FALLBACK':
                raise ValueError('Supply final photographic direction after viewing the selected references; the earlier draft is provisional')
            final=direction if direction is not None else state.get('direction_proposal')
            if final is None:raise ValueError('Supply final photographic direction after reference selection')
            if not isinstance(final,dict):raise ValueError('Final photographic direction must be an object')
            a.direction(temporary,**final)
        elif direction is not None:
            a.direction(temporary,**direction)
        return d.begin(temporary,tool_name,arguments,display_mode,protected_regions,input_references)
    ticket=d._transaction(path,apply)
    return dict(ticket,path=str(Path(path).resolve()),call_actual_tool_once=True)


def returned(path,submission_id,status,start_unix_ns,end_unix_ns,output_path=None,output_url=None,task_id=None,request_id=None,presented=False,geometry_changed=False):
    """Actual tool boundaries only; file proof is reused by hash, never a visual pass."""
    result=d.finish(path,submission_id,status,start_unix_ns,end_unix_ns,output_path,output_url,task_id,request_id,presented)
    value=_response(path);value['reused']=result['reused']
    if output_path is not None:
        check=p.check(path,output_path,geometry_changed=geometry_changed)
        value['file_flags']=check['flags'];value['visual_review_required']=True
        value['review_requirements']=c.requirements(w._load(path))
    return value


@w.measured('review_receipt')
def review(path,events,output_path,record_destination=None,brief=None):
    """Require explicit actual judgments; all original acceptance gates still run."""
    c.validate_review(w._load(path),events,output_path)
    w.transact(path,events,accept_output_path=output_path)
    result=_response(path)
    result['quality_observation']=m.sample(path)
    try:styles.record_accepted_use(w._load(path))
    except (OSError,ValueError) as error:result['style_usage_warning']=str(error)
    if record_destination is not None:
        result['record']=d.snapshot(path,record_destination,brief)
    return result


def main():
    routes={'recovery-restore-view':version_recovery.restore,'recovery-restored-status':version_recovery.status,
            'recovery-prepare':recovery.prepare,'recovery-status':recovery.status,
            'recovery-claim':recovery.claim,'recovery-observe':recovery.observe,'recovery-confirm':recovery.confirm,
            'checkpoint-export':checkpoints.export,'checkpoint-inspect':checkpoints.inspect,'checkpoint-restore':checkpoints.restore,
            'batch-create':batches.create,'batch-status':batches.summary,'batch-retry-failed':batches.retry_failed,'batch-completed':batches.completed,
            'version-register':history.register,'versions':history.history,'restore':history.restore,
            'revise':history.revise,'compare':history.compare,'delivered':history.delivered,'hints':history.hints,'current-version':history.current,
            'prepare':prepare,'submit':submit,'returned':returned,'review':review,'status':_response,
            'style-add':styles.add,'style-list':styles.list_references,'style-update':styles.update,'style-remove':styles.remove,
            'profile-show':preferences.show,'profile-set':preferences.save,'profile-reset':preferences.reset,
            'profile-rule-add':preferences.add_rule,'profile-rule-set':preferences.update_rule,
            'profile-rule-remove':preferences.remove_rule,'profile-history':preferences.history,'profile-undo':preferences.undo,
            'backup-export':backup.export_backup,'backup-inspect':backup.inspect_backup,'backup-import':backup.import_backup}
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=routes);args=parser.parse_args()
    try:print(json.dumps(routes[args.action](**json.load(sys.stdin)),ensure_ascii=False,allow_nan=False));return 0
    except c.InputError as error:print(json.dumps(dict(error.payload(),experience=experience.failure(error)),ensure_ascii=False),file=sys.stderr);return 1
    except (OSError,ValueError,TypeError,KeyError) as error:print(json.dumps({'error':str(error),'type':type(error).__name__,'experience':experience.failure(error)}),file=sys.stderr);return 1

if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    sys.exit(main())
