"""Small, standard-library photo workflow ledger; review receipts are human claims.

CLI: ``python workflow_session.py ACTION`` reads one JSON object from stdin and
writes one JSON result to stdout (errors are JSON on stderr, exit 1). ACTION is
initialize/bootstrap/issue/mask/resolve/review/accept/mark/tool/timing/download/transact.
Keys are the corresponding function's parameter names; initialize calls
create_job, issue calls add_issue, mask calls review_mask, resolve calls
resolve_issue, review calls add_review, accept calls accept_job, tool calls
record_tool, timing calls timing_summary, and download calls download_image.
Paths are ordinary JSON strings, never shell fragments. For example:
``echo '{"path":"job.json"}' | python workflow_session.py timing``.

Mask actual_scope is a list of target identifiers (a string denotes one exact
identifier). input_sha256 is the actual render/mask input: the original source
or an output already registered by add_review, including failed preview reviews.
Every receipt separately preserves job_source_sha256 as provenance; it does
not replace the actual mask input SHA. A corrected target needs its own verified
receipt on the final render's input lineage and a resolution tied to the final
output SHA. not_needed also binds the reviewed output SHA without requiring a mask.
New jobs use current-policy contract 3; acceptance revalidates their intake context.
Visual review remains an explicit human claim. add_review and accept lazily
inspect actual output bytes using existing Pillow, binding color scope to the file. Milestones are explicit observations recorded by mark;
accept_job does not invent unobserved render, save, or timing milestones. Local
readiness and visual acceptance may occur in either order after first_render;
save_completed follows both observed milestones.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import time
import functools
import inspect
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from runtime_io import atomic_json
import session_brief


MILESTONES = ('job_started', 'first_render', 'visual_accepted',
              'local_final_ready', 'save_completed')
# These are causal pairs, not the display order of MILESTONES. The first-render
# to save pair also enforces the transitive constraint when reviews are unmeasured.
MILESTONE_CAUSES = (('first_render', 'visual_accepted'),
                    ('first_render', 'local_final_ready'),
                    ('first_render', 'save_completed'),
                    ('visual_accepted', 'save_completed'),
                    ('local_final_ready', 'save_completed'))
BRIEF_PATH = '10_SYSTEM_CONFIG/SESSION_BRIEF.json'
POLICY_PATH = '10_SYSTEM_CONFIG/runtime_policy.json'
STAGES = ('intake','context_read','visual_diagnosis','reference_matching','upload',
          'render','download','visual_verification','file_verification','review_receipt','acceptance','save','ledger_transaction')


def measured(stage):
    """Measure actual local work, including errors; never time a claimed visual judgment.

    The decorator logs only this operation, not the work a receipt describes.
    Existing intake destinations and already closed jobs are never mutated.
    """
    def decorate(function):
        signature=inspect.signature(function)
        @functools.wraps(function)
        def wrapped(*args,**kwargs):
            bound=signature.bind(*args,**kwargs);path=bound.arguments['path']
            existed=Path(path).exists();wall=time.time_ns();mono=time.perf_counter_ns()
            if stage=='intake' and bound.arguments.get('started_unix_ns') is None:
                bound.arguments['started_unix_ns']=wall
            def observed(status,error_type=None):
                if not Path(path).is_file() or (stage=='intake' and existed):return
                state=_load(path)
                if state['status'] in ('failed','cancelled') or 'save_completed' in state['milestones']:return
                record_stage(path,stage,wall,time.time_ns(),status,
                             (time.perf_counter_ns()-mono)/1e9,'local_monotonic',error_type,
                             separate=status!='ok')
            try:result=function(*bound.args,**bound.kwargs)
            except BaseException as error:
                observed('error',type(error).__name__);raise
            observed('ok');return result
        return wrapped
    return decorate


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(field + ' must be nonempty text')
    return value.strip()


def _sha(value, field='sha256'):
    if not isinstance(value, str) or re.fullmatch(r'[0-9a-fA-F]{64}', value) is None:
        raise ValueError(field + ' must be a SHA-256 hex digest')
    return value.lower()


def _timestamp(value):
    if type(value) is not int or value < 0:
        raise ValueError('Timestamp must be a nonnegative integer of Unix nanoseconds')
    return value


def _boolean(value, field):
    if type(value) is not bool:
        raise ValueError(field + ' must be an explicit boolean')
    return value


def _file(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError('Expected an existing file: ' + str(path))
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path), 'sha256': digest.hexdigest()}


def bootstrap(project_root, expected_workflow_revision=None, observed_skill_revision=None):
    """Use a fresh local brief and canonical policy, never rebuilding either."""
    root = Path(project_root).resolve(strict=True)
    brief,policy = session_brief.load(root / BRIEF_PATH, root,return_policy=True)
    if brief.get('runtime_policy') != policy or brief.get('runtime_version') != policy.get('runtime_version'):
        raise ValueError('Session brief and canonical runtime policy are inconsistent')
    fast = policy.get('fast_edit_workflow')
    workflow_key = ('fast_edit_workflow' if isinstance(fast, dict) and 'revision' in fast
                    else 'development_workflow')
    workflow = policy.get(workflow_key)
    if not isinstance(workflow, dict):
        raise ValueError('Canonical workflow revision is missing')
    revision = _text(workflow.get('revision'), 'Canonical workflow revision')
    if expected_workflow_revision is not None and expected_workflow_revision != revision:
        raise ValueError('Expected workflow revision does not match canonical revision ' + revision)
    if observed_skill_revision is not None:
        _text(observed_skill_revision, 'Observed skill revision')
    return {
        'project_root': str(root),
        'workflow_revision': revision,
        'runtime_version': brief['runtime_version'],
        'composition_policy_version': brief.get('composition_policy', {}).get('policy_version'),
        'composition_revision': brief.get('composition_policy', {}).get('revision'),
        'creative_direction_revision': brief.get('creative_direction_policy', {}).get('revision'),
        'core_rule_role': brief.get('core_rule_role', 'legacy_style_guidance'),
        'style_config_version': brief['style_config_version'],
        'source_hashes': brief['source_hashes'],
        'document_hashes': brief['document_hashes'],
        'observed_skill_revision': observed_skill_revision,
        'stale_observed_skill': observed_skill_revision is not None and observed_skill_revision != revision,
        'rule_pointers': {
            'canonical_workflow': POLICY_PATH + '#/' + workflow_key,
            'development_workflow': POLICY_PATH + '#/development_workflow',
            'core_rules': BRIEF_PATH + '#/core_rules',
            'forbidden': BRIEF_PATH + '#/forbidden',
            'composition': BRIEF_PATH + '#/composition_policy',
            'canonical_composition': '10_SYSTEM_CONFIG/composition_policy.json',
            'creative_direction': POLICY_PATH + '#/creative_direction_policy',
        },
    }


def _load(path, editable=False):
    state = json.loads(Path(path).read_text(encoding='utf-8'))
    if state.get('schema_version') != 1 or state.get('status') not in ('in_progress', 'accepted', 'failed', 'cancelled'):
        raise ValueError('Unsupported workflow job state')
    if editable and state['status'] != 'in_progress':
        raise ValueError('Accepted or terminal job is immutable; initialize a new job for revisions')
    return state


def _save(path, state):
    atomic_json(path, state)
    return state


def _input_hash(state, input_sha256):
    value = _sha(input_sha256, 'input_sha256')
    known = {state['source']['sha256']} | {review['output']['sha256'] for review in state['reviews']}
    if value not in known:
        raise ValueError('Receipt input hash has no recorded job source/render lineage')
    return value


def _review_lineage(state):
    """Follow only prior render receipts, so a sibling output is not an ancestor."""
    source = state['source']['sha256']
    reviews = state['reviews']
    index = len(reviews) - 1
    lineage = {source}
    while index >= 0:
        review = reviews[index]
        if review.get('job_source_sha256') != source:
            raise ValueError('Review source lineage differs from job source')
        actual_input = _sha(review['input_sha256'], 'input_sha256')
        lineage.add(actual_input)
        if actual_input == source:
            return lineage
        index = next((prior for prior in range(index - 1, -1, -1)
                      if reviews[prior]['output']['sha256'] == actual_input), -1)
    raise ValueError('Final review input has no prior render lineage to the job source')


def _target(state, issue_id, target):
    issue = state['issues'].get(issue_id)
    if issue is None:
        raise ValueError('Unknown issue: ' + str(issue_id))
    if target not in issue['targets']:
        raise ValueError('Unknown target: ' + str(target))
    return issue['targets'][target]


def create_job(path, source_path, workflow_revision, started_unix_ns=None,
               project_root=None, context=None):
    """Create a new source-bound job; an existing ledger is never overwritten."""
    path = Path(path)
    if path.exists():
        raise FileExistsError('Job already exists: ' + str(path))
    if context is None:
        context=bootstrap(project_root or Path(__file__).resolve().parents[2],
                          expected_workflow_revision=workflow_revision)
    if context.get('workflow_revision')!=workflow_revision or not context.get('project_root'):
        raise ValueError('Job revision/context differs from verified project policy')
    bound={key:context[key] for key in ('project_root','workflow_revision','source_hashes','document_hashes')}
    state = {
        'schema_version': 1,
        'validation_contract': 3,
        'context': bound,
        'context_source_hashes': bound['source_hashes'],
        'protection_plan': None,
        'reference_query': None,
        'reference_selection': None,
        'status': 'in_progress',
        'workflow_revision': _text(workflow_revision, 'workflow_revision'),
        'source': _file(source_path),
        'issues': {},
        'reviews': [],
        'milestones': {'job_started': _timestamp(time.time_ns() if started_unix_ns is None else started_unix_ns)},
        'tools': [],
        'stages': [],
    }
    return _save(path, state)


def add_issue(path, issue_id, targets, observation):
    state = _load(path, editable=True)
    issue_id = _text(issue_id, 'issue_id')
    if issue_id in state['issues']:
        raise ValueError('Issue already exists: ' + issue_id)
    if not isinstance(targets, (list, tuple)) or not targets:
        raise ValueError('Issue targets must be a nonempty list')
    targets = [_text(target, 'target') for target in targets]
    if len(set(targets)) != len(targets):
        raise ValueError('Issue targets must be unique')
    state['issues'][issue_id] = {
        'observation': _text(observation, 'observation'),
        'targets': {target: {'status': 'open', 'mask_reviews': []} for target in targets},
    }
    return _save(path, state)


def review_mask(path, issue_id, target, input_sha256, actual_scope, verified, reason, mask_path=None):
    state = _load(path, editable=True)
    record = _target(state, issue_id, target)
    if isinstance(actual_scope, str):
        actual_scope = [actual_scope]
    if not isinstance(actual_scope, (list, tuple)) or not actual_scope:
        raise ValueError('actual_scope must be a nonempty list of selected target identifiers')
    receipt = {
        'input_sha256': _input_hash(state, input_sha256),
        'job_source_sha256': state['source']['sha256'],
        'actual_scope': [_text(item, 'actual_scope target') for item in actual_scope],
        'verified': _boolean(verified, 'verified'),
        'reason': _text(reason, 'reason'),
        'mask': _file(mask_path) if mask_path is not None else None,
    }
    record['mask_reviews'].append(receipt)
    return _save(path, state)


def resolve_issue(path, issue_id, target, status, reason, output_sha256=None):
    state = _load(path, editable=True)
    record = _target(state, issue_id, target)
    if status not in ('corrected', 'not_needed', 'blocked'):
        raise ValueError('Resolution status must be corrected, not_needed, or blocked')
    reason = _text(reason, 'reason')
    if status == 'not_needed' and output_sha256 is None and state['reviews']:
        output_sha256=state['reviews'][-1]['output']['sha256']
    if status in ('corrected','not_needed') and output_sha256 is None:
        raise ValueError('Closed target requires a reviewed output_sha256')
    output_sha256 = _sha(output_sha256, 'output_sha256') if output_sha256 is not None else None
    record.update(status=status, reason=reason, output_sha256=output_sha256)
    return _save(path, state)


def _inspect_output(output_path,cached=None):
    # Keep bootstrap/timing/ledger reading stdlib-only. File validation requires
    # existing Pillow, fails closed when absent, and never installs dependencies.
    from photo_workflow import inspect_image,INSPECTION_VERSION
    if isinstance(cached,dict) and cached.get('inspection_version')==INSPECTION_VERSION:
        identity=_file(output_path)
        if cached.get('path')==identity['path'] and cached.get('sha256')==identity['sha256']:
            import copy
            return copy.deepcopy(cached)
    return inspect_image(output_path)


def _color_scope(inspection, requested=None, profile_passed=False, assumption_reason=None):
    color = inspection['color']
    if requested == 'screen_srgb_assumed':
        if (profile_passed or color['status'] != 'unknown' or color.get('declarations') or
                inspection.get('format') != 'PNG' or inspection.get('mode') not in ('RGB','RGBA') or
                inspection.get('sample_depth') != 8):
            raise ValueError('Screen assumption requires an untagged 8-bit RGB PNG and cannot certify a profile')
        _text(assumption_reason,'Explicit screen sRGB assumption reason')
        return requested
    supported = color['status'] == 'declared'
    allowed = ('web_srgb_assumed' if color['basis'] == 'web_srgb_assumption' else
               'managed') if supported else 'visual_only'
    scope = allowed if requested is None else requested
    if scope not in ('managed', 'web_srgb_assumed', 'visual_only'):
        raise ValueError('Unsupported color_scope')
    if scope == 'managed' and allowed != 'managed':
        raise ValueError('color_scope exceeds actual declaration/assumption evidence')
    if scope != 'visual_only' and not supported:
        raise ValueError('color_scope requires a supported valid file declaration')
    if scope == 'visual_only' and profile_passed is True:
        raise ValueError('visual_only cannot claim a profile pass')
    return scope


@measured('review_receipt')
def add_review(path, output_path, input_sha256, visual_passed, profile_passed, note,
               color_scope=None, color_assumption_reason=None):
    state = _load(path, editable=True)
    inspection = _inspect_output(output_path,(state.get('render_result') or {}).get('inspection'))
    receipt = {
        'output': {'path':inspection['path'], 'sha256':inspection['sha256']},
        'inspection': inspection,
        'input_sha256': _input_hash(state, input_sha256),
        'job_source_sha256': state['source']['sha256'],
        'visual_passed': _boolean(visual_passed, 'visual_passed'),
        'profile_passed': _boolean(profile_passed, 'profile_passed'),
        'color_scope': _color_scope(inspection, color_scope, profile_passed, color_assumption_reason),
        'color_assumption_reason':color_assumption_reason,
        'note': _text(note, 'note'),
    }
    state['reviews'].append(receipt)
    return _save(path, state)


def set_protections(path, requirements, reason):
    state = _load(path, editable=True)
    if state['reviews'] or 'first_render' in state['milestones'] or state.get('protection_plan') is not None:
        raise ValueError('Protection contract is locked; define it once before rendering')
    if not isinstance(requirements, list):
        raise ValueError('Protection requirements must be a list, including an explicit empty list')
    targets = {}
    for requirement in requirements:
        target = _text(requirement.get('target'), 'Protection target')
        level = requirement.get('level')
        if target in targets or level not in ('semantic_identity', 'exact_content'):
            raise ValueError('Duplicate protection target or unsupported protection level')
        targets[target] = {'level':level, 'requirement':_text(requirement.get('requirement'), 'requirement'),
                           'reviews':[]}
    state['protection_plan'] = {'reason':_text(reason,'reason'), 'targets':targets}
    return _save(path,state)


def review_protection(path, target, output_sha256, status, method, content_recreated, reason, comparison_scope=None):
    state = _load(path, editable=True)
    plan = state.get('protection_plan') or {}
    if target not in plan.get('targets',{}):
        raise ValueError('Unknown protection target')
    record = plan['targets'][target]
    digest = _sha(output_sha256)
    if not state['reviews'] or state['reviews'][-1]['output']['sha256'] != digest:
        raise ValueError('Protection evidence must bind the latest reviewed output')
    if status not in ('met','failed','unverified'):
        raise ValueError('Invalid protection evidence status')
    if method not in ('pixel_comparison','manual_detail_comparison','documented_transform'):
        raise ValueError('Protection requires an actual comparison method')
    _boolean(content_recreated,'content_recreated')
    if state.get('execution_adapter') and status == 'met':
        if not isinstance(comparison_scope,list) or not comparison_scope:
            raise ValueError('Adapted protection review requires actual compared regions, not per-stroke certification')
        comparison_scope=[_text(x,'Compared region') for x in comparison_scope]
        planned=state['execution_adapter'].get('protected_regions',{}).get(target,[])
        if not set(planned).issubset(comparison_scope):
            raise ValueError('Protection review must cover every preplanned visible region')
        if content_recreated and method == 'documented_transform':
            raise ValueError('Generated protected content requires actual detail comparison')
    if record['level'] == 'exact_content' and status == 'met' and content_recreated:
        raise ValueError('Exact protection cannot pass known content recreation/redraw')
    record['reviews'].append({'output_sha256':digest,'status':status,'method':method,
                              'content_recreated':content_recreated,'reason':_text(reason,'reason'),
                              'comparison_scope':comparison_scope})
    return _save(path,state)


def select_references(path, branch, decisions, reason):
    state = _load(path, editable=True)
    if state['reviews'] or 'first_render' in state['milestones']:
        raise ValueError('Reference selection must be recorded before rendering')
    query = state.get('reference_query')
    if not query or query.get('source_sha256') != state['source']['sha256']:
        raise ValueError('Run the source-bound compact candidate query first')
    if branch not in ('MATCHED','PARTIAL','PROFESSIONAL_FALLBACK') or not isinstance(decisions,list):
        raise ValueError('Invalid reference branch or decisions')
    candidates = {x['reference_id'] for x in query['candidates']}
    seen, selected = set(), []
    clean = []
    for item in decisions:
        rid = item.get('reference_id'); decision = item.get('decision')
        if rid not in candidates or rid in seen:
            raise ValueError('Unknown or duplicate candidate decision')
        seen.add(rid)
        if decision not in ('adopt','partial','reject','unavailable'):
            raise ValueError('Invalid candidate decision')
        viewed = _boolean(item.get('viewed'), 'viewed')
        if decision in ('adopt','partial'):
            if not viewed:
                raise ValueError('Adopted references require actual visual inspection')
            selected.append(decision)
        clean.append({'reference_id':rid,'decision':decision,'viewed':viewed,
                      'scope':_text(item.get('scope'),'scope'), 'reason':_text(item.get('reason'),'reason')})
    if seen != candidates:
        raise ValueError('Every returned candidate needs a decision; not loaded is not no candidate')
    if ((branch == 'PROFESSIONAL_FALLBACK' and selected) or
        (branch == 'MATCHED' and 'adopt' not in selected) or
        (branch == 'PARTIAL' and not selected)):
        raise ValueError('Reference branch contradicts candidate decisions')
    state['reference_selection'] = {'branch':branch,'decisions':clean,'reason':_text(reason,'reason'),
                                     'query':query}
    return _save(path,state)


def save_intent(path, result_path):
    """Bind a new upload result path to the accepted bytes before saving."""
    state = _load(path)
    result = Path(result_path).resolve()
    if state['status'] != 'accepted' or _file(state['output']['path']) != state['output']:
        raise ValueError('A fresh accepted output is required for save intent')
    if result.exists():
        raise FileExistsError('Use a new result path; old upload receipts cannot confirm new bytes')
    if state.get('save_intent') is not None:
        if state['save_intent']['result_path'] == str(result): return state
        raise ValueError('An existing save intent must be resumed or explicitly investigated')
    state['save_intent'] = {'output_sha256':state['output']['sha256'], 'result_path':str(result),
                            'observed_unix_ns':time.time_ns()}
    return _save(path,state)


def complete_save(path, result_path, observed_unix_ns=None):
    """Observe a successful photo save, then persist its identity and endpoint.

    The endpoint covers the photo save acknowledgment, not this ledger's later
    upload. Run before building/saving the final record; never estimate old times.
    """
    state = _load(path)
    if state['status'] != 'accepted':
        raise ValueError('A fully accepted output is required before completion')
    output = state['output']
    if _file(output['path']) != output:
        raise ValueError('Accepted output changed before save confirmation')
    intent = state.get('save_intent')
    if (not intent or intent.get('output_sha256') != output['sha256'] or
            intent.get('result_path') != str(Path(result_path).resolve())):
        raise ValueError('A source-bound save intent is required before a successful receipt')
    result = json.loads(Path(result_path).read_text(encoding='utf-8'))
    entries = result.get('results',[]) if isinstance(result,dict) else []
    matches = [x for x in entries if isinstance(x,dict) and
               str(Path(x.get('local_path','')).resolve()) == output['path']]
    if len(matches) != 1 or matches[0].get('status') != 'succeeded' or matches[0].get('local_metadata_applied') is not True:
        raise ValueError('Exactly one matching successful save receipt is required')
    saved = matches[0]
    identity = saved.get('library_file_id') or saved.get('file_id')
    identity = _text(identity, 'Saved file identity')
    receipt = {'file_id':identity, 'version_id':saved.get('current_version_number',saved.get('version_id')),
               'output_sha256':output['sha256'], 'result':_file(result_path)}
    if 'save_completed' in state['milestones']:
        old = state.get('delivery_receipt',{})
        if old.get('file_id') != identity or old.get('output_sha256') != output['sha256']:
            raise ValueError('A different save cannot replace the recorded endpoint')
        return state
    now = _timestamp(time.time_ns() if observed_unix_ns is None else observed_unix_ns)
    if now < max(state['milestones'].values()):
        raise ValueError('Save observation precedes a recorded milestone')
    state['delivery_receipt'] = receipt
    state['milestones']['save_completed'] = now
    return _save(path,state)


def build_record(path, destination, brief=None, recipe=None, draft=False):
    """One compact record; full Lightroom design is optional route-specific data."""
    state = _load(path)
    protected = {Path(path).resolve(), Path(state['source']['path']).resolve()}
    protected.update(Path(r['output']['path']).resolve() for r in state['reviews'])
    if Path(destination).resolve() in protected:
        raise ValueError('Record cannot overwrite a ledger or photograph')
    if Path(destination).exists():
        raise FileExistsError('Record exists; use a new revision')
    _boolean(draft, 'draft')
    if not draft and (state['status'] != 'accepted' or not state.get('delivery_receipt') or
                      'save_completed' not in state['milestones']):
        raise ValueError('Final record requires accepted output and confirmed photo save')
    if not draft and _file(state['output']['path']) != state['output']:
        raise ValueError('Accepted output changed before final record')
    result = {'record_status':'draft' if draft else 'final',
              'workflow_revision':state['workflow_revision'], 'ledger':state,
              'brief':brief or {}, 'actual_recipe':recipe or {}, 'timing':timing_summary(path),
              'scope':'Actual applied route; no implicit 82-parameter Lightroom claim',
              'timing_endpoint':'save_completed is photo acknowledgment; record upload follows'}
    from delivery_metrics import observe
    result['quality_observation']=observe(state,_stage_sidecar(path,state))
    atomic_json(destination,result)
    return {'path':str(Path(destination).resolve()),'status':state['status'],
            'save_completed':state['milestones'].get('save_completed')}


@measured('acceptance')
def accept_job(path, output_path):
    """Accept only a fully resolved job with fresh source/output review receipts."""
    state = _load(path)
    if state['status'] in ('failed','cancelled'):
        raise ValueError('Terminal job cannot be accepted; prepare a new job')
    output = _file(output_path)
    if _file(state['source']['path'])['sha256'] != state['source']['sha256']:
        raise ValueError('Job source changed after initialization')
    if not state['reviews']:
        raise ValueError('Final output requires a visual and profile review')
    review = state['reviews'][-1]
    render = state.get('render_result')
    if render and (render.get('status') != 'ready' or render.get('acquired') != output or
                   review['input_sha256'] != render['input_sha256']):
        raise ValueError('Final output must be the acquired current render with matching reviewed input')
    if review['output']['sha256'] != output['sha256']:
        raise ValueError('Latest review hash differs from final output hash')
    if review.get('visual_passed') is not True or not review_color_ready(state,review):
        raise ValueError('Final visual and profile review must both pass')
    _text(review.get('note'), 'Review note')
    # The actual inspection was made by add_review. Equal SHA binds pixels AND
    # color metadata; re-hash the file rather than decoding unchanged bytes again.
    inspection = review.get('inspection')
    if not isinstance(inspection, dict) or inspection.get('sha256') != output['sha256']:
        raise ValueError('Final review needs a hash-bound actual file inspection')
    _color_scope(inspection, review.get('color_scope'), review.get('profile_passed'),review.get('color_assumption_reason'))
    if state.get('execution_adapter'):
        if not render or render.get('acquired') != output or not state.get('external_call_receipt'):
            raise ValueError('Adapted acceptance requires its actual registered tool result and call receipt')
    if state.get('validation_contract') != 3 or not state.get('context'):
        raise ValueError('Legacy job needs a new source-bound contract before new acceptance')
    context=state['context']
    current=bootstrap(context['project_root'])
    for key in ('workflow_revision','source_hashes','document_hashes'):
        if context.get(key)!=current[key]:
            raise ValueError('Job policy/context is stale; initialize a new task and recheck affected requirements')
    if state['workflow_revision']!=current['workflow_revision']:
        raise ValueError('Job policy revision differs from its verified context')
    if state.get('validation_contract') == 3:
        plan = state.get('protection_plan')
        if plan is None:
            raise ValueError('Protection plan must be assessed before full acceptance')
        for target, record in plan['targets'].items():
            evidence = record['reviews'][-1] if record['reviews'] else {}
            if evidence.get('status') != 'met' or evidence.get('output_sha256') != output['sha256']:
                raise ValueError('Unmet protection target: ' + target)
            if record['level'] == 'exact_content' and evidence.get('content_recreated') is not False:
                raise ValueError('Exact protection cannot pass recreated content: ' + target)
        if state.get('reference_selection') is None:
            raise ValueError('Source-bound reference selection evidence is required')
    lineage = _review_lineage(state)
    for issue_id, issue in state['issues'].items():
        for target, record in issue['targets'].items():
            label = issue_id + '/' + target
            if record['status'] not in ('corrected', 'not_needed'):
                raise ValueError('Unresolved target ' + label + ': ' + record['status'])
            _text(record.get('reason'), 'Resolution reason for ' + label)
            if record.get('output_sha256') != output['sha256']:
                raise ValueError('Closed target output hash differs from final output: ' + label)
            if record['status'] == 'not_needed':
                continue
            receipts = record.get('mask_reviews', [])
            if not receipts or receipts[-1].get('verified') is not True:
                raise ValueError('Corrected target requires a verified mask scope: ' + label)
            mask = receipts[-1]
            _input_hash(state, mask['input_sha256'])
            if mask.get('job_source_sha256') != state['source']['sha256'] or mask['input_sha256'] not in lineage:
                raise ValueError('Mask input is outside the final render source lineage: ' + label)
            if target not in mask['actual_scope']:
                raise ValueError('Verified mask scope omits target: ' + label)
            if mask.get('mask') is not None and _file(mask['mask']['path'])['sha256'] != mask['mask']['sha256']:
                raise ValueError('Reviewed mask file changed: ' + label)
    if state['status'] == 'accepted' and state.get('output', {}).get('sha256') != output['sha256']:
        raise ValueError('Accepted output hash cannot be replaced')
    state.update(status='accepted', output=output,
                 acceptance_scope=review.get('color_scope', 'managed'))
    return _save(path, state)


def review_color_ready(state, review):
    """A screen assumption is an explicit limited delivery scope, never a profile pass."""
    if review.get('profile_passed') is True:
        return True
    return (review.get('color_scope') == 'screen_srgb_assumed' and
            bool(review.get('color_assumption_reason')) and
            state.get('professional_direction',{}).get('output_use') == 'screen')


def mark(path, event_name, unix_ns=None):
    state = _load(path)
    if state['status'] in ('failed','cancelled'):raise ValueError('Terminal job is immutable')
    event_name = _text(event_name, 'event_name')
    timestamp = _timestamp(time.time_ns() if unix_ns is None else unix_ns)
    milestones = state['milestones']
    if event_name in milestones:
        raise ValueError('Milestone already recorded: ' + event_name)
    if timestamp < milestones['job_started']:
        raise ValueError('Milestone precedes job start')
    observed = dict(milestones, **{event_name: timestamp})
    for earlier, later in MILESTONE_CAUSES:
        if earlier in observed and later in observed and observed[earlier] > observed[later]:
            raise ValueError('Milestone causal order would reverse elapsed time: ' + earlier + ' before ' + later)
    milestones[event_name] = timestamp
    return _save(path, state)


def record_tool(path, name, start_unix_ns, end_unix_ns, status='ok'):
    state = _load(path)
    if state['status'] in ('failed','cancelled'):raise ValueError('Terminal job is immutable')
    start, end = _timestamp(start_unix_ns), _timestamp(end_unix_ns)
    if end < start:
        raise ValueError('Tool end precedes start')
    if start < state['milestones']['job_started']:
        raise ValueError('Tool interval precedes job start')
    state['tools'].append({'name': _text(name, 'name'), 'start_unix_ns': start,
                           'end_unix_ns': end, 'status': _text(status, 'status')})
    return _save(path, state)


def record_stage(path, stage, start_unix_ns, end_unix_ns, status='ok',
                 elapsed_seconds=None, source='external_observation', error_type=None, separate=False):
    """Observe a bounded stage. External wall time is API elapsed, not server compute."""
    state=_load(path)
    if state['status'] in ('failed','cancelled'):raise ValueError('Terminal job is immutable')
    if stage not in STAGES or status not in ('ok','error','cancelled'):
        raise ValueError('Unsupported stage or status')
    start,end=_timestamp(start_unix_ns),_timestamp(end_unix_ns)
    if end<start or start<state['milestones']['job_started']:
        raise ValueError('Stage interval precedes job or reverses time')
    if 'save_completed' in state['milestones'] and end>state['milestones']['save_completed']:
        raise ValueError('Stage interval exceeds photo-save endpoint')
    seconds=(end-start)/1e9 if elapsed_seconds is None else elapsed_seconds
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
        raise ValueError('Stage duration must be finite and nonnegative')
    if source not in ('external_observation','local_monotonic'):
        raise ValueError('Unsupported timing source')
    if error_type is not None:_text(error_type,'error_type')
    event={'stage':stage,'start_unix_ns':start,'end_unix_ns':end,
           'seconds':seconds,'status':status,'source':source,'error_type':error_type}
    _boolean(separate,'separate')
    if separate:
        # Failed operations preserve the original ledger's atomicity contract.
        sidecar=Path(str(path)+'.timing.json')
        extra=_stage_sidecar(path,state)
        extra['events'].append(event);atomic_json(sidecar,extra)
        return state
    state.setdefault('stages',[]).append(event)
    return _save(path,state)


def _stage_sidecar(path,state):
    sidecar=Path(str(path)+'.timing.json')
    identity={'source_sha256':state['source']['sha256'],'job_started':state['milestones']['job_started']}
    if not sidecar.exists():return dict(identity,events=[])
    value=json.loads(sidecar.read_text(encoding='utf-8'))
    if any(value.get(k)!=v for k,v in identity.items()):raise ValueError('Timing sidecar belongs to another task')
    return value


def finish_job(path, status, reason, unix_ns=None):
    """Close an unsuccessful task without inventing acceptance or save milestones."""
    state=_load(path,editable=True)
    if status not in ('failed','cancelled'):raise ValueError('Terminal status must be failed or cancelled')
    now=_timestamp(time.time_ns() if unix_ns is None else unix_ns)
    latest=max(list(state['milestones'].values())+[r['end_unix_ns'] for r in state['tools']+state.get('stages',[])+_stage_sidecar(path,state)['events']])
    if now<latest:raise ValueError('Terminal endpoint precedes an observed stage or milestone')
    state['status']=status;state['terminal']={'status':status,'reason':_text(reason,'reason'),'unix_ns':now}
    return _save(path,state)


@measured('ledger_transaction')
def transact(path, events, accept_output_path=None, save_result_path=None):
    """Validate ordered receipts on a private copy, then commit once. One writer/job.

    Events are {action, arguments}; an event cannot choose another ledger. Failed
    validation leaves the original bytes unchanged. This never supplies visual
    judgments: callers must have actually performed every review they record.
    """
    routes = {'issue': add_issue, 'mask': review_mask, 'resolve': resolve_issue,
              'review': add_review, 'mark': mark, 'tool': record_tool,
              'protect': set_protections, 'protection': review_protection, 'select': select_references,
              'stage':record_stage}
    if not isinstance(events, list) or not events:
        raise ValueError('events must be a nonempty list')
    path = Path(path).resolve(strict=True)
    _load(path)
    original = path.read_bytes()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('wb', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(original)
        for event in events:
            if not isinstance(event, dict) or set(event) != {'action', 'arguments'}:
                raise ValueError('Each event must contain action and arguments')
            action, arguments = event['action'], event['arguments']
            if not isinstance(action, str) or action not in routes:
                raise ValueError('Unsupported transaction action')
            if not isinstance(arguments, dict) or 'path' in arguments:
                raise ValueError('Event arguments cannot override the job path')
            routes[action](temporary, **arguments)
        if accept_output_path is not None:
            accept_job(temporary, accept_output_path)
        if save_result_path is not None:
            save_intent(temporary, save_result_path)
        result = _load(temporary)
        if path.read_bytes() != original:
            raise ValueError('Job changed during transaction; do not use concurrent writers')
        os.replace(temporary, path)
        temporary = None
        return {'path': str(path), 'status': result['status'], 'events_applied': len(events),
                'review_count': len(result['reviews']), 'output': result.get('output')}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
            Path(str(temporary)+'.timing.json').unlink(missing_ok=True)


def _merged_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def timing_summary(path):
    state = _load(path)
    milestones = state['milestones']
    started = milestones['job_started']
    intervals = sorted((item['start_unix_ns'], item['end_unix_ns']) for item in state['tools'])
    union = sum(end - start for start, end in _merged_intervals(intervals))
    terminal=state.get('terminal')
    finished = milestones.get('save_completed',terminal['unix_ns'] if terminal else None)
    endpoint='save_completed' if 'save_completed' in milestones else terminal['status'] if terminal else None
    coverage = None
    if finished is not None:
        clipped = _merged_intervals((max(start, started), min(end, finished))
                                   for start, end in intervals
                                   if end > started and start < finished)
        gaps, cursor = [], started
        for start, end in clipped:
            if start > cursor:
                gaps.append((cursor, start))
            cursor = end
        if cursor < finished:
            gaps.append((cursor, finished))
        occupied = sum(end - start for start, end in clipped)
        elapsed = finished - started
        coverage = {'scope': 'job_started through observed '+endpoint,
                    'elapsed_seconds': elapsed / 1e9,
                    'tool_seconds_union_in_scope': occupied / 1e9,
                    'outside_recorded_tools_seconds': (elapsed - occupied) / 1e9,
                    'tool_coverage_fraction': occupied / elapsed if elapsed else None,
                    'gaps': [{'start_unix_ns': start, 'end_unix_ns': end,
                              'seconds': (end - start) / 1e9} for start, end in gaps],
                    'attribution': 'Unattributed gaps may include unrecorded tools, reasoning, scheduling or other work; not a measured cloud/model stage.'}
    stage_events=state.get('stages',[])+_stage_sidecar(path,state)['events']
    stages={name:{'seconds_sum':None,'count':0,'failures':0} for name in STAGES}
    for event in stage_events:
        total=stages[event['stage']];total['seconds_sum']=(total['seconds_sum'] or 0)+event['seconds']
        total['count']+=1;total['failures']+=event['status']!='ok'
    stage_intervals=[(e['start_unix_ns'],e['end_unix_ns']) for e in stage_events]
    stage_union=sum(b-a for a,b in _merged_intervals(stage_intervals))
    combined=None
    if finished is not None:
        merged=_merged_intervals((max(a,started),min(b,finished)) for a,b in intervals+stage_intervals if b>started and a<finished)
        gaps=[];cursor=started
        for a,b in merged:
            if a>cursor:gaps.append({'start_unix_ns':cursor,'end_unix_ns':a,'seconds':(a-cursor)/1e9})
            cursor=b
        if cursor<finished:gaps.append({'start_unix_ns':cursor,'end_unix_ns':finished,'seconds':(finished-cursor)/1e9})
        combined={'elapsed_seconds':(finished-started)/1e9,'recorded_seconds_union':sum(b-a for a,b in merged)/1e9,
                  'unattributed_seconds':sum(g['seconds'] for g in gaps),'gaps':gaps,
                  'attribution':'Gaps are unmeasured; API elapsed includes possible transport/queueing. No inferred cloud/model time.'}
    return {
        'terminal':terminal,'stages':stages,'stage_events':stage_events,
        'unmeasured_stages':[s for s in STAGES if stages[s]['count']==0],
        'stage_coverage':{'seconds_union':stage_union/1e9,'combined_with_tools':combined},
        'milestone_unix_ns': {name: milestones.get(name) for name in MILESTONES},
        'elapsed_seconds': {name: (milestones[name] - started) / 1e9 if name in milestones else None
                            for name in MILESTONES},
        'tool_count': len(intervals),
        'tool_seconds_sum': sum(end - start for start, end in intervals) / 1e9,
        'tool_seconds_union': union / 1e9,
        'coverage': coverage,
        'note': 'Elapsed milestones start at job_started. Tool sums can overlap; missing milestones are unmeasured.',
    }


def download_image(url, destination, expected_sha256=None, timeout=30):
    """One urllib request; full decode/dimensions/color/hash validation before replacement."""
    if urlparse(url).scheme not in ('http', 'https'):
        raise ValueError('Image URL must use HTTP or HTTPS')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Download timeout must be finite and positive')
    expected = _sha(expected_sha256, 'expected_sha256') if expected_sha256 is not None else None
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with urlopen(Request(url, headers={'User-Agent': 'PCS-workflow-session/1'}), timeout=timeout) as response:
            with tempfile.NamedTemporaryFile('wb', dir=destination.parent, delete=False) as stream:
                temporary = stream.name
                digest, signature, size = hashlib.sha256(), b'', 0
                for block in iter(lambda: response.read(1024 * 1024), b''):
                    if len(signature) < 8:
                        signature = (signature + block)[:8]
                    digest.update(block)
                    size += len(block)
                    stream.write(block)
        if not (signature.startswith(b'\x89PNG\r\n\x1a\n') or signature.startswith(b'\xff\xd8\xff')):
            raise ValueError('Response has no PNG or JPEG signature')
        actual = digest.hexdigest()
        if expected is not None and actual != expected:
            raise ValueError('Downloaded image SHA-256 integrity mismatch')
        inspection = _inspect_output(temporary)
        if inspection['format'] not in ('PNG', 'JPEG') or min(inspection['dimensions']) <= 0:
            raise ValueError('Downloaded image format or dimensions invalid')
        if inspection['color']['status'] in ('invalid','conflict'):
            raise ValueError('Downloaded image has invalid color declarations')
        os.replace(temporary, destination)
        temporary = None
        return {'path': str(destination.resolve()), 'sha256': actual, 'bytes': size}
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def main(argv=None):
    routes = {'initialize': create_job, 'bootstrap': bootstrap, 'issue': add_issue,
              'mask': review_mask, 'resolve': resolve_issue, 'review': add_review,
              'accept': accept_job, 'mark': mark, 'tool': record_tool,
              'timing': timing_summary, 'download': download_image, 'transact': transact,
              'protect':set_protections, 'protection':review_protection, 'select':select_references,
              'saved':complete_save, 'record':build_record, 'save-intent':save_intent,
              'stage':record_stage,'finish':finish_job}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=routes)
    arguments = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError('CLI stdin must contain one JSON object of function arguments')
        result = routes[arguments.action](**payload)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, OSError, KeyError) as error:
        print(json.dumps({'error': str(error), 'type': type(error).__name__}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
