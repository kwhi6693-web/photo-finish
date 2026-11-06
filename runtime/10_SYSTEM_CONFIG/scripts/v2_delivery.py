"""Explicit v2 acceptance, host-receipt binding and read-only V1 retrieval.

Host JSON is evidence supplied by the trusted caller, not a signature or an SDK.
Never infers aesthetics, calls a renderer, uploads a file, or edits an old ledger.
External reviewed candidates retain their actual external renderer provenance.
"""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import os
import tempfile

from PIL import Image, ImageCms
from editorial_pipeline import hash_file


def load(path):
    with Path(path).open(encoding='utf-8') as stream:
        value=json.load(stream)
    if not isinstance(value,dict):
        raise ValueError('JSON object required')
    return value


def exclusive(path, record):
    target=Path(path)
    if target.suffix.lower()!='.json':
        raise ValueError('JSON destination required')
    parent=target.parent.resolve(strict=True)
    if any(p.is_symlink() for p in (target,*target.parents)):
        raise ValueError('symlink destination refused')
    target=parent/target.name
    if os.path.lexists(target):
        raise FileExistsError('never overwrite acceptance or version history')
    temp=None
    try:
        with tempfile.NamedTemporaryFile('w',dir=parent,encoding='utf-8',delete=False) as f:
            temp=Path(f.name)
            json.dump(record,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
            f.write('\n');f.flush();os.fsync(f.fileno())
        os.link(temp,target)
    finally:
        if temp is not None:temp.unlink(missing_ok=True)
    return record


def inspect(path, *, png=False):
    p=Path(path)
    if any(v.is_symlink() for v in (p,*p.parents)) or not p.is_file():
        raise ValueError('regular non-symlink image required')
    before=hash_file(p)
    with Image.open(p) as im:
        im.load()
        icc=im.info.get('icc_profile')
        if not icc:raise ValueError('embedded ICC required')
        ImageCms.ImageCmsProfile(BytesIO(icc))
        if png and (im.format!='PNG' or im.mode!='RGB' or im.getexif().get(274,1)!=1):
            raise ValueError('normalized RGB PNG required')
        result={'sha256':before,'bytes':p.stat().st_size,'dimensions':list(im.size),
                'icc_sha256':sha256(icc).hexdigest(),'format':im.format}
    if hash_file(p)!=before:raise ValueError('image changed during inspection')
    return result


def accept(original, candidate, provenance_json, review_json, destination):
    """Bind an already supplied user decision to exact bytes; never self-approve.

    External imports are accepted for delivery only. They do not pass the native
    renderer E2E gate or prove source fidelity without a separate actual audit.
    """
    source=inspect(original);output=inspect(candidate,png=True)
    proof_sha=hash_file(provenance_json);review_sha=hash_file(review_json)
    proof=load(provenance_json);review=load(review_json)
    if (proof.get('camera_original_sha256')!=source['sha256'] or
            proof.get('candidate_sha256')!=output['sha256']):
        raise ValueError('provenance source/output mismatch')
    origin=proof.get('renderer_origin')
    if origin not in ('pr47_native_controller','external_non_generative'):
        raise ValueError('explicit actual renderer origin required')
    if origin=='pr47_native_controller':
        receipt=load(proof['controller_receipt_path'])
        if (hash_file(proof['controller_receipt_path'])!=proof.get('controller_receipt_sha256') or
                receipt.get('camera_original_sha256')!=source['sha256'] or
                receipt.get('candidate_sha256')!=output['sha256'] or
                not str(receipt.get('status','')).startswith('PENDING') or
                receipt.get('formal_V1_registered') is not False):
            raise ValueError('pending native controller receipt mismatch')
    if (review.get('reviewer_role')!='end_user_final_editorial_authority' or
            review.get('user_final_photographic_quality')!='GO' or
            review.get('candidate_sha256')!=output['sha256'] or
            review.get('camera_original_sha256')!=source['sha256'] or
            not isinstance(review.get('decision_reference'),str) or
            not review['decision_reference'].strip()):
        raise ValueError('explicit source-bound end-user GO required')
    if hash_file(provenance_json)!=proof_sha or hash_file(review_json)!=review_sha:
        raise ValueError('acceptance evidence changed during validation')
    return exclusive(destination,{'schema':'photo-finish-v2-accepted/1',
        'source':source,'output':output,'renderer_origin':origin,
        'native_controller_e2e':origin=='pr47_native_controller',
        'provenance':proof,'provenance_sha256':proof_sha,
        'user_review':review,'user_review_sha256':review_sha,
        'third_party_independent_review':False,'formal_V1_registered':False})


def _payloads(value):
    if isinstance(value,dict):
        yield value
        for key in ('structuredContent','result','results','transfers'):
            if key in value:yield from _payloads(value[key])
        for block in value.get('content',[]):
            if isinstance(block,dict) and block.get('type')=='text':
                try:decoded=json.loads(block['text'])
                except (ValueError,KeyError):continue
                yield from _payloads(decoded)
    elif isinstance(value,list):
        for item in value:yield from _payloads(item)


def _readback_entries(value):
    for payload in _payloads(value):
        bindings=payload.get('partial_bindings',{}).get('selected_refs',{})
        for transfer in payload.get('transfers',[]):
            if not isinstance(transfer,dict):continue
            binding=bindings.get(transfer.get('transfer_id'),{})
            if binding and binding.get('library_file_id')!=transfer.get('library_file_id'):
                raise ValueError('host readback binding identity conflict')
            record=dict(transfer)
            if binding.get('workspace_sha256'):
                record['workspace_sha256']=binding['workspace_sha256']
            yield record


def _verified_readback_image(data, image, library_file_id):
    """Verify either host workspace placement or an actual signed-URL transfer.

    Signed-URL transfers have no host workspace path/digest. Bind the official
    materializer's local identity/version xattrs and transfer length, then let
    register/restore enforce the previously accepted, pinned full PNG identity.
    Never rewrite the host response or synthesize a host digest/path.
    """
    path=Path(image).resolve()
    matches=[]
    for entry in _readback_entries(data):
        if entry.get('library_file_id')!=library_file_id:
            continue
        if entry.get('workspace_path')==str(path):
            matches.append((entry,'workspace'))
        elif (entry.get('workspace_path') is None and
              isinstance(entry.get('download_url'),str) and
              entry['download_url'].startswith('https://')):
            version=entry.get('current_version_number')
            size=entry.get('size_bytes')
            if type(version) is not int or version<0 or type(size) is not int or size<0:
                continue
            try:
                local_id=os.getxattr(path,'user.library-file-id').decode('utf-8')
                local_version=os.getxattr(path,'user.library-file-version').decode('ascii')
            except (AttributeError,OSError,UnicodeError):
                continue
            if local_id==library_file_id and local_version==str(version):
                matches.append((entry,'signed_url'))
    if len(matches)!=1:
        raise ValueError('retrieved Library identity mismatch')
    entry,kind=matches[0]
    record=inspect(image,png=True)
    expected=entry.get('workspace_sha256',entry.get('sha256'))
    if kind=='workspace' or expected is not None:
        if expected!=record['sha256']:
            raise ValueError('readback SHA-256 mismatch')
    if kind=='signed_url' and entry['size_bytes']!=record['bytes']:
        raise ValueError('signed-URL materialization length mismatch')
    return record


def saved_identity(save_json, readback_json, image, library_file_id):
    """Require actual successful save plus materialized readback of same ID/bytes."""
    if not isinstance(library_file_id,str) or not library_file_id.startswith('libfile_'):
        raise ValueError('actual Library identity required')
    saved=list(_payloads(load(save_json)))
    if not any(x.get('library_file_id')==library_file_id and
               (x.get('status') in ('succeeded','success','created') or
                x.get('file_id')) and x.get('status') not in ('failed','error','pending')
               and not x.get('isError') for x in saved):
        raise ValueError('successful host save receipt missing')
    return _verified_readback_image(load(readback_json),image,library_file_id)


def register(accepted_json, save_json, readback_json, readback_image,
             library_file_id, destination):
    accepted_sha=hash_file(accepted_json)
    save_sha=hash_file(save_json);readback_sha=hash_file(readback_json)
    accepted=load(accepted_json)
    validate_accepted(accepted)
    output=saved_identity(save_json,readback_json,readback_image,library_file_id)
    if output!=accepted['output']:raise ValueError('saved image differs from accepted output')
    if (hash_file(accepted_json)!=accepted_sha or hash_file(save_json)!=save_sha or
            hash_file(readback_json)!=readback_sha):
        raise ValueError('version evidence changed during validation')
    return exclusive(destination,{'schema':'photo-finish-v2-version/1','label':'V1',
        'parent_version':None,'source':accepted['source'],'output':output,
        'renderer_origin':accepted['renderer_origin'],
        'native_controller_e2e':accepted['native_controller_e2e'],
        'acceptance':accepted,'acceptance_sha256':accepted_sha,
        'library_file_id':library_file_id,'save_receipt_sha256':save_sha,
        'readback_receipt_sha256':readback_sha,'formal_V1_registered':True,
        'iphone_save_confirmed':False,'cross_conversation_restore_verified':False})


def validate_accepted(accepted):
    """Recheck an embedded accepted record before any later version/index write.

    Trusted caller supplies the actual user's decision reference. This is an
    evidence consistency gate, not cryptographic proof of who authored JSON.
    """
    if not isinstance(accepted,dict) or accepted.get('schema')!='photo-finish-v2-accepted/1':
        raise ValueError('v2 acceptance record required')
    source=accepted.get('source',{});output=accepted.get('output',{})
    review=accepted.get('user_review',{});proof=accepted.get('provenance',{})
    if (not source.get('sha256') or not output.get('sha256') or
            review.get('reviewer_role')!='end_user_final_editorial_authority' or
            review.get('user_final_photographic_quality')!='GO' or
            review.get('candidate_sha256')!=output['sha256'] or
            review.get('camera_original_sha256')!=source['sha256'] or
            not isinstance(review.get('decision_reference'),str) or not review['decision_reference'].strip() or
            proof.get('candidate_sha256')!=output['sha256'] or proof.get('camera_original_sha256')!=source['sha256'] or
            accepted.get('renderer_origin') not in ('pr47_native_controller','external_non_generative') or
            accepted.get('renderer_origin')!=proof.get('renderer_origin') or
            accepted.get('native_controller_e2e')!=(accepted.get('renderer_origin')=='pr47_native_controller')):
        raise ValueError('explicit source-bound end-user GO and consistent provenance required')
    return accepted


def audit_pending(original,candidate,receipt_json,save_json,readback_json,readback_image,library_file_id,destination):
    """Audit genuine saved pending bytes, without accepting or registering V1."""
    source=inspect(original);output=inspect(candidate,png=True);receipt=load(receipt_json)
    if (receipt.get('camera_original_sha256')!=source['sha256'] or
            receipt.get('candidate_sha256')!=output['sha256'] or
            not str(receipt.get('status','')).startswith('PENDING') or receipt.get('formal_V1_registered') is not False):
        raise ValueError('actual pending source/output receipt mismatch')
    saved=saved_identity(save_json,readback_json,readback_image,library_file_id)
    if saved!=output:raise ValueError('saved pending file differs from actual candidate')
    return exclusive(destination,{'status':'PENDING_BYTES_AND_LIBRARY_ID_VERIFIED','source':source,'output':output,
        'library_file_id':library_file_id,'user_photographic_GO':'PENDING','formal_V1_registered':False,
        'render_calls':0,'ledger_writes':0,'iphone_save_confirmed':False,
        'cross_conversation_restore_verified':False})


def restore(version_json, expected_version_sha256, readback_json, readback_image):
    """Read-only retrieval; separate conversation scope must be verified by host."""
    if hash_file(version_json)!=expected_version_sha256:
        raise ValueError('retained version record SHA-256 mismatch')
    version=load(version_json)
    if (version.get('schema')!='photo-finish-v2-version/1' or
            version.get('formal_V1_registered') is not True or version.get('label')!='V1'):
        raise ValueError('formal V1 required')
    output=_verified_readback_image(load(readback_json),readback_image,version['library_file_id'])
    if output!=version['output']:
        raise ValueError('retrieved output bytes mismatch')
    if hash_file(version_json)!=expected_version_sha256:
        raise ValueError('version record changed during retrieval')
    return {'status':'VERIFIED_V1_READ_ONLY','label':'V1',
            'path':str(Path(readback_image).resolve()),'output':output,
            'render_calls':0,'ledger_writes':0,
            'cross_conversation_scope':'HOST_MUST_VERIFY_SEPARATELY'}
