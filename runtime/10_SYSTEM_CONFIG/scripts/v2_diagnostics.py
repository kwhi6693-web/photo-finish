"""Actual local self-test and immutable, same-source photographic diagnostics."""
from io import BytesIO
from pathlib import Path
import json,shutil,sys
from PIL import Image,ImageCms
import PIL
from multizone_editor import _grade
from source_lineage import SourceLineage,verify_source_lineage
from local_edit_qa import tonal_distribution,measure_pixel_change,postrender_defect_report
import v2_delivery as delivery


def native_capabilities():
    from v2_global_operation import SUPPORTED,STRENGTHS
    profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    source=Image.new('RGB',(8,8),(50,80,110));source.info['icc_profile']=profile
    edited=_grade(source,.78,1.0,(-2,2));stream=BytesIO()
    edited.save(stream,format='PNG',icc_profile=profile);stream.seek(0)
    with Image.open(stream) as im:
        im.load();passed=im.tobytes()==edited.tobytes() and im.info['icc_profile']==profile and im.tobytes()!=source.tobytes()
    ImageCms.profileToProfile(source,ImageCms.ImageCmsProfile(BytesIO(profile)),ImageCms.createProfile('sRGB'),outputMode='RGB')
    if int(PIL.__version__.split('.')[0])!=13 or not passed:raise ValueError('native Pillow13 self-test failed')
    return {'status':'LOCAL_RUNTIME_SELFTEST','python':sys.version.split()[0],'pillow':PIL.__version__,
            'native_selftest_passed':True,'local_edge_modes':['soft','pixel_locked','graded'],
            'global_operations':sorted(SUPPORTED),'global_strengths':sorted(STRENGTHS),
            'graded_reach':['source_luma_range','normalized_linear_gradient'],
            'non_generative':True,'semantic_segmentation_verified':False,
            'denoise_verified':False,'arbitrary_provider_alpha_preserved':False,
            'external_binaries':{name:{'detected':bool(shutil.which(name)),'operationally_verified':False}
                                 for name in ('darktable-cli','rawtherapee-cli','gimp')},
            'photographic_quality':'NOT_CERTIFIED_BY_SELFTEST'}


def quality_report(original,lineage_json,candidate,receipt_json,destination):
    receipt_sha=delivery.hash_file(receipt_json)
    raw=delivery.load(lineage_json)
    fields=SourceLineage.__dataclass_fields__
    values={key:raw[key] for key in fields}
    for key in ('original_size','working_size'):values[key]=tuple(values[key])
    lineage=SourceLineage(**values)
    if not verify_source_lineage(original,lineage):raise ValueError('actual source lineage required')
    proof=delivery.load(receipt_json);source=delivery.inspect(original);output=delivery.inspect(candidate,png=True)
    if (proof.get('candidate_sha256')!=output['sha256'] or
            proof.get('camera_original_sha256')!=source['sha256'] or
            proof.get('working_source_sha256')!=lineage.working_sha256 or
            not str(proof.get('status','')).startswith('PENDING') or proof.get('formal_V1_registered') is not False):
        raise ValueError('pending source/output receipt mismatch')
    with Image.open(lineage.working_path) as a,Image.open(candidate) as b:
        a.load();b.load()
        if a.size!=b.size or a.info['icc_profile']!=b.info['icc_profile']:
            raise ValueError('same-geometry managed comparison required; do not rescale unrelated candidates')
        result={'source':source,'candidate':output,'working_source_sha256':lineage.working_sha256,
                'source_distribution':tonal_distribution(a),'candidate_distribution':tonal_distribution(b),
                'actual_changes':measure_pixel_change(a,b,Image.new('L',a.size,255)),
                'postrender_defect_advisory':postrender_defect_report(a,b),
                'user_decision_authority':'UNTOUCHED_SEPARATE_USER_RECORD',
                'defect_scope':'uncalibrated source-relative strong-rim and dark-gradient warnings only',
                'photographic_quality':'PENDING_USER_REVIEW','render_calls':0,'ledger_writes':0,
                'scope':'same-source descriptive measurements; full frame and relevant 1:1 visual review still required'}
    if (not verify_source_lineage(original,lineage) or delivery.hash_file(candidate)!=output['sha256'] or
            delivery.hash_file(receipt_json)!=receipt_sha):
        raise ValueError('quality source, candidate or receipt changed during measurement')
    return delivery.exclusive(destination,result)
