"""Reproducible planning engine. Does not claim to render Adobe's processing pipeline."""
from pathlib import Path
from copy import deepcopy
import argparse,json,math
import time
from concurrent.futures import ThreadPoolExecutor
from runtime_io import validate_roi
from analysis_cache import analyze

ROOT=Path(__file__).resolve().parents[2]

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def choose_parameters(config,tags):
    unknown=set(tags)-set(config['scenes'])
    if unknown:raise ValueError('Unknown scene tags: '+','.join(sorted(unknown)))
    primary=next((c for c in config['composition']['primary_priority'] if c in tags),'L')
    p=deepcopy(config['scenes'][primary]['parameters']); applied=[]
    if 'C' in tags and primary!='C':
        p['Highlights2012']=min(p['Highlights2012'],-35);p['Dehaze']=min(p['Dehaze'],2)
        applied.append('C: protect rain/reflective highlights; no full-preset addition')
    if 'H' in tags and primary!='H':
        p['Highlights2012']=min(p['Highlights2012'],-40);p['Whites2012']=min(p['Whites2012'],-12)
        p['Shadows2012']=max(p['Shadows2012'],15);p['Clarity2012']=min(p['Clarity2012'],3)
        applied.append('H: bounded highlight and shadow protection')
    if 'K' in tags:
        p['PostCropVignetteAmount']=0;p['Dehaze']=min(p['Dehaze'],1)
        applied.append('K: evaluate framing before preserving or cropping; exposure requires scene ROI')
    return primary,p,applied

def distance(a,b):
    # Numeric distance only, no semantic or perceptual-accuracy claim.
    av=[a['median_nonblack_yprime'],a['warm_fraction_eligible'],a['cool_fraction_eligible'],a['yprime_quantiles']['95']]
    bv=[b['median_nonblack_yprime'],b['warm_fraction_eligible'],b['cool_fraction_eligible'],b['yprime_quantiles']['95']]
    return math.sqrt(sum(((x-y)*weight)**2 for x,y,weight in zip(av,bv,[2,1,1,1]))/4)

def match_references(index,metric,tags,exclude_ids=(),exclude_group=None):
    effective_tags=set(tags)-{'L'}
    if not effective_tags:return []  # Unclassified fallback is not semantic evidence.
    candidates=[r for r in index if r['include_in_dna'] and r['id'] not in exclude_ids and r['scene_group']!=exclude_group]
    matched=[r for r in candidates if effective_tags&set(r['tags'])]
    if not matched:return []
    candidates=matched
    ranked=[]
    for r in candidates:
        overlap=effective_tags&set(r['tags'])
        d=distance(metric,r['measured_roi'])
        ranked.append(dict(reference_id=r['id'],filename=r['original_filename'],overlap=sorted(overlap),
                           numerical_distance=round(d,5),reason='Scene-tag overlap first; then ROI tone and warm/cool composition. Human check required.',
                           _key=(-len(overlap),d,-r['style_weight'])))
    ranked.sort(key=lambda r:r['_key'])
    for r in ranked:r.pop('_key')
    return ranked[:3]

def mask_rules(primary,tags):
    masks=[dict(order=1,type='Subject or Object / Brush',region='重要主体，避开灯芯和刻意近黑框景',
       values={'Exposure':.20,'Shadows':12,'Texture':3},range='Exposure 0 to +0.45EV; Shadows 0 to +20',
       condition='仅主体辨识不足且并非有意剪影时启用；日落亭阁/人物剪影不强行提亮',risk='过亮会失去空间关系；先看100%细节与边界')]
    if set(tags)&set(['C','E','F','G','H']):
        masks.append(dict(order=2,type='Luminance Range intersect Brush/Object',region='灯芯周围的亮部与暖窗；不覆盖整面暖墙',values={'Highlights':-25,'Whites':-10,'Saturation':-5},range='Highlights -10 to -40; Whites 0 to -20',condition='仅有亮光源时',risk='压低过多会把发光体变灰；已剪切JPEG不能恢复真实细节'))
    if set(tags)&set(['A','D','E','F']):
        masks.append(dict(order=3,type='Sky subtract foreground',region='实际天空，减去树枝与建筑边缘',values={'Exposure':-.10,'Highlights':-15,'Saturation':-5,'Dehaze':0},range='Exposure -0.25 to +0.15; Saturation -10 to +3',condition='确认天空存在且需要分离时；本例只是操作方案',risk='过度去朦胧和降曝光导致断层，树缘可能出光晕'))
        if primary=='D':
            masks[-1]['values']={'Exposure':0,'Highlights':-10,'Saturation':-3,'Dehaze':0}
            masks[-1]['condition']='自然曙暮光渐变确需修正时；允许天空较亮，不机械降低曝光'
    if 'C' in tags:
        masks.append(dict(order=4,type='Brush or Linear Gradient intersect Luminance Range',region='湿路反射，沿真实反射方向',values={'Exposure':.10,'Highlights':-10,'Clarity':3},range='Exposure 0 to +0.20; Clarity 0 to +5',condition='反射确实存在，且不应强于光源',risk='提亮路面会增噪；不能凭空制造反射'))
    if 'I' in tags:
        masks.append(dict(order=5,type='Color Range intersect Brush/Object',region='实际叶片与树冠；减去车辆、衣物、路牌、天空与灯光',values={'Saturation':-8,'Shadows':8,'Texture':5},range='Saturation -15 to 0; Shadows 0 to +15',condition='实际植被过鲜或失层次，先确认材质而非只按绿色选区',risk='过度降饱和会变灰，负色温会导致蓝叶；选区遗漏会改变绿色主体'))
    if primary=='G':
        masks.append(dict(order=3,type='Object / Brush',region='纸张、书脊与木纹',values={'Exposure':.15,'Saturation':-5,'Texture':5},range='Exposure 0 to +0.3; Saturation -10 to 0',condition='文字与纸张可读性不足',risk='纸张不必校成纯白；不要把木材的暖色去掉'))
    if primary=='J':
        masks.append(dict(order=2,type='Person skin subtract eyes/lips/hair',region='真实皮肤，需检测并人工检查蒙版',values={'Exposure':.20,'Texture':-3,'Clarity':-2,'Saturation':0},range='Exposure 0 to +0.35; Texture -5 to 0',condition='脸部是主体；无面部参考，禁止强行染肤色',risk='肤色尚未验证，勿塑料磨皮或改变人物身份'))
    if 'K' in tags:
        masks.append(dict(order=0,type='Brush / Object selection',region='窗口外有效画面；减去车内、后视镜与伞沿',values={'Exposure':0},range='0 to +0.4 only if subject unreadable',condition='先定义此区域，再判断全局曝光',risk='矩形ROI只是统计区域，不等于可直接使用的精确蒙版'))
    return sorted(masks,key=lambda m:m['order'])

def load_context():
    config=read_json(ROOT/'10_SYSTEM_CONFIG/style_config.json')
    config['composition_policy']=read_json(ROOT/'10_SYSTEM_CONFIG/composition_policy.json')
    policy=read_json(ROOT/'10_SYSTEM_CONFIG/runtime_policy.json')
    config['creative_direction_policy']=policy.get('creative_direction_policy',{})
    return config,read_json(ROOT/'10_SYSTEM_CONFIG/reference_index.json')

def plan(path,tags=(),roi=None,*,cache_dir=None,use_cache=True,context=None,timing=None):
    started=time.perf_counter();t=started
    cfg,index=context if context is not None else load_context()
    context_seconds=time.perf_counter()-t
    tags=list(dict.fromkeys(tags)) or ['L'];primary,p,modifiers=choose_parameters(cfg,tags)
    roi=validate_roi(roi)
    t=time.perf_counter();data,analysis_diag=analyze(path,roi,cache_dir=cache_dir,use_cache=use_cache);analysis_seconds=time.perf_counter()-t
    meta=data['metadata'];full=data['measured_full'];metric=data['measured_evaluation_roi']
    t=time.perf_counter();refs=match_references(index,metric,tags);matching_seconds=time.perf_counter()-t;t=time.perf_counter()
    warnings=['All values DESIGNED. Adobe import/rendering and paired reproduction remain unverified.',
      'Scene labels require visual confirmation; numeric engine does not infer time/weather from darkness.']
    if meta['color_management'].startswith('ASSUMED'):warnings.append('Untagged file: assuming sRGB. Confirm gamut before color-critical use.')
    if full['near_black_allRGB_le4']>.35 and not roi:warnings.append('Large near-black area: possible framing. No automatic exposure reduction; define ROI.')
    if 'K' in tags and not roi:
        exposure=0;warnings.append('K scene without ROI: exposure stays 0 until visible scene is selected.')
    elif refs:
        ref=next(r for r in index if r['id']==refs[0]['reference_id'])
        target=ref['measured_roi']['linear_Y_quantiles']['50'];current=metric['linear_Y_quantiles']['50']
        # Radiometric first approximation, bounded and explicitly not Lightroom-accurate inversion.
        exposure=round(float(max(-.7,min(.7,math.log2(max(target,.004)/max(current,.004))))),2)
        if full['near_black_allRGB_le4']>.35 and not roi:exposure=max(0,exposure)
    else:exposure=0
    p['Exposure2012']=exposure
    if full['any_channel_ge250']>.01:warnings.append('At least 1% pixels have a channel >=250; inspect light sources and existing channel clipping.')
    if not refs:warnings.append('No directly matching reference; current assistant must independently choose photographic direction. Numerical recipe is an optional starting draft.')
    if meta['sha256'] in {r['metadata']['sha256'] for r in index}:warnings.append('Input exactly matches an existing reference. Plan is a non-destructive diagnostic demonstration, not a new untreated original.')
    delta={k:v-cfg['base'][k] for k,v in p.items() if isinstance(v,(int,float)) and isinstance(cfg['base'][k],(int,float))}
    result=dict(role='EDIT_TARGET',style_version=cfg['dna_version'],source=str(path),metadata=meta,
       scene_tags=tags,scene_source='user_or_current_assistant_visual_labels' if tags!=['L'] else 'unclassified_safe_fallback',
       composition_assessment=dict(status=cfg.get('composition_policy',{}).get('default_assessment','REVIEW_REQUIRED'),
          decision=None,assessment_source='Visual assessment required from current assistant or user; numeric engine has not judged framing',
          policy=deepcopy(cfg.get('composition_policy',{})),observed_composition_problem_or_preserve_reason=None,
          expression_goal_and_choice_reason=None,generated_or_removed_regions_if_any=[],
          proposed_operations=[],framing_geometry_if_applicable=None,content_and_resolution_tradeoff=None,
          effect_comparison_if_actually_rendered=None,render_status='NOT_APPLIED'),
       primary_scene=primary,primary_name=cfg['scenes'][primary]['name'],modifiers=modifiers,
       measured_full=full,measured_evaluation_roi=metric,roi=roi,references=refs,
       reference_evidence_limits=[dict(reference_id=m['reference_id'],capabilities=r.get('reference_capabilities',{}),
           scene_evidence_roles=r.get('scene_evidence_roles',{}),individual_note=r['individual_note'])
           for m in refs for r in index if r['id']==m['reference_id']],
       applicable_core_rules=['CORE-01','CORE-02','CORE-03','CORE-04'],
       core_rule_role='advisory_reference' if cfg.get('creative_direction_policy') else 'legacy_style_guidance',
       creative_direction_assessment=dict(status='REVIEW_REQUIRED',direction=None,
          policy=deepcopy(cfg.get('creative_direction_policy',{})),
          assessment_source='Current assistant must choose expression, framing, light, palette and finish; numeric engine has not made artistic judgments'),
       parameter_draft_role='Optional legacy recipe; parameter ranges and reference style are not aesthetic limits under the current creative policy',
       stable_parameters=deepcopy(cfg['base']),scene_patch_absolute=deepcopy(cfg['scenes'][primary]['patch_absolute']),
       image_corrections={'Exposure2012':exposure,'white_balance':'As Shot first; manually neutralize a known neutral surface without erasing lighting',
                         'exposure_method':'Bounded log2 ratio of linear Y ROI medians; heuristic, not Lightroom response inversion'},
       conditional_image_rule_candidates=deepcopy(cfg.get('image_specific_rule_candidates',[])) if set(tags)&{'A','I'} else [],
       final_parameters=p,delta_from_base=delta,parameter_metadata=deepcopy(cfg['parameter_metadata']),
       masks=mask_rules(primary,tags),expected_effect=cfg['scenes'][primary]['rule'],
       manual_checks=['expression, framing, light hierarchy, palette and finish assessed under current creative direction','composition assessed: choose the most expressive framing under current COMPOSITION-01; no original-framing preference','intentional white/skin rendering and recognizable identity checked','no unintended sky banding','intentional light cores versus unwanted halos','100% noise and texture','reference applicability checked without aesthetic veto'],
       warnings=warnings,render_status='NOT_RENDERED; references not modified',reference_index_mutated=False)
    if timing is not None:timing.update(context_seconds=context_seconds,analysis_seconds=analysis_seconds,matching_seconds=matching_seconds,
        parameter_assembly_seconds=time.perf_counter()-t,total_seconds=time.perf_counter()-started,analysis_cache=analysis_diag)
    return result

def plan_batch(requests,*,cache_dir=None,use_cache=True,workers=2):
    if not isinstance(workers,int) or not 1<=workers<=2:raise ValueError('workers must be 1 or 2 to bound full-resolution memory use')
    started=time.perf_counter();context=load_context();context_seconds=time.perf_counter()-started
    def one(item):
        t=time.perf_counter();timing={}
        try:
            result=plan(item['image'],item.get('scenes',()),item.get('roi'),cache_dir=cache_dir,use_cache=use_cache,context=context,timing=timing)
            return {'status':'ok','plan':result,'seconds':time.perf_counter()-t,'timing':timing}
        except (OSError,ValueError,KeyError,TypeError,RuntimeError) as error:
            return {'status':'error','source':item.get('image'),'error_type':type(error).__name__,'message':str(error),'seconds':time.perf_counter()-t}
    if workers==1:results=[one(item) for item in requests]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:results=list(pool.map(one,requests))
    return {'results':results,'seconds':time.perf_counter()-started,'workers':workers,'context_seconds':context_seconds,
       'scope':'Local planning only; scene labels and composition still require visual assessment; no cloud rendering executed'}

def propose(paths,authorized):
    if not authorized:raise ValueError('New reference intake requires explicit authorization. No implicit target-to-reference promotion.')
    from color_metrics import load_image,measure,phash
    idx=read_json(ROOT/'10_SYSTEM_CONFIG/reference_index.json');seen={r['metadata']['sha256']:r['id'] for r in idx}
    n=max(int(r['id'].split('-')[1]) for r in idx)+1;out=[]
    for path in paths:
        im,meta=load_image(path)
        duplicate=seen.get(meta['sha256'])
        rid=duplicate or f'REF-{n:04d}'
        if not duplicate:n+=1;seen[meta['sha256']]=rid
        out.append(dict(proposed_id=rid,source=str(path),role='STYLE_REFERENCE_PROPOSAL',duplicate_of=duplicate,
            metadata=meta,measured=measure(im),phash63=phash(im),include_in_dna=False,
            reason='Needs visual grouping, near-duplicate review, weighted comparison and core-change approval before merge'))
    return dict(proposal_only=True,current_index_unchanged=True,items=out,next_step='Review incremental versus core changes; preserve old config; approve any core changes before a new version')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    a=sub.add_parser('plan');a.add_argument('image');a.add_argument('--scenes',default='');a.add_argument('--roi',default='');a.add_argument('--out',required=True)
    a.add_argument('--no-cache',action='store_true');a.add_argument('--cache-dir')
    c=sub.add_parser('batch-plan');c.add_argument('manifest');c.add_argument('--out',required=True);c.add_argument('--workers',type=int,choices=[1,2],default=2)
    c.add_argument('--no-cache',action='store_true');c.add_argument('--cache-dir')
    b=sub.add_parser('propose-reference');b.add_argument('images',nargs='+');b.add_argument('--authorized',action='store_true');b.add_argument('--out',required=True)
    args=parser.parse_args()
    dest=Path(args.out)
    if dest.exists():parser.error('Output exists; choose a new output path to preserve history')
    if args.command=='plan':
        roi=[float(x) for x in args.roi.split(',')] if args.roi else None
        if roi and (len(roi)!=4 or not all(0<=x<=1 for x in roi) or roi[0]>=roi[2] or roi[1]>=roi[3]):parser.error('ROI must be x0,y0,x1,y1 in [0,1], with positive size')
        result=plan(args.image,[x.strip().upper() for x in args.scenes.split(',') if x.strip()],roi,cache_dir=args.cache_dir,use_cache=not args.no_cache)
    elif args.command=='batch-plan':
        result=plan_batch(read_json(args.manifest),cache_dir=args.cache_dir,use_cache=not args.no_cache,workers=args.workers)
    else:result=propose(args.images,args.authorized)
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8', newline='\n')
    print('Saved',dest)

if __name__=='__main__':main()
