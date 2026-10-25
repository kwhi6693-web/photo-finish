"""Reproducible local metadata microbenchmark, not host/image-service latency."""
from pathlib import Path
import json,statistics,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts'))
import style_library as s

def benchmark(count=1000,repeats=30):
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)/'private'
        # Metadata-only synthetic catalog: deliberately no photographs/visual claims.
        with s._catalog(root,write=True) as db:
            for i in range(count):
                sha=format(i,'064x')
                entry=dict(id='personal_'+sha,sha256=sha,subject='Synthetic '+str(i),labels=['柔光','旅行'],tags=[],
                           individual_note='metadata benchmark',private_relative_path='images/'+sha+'.png')
                db.execute('INSERT INTO styles VALUES (?,?)',(entry['id'],json.dumps(entry)))
        def sample():
            start=time.perf_counter_ns();rows=s.records(root,query='柔和 旅行');duration=(time.perf_counter_ns()-start)/1e6
            assert len(rows)==count
            return duration
        s._decoded.cache_clear();cold=sample()
        values=[sample() for _ in range(repeats)]
        info=s._decoded.cache_info()
        return dict(scope='local SQLite metadata reads, normalization, keyword expansion; excludes image decode, host, rendering, network and actual end-to-end delivery',
                    python=sys.version.split()[0],records=count,repeats=repeats,cold_ms=cold,warm_median_ms=statistics.median(values),
                    cache_hits=info.hits,cache_misses=info.misses,cache_capacity=info.maxsize)
if __name__=='__main__':print(json.dumps(benchmark(),indent=2))
