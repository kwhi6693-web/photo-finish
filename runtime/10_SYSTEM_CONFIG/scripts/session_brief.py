"""Compact assistant entry point with source-hash freshness checks."""
from pathlib import Path
import hashlib,json
from runtime_io import atomic_json

SOURCES=['10_SYSTEM_CONFIG/style_config.json','10_SYSTEM_CONFIG/reference_index.json','05_STYLE_DNA/style_dna.json','10_SYSTEM_CONFIG/runtime_policy.json','10_SYSTEM_CONFIG/composition_policy.json']
DOCUMENT_SOURCES=['我的照片美化偏好与修图标准.md']

def hashes(root):return {p:hashlib.sha256((Path(root)/p).read_bytes()).hexdigest() for p in SOURCES}
def document_hashes(root):return {p:hashlib.sha256((Path(root)/p).read_bytes()).hexdigest() for p in DOCUMENT_SOURCES}

def validate_policy_copies(policy):
    defaults=policy.get('beautification_defaults',{})
    for key in ('fast_edit_workflow','development_workflow','style_matching_policy',
                'creative_direction_policy','workflow_update_policy','color_delivery_policy',
                'protection_policy','photographic_naturalness_policy','execution_adapter_policy'):
        if key in defaults and key in policy and defaults[key]!=policy[key]:
            raise ValueError('Nested policy mirror drift: '+key)
    if 'composition' in defaults and 'composition_policy' in policy and defaults['composition']!=policy['composition_policy']:
        raise ValueError('Nested policy mirror drift: composition')

def creative_fields(policy):
    """Current creative policy overrides legacy aesthetic vetoes, not evidence checks."""
    current=policy.get('creative_direction_policy')
    if not current:return {}
    return {'creative_direction_policy':current,'core_rule_role':'advisory_reference',
            'forbidden':current['execution_integrity']['forbidden']}

def build(root,destination):
    root=Path(root);cfg,index,dna,policy,composition=[json.loads((root/p).read_text(encoding='utf-8')) for p in SOURCES]
    brief={'runtime_version':policy['runtime_version'],'style_config_version':cfg['dna_version'],'reference_count':len(index),'source_hashes':hashes(root),'document_hashes':document_hashes(root),
        'core_rules':dna['core_rules'],'allowed_variation':dna['allowed_variation'],'forbidden':dna['forbidden'],'composition_policy':composition,
        'base':cfg['base'],'scene_priority':cfg['composition']['primary_priority'],
        'scenes':{k:{field:v for field,v in scene.items() if field in ['name','patch_absolute','identification','rule','rule_reliability','reference_ids','raw_temperature_policy','visual_time_certainty']} for k,scene in cfg['scenes'].items()},
        'references':[{k:r.get(k) for k in ['id','relative_path','tags','subject','lighting_inferred','scene_group','individual_note','reference_capabilities']} for r in index],
        'runtime_policy':policy,'use':'Load once per editing task; read matching reference details and actual photos as needed. This brief does not replace the full planning configuration.'}
    current=creative_fields(policy)
    if current:
        brief['legacy_style_forbidden']=dna['forbidden']
        brief.update(current)
    atomic_json(destination,brief);return brief

def load(path,root,return_policy=False):
    brief=json.loads(Path(path).read_text(encoding='utf-8'))
    # One bounded read per authoritative source, shared by hashing and parsing.
    source_bytes={name:(Path(root)/name).read_bytes() for name in SOURCES}
    document_bytes={name:(Path(root)/name).read_bytes() for name in DOCUMENT_SOURCES}
    if brief['source_hashes']!={name:hashlib.sha256(data).hexdigest() for name,data in source_bytes.items()}:raise ValueError('Session brief is stale; rebuild from current sources before use')
    if brief.get('document_hashes')!={name:hashlib.sha256(data).hexdigest() for name,data in document_bytes.items()}:raise ValueError('Session brief document/master context is stale; rebuild and synchronize current sources')
    current_composition=json.loads(source_bytes['10_SYSTEM_CONFIG/composition_policy.json'])
    if brief.get('composition_policy')!=current_composition:raise ValueError('Session brief composition policy is inconsistent with canonical composition source')
    policy=json.loads(source_bytes['10_SYSTEM_CONFIG/runtime_policy.json'])
    validate_policy_copies(policy)
    declared=policy.get('entrypoint_documents',{})
    for name,expected in declared.items():
        if brief['document_hashes'].get(name)!=expected:
            raise ValueError('Master document hash drift: '+name)
    expected=creative_fields(policy)
    if brief.get('creative_direction_policy')!=policy.get('creative_direction_policy'):
        raise ValueError('Session brief creative direction differs from canonical policy')
    if any(brief.get(key)!=value for key,value in expected.items()):
        raise ValueError('Session brief creative constraints differ from canonical policy')
    return (brief,policy) if return_policy else brief
