"""Advisory post-render checks on *actual* same-source RGB pixels.

These are reproducible indicators, not full perceptual detectors and not
photographic GO. Never modify image bytes or override the existing STOP gates.
"""
from PIL import Image


def _rgb_pair(source, candidate):
    if (not isinstance(source, Image.Image) or not isinstance(candidate, Image.Image)
            or source.mode != 'RGB' or candidate.mode != 'RGB'
            or source.size != candidate.size):
        raise ValueError('actual same-geometry RGB source and candidate required')
    return source.size


def strong_edge_overshoot(source, candidate):
    """Find *new* isolated bright/dark rims beside source-recorded edges.

    A conservative strong-overshoot heuristic: a candidate local extremum
    exceeds its two flanks while the source had an edge but no comparable
    extremum. Does not certify lack of subtle or broad halos.
    """
    width, height = _rgb_pair(source, candidate)
    src = source.convert('L').tobytes()
    dst = candidate.convert('L').tobytes()
    checked = flagged = 0
    largest = 0
    examples = []
    def check(a, b, c, x, y):
        nonlocal checked, flagged, largest
        left, center, right = src[a], src[b], src[c]
        if abs(left-right) < 24 or not min(left,right)-8 <= center <= max(left,right)+8:
            return
        checked += 1
        low, mid, high = dst[a], dst[b], dst[c]
        exceed = max(mid - max(low,high), min(low,high) - mid, 0)
        # Local edit can make a genuine edge more pronounced. Only a new,
        # conspicuous *extremum* that differs from source merits a warning.
        if exceed >= 24 and abs(mid-center) >= 32:
            flagged += 1
            largest = max(largest, exceed)
            if len(examples)<8:examples.append([x,y])
    for y in range(2,height-2,3):
        offset=y*width
        for x in range(2,width-2):
            center=offset+x
            check(center-2,center,center+2,x,y)
    for x in range(2,width-2,3):
        for y in range(2,height-2):
            center=y*width+x
            check(center-2*width,center,center+2*width,x,y)
    return {'strong_edge_overshoot_warning':flagged>=3,
            'candidate_rim_hits':flagged,'eligible_source_edge_samples':checked,
            'largest_new_overshoot_level':largest,'sample_coordinates':examples,
            'method':'new grayscale local-extrema overshoot near high-contrast source edge; stride 3 in perpendicular scan',
            'limit':'strong narrow rims only; subtle, broad, chroma-only halos may be missed; advisory, not perceptual GO'}


def new_dark_gradient_banding(source,candidate):
    """Detect repeated *new* long plateaus and quantized jumps in dark gradients.

    Compare each source channel with its candidate channel, selecting only
    initially smooth, low-light regions; count repeated flattened steps.
    This deliberately does not claim to detect all night-sky color banding.
    """
    width,height=_rgb_pair(source,candidate)
    src=source.tobytes();dst=candidate.tobytes()
    source_luma=source.convert('L').tobytes()
    candidate_luma=candidate.convert('L').tobytes()
    found=0; sampled=0;affected=0; max_step=0; examples=[]
    def scan(start,length,step,orient,line):
        nonlocal found,sampled,affected,max_step
        sampled+=1;line_found=0
        for i in range(3,length-3):
            left=start+(i-1)*step;right=start+i*step
            if max(source_luma[left],source_luma[right],candidate_luma[left],candidate_luma[right])>110:
                continue
            for channel in range(3):
                li=left*3+channel;ri=right*3+channel
                sv0=src[li];sv1=src[ri];ov0=dst[li];ov1=dst[ri]
                new_step=abs(ov0-ov1)
                if new_step<7 or abs(sv0-sv1)>2:
                    continue
                lb=[start+(i-j)*step for j in (3,2,1)]
                rb=[start+(i+j)*step for j in (0,1,2)]
                svals=[src[p*3+channel] for p in lb+rb]
                if max(svals)-min(svals)>5:
                    continue
                avals=[dst[p*3+channel] for p in lb]
                bvals=[dst[p*3+channel] for p in rb]
                if max(avals)-min(avals)>1 or max(bvals)-min(bvals)>1:
                    continue
                found+=1;line_found+=1;max_step=max(max_step,new_step)
                if len(examples)<8:
                    examples.append({'axis':orient,'line':line,'position':i,'channel':'RGB'[channel]})
                break
        if line_found>=3:
            affected+=1
    for y in range(0,height,4):scan(y*width,width,1,'horizontal',y)
    for x in range(0,width,4):scan(x,height,width,'vertical',x)
    return {'new_dark_banding_warning':found>=24 and affected>=6,
            'new_flat_step_hits':found,'sampled_lines':sampled,
            'affected_lines_with_3plus_hits':affected,'max_new_step_level':max_step,
            'sample_locations':examples,
            'method':'source-relative RGB plateau/step survey in dark smooth areas; every fourth row and column',
            'limit':'advisory strong repeated quantization only; pre-existing bands, subtle bands and complex textured color skies can escape'}


def postrender_defect_report(source,candidate):
    """Read-only results; warnings require human 1:1 confirmation."""
    _rgb_pair(source,candidate)
    return {'halo':strong_edge_overshoot(source,candidate),
            'banding':new_dark_gradient_banding(source,candidate),
            'photographic_quality':'NOT_INFERRED',
            'decision':'ADVISORY_REVIEW_NOT_AUTOMATIC_GO_OR_STOP'}
