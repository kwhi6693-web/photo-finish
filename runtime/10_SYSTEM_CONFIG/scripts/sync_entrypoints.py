"""Maintenance-only synchronization from canonical policy and project guides."""
from pathlib import Path
import hashlib,json,re
from runtime_io import atomic_json
from session_brief import build

MIRRORS=('fast_edit_workflow','development_workflow','style_matching_policy','creative_direction_policy',
         'workflow_update_policy','color_delivery_policy','protection_policy','photographic_naturalness_policy','execution_adapter_policy')
GUIDES={'FAST_EDIT_WORKFLOW.md':'fast-edit-workflow.md','CREATIVE_DIRECTION_POLICY.md':'creative-direction.md',
        'DEVELOPMENT_WORKFLOW.md':'professional-development.md','AUTOMATIC_DELIVERY.md':'automatic-delivery.md',
        'PROFESSIONAL_WORKFLOW.md':'professional-workflow.md','DELIVERY_ADAPTER.md':'delivery-adapter.md',
        'NATIVE_ADJUSTMENT_ROUTE.md':'native-adjustment-route.md'}

def synchronize(root,skill=None):
    root=Path(root);cfg=root/'10_SYSTEM_CONFIG';policy=json.loads((cfg/'runtime_policy.json').read_text(encoding='utf-8'));revision=policy['fast_edit_workflow']['revision']
    defaults=policy['beautification_defaults']
    for key in MIRRORS:
        if key in policy:defaults[key]=policy[key]
    defaults['composition']=policy['composition_policy']
    for name in GUIDES:
        path=cfg/name;lines=path.read_text(encoding='utf-8').splitlines(keepends=True)
        # Guide headers describe the current orchestration, not historical releases.
        heading=''.join(lines[:6])
        heading=re.sub(r'\d{4}-\d{2}-\d{2}\.\d+',revision,heading)
        text=heading+''.join(lines[6:])
        if text!=path.read_text(encoding='utf-8'):path.write_text(text, encoding='utf-8', newline='\n')
    for name,title in [('QUICK_START.md','日常执行入口'),('NEW_PHOTO_WORKFLOW.md','新照片现行入口')]:
        (cfg/name).write_text(f'# {title}\n\n执行编排{revision}。复用已加载现行[总规范](../我的照片美化偏好与修图标准.md)；字段按需见[工具与交付接口](DELIVERY_ADAPTER.md)。机器权威runtime_policy.json#/execution_adapter_policy。\n\nphoto_edit.py：实际看原片后prepare合并接入/候选；实际参考判断后submit合并保护/取舍/最终方向/问题/调用登记；真实工具两侧计时，returned合并返回与文件检查；实际全幅/细节终检后review合并证据/验收/可选快照。路径+实际SHA256+检查版本相同才复用正式文件检查；验收重核现行上下文与全部质量/保护条件。\n\n展示、用途接受与保存分开；无权威平台回执pending_confirmation，不等待或重传图。默认逐张只输出最终成片；表达更充分、构图自由、去AI味及题字与原图可见内容一致保留。普通EDIT不跑维护、82项研究、报告或全库导出。\n', encoding='utf-8', newline='\n')
    if skill:
        skill=Path(skill)
        links=dict(GUIDES,**{'NATIVE_ADJUSTMENT_ROUTE.md':'native-adjustment-route.md','COMPOSITION_POLICY.md':'composition-guides.md'})
        for source,target in GUIDES.items():
            text=(cfg/source).read_text(encoding='utf-8')
            for old,new in links.items():text=re.sub(r'\]\('+re.escape(old)+r'(?=[)#])',']('+new,text)
            (skill/'references'/target).write_text(text, encoding='utf-8', newline='\n')
        body=(skill/'SKILL.md').read_text(encoding='utf-8');body=re.sub(r'当前编排\d{4}-\d{2}-\d{2}\.\d+', '当前编排'+revision,body);(skill/'SKILL.md').write_text(body, encoding='utf-8', newline='\n')
        entry=policy['entrypoint_skill'];entry['revision']=revision
        names=set(entry['files'])|{'references/delivery-adapter.md'}
        entry['files']={name:hashlib.sha256((skill/name).read_bytes()).hexdigest() for name in sorted(names)}
    policy['entrypoint_documents']={'我的照片美化偏好与修图标准.md':hashlib.sha256((root/'我的照片美化偏好与修图标准.md').read_bytes()).hexdigest()}
    atomic_json(cfg/'runtime_policy.json',policy)
    for name,key in [('BEAUTIFICATION_POLICY.json','beautification_defaults'),('FAST_EDIT_WORKFLOW.json','fast_edit_workflow'),('DEVELOPMENT_WORKFLOW.json','development_workflow')]:atomic_json(cfg/name,policy[key])
    build(root,cfg/'SESSION_BRIEF.json')
    return {'revision':revision,'generated_entrypoints':2,'skill_guides':len(GUIDES) if skill else 0}

if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    import sys
    payload = json.load(sys.stdin)
    print(json.dumps(synchronize(payload['project_root'], payload.get('skill_root')), ensure_ascii=False))
