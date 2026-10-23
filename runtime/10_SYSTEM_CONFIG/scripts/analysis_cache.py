"""Content-addressed exact analysis cache. Never edits source image pixels."""
from pathlib import Path
import hashlib,json,time,threading
from functools import lru_cache
from importlib.metadata import version
from importlib.util import find_spec
from runtime_io import atomic_json,digest,validate_roi

DEFAULT_CACHE=Path(__file__).resolve().parents[2]/'10_SYSTEM_CONFIG/runtime_cache/analysis'
SCHEMA=1
_pil_spec=find_spec('PIL')
_cms_files=sorted(Path(_pil_spec.origin).parent.glob('_imagingcms*.so')) if _pil_spec else []
_signature=hashlib.sha256(b''.join((Path(__file__).parent/name).read_bytes() for name in ['color_metrics.py','analysis_cache.py','runtime_io.py'])+
    str(tuple(version(name) for name in ['Pillow','numpy','scipy'])).encode()+
    b''.join(hashlib.sha256(p.read_bytes()).digest() for p in _cms_files)).hexdigest()

@lru_cache(maxsize=128)
def _lock(key):return threading.Lock()

def analyze(path,roi=None,*,cache_dir=None,use_cache=True):
    started=time.perf_counter();roi=validate_roi(roi)
    source=Path(path);source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    base={'schema':SCHEMA,'implementation':_signature,'source_sha256':source_hash}
    directory=Path(cache_dir) if cache_dir is not None else DEFAULT_CACHE
    diag={'full_cache_hit':False,'roi_cache_hit':False,'warnings':[]}
    def read(kind,region=None):
        key=digest(dict(base,kind=kind,roi=region));dest=directory/(key+'.json')
        if use_cache:
            try:
                item=json.loads(dest.read_text(encoding='utf-8'))
                if item['key']==key and digest(item['payload'])==item['payload_sha256']:
                    return item['payload'],dest,key
            except (OSError,ValueError,KeyError,TypeError):pass
        return None,dest,key
    def write(dest,key,payload):
        if not use_cache:return
        try:atomic_json(dest,{'key':key,'payload':payload,'payload_sha256':digest(payload)})
        except OSError as error:diag['warnings'].append('Cache unavailable; actual measurement retained: '+type(error).__name__)
    # Coalesce simultaneous requests for the same image; ROI entries share its full analysis.
    with _lock(source_hash):
        full,full_path,full_key=read('full');diag['full_cache_hit']=full is not None
        region,roi_path,roi_key=read('roi',roi) if roi is not None else (None,None,None)
        diag['roi_cache_hit']=roi is not None and region is not None
        if full is None or (roi is not None and region is None):
            from color_metrics import load_image,measure,crop_roi
            image,metadata=load_image(source)
            if metadata['sha256']!=source_hash:raise RuntimeError('Input changed during analysis; reselect the stable source before continuing')
            if full is None:
                full={'metadata':metadata,'measured_full':measure(image)};write(full_path,full_key,full)
            if roi is not None and region is None:
                region=measure(crop_roi(image,roi),palette=False);write(roi_path,roi_key,region)
        result={'metadata':full['metadata'],'measured_full':full['measured_full'],
            'measured_evaluation_roi':region if roi is not None else full['measured_full']}
    diag['seconds']=time.perf_counter()-started
    return result,diag
