"""CLI for inspected, source-linked Photo Finish 2.0 native PNG trials.

Usage via the packaged scripts/run_photo_finish.py wrapper:
  v2_native_entry prepare ORIGINAL WORKING.png LINEAGE.json
  v2_native_entry render ORIGINAL LINEAGE.json PLAN.json ZONES.json OUTPUT.png RECEIPT.json

JSON plans and masks must be made AFTER actual source/mask inspection. They
are not automatically inferred, an edit authorization, a real visual approval
or formal V1/Library persistence. Never pass untrusted external JSON as code.
"""
import argparse
from dataclasses import asdict
from pathlib import Path
import json
import os
import tempfile

from PIL import Image

from source_lineage import SourceLineage, prepare_working_source
from editorial_contract import EditorialPlan, ProvenCapabilities
from multizone_editor import ToneZone
from native_workflow import run_native_photo_trial
from editorial_pipeline import hash_file


def _exclusive_json(path, data):
    target=Path(path)
    if target.suffix.lower()!='.json':
        raise ValueError('actual receipt destination must be JSON')
    parent=target.parent.resolve(strict=True)
    target=parent/target.name
    if os.path.lexists(target):
        raise FileExistsError('do not overwrite a provenance/quality receipt')
    temp=None
    try:
        with tempfile.NamedTemporaryFile('w', dir=parent, encoding='utf-8',
                                         newline='\n', delete=False) as stream:
            temp=Path(stream.name)
            json.dump(data,stream,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)
            stream.write('\n')
        os.link(temp,target)
        return str(target)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def _load_data(path):
    with Path(path).open(encoding='utf-8') as stream:
        result=json.load(stream)
    if not isinstance(result,dict):
        raise ValueError('expected a source-identified JSON object')
    return result


def prepare(original, working, manifest):
    proof=prepare_working_source(original,working)
    record=asdict(proof)
    record['original_size']=list(proof.original_size)
    record['working_size']=list(proof.working_size)
    record['formal_V1_registered']=False
    record['photographic_quality_accepted']=False
    _exclusive_json(manifest,record)
    return {'stage':'working_source_ready_for_actual_mask_review',
            'working_source_sha256':proof.working_sha256,
            'original_sha256':proof.original_sha256,
            'managed_png_path':proof.working_path,
            'lineage_record_path':str(Path(manifest).resolve())}


def _lineage(record):
    keys=SourceLineage.__dataclass_fields__
    values={key:value for key,value in record.items() if key in keys}
    for key in ('original_size','working_size'):
        if key not in values or not isinstance(values[key],list) or len(values[key])!=2:
            raise ValueError('invalid geometry in source lineage')
        values[key]=tuple(values[key])
    return SourceLineage(**values)


def _load_mask(spec,name):
    path=Path(spec[name+'_path'])
    if not path.is_file() or path.is_symlink():
        raise ValueError('actual mask component missing or symlinked: '+name)
    recorded=spec.get(name+'_sha256')
    if hash_file(path)!=recorded:
        raise ValueError('actual mask component changed since visual review: '+name)
    with Image.open(path) as image:
        image.load()
        if image.mode!='L':
            raise ValueError('actual mask component must be L mode: '+name)
        return image.copy()


def _zones(record):
    if not isinstance(record,dict) or record.get('masks_visually_inspected') is not True:
        raise ValueError('real-mask visual inspection is missing')
    defs=record.get('zones')
    if not isinstance(defs,list) or not 2<=len(defs)<=4:
        raise ValueError('two to four separately reviewed zones required')
    result=[]
    for spec in defs:
        if not isinstance(spec,dict) or spec.get('reviewed') is not True:
            raise ValueError('per-region mask review missing')
        result.append(ToneZone(
            name=spec['name'],mask=_load_mask(spec,'mask'),
            core=_load_mask(spec,'core'),allowed=_load_mask(spec,'allowed'),
            protected=_load_mask(spec,'protected'),gamma=spec['gamma'],
            saturation=spec.get('saturation',1.0),purpose=spec['purpose'],
            edge_mode=spec.get('edge_mode','soft'),
            boundary_visually_inspected=spec.get('boundary_visually_inspected',False)))
    return result


def render(original, lineage_json, plan_json, zones_json, output, receipt_json):
    lineage=_lineage(_load_data(lineage_json))
    plan=EditorialPlan(**_load_data(plan_json))
    mask_plan=_load_data(zones_json)
    if mask_plan.get('source_sha256')!=lineage.working_sha256:
        raise ValueError('mask plan belongs to another working source')
    if mask_plan.get('geometry_id')!=str(mask_plan.get('geometry_id','')):
        raise ValueError('invalid geometry ID')
    with Image.open(lineage.working_path) as image:
        image.load()
        profile=image.info.get('icc_profile')
    pending=run_native_photo_trial(
        original,lineage,plan,_zones(mask_plan),
        source_visually_inspected=mask_plan.get('source_visually_inspected') is True,
        masks_visually_inspected=True,
        capabilities=ProvenCapabilities(True,True,True,True,
                                         verified_local_masks=True,
                                         edge_transition_verified=mask_plan.get('edge_transition_verified') is True),
        geometry_id=mask_plan['geometry_id'],expected_icc_bytes=profile,
        destination=output)
    record={'status':pending.status,'camera_original_sha256':pending.camera_original_sha256,
            'working_source_sha256':pending.working_source_sha256,
            'candidate_sha256':pending.candidate_sha256,'candidate_path':pending.candidate_path,
            'spatial_direction':pending.spatial_direction,
            'technical_receipt':pending.technical_receipt,
            'formal_V1_registered':False,'photographic_quality_accepted':False}
    _exclusive_json(receipt_json,record)
    return {'stage':pending.status,'native_png_path':pending.candidate_path,
            'source_sha256':pending.camera_original_sha256,
            'pending_output_sha256':pending.candidate_sha256,
            'formal_V1_registered':False,'photographic_quality_accepted':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='stage',required=True)
    p=sub.add_parser('prepare')
    for name in ('original','working','manifest'):
        p.add_argument(name)
    r=sub.add_parser('render')
    for name in ('original','lineage_json','plan_json','zones_json','output','receipt_json'):
        r.add_argument(name)
    args=parser.parse_args(argv)
    if args.stage=='prepare':
        result=prepare(args.original,args.working,args.manifest)
    else:
        result=render(args.original,args.lineage_json,args.plan_json,
                      args.zones_json,args.output,args.receipt_json)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
