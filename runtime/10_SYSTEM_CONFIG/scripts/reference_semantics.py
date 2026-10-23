"""Transparent metadata retrieval, not automatic image understanding or aesthetic scoring."""
VERSION='intent_metadata_v1'
FIELDS=('subject','light','material','expression')
TERMS={
 'architecture':('建筑','立面','塔楼','亭','屋檐','园林','窗','门廊','architecture'),
 'garden':('园林','庭院','亭','松','garden'),
 'foliage':('树','林','枝','叶','植','松','foliage'),
 'water':('湖','河','水面','游船','water'),
 'urban':('城市','街','道路','车辆','车流','路牌','urban'),
 'portrait':('人物','人像','portrait'),
 'sunlight':('日光','受光','晴','斑驳','sunlight'),
 'warm_light':('暖光','暖灯','琥珀','warm_light'),
 'soft_light':('阴天','柔散','低反差','soft_light'),
 'night':('夜景','夜间','night'),
 'wood':('木','wood'), 'stone':('石','stone'), 'tile':('瓦','tile'),
 'glass':('玻璃','glass'), 'metal':('金属','metal'),
 'depth':('层次','前景','中景','远景','depth'),
 'reflection':('反射','倒影','reflection'),
 'low_key':('深黑','剪影','低调','low_key'),
}

def normalize_intent(value):
    if value is None:return {}
    if not isinstance(value,dict) or set(value)-set(FIELDS):raise ValueError('Intent uses subject/light/material/expression lists')
    result={}
    for field,items in value.items():
        if not isinstance(items,list) or len(items)>12 or any(x not in TERMS for x in items):
            raise ValueError('Intent requires supported observed semantic labels')
        result[field]=sorted(set(items))
    return result

def assess(intent,reference):
    text=' '.join(str(reference.get(k,'')) for k in ('subject','individual_note','scene_description'))
    inferred={label for label,words in TERMS.items() if any(word in text for word in words)}
    matches={field:sorted(set(labels)&inferred) for field,labels in intent.items()}
    weights={'subject':4,'light':3,'material':2,'expression':1}
    return {'basis':'index_metadata_inferred; not visual validation','method':VERSION,
            'matches':matches,'unmatched':{f:sorted(set(labels)-inferred) for f,labels in intent.items()},
            'retrieval_score':sum(weights[f]*len(labels) for f,labels in matches.items()),
            'aesthetic_quality_established':False,'match_probability':None}
