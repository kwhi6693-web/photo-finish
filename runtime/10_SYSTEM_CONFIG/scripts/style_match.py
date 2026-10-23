"""Read-only source features against frozen reference measurements; never a style verdict.

Pillow only. Analysis thumbnails/color transforms stay in memory. The frozen
index supplies reference measurements; reference photographs need only be
loaded for actual visual selection. No model weights, edits or library writes.
"""
from io import BytesIO
import math
from PIL import Image, ImageCms, ImageOps

VERSION='source_pixel_features_v1'

def features(path, source_sha256):
    with Image.open(path) as original:
        original.load()
        image=ImageOps.exif_transpose(original).convert('RGB')
        image.thumbnail((256,256),Image.Resampling.LANCZOS)
        profile=original.info.get('icc_profile')
        if profile:
            image=ImageCms.profileToProfile(image,ImageCms.ImageCmsProfile(BytesIO(profile)),
                ImageCms.createProfile('sRGB'),outputMode='RGB',renderingIntent=1)
            basis='embedded_ICC_to_sRGB_for_analysis_only'
        else:
            basis='untagged_RGB_assumed_sRGB_for_matching_only; not delivery color evidence'
        hsv_image=image.convert('HSV')
        pixels=list(getattr(image,'get_flattened_data',image.getdata)())
        hsv=list(getattr(hsv_image,'get_flattened_data',hsv_image.getdata)())
        luma=[0]*32;hue=[0]*36;dark=0
        for (r,g,b),(h,s,v) in zip(pixels,hsv):
            y=(.2126*r+.7152*g+.0722*b)/255
            luma[min(31,int(y*32))]+=1;dark+=y<=.1
            if s/255>.2 and v/255>.12:hue[min(35,int(h*36/255))]+=1
        return {'version':VERSION,'source_sha256':source_sha256,'sample_dimensions':list(image.size),
                'color_basis':basis,'luma_histogram32':luma,'hue_histogram36_eligible':hue,
                'mean_hsv_saturation':sum(p[1]/255 for p in hsv)/len(pixels),
                'dark_yprime_le0_10':dark/len(pixels)}

def _normalized(value, size):
    if not isinstance(value,list) or len(value)!=size or any(
        type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in value):
        raise ValueError('Invalid histogram')
    total=sum(value)
    return [v/total for v in value] if total else [0.0]*size

def distance(source, reference):
    """Relative distance, not a probability or semantic/material match."""
    try:
        a,b=(_normalized(x['luma_histogram32'],32) for x in (source,reference))
        cumulative=0;tone=0
        for x,y in zip(a,b):cumulative+=x-y;tone+=abs(cumulative)/32
        a,b=(_normalized(x['hue_histogram36_eligible'],36) for x in (source,reference))
        color=sum(abs(x-y) for x,y in zip(a,b))/2
        scalar=[]
        for key in ('mean_hsv_saturation','dark_yprime_le0_10'):
            values=[x[key] for x in (source,reference)]
            if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in values):raise ValueError('Invalid scalar')
            scalar.append(abs(values[0]-values[1]))
        parts={'tone':tone,'hue':color,'saturation':scalar[0],'shadow_fraction':scalar[1]}
        return {'feature_status':'available','visual_distance':round(.45*tone+.25*color+.15*scalar[0]+.15*scalar[1],8),
                'distance_components':parts}
    except (KeyError,TypeError,ValueError):
        return {'feature_status':'unavailable','visual_distance':None,'distance_components':None}
