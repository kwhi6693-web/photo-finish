"""Reusable native-resolution inspection, not a renderer or visual reviewer.

Requires Pillow in the current runtime. CLI: prepare|check|export-web, one JSON
object on stdin. prepare/check never modify images; export-web writes a separate
metadata-only PNG derivative and preserves source/pixels. Missing or
different ICC, geometry and clipping are observations requiring review, never
an aesthetic score or automatic semantic/visual acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import sys
import time

from PIL import Image, ImageChops, ImageCms
import workflow_session as workflow
from runtime_io import atomic_json
from png_color import declaration, export_web
from style_match import features, distance, VERSION as MATCH_METHOD
import style_library

INSPECTION_VERSION=2


def inspect_image(path):
    identity = workflow._file(path)
    with Image.open(identity['path']) as image:
        image.load()
        profile = image.info.get('icc_profile') or b''
        profile_status = 'missing'
        if profile:
            try:
                ImageCms.ImageCmsProfile(io.BytesIO(profile))
                profile_status = 'parseable'
            except (OSError, ValueError, TypeError):
                profile_status = 'invalid'
        result = dict(identity, inspection_version=INSPECTION_VERSION,format=image.format, mode=image.mode,
                      dimensions=list(image.size), pixels=image.width * image.height,
                      exif_orientation=image.getexif().get(274, 1),
                      icc={'status': profile_status, 'bytes': len(profile),
                           'sha256': hashlib.sha256(profile).hexdigest() if profile else None})
        if image.format == 'PNG':
            with open(identity['path'], 'rb') as stream:
                header = stream.read(26)
            result['sample_depth'] = header[24] if len(header) == 26 else None
        result['color'] = declaration(identity['path'], image, profile_status)
        if image.mode in ('RGB', 'RGBA'):
            rgb = image.convert('RGB')
            channels = rgb.split()
            maximum = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
            minimum = ImageChops.darker(ImageChops.darker(channels[0], channels[1]), channels[2])
            result['clipping'] = {
                'definition': '8-bit decoded RGB code value 255; not proof of lost raw detail',
                'per_channel_255': dict(zip(('R', 'G', 'B'), [band.histogram()[255] for band in channels])),
                'any_channel_255': maximum.histogram()[255],
                'all_channels_255': minimum.histogram()[255]}
        else:
            result['clipping'] = None
    if workflow._file(path)['sha256'] != identity['sha256']:
        raise ValueError('Image changed during inspection')
    return result


@workflow.measured('intake')
def prepare(project_root, source_path, path, started_unix_ns=None,
            expected_workflow_revision=None, observed_skill_revision=None):
    started = time.time_ns() if started_unix_ns is None else started_unix_ns
    if Path(path).exists():
        raise FileExistsError('Job already exists: ' + str(path))
    context_start=time.time_ns();context_mono=time.perf_counter_ns()
    context = workflow.bootstrap(project_root, expected_workflow_revision, observed_skill_revision)
    context_end=time.time_ns();context_seconds=(time.perf_counter_ns()-context_mono)/1e9
    baseline = inspect_image(source_path)
    state = workflow.create_job(path, source_path, context['workflow_revision'], started, context=context)
    if baseline['sha256'] != state['source']['sha256']:
        Path(path).unlink()
        raise ValueError('Source changed during initialization')
    state['source_inspection'] = baseline
    state['context_source_hashes'] = context['source_hashes']
    workflow._save(path, state)
    workflow.record_stage(path,'context_read',context_start,context_end,
                          elapsed_seconds=context_seconds,source='local_monotonic')
    return {'path': str(Path(path).resolve()), 'context': context, 'source': baseline,
            'status': state['status'], 'visual_review_required': True}


@workflow.measured('reference_matching')
def candidates(path, project_root, tags, limit=3, intent=None,
               style_library_root=None, style_query=None, style_ids=None, style_group=None):
    """Scene-filtered pixel-feature rerank; actual visual selection remains required."""
    state = workflow._load(path, editable=True)
    if state.get('direction_workflow')=='reference_first_v1' and state.get('professional_direction'):
        raise ValueError('Reference query is locked with final photographic direction')
    if state['reviews'] or 'first_render' in state['milestones']:
        raise ValueError('Query references before rendering')
    if not isinstance(tags, list) or type(limit) is not int or not 1 <= limit <= 3:
        raise ValueError('Scene tags must be a list; limit must be 1 through 3')
    root = Path(project_root).resolve(strict=True)
    index_path = root/'10_SYSTEM_CONFIG/reference_index.json'
    config = json.loads((root/'10_SYSTEM_CONFIG/style_config.json').read_text(encoding='utf-8'))
    if set(tags) - set(config['scenes']):
        raise ValueError('Unknown scene tags')
    index = json.loads(index_path.read_text(encoding='utf-8'))
    identity = workflow._file(index_path)
    expected = state.get('context_source_hashes',{}).get('10_SYSTEM_CONFIG/reference_index.json')
    if expected is not None and expected != identity['sha256']:
        raise ValueError('Reference index changed since intake')
    if workflow._file(state['source']['path']) != state['source']:
        raise ValueError('Source changed since intake')
    effective = set(tags) - {'L'}
    ranked = [r for r in index if r['include_in_dna'] and effective.intersection(r['tags'])]
    personal = style_library.records(style_library_root, style_query, style_ids, group=style_group)
    # Untagged collections remain usable; explicit user requests override scene hints.
    personal = [r for r in personal if style_ids is not None or style_query is not None or style_group is not None or not effective or
                not set(r['tags'])-{'L'} or effective.intersection(r['tags'])]
    if (style_query is not None or style_group is not None) and not personal:
        raise ValueError('No requested personal style matches the selector and observed scene; resolve the explicit request')
    if style_ids is not None or style_query is not None or style_group is not None:
        ranked = []
    ranked += personal
    prior=state.get('reference_query') or {}
    measured=prior.get('features')
    if not measured or measured.get('version')!=MATCH_METHOD or measured.get('source_sha256')!=state['source']['sha256']:
        measured=features(state['source']['path'],state['source']['sha256']) if ranked else None
    scores={r['id']:distance(measured,r.get('measured_full',{})) for r in ranked}
    from reference_semantics import assess, normalize_intent, VERSION as SEMANTIC_VERSION
    intent=normalize_intent(intent)
    semantic={r['id']:assess(intent,r) for r in ranked}
    ranked.sort(key=lambda r:(r.get('origin') != 'personal', -semantic[r['id']]['retrieval_score'], not r.get('pinned',False), -len(effective.intersection(r['tags'])),
                 scores[r['id']]['visual_distance'] is None,
                 scores[r['id']]['visual_distance'] if scores[r['id']]['visual_distance'] is not None else 1,
                 -r['style_weight'],r['id']))
    if workflow._file(state['source']['path']) != state['source']:
        raise ValueError('Source changed during reference matching')
    shortlisted = []
    unavailable = []
    for reference in ranked:
        if len(shortlisted) == limit:
            break
        if reference.get('origin') == 'personal':
            try:
                style_library.verify(reference)
            except ValueError:
                unavailable.append(reference['id'])
                if style_ids:
                    raise
                continue
        shortlisted.append(reference)
    if (style_query is not None or style_group is not None) and not shortlisted:
        raise ValueError('No requested personal style is available; inspect the missing or changed references')
    query = {'source_sha256':state['source']['sha256'], 'index_sha256':identity['sha256'],
             'tags':tags, 'scope':'Scene-filtered tone/color pixel-feature shortlist, then actual material/light/semantic visual judgment',
             'method':MATCH_METHOD,'features':measured,'semantic_method':SEMANTIC_VERSION,
             'intent':intent,'visual_suitability_established':False,
             'match_probability':None,'limitations':'Relative tone/color distance is not style quality or semantic compatibility. Sparse/no suitable references use professional judgment; no forced transfer.',
             'eligible_count':len(ranked), 'limit':limit,
             'personal_library':{'root':str(style_library.location(style_library_root)),'query':style_query,'requested_ids':style_ids,'group':style_group,
                                 'unavailable_ids':unavailable},
             'candidates':[{'reference_id':r['id'],'filename':r['original_filename'],
                            'overlap':sorted(effective.intersection(r['tags'])),
                            'note':r.get('individual_note',''), 'subject':r.get('subject',''),
                            'library_file_id':r.get('library_file_id'), 'relative_path':r.get('relative_path'),
                            'path':r.get('path'), 'sha256':r.get('sha256'),
                            'origin':r.get('origin','project'), 'labels':r.get('labels',[]),
                            'group':r.get('group',''),'pinned':r.get('pinned',False),'use_for':r.get('use_for',[]),
                            'semantic_evidence':semantic[r['id']], **scores[r['id']]} for r in shortlisted]}
    state['reference_query'] = query
    state['reference_selection'] = None
    workflow._save(path,state)
    return query


@workflow.measured('file_verification')
def check(path, output_path, input_path=None, mask_path=None, geometry_changed=False,
          receipt_path=None):
    workflow._boolean(geometry_changed, 'geometry_changed')
    state = workflow._load(path)
    source = workflow._file(state['source']['path'])
    if source['sha256'] != state['source']['sha256']:
        raise ValueError('Job source changed after initialization')
    baseline = state.get('source_inspection')
    if baseline is None or baseline['sha256'] != source['sha256']:
        baseline = inspect_image(source['path'])
    output = workflow._inspect_output(output_path,(state.get('render_result') or {}).get('inspection'))
    same_geometry = (baseline['dimensions'] == output['dimensions'] and
                     baseline['exif_orientation'] == output['exif_orientation'])
    same_profile = baseline['icc']['sha256'] == output['icc']['sha256']
    comparable = (same_geometry and same_profile and baseline['mode'] == output['mode']
                  and baseline['icc']['status'] == output['icc']['status'] == 'parseable'
                  and baseline['clipping'] is not None and output['clipping'] is not None)
    flags = []
    if not same_geometry and not geometry_changed:
        flags.append('unrecorded_geometry_change')
    if not same_profile:
        flags.append('icc_changed_requires_color_review')
    if output['icc']['status'] != 'parseable':
        flags.append('icc_' + output['icc']['status'])
    if output['color']['status'] != 'declared':
        flags.append('color_space_' + output['color']['status'])
    delta = (output['clipping']['any_channel_255'] - baseline['clipping']['any_channel_255']
             if comparable else None)
    if delta is not None and delta > 0:
        flags.append('clipping_increased_review_before_local_edits')
    locality = None
    if mask_path is not None:
        if input_path is None:
            raise ValueError('A local mask check requires the actual input_path')
        actual_input = workflow._file(input_path)
        workflow._input_hash(state, actual_input['sha256'])
        mask_identity = workflow._file(mask_path)
        with Image.open(input_path) as before, Image.open(output_path) as after, Image.open(mask_path) as mask:
            before.load(); after.load(); mask.load()
            if before.size != after.size or mask.size != before.size or before.mode != after.mode:
                raise ValueError('Local pixel check requires equal dimensions and modes')
            if before.mode not in ('RGB', 'RGBA'):
                raise ValueError('Local pixel check supports RGB/RGBA only')
            if before.info.get('icc_profile') != after.info.get('icc_profile'):
                raise ValueError('Local pixel check requires the same ICC bytes')
            differences = ImageChops.difference(before, after).split()
            changed = differences[0]
            for band in differences[1:]:
                changed = ImageChops.lighter(changed, band)
            changed = changed.point([0] + [255] * 255)
            # Any nonzero mask value is included; this is not semantic proof.
            outside = mask.convert('L').point([255] + [0] * 255)
            outside_changed = ImageChops.multiply(changed, outside).histogram()[255]
            locality = {'input': actual_input, 'mask': mask_identity,
                        'outside_mask_changed_pixels': outside_changed,
                        'semantic_scope_verified': False}
            if outside_changed:
                flags.append('pixels_changed_outside_mask')
        if workflow._file(input_path) != actual_input or workflow._file(mask_path) != mask_identity:
            raise ValueError('Local check inputs changed during inspection')
    if workflow._file(output_path)['sha256'] != output['sha256']:
        raise ValueError('Output changed during inspection')
    result = {'source_sha256': source['sha256'], 'output': output,
              'same_geometry': same_geometry, 'geometry_change_declared': geometry_changed,
              'same_icc_bytes': same_profile, 'clipping_comparable': comparable,
              'any_channel_255_delta': delta, 'locality': locality, 'flags': flags,
              'color_review': {'declaration_status': output['color']['status'],
                               'basis': output['color']['basis'],
                               'calibrated_fidelity_verified': False},
              'visual_review_required': True, 'accepted': False}
    if receipt_path is not None:
        destinations = {Path(item).resolve() for item in
                        (path, source['path'], output_path, input_path, mask_path) if item is not None}
        if Path(receipt_path).resolve() in destinations:
            raise ValueError('Receipt cannot overwrite a job or photograph')
        atomic_json(receipt_path, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'check', 'export-web', 'candidates'))
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError('CLI stdin must be one JSON object')
        result = {'prepare': prepare, 'check': check, 'export-web': export_web,
                  'candidates':candidates}[args.action](**payload)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, OSError, KeyError) as error:
        print(json.dumps({'error': str(error), 'type': type(error).__name__}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    sys.exit(main())
