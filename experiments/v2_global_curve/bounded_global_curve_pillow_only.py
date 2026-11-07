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


def plan_from_stats(p01,p50,p99):
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
    return CurveParameters(xs,ys)


def apply_curve(source,params):
    if source.mode != 'RGB':
        raise ValueError('ICC-converted sRGB source required')
    if not (.5<=params.chroma_multiplier<=1.6 and 0<=params.dither_strength<=.75):
        raise ValueError('unbounded strength')
    curve,max_slope = pchip_dense(params.input_knots,params.output_knots)
    if max_slope>3.25:
        raise ValueError('over-steep curve')
    def sample(v):
        pos = max(0,min(255,v))*10
        ix = min(2549,int(pos))
        t = pos-ix
        return curve[ix]*(1-t)+curve[ix+1]*t
    w,h = source.size
    out = bytearray(w*h*3)
    limited = 0
    for j,(r,g,b) in enumerate(source.get_flattened_data()):
        y = encoded_luma((r,g,b))
        target = sample(y)
        if params.dither_strength:
            x=j%w
            row=j//w
            hv=(x*2654435761+row*2246822519+0x54F4A11)&0xffffffff
            hv ^=hv>>13
            hv=(hv*1274126177)&0xffffffff
            hv ^=hv>>16
            target=max(0.,min(254.8,target+(hv/4294967296.-.5)*params.dither_strength))
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
            out[3*j+ix]=max(0,min(254,round(target+weight*d)))
    return (Image.frombytes('RGB',(w,h),bytes(out)),
            {'max_curve_derivative':max_slope,
             'chroma_limited_pct':100*limited/(w*h),
             'pixel_count':w*h})
