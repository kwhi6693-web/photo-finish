"""Run the packaged controller in a checked, private Python environment."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def runtime_path():
    if sys.platform == 'win32':
        base = Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local')
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library/Application Support'
    else:
        base = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    return base / 'photo-finish/python-runtime'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup', action='store_true', help='Explicitly create runtime and install declared Pillow dependency')
    parser.add_argument('--host-proxy', action='store_true', help='Explicitly opt in to validated loopback HTTPS_PROXY gateway')
    parser.add_argument('entry', choices=['doctor', 'photo_edit', 'workflow_session',
                                        'photo_workflow', 'delivery_adapter', 'delivery_automation'])
    args, remaining = parser.parse_known_args(argv)
    folder = runtime_path()
    python = folder / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    environment.pop('PYTHONPATH', None)
    environment.pop('PYTHONHOME', None)
    if args.setup:
        if not python.is_file(): venv.EnvBuilder(with_pip=True).create(folder)
        subprocess.run([str(python), '-m', 'pip', 'install', 'Pillow>=13.0.0,<14'], env=environment, check=True)
    if not python.is_file():
        parser.error('Private runtime missing; run this entry with --setup first')
    check = subprocess.run([str(python), '-I', '-c',
                            'import PIL; assert 13 <= int(PIL.__version__.split(".")[0]) < 14'],
                           env=environment, capture_output=True)
    if check.returncode:
        parser.error('Private runtime needs Pillow 13; run --setup to repair it')
    if args.host_proxy:
        sys.path.insert(0, str(ROOT / 'runtime/10_SYSTEM_CONFIG/scripts'))
        from verified_proxy import VerifiedProxy
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        VerifiedProxy(proxy)  # Validate before passing the explicit setting onward.
        environment['PHOTO_FINISH_DOWNLOAD_PROXY'] = proxy
    script = (ROOT / 'tools/doctor.py' if args.entry == 'doctor' else
              ROOT / 'runtime/10_SYSTEM_CONFIG/scripts' / (args.entry + '.py'))
    return subprocess.run([str(python), '-B', str(script), *remaining], env=environment).returncode


if __name__ == '__main__':
    raise SystemExit(main())
