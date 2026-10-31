"""Regression tests for conservative kill-matrix completeness handling."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/imp-kill-matrix/scripts/kill_matrix.py"
spec = importlib.util.spec_from_file_location("imp_kill_matrix", SCRIPT)
km = importlib.util.module_from_spec(spec)
spec.loader.exec_module(km)

class KillMatrixAdviceTests(unittest.TestCase):
    def setUp(self):
        self.mutants = [{
            "id": "m1", "location": "src/x.ts:1", "mutator": "arithmetic",
            "description": "", "status": "killed",
            "killed_by": {"t1"}, "covered_by": {"t1", "t2"}
        }]
        self.tests = {
            "t1": {"name": "test one", "file": "x.test.ts"},
            "t2": {"name": "test two", "file": "x.test.ts"}
        }

    def test_unknown_matrix_withholds_pruning(self):
        result = km.analyse(self.mutants, dict(self.tests), None, set(), False)
        self.assertFalse(result["advice"])
        self.assertFalse(result["redundant"])
        self.assertFalse(result["zero_kill"])
        self.assertTrue(result["warnings"])

    def test_incomplete_matrix_withholds_pruning(self):
        result = km.analyse(self.mutants, dict(self.tests), False, set(), False)
        self.assertFalse(result["advice"])

    def test_verified_complete_matrix_enables_diagnostics(self):
        result = km.analyse(self.mutants, dict(self.tests), True, set(), False)
        self.assertTrue(result["advice"])

    def test_explicit_full_matrix_override(self):
        result = km.analyse(self.mutants, dict(self.tests), None, set(), True)
        self.assertTrue(result["advice"])

if __name__ == "__main__":
    unittest.main()
