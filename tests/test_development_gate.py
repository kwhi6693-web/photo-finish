"""Development checks must protect the real released bytes and test current code separately."""
from contextlib import contextmanager
from pathlib import Path
import subprocess
import tempfile
import unittest

import verify_packages as packages
import verify_release_preparation as preparation


class DevelopmentGateTests(unittest.TestCase):
    @contextmanager
    def checkout(self):
        actual = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            subprocess.run(['git', 'clone', '-q', '--shared', str(actual), str(root)], check=True)
            subprocess.run(['git', 'checkout', '-q', '--detach', 'v1.5.1'], cwd=root, check=True)
            yield root

    def test_changed_development_source_does_not_relabel_frozen_release(self):
        self.assertTrue(callable(getattr(packages, 'released', None)), 'Missing immutable release gate')
        with self.checkout() as root:
            code = root / 'runtime/10_SYSTEM_CONFIG/scripts/experience.py'
            code.write_bytes(code.read_bytes() + b'\n# Synthetic development change\n')
            self.assertEqual(packages.released(root)['scope'], 'immutable_released_source')
            with self.assertRaises(ValueError):
                packages.canonical(root)

    def test_moved_release_tag_and_changed_staged_bytes_are_rejected(self):
        self.assertTrue(callable(getattr(packages, 'released', None)), 'Missing immutable release gate')
        with self.checkout() as root:
            staged = root / 'dist/v1.5.1/photo-finish.zip'
            original = staged.read_bytes()
            staged.write_bytes(b'Synthetic changed staged archive')
            with self.assertRaises(ValueError): packages.released(root)
            staged.write_bytes(original)
            subprocess.run(['git', 'tag', '-f', 'v1.5.1', 'v1.5.0'], cwd=root,
                           check=True, capture_output=True)
            with self.assertRaises(ValueError): packages.released(root)

    def test_current_candidate_is_independently_built_and_loaded(self):
        self.assertIn('candidate', __import__('inspect').signature(preparation.verify).parameters,
                      'Missing current-source candidate installation check')
        actual = Path(__file__).resolve().parents[1]
        result = preparation.verify(actual, candidate=True)
        self.assertEqual(result['scope'], 'development_candidate_not_release')
        self.assertEqual(result['deterministic_builds'], 2)
        self.assertEqual(result['isolated_install']['status'], 'passed')
