"""Run local synthetic protocol/security regressions; never call image services."""
from pathlib import Path
import os,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    import sys
    for _photo_finish_stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(_photo_finish_stream, 'reconfigure'):
            _photo_finish_stream.reconfigure(encoding='utf-8')
    scripts = ROOT / 'runtime/10_SYSTEM_CONFIG/scripts'
    sys.path.insert(0, str(scripts))
    sys.path.insert(0, str(ROOT / 'tools'))
    loader = unittest.TestLoader()
    suite = loader.discover(str(scripts), pattern='verify_*.py')
    suite.addTests(loader.discover(str(ROOT / 'tests'), pattern='test_*.py', top_level_dir=str(ROOT)))
    # A developer's real reference collection must never influence synthetic tests.
    previous = os.environ.get('PHOTO_FINISH_STYLE_LIBRARY')
    try:
        with tempfile.TemporaryDirectory(prefix='photo-finish-tests-') as folder:
            os.environ['PHOTO_FINISH_STYLE_LIBRARY'] = str(Path(folder)/'styles')
            result = unittest.TextTestRunner(verbosity=1).run(suite)
    finally:
        if previous is None:
            os.environ.pop('PHOTO_FINISH_STYLE_LIBRARY', None)
        else:
            os.environ['PHOTO_FINISH_STYLE_LIBRARY'] = previous
    sys.exit(not result.wasSuccessful())
