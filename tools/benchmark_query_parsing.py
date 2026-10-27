"""Rejected query-only prototype; never installs a cache into runtime source.

Local metadata benchmark only; no host, editor, network or real photographs.
"""
import json
import re
import statistics
import sys
from functools import lru_cache
from pathlib import Path
import benchmark_metadata as baseline
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/10_SYSTEM_CONFIG/scripts'))
import style_library as styles

@lru_cache(maxsize=256)
def groups(query, synonyms):
    query=query.casefold()
    for filler in ('找那种','帮我找','适合','的参考','的风格','参考照片'):
        query=query.replace(filler,' ')
    result=[]
    for aliases in synonyms:
        found=False
        for word in sorted(aliases,key=len,reverse=True):
            if word in query:query=query.replace(word,' ');found=True
        if found:result.append(aliases)
    result.extend((word,) for word in re.split(r'[\s、，,。；;！？]+',query) if word)
    return tuple(result)

def prototype(query,text):
    terms=groups(query,styles.SYNONYMS);text=text.casefold()
    return bool(terms) and all(any(word in text for word in aliases) for aliases in terms)

def benchmark():
    original=styles._matches
    queries=['柔和 旅行','找那种宁静的参考','QUIET','的参考','建筑 夜景']
    texts=['柔光旅游','宁静木质','quiet room','建筑夜景','']
    assert all(original(q,t)==prototype(q,t) for q in queries for t in texts)
    results=[]
    try:
        for i in range(6):
            order=[('before',original),('after',prototype)]
            for name,fn in (order if i%2==0 else order[::-1]):
                styles._matches=fn
                result=baseline.benchmark(count=1000,repeats=15)
                results.append(dict(result,variant=name))
    finally:styles._matches=original
    return dict(scope='local metadata only; no persisted runtime optimization',results=results,
                summary={n:statistics.median(x['warm_median_ms'] for x in results if x['variant']==n) for n in ('before','after')},
                query_cache=str(groups.cache_info()),external_calls=0)

if __name__=='__main__':print(json.dumps(benchmark(),indent=2))
