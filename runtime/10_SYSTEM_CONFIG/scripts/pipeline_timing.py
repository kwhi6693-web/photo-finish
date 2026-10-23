"""Record observed stage times; missing cloud stages remain unmeasured."""
from pathlib import Path
from contextlib import contextmanager
import json,math,time,uuid
from runtime_io import atomic_json

EXPECTED=['context_read','visual_diagnosis','numeric_planning','native_preview','cloud_submit','cloud_render','download','visual_verification','delivery_build','save']

class Trace:
    def __init__(self,directory):self.directory=Path(directory)
    def record(self,stage,start_unix_ns,end_unix_ns,*,source='observed_local',status='ok',error_type=None,elapsed_seconds=None):
        if end_unix_ns<start_unix_ns:raise ValueError('End precedes start')
        seconds=(end_unix_ns-start_unix_ns)/1e9 if elapsed_seconds is None else elapsed_seconds
        if not math.isfinite(seconds) or seconds<0:raise ValueError('Duration must be finite and nonnegative')
        event={'stage':stage,'start_unix_ns':start_unix_ns,'end_unix_ns':end_unix_ns,'seconds':seconds,'source':source,'status':status,'error_type':error_type}
        atomic_json(self.directory/(uuid.uuid4().hex+'.json'),event)
        return event
    @contextmanager
    def span(self,stage):
        wall=time.time_ns();monotonic=time.perf_counter();status='ok';error=None
        try:yield
        except BaseException as exc:status='error';error=type(exc).__name__;raise
        finally:self.record(stage,wall,time.time_ns(),status=status,error_type=error,elapsed_seconds=time.perf_counter()-monotonic)
    def summary(self):
        events=[json.loads(p.read_text()) for p in sorted(self.directory.glob('*.json'))];stages={}
        for event in events:
            stage=stages.setdefault(event['stage'],{'seconds_sum':0,'count':0,'failures':0})
            stage['seconds_sum']+=event['seconds'];stage['count']+=1;stage['failures']+=event['status']!='ok'
        wall=(max(e['end_unix_ns'] for e in events)-min(e['start_unix_ns'] for e in events))/1e9 if events else None
        return {'stages':stages,'observed_span_seconds':wall,'unmeasured_stages':[s for s in EXPECTED if s not in stages],
            'note':'Durations may overlap; stage sums are not end-to-end elapsed time. No missing stage is treated as zero.'}
