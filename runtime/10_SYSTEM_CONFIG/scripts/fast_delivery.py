"""Legacy Lightroom-research export; not the ordinary EDIT record controller.

For current compact records use workflow_session.build_record. This compatibility
interface intentionally requires a complete historical Lightroom design.

Does not re-encode/copy images, render PDF, embed base64, upload, or rebuild style.
"""
from pathlib import Path
import csv,hashlib,json,time,html,os
from runtime_io import atomic_json
from pipeline_timing import Trace

ROOT=Path(__file__).resolve().parents[2]

def build(items,destination,*,project_root=ROOT):
    started_wall=time.time_ns();started=time.perf_counter()
    root=Path(project_root);destination=Path(destination)
    if destination.exists():raise FileExistsError('Preserve prior delivery; choose a new records directory')
    cfg=json.loads((root/'10_SYSTEM_CONFIG/style_config.json').read_text(encoding='utf-8'));records=[];rows=[]
    # Validate every item before publishing records. Files stay in their original locations.
    for item in items:
        source=Path(item['source']);output=Path(item['output']);plan=json.loads(Path(item['plan']).read_text(encoding='utf-8'))
        status=plan.get('visual_fidelity_review',{}).get('status','')
        if not status.startswith('passed'):raise ValueError('Final visual verification is required before delivery')
        source_sha=hashlib.sha256(source.read_bytes()).hexdigest();output_sha=hashlib.sha256(output.read_bytes()).hexdigest()
        if item.get('expected_source_sha256')!=source_sha:raise ValueError('Source does not match the reviewed render input')
        if plan.get('actual_render',{}).get('output_sha256')!=output_sha:raise ValueError('Output does not match the accepted native render')
        values=plan['lightroom_design']['full_parameters']
        if set(values)!=set(cfg['base']):raise ValueError('Complete Lightroom design required')
        records.append({'source':str(source),'source_sha256':source_sha,'output':str(output),'output_sha256':output_sha,'plan':plan})
        for key,value in values.items():
            meta=cfg['parameter_metadata'][key]
            rows.append([plan['source_id'],key,json.dumps(cfg['base'][key],ensure_ascii=False),json.dumps(value,ensure_ascii=False),json.dumps(meta,ensure_ascii=False)])
    if not records:raise ValueError('No reviewed native outputs')
    destination.mkdir(parents=True)
    trace=Trace(destination/'timing')
    with trace.span('delivery_write'):
        manifest=destination/'EDIT_RECORD.json';table=destination/'LIGHTROOM_PARAMETERS.csv';notes=destination/'EDIT_README.md'
        atomic_json(manifest,{'runtime_version':'1.5.0','items':records,'parameters_evidence':'DESIGNED; actual native recipe is recorded separately in each plan',
            'images_reencoded':False,'reference_promotion_authorized':False,'photo_files_are_separate_deliverables':True})
        with table.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(['source_id','parameter','base','recommended','definition_range_conditions_risk']);writer.writerows(rows)
        comparison=destination/'COMPARE.html';pairs=[]
        for record in records:
            source=html.escape(Path(os.path.relpath(record['source'],destination)).as_posix(),quote=True)
            output=html.escape(Path(os.path.relpath(record['output'],destination)).as_posix(),quote=True)
            title=html.escape(record['plan']['source_id'])
            pairs.append(f'<h2>{title}</h2><div class="pair"><figure><figcaption>原图</figcaption><img src="{source}" alt="原图"></figure><figure><figcaption>已验证成片</figcaption><img src="{output}" alt="成片"></figure></div>')
        comparison.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>原图与成片对比</title><style>body{font:16px/1.6 system-ui,sans-serif;max-width:1100px;margin:auto;padding:20px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0}img{width:100%;height:65vh;object-fit:contain;background:#eee}</style><h1>原图与成片</h1><p>使用项目内图片的相对路径，不重编码或嵌入照片。请保留项目目录结构；单独下载此HTML不会包含图片。</p>'+''.join(pairs)+'</html>',encoding='utf-8')
        notes.write_text('# 修图内部记录\n\n默认逐张只展示最终成片，不附说明；本记录及参数、对比仅在用户索取时提供。\n\n成片独立交付，本目录不重复嵌入或压缩照片。EDIT_RECORD.json保留每张完整诊断、参考、三层参数、构图、局部蒙版与实际原生配方；CSV提供全部建议参数及定义。COMPARE.html引用项目内原图/成片，保留目录结构即可并排查看；单独下载HTML不包含照片。只有当次明确要求对比时才展示原图与成片。\n\nLightroom完整参数为DESIGNED，未通过完整Lightroom渲染验证。实际已执行参数与尚未执行的蒙版分别记录。原片与成片不自动进入参考库。\n',encoding='utf-8')
    trace.record('delivery_build',started_wall,time.time_ns(),elapsed_seconds=time.perf_counter()-started)
    return {'manifest':str(manifest),'parameters':str(table),'readme':str(notes),'comparison':str(comparison),'images':[r['output'] for r in records],'timing':trace.summary()}
