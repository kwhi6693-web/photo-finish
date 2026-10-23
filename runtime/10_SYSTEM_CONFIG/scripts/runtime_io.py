"""Small standard-library helpers shared by the photo workflow."""
from pathlib import Path
import hashlib,json,math,os,tempfile

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);name=None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False, newline='\n') as f:
            name=f.name;json.dump(value,f,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        os.replace(name,path)
    finally:
        if name and os.path.exists(name):os.unlink(name)

def validate_roi(roi):
    if roi is None:return None
    if len(roi)!=4 or any(not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=1 for x in roi):
        raise ValueError('ROI must contain four finite coordinates in [0,1]')
    if roi[0]>=roi[2] or roi[1]>=roi[3]:raise ValueError('ROI must have positive width and height')
    return list(roi)
