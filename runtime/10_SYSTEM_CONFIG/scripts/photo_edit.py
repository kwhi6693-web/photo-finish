"""Compact daily entry points. No renderer and no automatic visual judgments.

prepare merges intake/direction/candidate retrieval; submit binds actual choices
and call parameters; returned attaches the real tool result and file inspection;
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


def _response(path):
    state=w._load(path);render=state.get('render_result') or {};review=state['reviews'][-1] if state['reviews'] else {}
    inspection=render.get('inspection') or review.get('inspection') or state.get('source_inspection') or {}
    return {'path':str(Path(path).resolve()),'workflow_revision':state['workflow_revision'],
            'source_sha256':state['source']['sha256'],'output':render.get('acquired'),
            'dimensions':inspection.get('dimensions'),'color':inspection.get('color'),
            'next':a.plan(path)}


def prepare(project_root,source_path,path,direction,tags,intent=None,started_unix_ns=None,observed_skill_revision=None,evaluation_kind='unclassified',scenario=None,
            style_library_root=None,style_query=None,style_ids=None):
    """One local call; actual original-image observation must precede supplied direction."""
    if not isinstance(direction,dict) or 'path' in direction:raise ValueError('Explicit photographic direction object required')
    if evaluation_kind not in m.KINDS:raise ValueError('evaluation_kind must be live/replay/synthetic/unclassified')
    if scenario is not None:w._text(scenario,'scenario')
    target=Path(path).resolve()
    if target.exists():raise FileExistsError('Job already exists')
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as folder:
        temporary=Path(folder)/'job.json'
        p.prepare(project_root,source_path,temporary,started_unix_ns=started_unix_ns,observed_skill_revision=observed_skill_revision)
        a.direction(temporary,**direction)
        candidates=p.candidates(temporary,project_root,tags,intent=intent,
                                style_library_root=style_library_root,style_query=style_query,style_ids=style_ids)
        state=w._load(temporary);state['evaluation']={'kind':evaluation_kind,'scenario':scenario or ('/'.join(tags) if tags else 'unclassified')}
        w._save(temporary,state)
        # Atomic no-overwrite publication after every preparation step succeeds.
        os.link(temporary,target)
    value=_response(path)
    value['master_sha256']=w._load(path)['context']['document_hashes']['我的照片美化偏好与修图标准.md']
    value['candidates']=[{key:item.get(key) for key in ('reference_id','relative_path','library_file_id','path','sha256','origin','labels','subject','note','semantic_evidence')} for item in candidates['candidates']]
    value['personal_library']=candidates['personal_library']
    value['reference_limits']=candidates['limitations']
    return value


def submit(path,protections,selection,tool_name,arguments,protected_regions,issues=None,display_mode='platform_auto',fidelity=None,input_references=None):
    """Atomic source-bound decision and submission reservation, before the actual tool call."""
    if not isinstance(protections,dict) or not isinstance(selection,dict):raise ValueError('Explicit protection and reference decisions required')
    plan=c.fidelity_plan(protections,protected_regions,fidelity)
    events=[{'action':'protect','arguments':protections},{'action':'select','arguments':selection}]
    for issue in issues or []:events.append({'action':'issue','arguments':issue})
    def apply(temporary):
        w.transact(temporary,events)
        state=w._load(temporary);state['fidelity_plan']=plan;state['fidelity_source_sha256']=state['source']['sha256'];w._save(temporary,state)
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
    if record_destination is not None:
        result['record']=d.snapshot(path,record_destination,brief)
    return result


def main():
    routes={'prepare':prepare,'submit':submit,'returned':returned,'review':review,'status':_response,
            'style-add':styles.add,'style-list':styles.list_references,'style-remove':styles.remove}
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=routes);args=parser.parse_args()
    try:print(json.dumps(routes[args.action](**json.load(sys.stdin)),ensure_ascii=False,allow_nan=False));return 0
    except c.InputError as error:print(json.dumps(error.payload(),ensure_ascii=False),file=sys.stderr);return 1
    except (OSError,ValueError,TypeError,KeyError) as error:print(json.dumps({'error':str(error),'type':type(error).__name__}),file=sys.stderr);return 1

if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    sys.exit(main())
