"""Numerical post-render diagnostics. Never certify visual or aesthetic quality."""
from PIL import Image, ImageChops, ImageStat


def measure_pixel_change(before, after, region):
    if before.mode!='RGB' or after.mode!='RGB' or before.size!=after.size:
        raise ValueError('same-geometry RGB pixels required for change monitoring')
    if region.mode!='L' or region.size!=before.size:
        raise ValueError('same-geometry region required for change monitoring')
    roi=region.point(lambda v:255 if v else 0)
    count=roi.histogram()[255]
    if not count:
        raise ValueError('nonempty actual region required')
    diff=ImageChops.difference(before,after)
    channels=diff.split()
    any_change=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
    changed=ImageChops.multiply(any_change.point(lambda v:255 if v else 0),roi).histogram()[255]
    stats=ImageStat.Stat(diff,mask=roi)
    maximum=max(ImageChops.multiply(band,roi).getextrema()[1] for band in channels)
    def luma_delta(mask):
        if not mask.getbbox(): return None
        return ImageStat.Stat(after.convert('L'),mask=mask).mean[0]-ImageStat.Stat(before.convert('L'),mask=mask).mean[0]
    foreground=luma_delta(roi)
    background=luma_delta(ImageChops.invert(roi))
    return {
        'region_pixels':count, 'max_abs_channel_delta':maximum,
        'mean_abs_channel_delta':sum(stats.mean)/3,
        'changed_pixel_fraction':changed/count,
        'region_encoded_luma_delta':foreground,
        'background_encoded_luma_delta':background,
        'subject_relative_background_luma_delta':None if background is None else foreground-background,
        'luma_definition':'Pillow RGB-to-L encoded BT.601 approximation, not linear luminance',
        'under_powered':None,
        'under_powered_calibration':'PENDING_REAL_MULTI_CATEGORY_CALIBRATION',
        'diagnostic_notice':'UNDER_POWERED thresholds unavailable; review measured changes and actual photograph',
    }


def inspect_output_edges(before, after, graded, alpha):
    """Test actual output against an alpha/texture-aware mathematical budget.

    Adjacent output edit deltas obey the product-rule bound for alpha times
    the actual tonal effect. Two levels cover composite rounding, plus two
    for independently clamped newly-white RGB channels. This is an arithmetic
    integrity check, not a perceptual halo detector or a calibrated aesthetic
    threshold. Visual full-frame and 1:1 review remains mandatory.
    """
    if (any(im.mode!='RGB' or im.size!=before.size for im in (before,after,graded))
            or alpha.mode!='L' or alpha.size!=before.size):
        raise ValueError('same-geometry RGB output and L alpha required')
    box=alpha.getbbox()
    if box is None: raise ValueError('output edge alpha is empty')
    # Include a one-pixel exterior ring so escaped edits and support edges count.
    x0,y0,x1,y1=box
    box=(max(0,x0-1),max(0,y0-1),min(before.width,x1+1),min(before.height,y1+1))
    b=before.crop(box).tobytes();o=after.crop(box).tobytes();g=graded.crop(box).tobytes()
    a=alpha.crop(box).tobytes();width=box[2]-box[0];height=box[3]-box[1]
    pairs=0;max_step=0;max_excess=0.0;max_composite_error=0.0
    for p,weight in enumerate(a):
        for c in range(3):
            i=p*3+c
            expected=b[i]+weight*(g[i]-b[i])/255
            error=abs(o[i]-expected)
            max_composite_error=max(max_composite_error,error)
            # Half-level rounding plus a one-level newly-white clamp.
            if error>1.51: raise ValueError('actual output edge/composite differs from executed alpha')
        for q in (p+1 if p%width+1<width else -1,p+width if p//width+1<height else -1):
            if q<0 or not (0<a[p]<255 or 0<a[q]<255 or a[p]!=a[q]): continue
            pairs+=1
            for c in range(3):
                i=p*3+c;j=q*3+c
                dp=g[i]-b[i];dq=g[j]-b[j]
                step=abs((o[i]-b[i])-(o[j]-b[j]))
                budget=abs(dp-dq)*max(a[p],a[q])/255+max(abs(dp),abs(dq))*abs(a[p]-a[q])/255+4
                max_step=max(max_step,step);max_excess=max(max_excess,step-budget)
                if step>budget: raise ValueError('actual output edge exceeds texture-aware continuity budget')
    return {'output_edge_qa_passed':True,'boundary_neighbor_pairs':pairs,
            'max_actual_edit_neighbor_step':max_step,'max_budget_excess':max_excess,
            'max_composite_rounding_error':max_composite_error,
            'method':'actual RGB delta / alpha product-rule bound and composite residual',
            'visual_edge_review':'PENDING'}
