"""Deterministic reference measurements. No image edits or inferred RAW metadata."""
from pathlib import Path
from io import BytesIO
import hashlib
import numpy as np
from PIL import Image, ImageOps, ImageCms, ExifTags
from runtime_io import validate_roi

VERSION = '1.0.0'

def load_image(path):
    p = Path(path)
    with Image.open(p) as src:
        raw_exif=src.getexif()
        exif = {ExifTags.TAGS.get(k, str(k)): str(v) for k,v in raw_exif.items()}
        nested=raw_exif.get_ifd(34665) if 34665 in raw_exif else {}
        exif.update({ExifTags.TAGS.get(k,str(k)):str(v) for k,v in nested.items()})
        info = dict(src.info)
        fmt, size, mode = src.format, src.size, src.mode
        im = ImageOps.exif_transpose(src).convert('RGB')
    icc = info.get('icc_profile')
    if icc:
        profile = ImageCms.ImageCmsProfile(BytesIO(icc))
        profile_name = ImageCms.getProfileDescription(profile).strip()
        im = ImageCms.profileToProfile(im, profile, ImageCms.createProfile('sRGB'), outputMode='RGB', renderingIntent=1)
        handling = 'embedded ICC converted to sRGB, relative colorimetric; out-of-gamut clipping possible'
    else:
        profile_name = 'sRGB (EXIF ColorSpace=1)' if nested.get(40961)==1 else None
        handling = 'EXIF_declared_sRGB; no embedded ICC transform required' if profile_name else 'ASSUMED_sRGB_UNTAGGED; actual source gamut unknown'
    return im, dict(format=fmt, original_size=list(size), oriented_size=list(im.size), mode=mode,
                    exif=exif, embedded_icc=bool(icc), profile_name=profile_name,
                    color_management=handling, sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def phash(im):
    from scipy.fft import dctn
    a=np.asarray(im.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=float)
    v=dctn(a,norm='ortho')[:8,:8].reshape(-1)[1:]
    return ''.join('1' if x>np.median(v) else '0' for x in v)

def lab(rgb):
    lin=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    xyz=lin @ np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]]).T
    xyz=xyz / np.array([.95047,1,1.08883])
    f=np.where(xyz>(6/29)**3,np.cbrt(xyz),xyz/(3*(6/29)**2)+4/29)
    return np.stack([116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])],axis=-1)

def measure(im, palette=True):
    a=np.asarray(im,dtype=np.float32)/255
    y=a @ np.array([.2126,.7152,.0722],dtype=np.float32) # gamma encoded luma, not luminance
    lin=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    yl=lin @ np.array([.2126729,.7151522,.0721750],dtype=np.float32)
    lstar=np.where(yl>(6/29)**3,116*np.cbrt(yl)-16,yl*(29/3)**3)
    hsv=np.asarray(im.convert('HSV'),dtype=np.float32)/255
    h,s,v=hsv[...,0]*360,hsv[...,1],hsv[...,2]
    eligible=(s>.20)&(v>.12)
    warm=eligible&(h>=10)&(h<65)
    cool=eligible&(h>=160)&(h<265)
    qs=[1,5,10,25,50,75,90,95,99]
    nonblack=y>.04
    bands={}
    for name,mask in [('shadow',y<.1),('midtone',(y>=.1)&(y<.6)),('highlight',y>=.6)]:
        if mask.any():
            pixels=a[mask]
            bands[name]={'fraction':float(mask.mean()),'mean_srgb':np.mean(pixels,axis=0).round(5).tolist(),
                         'median_lab_d65':np.median(lab(pixels[::max(1,len(pixels)//40000)]),axis=0).round(3).tolist()}
        else: bands[name]={'fraction':0,'mean_srgb':None,'median_lab_d65':None}
    thumb=np.asarray(im.convert('L').resize((360,480)),dtype=float)/255
    local_rms=float(np.sqrt((np.diff(thumb,axis=0)**2).mean()+(np.diff(thumb,axis=1)**2).mean()))
    max_rgb=a.max(axis=-1)
    result={'pixels':int(y.size),'yprime_quantiles':dict(zip(map(str,qs),np.quantile(y,np.array(qs)/100).round(6).tolist())),
       'linear_Y_quantiles':dict(zip(map(str,qs),np.quantile(yl,np.array(qs)/100).round(6).tolist())),
       'Lstar_quantiles':dict(zip(map(str,qs),np.quantile(lstar,np.array(qs)/100).round(3).tolist())),
       'near_black_allRGB_le4':float((max_rgb<=4/255).mean()),
       'dark_yprime_le0_10':float((y<=.10).mean()),'white_allRGB_ge250':float((a.min(axis=-1)>=250/255).mean()),
       'any_channel_ge250':float((max_rgb>=250/255).mean()),
       'median_nonblack_yprime':float(np.median(y[nonblack])) if nonblack.any() else 0,
       'mean_hsv_saturation':float(s.mean()),'eligible_color_fraction':float(eligible.mean()),
       'warm_fraction_frame':float(warm.mean()),'cool_fraction_frame':float(cool.mean()),
       'warm_fraction_eligible':float(warm.sum()/max(1,eligible.sum())),
       'cool_fraction_eligible':float(cool.sum()/max(1,eligible.sum())),
       'hue_histogram36_eligible':np.histogram(h[eligible],bins=np.arange(0,361,10))[0].tolist(),
       'luma_histogram32':np.histogram(y,bins=np.linspace(0,1,33))[0].tolist(),
       'tone_bands':bands,'thumbnail_gradient_rms':local_rms}
    if palette:
        from scipy.cluster.vq import kmeans2
        pix=a.reshape(-1,3); sample=pix[::max(1,len(pix)//16000)]
        coords=lab(sample)
        centers,labels=kmeans2(coords,6,iter=25,minit='++',seed=42)
        swatches=[]
        for k in range(6):
            mask=labels==k
            if not mask.any(): continue
            rgb=np.median(sample[mask],axis=0)
            swatches.append({'hex':'#'+''.join(f'{int(round(c*255)):02X}' for c in rgb),
                             'sample_fraction':float(mask.mean()),'median_lab':np.median(coords[mask],axis=0).round(3).tolist()})
        result['palette_lab_kmeans6']=sorted(swatches,key=lambda z:-z['sample_fraction'])
    return result

def crop_roi(im, roi):
    validate_roi(roi)
    w,h=im.size
    box=tuple(int(round(c*d)) for c,d in zip(roi,[w,h,w,h]))
    if box[0]>=box[2] or box[1]>=box[3]:raise ValueError('ROI rounds to zero pixels at this image resolution')
    return im.crop(box)
