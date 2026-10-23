"""Lightweight input contracts; never infer visual passes or weaken core checks."""
from pathlib import Path
import inspect
import workflow_session as w


class InputError(ValueError):
    def __init__(self,field,message,hint):
        super().__init__(f'{field}: {message}. {hint}')
        self.field=field;self.hint=hint
    def payload(self):
        return {'error':str(self),'type':'InputError','code':'INVALID_REVIEW_INPUT',
                'field':self.field,'hint':self.hint,'automatic_visual_acceptance':False}


def text_list(value,field):
    if not isinstance(value,list) or not value or any(not isinstance(x,str) or not x.strip() for x in value):
        raise InputError(field,'expected a nonempty list of text','Use ["region or target identifier"], not a description string')
    return value


def fidelity_plan(protections,regions,plan):
    requirements=protections.get('requirements',[])
    if not isinstance(requirements,list):raise InputError('protections.requirements','expected a list','Use explicit target/level/requirement objects')
    targets={x.get('target'):x for x in requirements if isinstance(x,dict)}
    if not targets:
        if plan not in (None,{}):raise InputError('fidelity','no protected targets','Use {} when no source-content protection is required')
        return {}
    if not isinstance(plan,dict) or set(plan)!=set(targets):
        raise InputError('fidelity','one plan per protected target is required','Each target needs strategy, capability_basis and repair_route; these are plans, not passed evidence')
    for target,entry in plan.items():
        field='fidelity.'+str(target)
        if not isinstance(entry,dict) or set(entry)!={'strategy','capability_basis','repair_route'}:
            raise InputError(field,'expected strategy/capability_basis/repair_route','Describe actual available capability and a concrete correction route')
        if entry['strategy'] not in ('native_preserved','local_excluded','generative_compare'):
            raise InputError(field+'.strategy','unsupported strategy','Use native_preserved, local_excluded or generative_compare')
        for name in ('capability_basis','repair_route'):w._text(entry[name],field+'.'+name)
        if targets[target].get('level')=='exact_content' and entry['strategy']=='generative_compare':
            raise InputError(field,'generative reconstruction cannot satisfy exact_content','Use an actually available source-preserving route or keep this requirement blocked')
        text_list(regions.get(target), 'protected_regions.'+str(target))
    return plan


def requirements(state):
    """Return structural scopes only; no invented judgments, status or passed flags."""
    return {'protection_comparison_scopes':(state.get('execution_adapter') or {}).get('protected_regions',{}),
      'issue_target_ids':{key:list(value['targets']) for key,value in state['issues'].items()},
      'types':{'comparison_scope':'list[str], covering every preplanned region',
               'actual_scope':'list[str], containing this exact issue target ID'},
      'fidelity_plan':state.get('fidelity_plan',{}),
      'actual_visual_review_required':True}


def validate_review(state,events,output_path):
    if not isinstance(events,list) or not events:
        raise InputError('events','expected a nonempty list','Supply actual review and all required protection/issue receipts')
    routes={'review':w.add_review,'mask':w.review_mask,'resolve':w.resolve_issue,
            'protection':w.review_protection,'mark':w.mark,'stage':w.record_stage}
    review_seen=False
    for i,event in enumerate(events):
        field=f'events[{i}]'
        if not isinstance(event,dict) or set(event)!={'action','arguments'}:
            raise InputError(field,'expected action and arguments','Use {"action":"review","arguments":{...}}')
        action=event['action'];args=event['arguments']
        if not isinstance(action,str) or action not in routes or not isinstance(args,dict) or 'path' in args:
            raise InputError(field,'unsupported action or arguments','Use review/mask/resolve/protection/mark/stage without overriding path')
        try:inspect.signature(routes[action]).bind('job.json',**args)
        except TypeError as error:raise InputError(field+'.arguments',str(error),'Use the documented function fields') from error
        if action=='review':
            review_seen=True
            if Path(args['output_path']).resolve()!=Path(output_path).resolve():
                raise InputError(field+'.output_path','differs from accepted output','Review the same actual formal file that will be accepted')
            w._boolean(args['visual_passed'],'visual_passed');w._boolean(args['profile_passed'],'profile_passed')
        if action=='mask':
            scope=text_list(args['actual_scope'],field+'.actual_scope')
            if args['target'] not in scope:
                raise InputError(field+'.actual_scope','omits exact target ID','Include '+str(args['target'])+'; put free-form comparison details in reason')
        if action=='protection' and args.get('status')=='met':
            target=args['target'];scope=text_list(args.get('comparison_scope'),field+'.comparison_scope')
            expected=(state.get('execution_adapter') or {}).get('protected_regions',{}).get(target,[])
            missing=set(expected)-set(scope)
            if missing:raise InputError(field+'.comparison_scope','omits preplanned regions','Compare and include: '+', '.join(sorted(missing)))
            plan=state.get('fidelity_plan',{}).get(target,{})
            if plan.get('strategy') in ('native_preserved','local_excluded') and args.get('content_recreated') is not False:
                raise InputError(field+'.content_recreated','contradicts source-preservation plan','Correct the output or record failed/unverified evidence; do not claim preserved pixels after reconstruction')
    if not review_seen:raise InputError('events','missing actual review','Supply the actual visual/color judgment; the interface never creates one')
