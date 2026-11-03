"""All daily controllers use the same checked interpreter without implicit setup."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('controller_launcher', Path(__file__).resolve().parents[1] / 'scripts/run_photo_finish.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def test_daily_entries_share_checked_runtime_and_forward_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);python=root/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
            python.parent.mkdir();python.touch()
            for entry in ('photo_edit','workflow_session','photo_workflow','delivery_adapter','delivery_automation','doctor'):
                with self.subTest(entry=entry),patch.object(launcher,'runtime_path',return_value=root),patch.object(launcher.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
                    self.assertEqual(launcher.main([entry,'status']),0)
                    self.assertEqual(run.call_count,2)
                    self.assertEqual(run.call_args_list[0].args[0][:2],[str(python),'-I'])
                    child=run.call_args_list[1]
                    self.assertEqual(child.args[0][:2],[str(python),'-B'])
                    self.assertEqual(child.args[0][-1],'status')
                    self.assertNotIn('PYTHONPATH',child.kwargs['env'])
                    self.assertEqual(child.kwargs['env']['PYTHONDONTWRITEBYTECODE'],'1')

    def test_incompatible_runtime_never_starts_controller_or_installs_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);python=root/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
            python.parent.mkdir();python.touch()
            with patch.object(launcher,'runtime_path',return_value=root),patch.object(launcher.subprocess,'run',return_value=subprocess.CompletedProcess([],1)) as run:
                with self.assertRaises(SystemExit):launcher.main(['photo_edit','prepare'])
                self.assertEqual(run.call_count,1)
