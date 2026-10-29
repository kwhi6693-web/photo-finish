"""Anonymous installed-package smoke tests, run only in an isolated subprocess."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import types
import unittest


def verify(skill, tests):
    skill, tests = Path(skill).resolve(), Path(tests).resolve()
    scripts = skill / 'runtime/10_SYSTEM_CONFIG/scripts'
    sys.path.insert(0, str(scripts))
    # Load the installed entrypoint and verify current hashes before exercising protocols.
    doctor_spec = importlib.util.spec_from_file_location('installed_doctor', skill / 'tools/doctor.py')
    doctor = importlib.util.module_from_spec(doctor_spec)
    doctor_spec.loader.exec_module(doctor)
    capability = doctor.check(skill)
    from session_brief import load
    brief = load(skill / 'runtime/10_SYSTEM_CONFIG/SESSION_BRIEF.json', skill / 'runtime')
    if brief['runtime_version'] != '1.5.5':
        raise ValueError('Installed runtime is not v1.5.5')
    # Reuse existing anonymous tests; give their relative paths the installed root.
    # No repository runtime directory is put on sys.path and no test alters the package.
    names = ('test_manual_display', 'test_versions', 'test_save_resume',
             'test_fault_injection_release', 'test_experience', 'test_local_routes')
    suite = unittest.TestSuite()
    for name in names:
        module = types.ModuleType(name)
        module.__file__ = str(skill / 'tests' / (name + '.py'))
        sys.modules[name] = module
        exec(compile((tests / (name + '.py')).read_bytes(), module.__file__, 'exec'), module.__dict__)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise ValueError('Installed anonymous regressions failed or skipped')
    production = ('experience', 'task_history', 'photo_edit', 'photo_workflow',
                  'workflow_session', 'delivery_adapter', 'workflow_integrity', 'session_brief')
    for name in production:
        if not Path(sys.modules[name].__file__).resolve().is_relative_to(scripts):
            raise ValueError('Test loaded runtime outside installed package: ' + name)
    return {'status': 'passed', 'runtime_version': brief['runtime_version'],
            'tests': result.testsRun, 'skipped': len(result.skipped),
            'production_module_origin': 'extracted_package_only',
            'entrypoint_sha256': hashlib.sha256((skill / 'SKILL.md').read_bytes()).hexdigest(),
            'integrity': capability['status'],
            'host_scope': 'isolated_python_loader_not_chatgpt_registration_or_real_display'}


if __name__ == '__main__':
    print(json.dumps(verify(*sys.argv[1:]), ensure_ascii=False))
