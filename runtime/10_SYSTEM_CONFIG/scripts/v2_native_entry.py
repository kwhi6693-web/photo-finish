"""CLI for inspected, source-linked Photo Finish 2.0 native PNG trials.

Usage via the packaged scripts/run_photo_finish.py wrapper:
  v2_native_entry prepare ORIGINAL WORKING.png LINEAGE.json
  v2_native_entry decide ORIGINAL LINEAGE.json OBSERVATION.json PLAN.json DECISION.json\n  v2_native_entry render ORIGINAL LINEAGE.json PLAN.json ZONES.json OUTPUT.png RECEIPT.json
  v2_native_entry reframe ORIGINAL LINEAGE.json PENDING.png PENDING_RECEIPT.json FRAME_PLAN.json CROPPED.png RECEIPT.json

JSON plans and masks must be made AFTER actual source/mask inspection. They
are not automatically inferred, an edit authorization, a real visual approval
or formal V1/Library persistence. Never pass untrusted external JSON as code.
"""
import argparse
from dataclasses import asdict
from pathlib import Path
import json
import os
import sys
import tempfile

# -I removes the script directory from sys.path; restore only the verified
# installed location rather than using cwd, PYTHONPATH or user site-packages.
_RUNTIME_DIR = str(Path(__file__).resolve().parent)
if _RUNTIME_DIR not in sys.path:
    sys.path.insert(0, _RUNTIME_DIR)

from PIL import Image

from source_lineage import SourceLineage, prepare_working_source, verify_source_lineage
from editorial_contract import EditorialPlan, ProvenCapabilities
from adaptive_route import choose_adaptive_route
from v2_photo_direction import compile_observed_direction
from provider_mask_handoff import import_exact_provider_mask
from native_framing import reframe_pending_native
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


def _require_unused_output(path, extension):
    """Fail before editing if the required output or its receipt already exists."""
    destination=Path(path)
    if destination.suffix.lower()!=extension:
        raise ValueError('invalid destination extension: '+extension)
    parent=destination.parent.resolve(strict=True)
    if not parent.is_dir():
        raise ValueError('output parent must be an existing directory')
    destination=parent/destination.name
    if os.path.lexists(destination):
        raise FileExistsError('destination already exists: '+str(destination))


def _rollback_unreceipted_png(path, expected_sha256, receipt_path):
    """Remove only our verified pending PNG when final receipt never appeared.

    This is crash/error cleanup, not a transactional promise across process
    termination or external actors. Never unlink an occupied receipt or a
    symlink, and never remove a changed output owned by another actor.
    """
    if os.path.lexists(receipt_path):
        return
    target=Path(path)
    if target.is_symlink() or not target.is_file():
        return
    if hash_file(target)==expected_sha256:
        target.unlink()


def prepare(original, working, manifest):
    # Fail before file work if the paths are occupied, then recover safely
    # from a late receipt-write failure without touching any source file.
    _require_unused_output(working,'.png')
    _require_unused_output(manifest,'.json')
    proof=prepare_working_source(original,working)
    record=asdict(proof)
    record['original_size']=list(proof.original_size)
    record['working_size']=list(proof.working_size)
    record['formal_V1_registered']=False
    record['photographic_quality_accepted']=False
    try:
        _exclusive_json(manifest,record)
    except BaseException:
        _rollback_unreceipted_png(proof.working_path,proof.working_sha256,manifest)
        raise
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


def decide(original, lineage_json, observation_json, plan_json, decision_json):
    """Compile a real-photo observation, never fabricate a mask or an edit.

    Source-specific observations must already have been made by an actual
    observer. This adapter only verifies byte lineage and compiles plan logic.
    """
    _require_unused_output(plan_json,'.json')
    _require_unused_output(decision_json,'.json')
    if Path(plan_json).resolve()==Path(decision_json).resolve():
        raise ValueError('plan and decision receipt destinations must differ')
    lineage=_lineage(_load_data(lineage_json))
    if not verify_source_lineage(original,lineage):
        raise ValueError('real source lineage verification required')
    observation_before=hash_file(observation_json)
    observation=_load_data(observation_json)
    result=compile_observed_direction(
        observation,camera_original_sha256=lineage.original_sha256,
        working_source_sha256=lineage.working_sha256)
    if hash_file(observation_json)!=observation_before:
        raise ValueError('visual observation changed during decision')
    plan_path=None
    plan_hash=None
    if result.plan is not None:
        plan_path=_exclusive_json(plan_json,asdict(result.plan))
        plan_hash=hash_file(plan_path)
    record={'status':result.action,'reason':result.reason,
            'camera_original_sha256':lineage.original_sha256,
            'working_source_sha256':lineage.working_sha256,
            'visual_observation_sha256':observation_before,
            'observation_origin':observation.get('observation_origin'),
            'risk_flags':list(result.risk_flags),
            'scene_complexity':result.scene_complexity,
            'source_visually_inspected':result.source_visually_inspected,
            'masks_visually_inspected':False,
            'pending_plan_path':plan_path,'pending_plan_sha256':plan_hash,
            'candidate_sha256':None,'photographic_quality_accepted':False,
            'formal_V1_registered':False}
    try:
        _exclusive_json(decision_json,record)
    except BaseException:
        if plan_path is not None:
            _rollback_unreceipted_png(plan_path,plan_hash,decision_json)
        raise
    return {'stage':result.action,'reason':result.reason,
            'pending_plan_path':plan_path,
            'camera_original_sha256':lineage.original_sha256,
            'masks_visually_inspected':False,
            'photographic_quality_accepted':False,'formal_V1_registered':False}


def ingest_mask(original, lineage_json, provider_source, raw_mask,
                provider_response_json, output, receipt_json):
    """Materialize one authentic, unapproved provider mask in private storage.

    Never fetch a URL, infer semantic reliability, or declare an accepted V1.
    The caller must supply independently acquired full original provider bytes.
    """
    _require_unused_output(output,'.png')
    _require_unused_output(receipt_json,'.json')
    lineage=_lineage(_load_data(lineage_json))
    result=import_exact_provider_mask(
        original,lineage,provider_source,raw_mask,
        _load_data(provider_response_json),output)
    record=asdict(result)
    record['mask_visually_inspected']=False
    record['semantic_mask_accepted']=False
    record['photographic_quality_accepted']=False
    record['formal_V1_registered']=False
    try:
        _exclusive_json(receipt_json,record)
    except BaseException:
        _rollback_unreceipted_png(result.canonical_mask_path,
                                  result.canonical_mask_sha256,receipt_json)
        raise
    return {'stage':result.status,'canonical_mask_path':result.canonical_mask_path,
            'canonical_mask_sha256':result.canonical_mask_sha256,
            'camera_original_sha256':result.camera_original_sha256,
            'semantic_mask_accepted':False,'formal_V1_registered':False}


def reframe(original, lineage_json, native_png, native_receipt_json,
            frame_plan_json, output, receipt_json):
    """Pending native-source pixel crop, never a formal V1 or photo acceptance."""
    _require_unused_output(output,'.png')
    _require_unused_output(receipt_json,'.json')
    lineage=_lineage(_load_data(lineage_json))
    pending=reframe_pending_native(
        original,lineage,native_png,_load_data(native_receipt_json),
        _load_data(frame_plan_json),output)
    try:
        _exclusive_json(receipt_json,asdict(pending))
    except BaseException:
        _rollback_unreceipted_png(pending.output_path,pending.output_sha256,receipt_json)
        raise
    return {'stage':pending.status,'source_sha256':pending.camera_original_sha256,
            'native_png_path':pending.output_path,
            'pending_output_sha256':pending.output_sha256,
            'photographic_quality_accepted':False,'formal_V1_registered':False}


def render(original, lineage_json, plan_json, zones_json, output, receipt_json):
    # Avoid producing an untracked candidate when its receipt path is already
    # occupied. The exporter independently enforces no-overwrite on PNG bytes.
    _require_unused_output(output,'.png')
    _require_unused_output(receipt_json,'.json')
    lineage=_lineage(_load_data(lineage_json))
    plan=EditorialPlan(**_load_data(plan_json))
    mask_plan=_load_data(zones_json)
    if mask_plan.get('source_sha256')!=lineage.working_sha256:
        raise ValueError('mask plan belongs to another working source')
    # The route must be tied to actual camera and color-managed working bytes,
    # before it can write even a retain-original or STOP audit receipt.
    if not verify_source_lineage(original,lineage):
        raise ValueError('real camera/working image identity missing')
    route=choose_adaptive_route(
        plan,observed_source_sha256=lineage.working_sha256,
        source_visually_inspected=mask_plan.get('source_visually_inspected') is True,
        evidence=mask_plan)
    if route.action!='ELIGIBLE_MULTIZONE':
        # Explicit retain-original is not an edited file, nor a formal V1.
        # STOP is a documented refusal, never silently relabeled as retention.
        record={'status':route.action,'route':asdict(route),
                'camera_original_sha256':lineage.original_sha256,
                'working_source_sha256':lineage.working_sha256,
                'candidate_sha256':None,'candidate_path':None,
                'formal_V1_registered':False,'photographic_quality_accepted':False}
        _exclusive_json(receipt_json,record)
        return {'stage':route.action,'reason':route.reason,
                'native_png_path':None,'pending_output_sha256':None,
                'source_sha256':lineage.original_sha256,
                'formal_V1_registered':False,'photographic_quality_accepted':False}
    geometry_id=mask_plan.get('geometry_id')
    if not isinstance(geometry_id,str) or not geometry_id.strip():
        raise ValueError('invalid geometry ID')
    # File SHA, dimensions, and actual mask pixels are audited separately.
    # A supplied reviewer flag alone NEVER certifies an eligible mask.
    zones=_zones(mask_plan)
    with Image.open(lineage.working_path) as image:
        image.load()
        profile=image.info.get('icc_profile')
    pending=run_native_photo_trial(
        original,lineage,plan,zones,
        source_visually_inspected=True,masks_visually_inspected=True,
        capabilities=ProvenCapabilities(True,True,True,True,
                                         verified_local_masks=True,
                                         edge_transition_verified=mask_plan.get('edge_transition_verified') is True),
        geometry_id=geometry_id,expected_icc_bytes=profile,
        destination=output)
    record={'status':pending.status,'route':asdict(route),
            'camera_original_sha256':pending.camera_original_sha256,
            'working_source_sha256':pending.working_source_sha256,
            'candidate_sha256':pending.candidate_sha256,'candidate_path':pending.candidate_path,
            'spatial_direction':pending.spatial_direction,
            'technical_receipt':pending.technical_receipt,
            'formal_V1_registered':False,'photographic_quality_accepted':False}
    try:
        _exclusive_json(receipt_json,record)
    except BaseException:
        _rollback_unreceipted_png(pending.candidate_path,pending.candidate_sha256,receipt_json)
        raise
    return {'stage':pending.status,'route':asdict(route),
            'native_png_path':pending.candidate_path,
            'source_sha256':pending.camera_original_sha256,
            'pending_output_sha256':pending.candidate_sha256,
            'formal_V1_registered':False,'photographic_quality_accepted':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='stage',required=True)
    p=sub.add_parser('prepare')
    for name in ('original','working','manifest'):
        p.add_argument(name)
    d=sub.add_parser('decide')
    for name in ('original','lineage_json','observation_json',
                 'plan_json','decision_json'):
        d.add_argument(name)
    m=sub.add_parser('ingest-mask')
    for name in ('original','lineage_json','provider_source','raw_mask',
                 'provider_response_json','output','receipt_json'):
        m.add_argument(name)
    f=sub.add_parser('reframe')
    for name in ('original','lineage_json','native_png','native_receipt_json',
                 'frame_plan_json','output','receipt_json'):
        f.add_argument(name)
    r=sub.add_parser('render')
    for name in ('original','lineage_json','plan_json','zones_json','output','receipt_json'):
        r.add_argument(name)
    args=parser.parse_args(argv)
    if args.stage=='prepare':
        result=prepare(args.original,args.working,args.manifest)
    elif args.stage=='decide':
        result=decide(args.original,args.lineage_json,args.observation_json,
                      args.plan_json,args.decision_json)
    elif args.stage=='ingest-mask':
        result=ingest_mask(args.original,args.lineage_json,args.provider_source,
                           args.raw_mask,args.provider_response_json,
                           args.output,args.receipt_json)
    elif args.stage=='reframe':
        result=reframe(args.original,args.lineage_json,args.native_png,
                       args.native_receipt_json,args.frame_plan_json,
                       args.output,args.receipt_json)
    else:
        result=render(args.original,args.lineage_json,args.plan_json,
                      args.zones_json,args.output,args.receipt_json)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
