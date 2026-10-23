"""Explicit maintenance only; keep public entrypoints/hashes coherent."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/10_SYSTEM_CONFIG/scripts'))
from sync_entrypoints import synchronize
if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    print(synchronize(ROOT / 'runtime', ROOT))
