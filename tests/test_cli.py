"""Exercise the commands and plotting lesson with the running Python version."""

import csv
import gzip
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "lheanalyzer/lhe_analyzer.py"
PILOT = ROOT / "examples/gg_h_eta0_pilot.lhe.gz"
OBSERVABLES = {"pt_h", "pt_eta0", "m_h_eta0", "y_h", "y_eta0", "delta_phi"}


class CommandLineTests(unittest.TestCase):
    def run_analysis(self, *arguments, module=False, script=SCRIPT):
        command = [sys.executable]
        command += ["-m", "lheanalyzer.lhe_analyzer"] if module else [str(script)]
        return subprocess.run(command + [str(arg) for arg in arguments], cwd=ROOT,
                              capture_output=True, text=True, timeout=90)

    def assert_outputs(self, directory, selected, normalization, observables=OBSERVABLES):
        summary = json.loads((directory / "summary.json").read_text())
        self.assertEqual(summary["input_events"], 100)
        self.assertEqual(summary["selected_events"], selected)
        self.assertEqual(summary["normalization"], normalization)
        self.assertEqual(set(summary["histograms"]), observables)
        self.assertEqual({p.stem for p in directory.glob("*.pdf")}, observables)
        self.assertEqual({p.stem for p in directory.glob("*.png")}, observables)
        for name in observables:
            self.assertTrue((directory / (name + ".pdf")).read_bytes().startswith(b"%PDF"))
            self.assertTrue((directory / (name + ".png")).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        expected = selected / 100
        if normalization == "cross-section":
            expected *= summary["cross_section_pb"]
        with (directory / "histograms.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["observable"] for row in rows}, observables)
        for name in observables:
            integral = 0.0
            for row in rows:
                if row["observable"] == name:
                    density = float(row["density"])
                    error = float(row["density_mc_error"])
                    self.assertTrue(math.isfinite(density) and math.isfinite(error))
                    self.assertGreaterEqual(error, 0)
                    integral += density * (float(row["right"]) - float(row["left"]))
            flow = summary["histograms"][name]
            integral += flow["underflow_integral"] + flow["overflow_integral"]
            self.assertAlmostEqual(integral, expected, delta=1e-12)

    def test_real_sample_entry_points_and_overwrite(self):
        # Both entry points and both LHE formats, with spaces in file paths.
        with tempfile.TemporaryDirectory(prefix="analysis outputs ") as temporary:
            root = Path(temporary)
            destination = root / "plots"
            result = self.run_analysis(PILOT, "pilot", "--output-dir", destination)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_outputs(destination / "pilot", 100, "cross-section")

            original = (destination / "pilot/summary.json").read_bytes()
            duplicate = self.run_analysis(PILOT, "pilot", "--output-dir", destination)
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("non-empty", duplicate.stderr)
            self.assertEqual((destination / "pilot/summary.json").read_bytes(), original)

            overwrite = self.run_analysis(PILOT, "pilot", "--output-dir", destination,
                                          "--overwrite", "--min-pt-h", "100")
            self.assertEqual(overwrite.returncode, 0, overwrite.stderr)
            self.assert_outputs(destination / "pilot", 59, "cross-section")

            plain = root / "event sample.lhe"
            with gzip.open(PILOT, "rb") as handle:
                plain.write_bytes(handle.read())
            result = self.run_analysis(plain, "shape", "--output-dir", destination,
                                       "--normalization", "shape", "--min-pt-h", "100",
                                       module=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_outputs(destination / "shape", 59, "shape")

    def test_help_and_invalid_arguments(self):
        help_result = self.run_analysis("--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("--normalization", help_result.stdout)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "plots"
            cases = [
                ([PILOT, "bad tag"], "tag must start"),
                ([PILOT, "test", "--min-pt-h", "-1"], "finite and non-negative"),
                ([PILOT, "test", "--min-pt-h", "nan"], "finite and non-negative"),
                ([PILOT, "test", "--min-pt-h", "1000000"], "No selected events"),
                ([Path(temporary) / "missing.lhe", "test"], "Analysis failed"),
            ]
            for arguments, message in cases:
                with self.subTest(arguments=arguments):
                    result = self.run_analysis(*arguments, "--output-dir", destination)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(destination.exists())

    def test_readme_pair_rapidity_exercise(self):
        # Use the actual instructions, so documentation and code cannot drift.
        readme = (ROOT / "README.md").read_text()
        code = SCRIPT.read_text()
        markers = ["    selected_weights = []",
                   "        # Add your new calculation and append its value here.",
                   "    # Add your new plot here."]
        for step, marker in enumerate(markers, start=1):
            section = readme.split("### Step {}:".format(step), 1)[1]
            snippet = re.search(r"```python\n(.*?)\n```", section, re.S).group(1)
            self.assertEqual(code.count(marker), 1)
            code = code.replace(marker, snippet + "\n\n" + marker)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            script = directory / "lhe_analyzer.py"
            script.write_text(code)
            shutil.copy2(ROOT / "lheanalyzer/lhe_tools.py", directory / "lhe_tools.py")
            result = self.run_analysis(PILOT, "exercise", "--output-dir", directory,
                                       script=script)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_outputs(directory / "exercise", 100, "cross-section",
                                OBSERVABLES | {"y_pair"})


if __name__ == "__main__":
    unittest.main()
