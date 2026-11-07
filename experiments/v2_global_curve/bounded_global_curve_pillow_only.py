"""Experimental, non-generative bounded global curve. NOT a shipping controller route.

Input must already be converted via ICC to encoded sRGB RGB. This prototype
uses Pillow and the Python standard library only; no NumPy or private assets.
No photographic acceptance, semantic mask or pixel-protection claim is made.
"""
from bisect import bisect_right
from dataclasses import dataclass
from math import isfinite
from PIL import Image


def encoded_luma(pixel):
    r, g, b = pixel
    return .299*r+.587*g+.114*b


def frame_stats(source):
    if source.mode != 'RGB':
        raise ValueError('color-managed sRGB RGB required')
    data = sorted(encoded_luma(p) for p in source.get_flattened_data())
    if not data:
        raise ValueError('empty input')
    def p(q):
        pos = (len(data)-1)*q/100
        lo = int(pos)
        hi = min(lo+1, len(data)-1)
        return data[lo]*(1-(pos-lo))+data[hi]*(pos-lo)
    return {'p01': p(1), 'p50': p(50), 'p99': p(99)}


def smooth_luma_range_from_reviewed_roi(source, roi):
    """Return sRGB encoded-luma P01..P99 for a pre-reviewed smooth scene ROI.

    This helper only measures pixels. It cannot establish that the selected
    rectangle is truly smooth sky; the scene/ROI must be reviewed externally.
    """
    if source.mode != 'RGB':
        raise ValueError('color-managed RGB source required')
    if (not isinstance(roi,(tuple,list)) or len(roi)!=4 or
            any(type(v)!=int for v in roi)):
        raise ValueError('four integer ROI coordinates required')
    x0,y0,x1,y1=roi
    w,h=source.size
    if not 0<=x0<x1<=w or not 0<=y0<y1<=h or (x1-x0)*(y1-y0)<64:
        raise ValueError('invalid reviewed smooth ROI')
    stats=frame_stats(source.crop(tuple(roi)))
    if stats['p01']>=stats['p99']:
        raise ValueError('smooth ROI has no measurable luminance variation')
    return (stats['p01'],stats['p99'])


def pchip_dense(xs, ys, point_count=2551):
    if (len(xs) != len(ys) or len(xs) < 3 or xs[0] != 0 or xs[-1] != 255 or
            ys[0] != 0 or ys[-1] != 255):
        raise ValueError('invalid fixed endpoints')
    if any(not isfinite(t) for t in list(xs)+list(ys)):
        raise ValueError('nonfinite curve')
    if (any(b<=a for a,b in zip(xs,xs[1:])) or
            any(b<=a for a,b in zip(ys,ys[1:]))):
        raise ValueError('non-increasing knots')
    h = [b-a for a,b in zip(xs,xs[1:])]
    m = [(b-a)/t for a,b,t in zip(ys,ys[1:],h)]
    d = [0.0]*len(xs)
    for i in range(1,len(xs)-1):
        if m[i-1]*m[i] <= 0:
            continue
        w1 = 2*h[i]+h[i-1]
        w2 = h[i]+2*h[i-1]
        d[i] = (w1+w2)/(w1/m[i-1]+w2/m[i])
    d[0] = ((2*h[0]+h[1])*m[0]-h[0]*m[1])/(h[0]+h[1])
    d[-1] = ((2*h[-1]+h[-2])*m[-1]-h[-1]*m[-2])/(h[-1]+h[-2])
    for ix, slope in ((0,m[0]),(-1,m[-1])):
        if d[ix]*slope < 0:
            d[ix] = 0
        if abs(d[ix]) > 3*abs(slope):
            d[ix] = 3*slope
    dx = 255/(point_count-1)
    out = []
    for k in range(point_count):
        x = k*dx
        ix = max(0,min(len(xs)-2,bisect_right(xs,x)-1))
        t = (x-xs[ix])/h[ix]
        y = ((2*t**3-3*t**2+1)*ys[ix]+(t**3-2*t**2+t)*h[ix]*d[ix]+
             (-2*t**3+3*t**2)*ys[ix+1]+(t**3-t**2)*h[ix]*d[ix+1])
        out.append(max(0,min(255,float(y))))
    out[0],out[-1] = 0.,255.
    if any(b+1e-6 < a for a,b in zip(out,out[1:])):
        raise ValueError('nonmonotone result')
    slope = max((b-a)/dx for a,b in zip(out,out[1:]))
    return out,slope


@dataclass(frozen=True)
class CurveParameters:
    input_knots: tuple
    output_knots: tuple
    chroma_multiplier: float = 1.6
    dither_strength: float = .7
    # Required for sky plans; measured from a reviewed smooth source ROI.
    # Other scene types may omit this optional experimental constraint.
    smooth_luma_range: tuple | None = None


def plan_from_stats(p01,p50,p99, *, smooth_luma_range=None):
    """One strictly bounded sky-like experiment, not a universal auto decision."""
    if not (50<p01<100 and 85<p50<130 and 110<p99<175 and p99-p01<85):
        raise ValueError('source outside experimental domain')
    p01o = max(0,min(255,p01-6.7))
    mid = min(255,p50+22.3)
    p99o = min(226,p99+84)
    xs = (0.,max(8,p01-23),p01,p50,p99,p99+26,p99+70,255.)
    ys = (0.,max(4,p01-25),p01o,mid,p99o,min(242,p99o+15),
          min(252,p99o+26),255.)
    if any(b<=a for a,b in zip(xs,xs[1:])) or any(b<=a for a,b in zip(ys,ys[1:])):
        raise ValueError('invalid curve for scene')
    if smooth_luma_range is None:
        raise ValueError('reviewed smooth input-luminance interval required for sky plan')
    return CurveParameters(xs,ys,smooth_luma_range=smooth_luma_range)


def apply_curve(source,params):
    if source.mode != 'RGB':
        raise ValueError('ICC-converted sRGB source required')
    if not (.5<=params.chroma_multiplier<=1.6 and 0<=params.dither_strength<=.75):
        raise ValueError('unbounded strength')
    curve,max_slope = pchip_dense(params.input_knots,params.output_knots)
    if max_slope>3.25:
        raise ValueError('over-steep curve')
    smooth_peak=None
    if params.smooth_luma_range is not None:
        interval=params.smooth_luma_range
        if (not isinstance(interval,(tuple,list)) or len(interval)!=2 or
                any(type(v) not in (int,float) or not isfinite(v) for v in interval)):
            raise ValueError('invalid reviewed smooth input-luminance interval')
        lo,hi=interval
        if not 0<=lo<hi<=255:
            raise ValueError('invalid reviewed smooth input-luminance interval')
        dx=255/(len(curve)-1)
        # Include every LUT segment intersecting the measured smooth range.
        smooth_peak=max((curve[i+1]-curve[i])/dx
                        for i in range(len(curve)-1)
                        if i*dx<hi and (i+1)*dx>lo)
        if smooth_peak>2.5+1e-8:
            raise ValueError('smooth-region curve slope exceeds 2.5')
    def sample(v):
        pos = max(0,min(255,v))*10
        ix = min(2549,int(pos))
        t = pos-ix
        return curve[ix]*(1-t)+curve[ix+1]*t
    w,h = source.size
    out = bytearray(w*h*3)
    limited = 0
    # One zero-mean triangular (TPDF) value per pixel, reused across RGB
    # so neutral skies do not acquire artificial chromatic speckles.
    # Curve/chroma calculations stay floating point until final rounding.
    def unit_hash(seed):
        value=(seed ^ (seed >> 16))*0x7FEB352D & 0xffffffff
        value=(value ^ (value >> 15))*0x846CA68B & 0xffffffff
        return (value ^ (value >> 16))/4294967296.
    for j,(r,g,b) in enumerate(source.get_flattened_data()):
        y = encoded_luma((r,g,b))
        target = sample(y)
        # TPDF = difference of two deterministic uniforms, applied only
        # immediately before final 8-bit rounding (not before chroma limiting).
        dither=0.
        if params.dither_strength:
            x=j%w
            row=j//w
            seed=(x*0x9E3779B1+row*0x85EBCA6B+0x54F4A11)&0xffffffff
            dither=(unit_hash(seed)-unit_hash(seed ^ 0xC2B2AE35))*params.dither_strength
        dif=(r-y,g-y,b-y)
        weight=params.chroma_multiplier
        for d in dif:
            if d>1e-5:
                weight=min(weight,(254.5-target)/d)
            elif d<-1e-5:
                weight=min(weight,target/(-d))
        weight=max(0.,weight)
        if weight+1e-5<params.chroma_multiplier:
            limited+=1
        for ix,d in enumerate(dif):
            out[3*j+ix]=max(0,min(254,round(target+weight*d+dither)))
    return (Image.frombytes('RGB',(w,h),bytes(out)),
            {'max_curve_derivative':max_slope,
             'smooth_interval_max_curve_derivative':smooth_peak,
             'smooth_interval_slope_limit':2.5 if smooth_peak is not None else None,
             'smooth_luma_range':list(params.smooth_luma_range) if smooth_peak is not None else None,
             'chroma_limited_pct':100*limited/(w*h),
             'pixel_count':w*h})

def rgb_gap_report(source, candidate, roi=None):
    """Advisory source-relative 8-bit code gaps for each RGB channel.

    Histogram gaps are not proof of perceptible banding: JPEG quantization,
    small areas and different image ranges can also create missing codes.
    Always review aligned original/candidate 1:1 sky crops.
    """
    if source.mode!='RGB' or candidate.mode!='RGB' or source.size!=candidate.size:
        raise ValueError('same-geometry color-managed RGB required')
    w,h=source.size
    if roi is None:
        roi=(0,0,w,h)
    x0,y0,x1,y1=roi
    if (not all(type(v)==int for v in roi) or not 0<=x0<x1<=w or
            not 0<=y0<y1<=h):
        raise ValueError('invalid same-geometry ROI')
    before=source.crop(roi)
    after=candidate.crop(roi)
    n=(x1-x0)*(y1-y0)
    if n<64:
        raise ValueError('ROI too small for histogram gaps')
    def channel_stats(band):
        counts=band.histogram()
        levels=[]
        for code,count in enumerate(counts):
            levels.extend([code]*count)
        lo=levels[int((n-1)*.01)]
        hi=levels[int((n-1)*.99)]
        interior=max(0,hi-lo-1)
        gap_count=longest=run=0
        for code in range(lo+1,hi):
            if counts[code]==0:
                gap_count+=1
                run+=1
                longest=max(run,longest)
            else:
                run=0
        return {'p01_code':lo,'p99_code':hi,
                'interior_codes':interior,'missing_codes':gap_count,
                'interior_gap_fraction':round(gap_count/interior,6) if interior else 0.,
                'longest_missing_run':longest}
    channels={}
    for name,b,a in zip(('R','G','B'),before.split(),after.split()):
        sb=channel_stats(b)
        sa=channel_stats(a)
        channels[name]={'source':sb,'candidate':sa,
                        'new_gap_fraction':round(sa['interior_gap_fraction']-
                                                 sb['interior_gap_fraction'],6)}
    return {'roi':list(roi),'pixel_count':n,'channels':channels,
            'max_new_gap_fraction':max(v['new_gap_fraction'] for v in channels.values()),
            'interpretation':'advisory only; check aligned 1:1 sky gradients and RGB channel steps'}
