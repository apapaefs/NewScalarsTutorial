"""Reconstruction, selection, normalisation, and executable worksheet checks."""

import csv
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

import numpy as np

from lheanalyzer.lhe_analyzer import invariant_mass
from lheanalyzer.lhe_four_lepton import analyze
from lheanalyzer.lhe_tools import Particle, histogram, read_lhe

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/gg_h_eta0_2e2mu_toy.lhe"
STARTER = ROOT / "lheanalyzer/lhe_four_lepton.py"
GUIDE = ROOT / "docs/four_lepton.md"


def completed_source(additions=2):
    """Apply the guide snippets for one or both new masses, in worksheet order."""
    snippets = re.findall(r"<!-- exercise: (lists|calculations|plots) -->\n"
                          r"```python\n(.*?)\n```", GUIDE.read_text(), re.S)
    if len(snippets) != 6:
        raise AssertionError("Expected three guide snippets for each new mass.")
    source = STARTER.read_text()
    for kind, code in snippets[:3 * additions]:
        marker = next(line for line in source.splitlines()
                      if line.lstrip().startswith(f"# EXERCISE {kind.upper()}:"))
        source = source.replace(marker, code + "\n" + marker, 1)
    return source


def completed_module():
    module = types.ModuleType("lheanalyzer.completed_four_lepton")
    module.__package__ = "lheanalyzer"
    exec(compile(completed_source(), str(STARTER), "exec"), module.__dict__)
    return module


def decay_tables(text):
    """Read the width and branching rows needed for the benchmark checks."""
    widths, branches = {}, {}
    current = None
    for line in text.splitlines():
        fields = line.split("#", 1)[0].split()
        if not fields:
            continue
        if fields[0].upper() == "DECAY":
            current = int(fields[1])
            widths[current] = float(fields[2])
            branches[current] = {}
        elif fields[0].upper() == "BLOCK" or fields[0].startswith("<"):
            current = None
        elif current is not None:
            daughters = tuple(sorted(int(p) for p in fields[2:]))
            branches[current][daughters] = float(fields[0])
    return widths, branches


class FourLeptonTests(unittest.TestCase):
    def setUp(self):
        self.sample = read_lhe(FIXTURE)

    def test_reconstruction_and_status_filtering(self):
        complete = completed_module()
        events = [list(event) + [Particle(25, 2, 0, 0, 0, 125, 125)]
                  for event in self.sample.events]
        output, weights, checks, flow = complete.analyze(events, self.sample.weights)
        np.testing.assert_allclose(output["m_ee"], 90, atol=1e-9)
        np.testing.assert_allclose(output["m_mumu"], 90, atol=1e-9)
        np.testing.assert_allclose(output["m_4l"], 400, atol=1e-9)
        self.assertEqual(weights, [2., 1., -.5])
        self.assertEqual([len(w) for w in flow.values()], [3, 3, 3])
        self.assertLess(checks["max_four_momentum_residual_GeV"], 1e-10)

    def test_topology_and_cutflow_with_signed_weights(self):
        invalid = [p._replace(pdg=22) if p.pdg == 13 else p
                   for p in self.sample.events[0]]
        output, selected, _, flow = analyze(
            self.sample.events + [invalid], self.sample.weights + [4.], 10.)
        self.assertEqual([len(w) for w in flow.values()], [4, 3, 2])
        self.assertEqual(selected, [1., -.5])
        self.assertEqual(len(output["m_ee"]), 2)
        self.assertEqual(math.fsum(flow["input"]), 6.5)
        self.assertEqual(math.fsum(flow["correct_final_state"]), 2.5)
        self.assertEqual(math.fsum(flow["lepton_pt"]), .5)
        with self.assertRaisesRegex(ValueError, "No compatible events"):
            analyze([invalid], [1.])
        extra = self.sample.events[0] + [Particle(22, 1, 0, 0, 0, 0, 0)]
        with self.assertRaisesRegex(ValueError, "No compatible events"):
            analyze([extra], [1.])
        decayed_h = [p._replace(status=2) if p.pdg == 25 else p
                     for p in self.sample.events[0]]
        with self.assertRaisesRegex(ValueError, "stable Higgs"):
            analyze([decayed_h], [1.])

    def test_threshold_boundary_and_empty_selection(self):
        _, selected, _, _ = analyze(self.sample.events, self.sample.weights, 45.)
        self.assertEqual(selected, [1.])
        output, selected, _, flow = analyze(self.sample.events, self.sample.weights, 1e6)
        self.assertEqual(output["m_ee"], [])
        self.assertEqual(selected, [])
        self.assertEqual(len(flow["correct_final_state"]), 3)
        self.assertEqual(flow["lepton_pt"], [])
        for threshold in (-1, float("nan"), float("inf")):
            with self.assertRaisesRegex(ValueError, "finite and non-negative"):
                analyze(self.sample.events, self.sample.weights, threshold)

    def test_complete_worksheet_cli_and_normalisation(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "completed_four_lepton.py"
            script.write_text(completed_source())
            environment = dict(os.environ, PYTHONPATH=str(ROOT / "lheanalyzer"))
            cases = [("cross-section", 0, 3, 8.),
                     ("cross-section", 10, 2, 1.6),
                     ("shape", 10, 2, .2),
                     ("cross-section", 1e6, 0, 0.)]
            for index, (mode, cut, count, integral) in enumerate(cases):
                with self.subTest(mode=mode, cut=cut):
                    tag = f"check_{index}"
                    subprocess.run([sys.executable, str(script), str(FIXTURE), tag,
                                    "--output-dir", directory, "--normalization", mode,
                                    "--min-lepton-pt", str(cut)], env=environment,
                                   check=True, capture_output=True, text=True)
                    destination = Path(directory) / tag
                    summary = json.loads((destination / "summary.json").read_text())
                    self.assertEqual(summary["selected_events"], count)
                    self.assertTrue(summary["selection"]["higgs_stable"])
                    self.assertNotIn("min_pt_h_GeV", summary)
                    self.assertEqual(len(list(destination.glob("*.png"))), 3)
                    self.assertEqual(len(list(destination.glob("*.pdf"))), 3)
                    with (destination / "histograms.csv").open() as handle:
                        rows = list(csv.DictReader(handle))
                    for observable in ("m_ee", "m_mumu", "m_4l"):
                        plotted = sum(float(r["density"]) * (float(r["right"]) - float(r["left"]))
                                      for r in rows if r["observable"] == observable)
                        flow = summary["histograms"][observable]
                        plotted += flow["underflow_integral"] + flow["overflow_integral"]
                        self.assertAlmostEqual(plotted, integral)
                    with (destination / "cutflow.csv").open() as handle:
                        stages = list(csv.DictReader(handle))
                    self.assertEqual(int(stages[-1]["events"]), count)
                    self.assertAlmostEqual(float(stages[-1]["cross_section_pb"]),
                                           summary["selected_cross_section_pb"])
                    expected_sumw2 = 5.25 if cut == 0 else (1.25 if count else 0.)
                    self.assertAlmostEqual(float(stages[-1]["sumw2"]), expected_sumw2)

    def test_starter_cli_and_output_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, str(STARTER), str(FIXTURE), "starter",
                       "--output-dir", directory]
            subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertEqual(len(list((Path(directory) / "starter").glob("*.png"))), 1)
            repeated = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("--overwrite", repeated.stderr)
            invalid = subprocess.run(command + ["--min-lepton-pt", "nan"],
                                     capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("finite and non-negative", invalid.stderr)

    def test_beginner_walkthrough_commands(self):
        commands = re.findall(r"<!-- student-command: (\w+) -->\n"
                              r"```bash\n(.*?)\n```", GUIDE.read_text(), re.S)
        self.assertEqual([stage for stage, _ in commands],
                         ["start", "two_masses", "complete", "cut"])
        steps = [(STARTER.read_text(), {"m_ee"}, 100),
                 (completed_source(additions=1), {"m_ee", "m_mumu"}, 100),
                 (completed_source(), {"m_ee", "m_mumu", "m_4l"}, 100),
                 (completed_source(), {"m_ee", "m_mumu", "m_4l"}, 95)]
        with tempfile.TemporaryDirectory(prefix="four_lepton_walkthrough_") as directory:
            workspace = Path(directory)
            (workspace / "lheanalyzer").mkdir()
            (workspace / "examples").mkdir()
            for name in ("lhe_tools.py", "lhe_analyzer.py"):
                shutil.copy2(ROOT / "lheanalyzer" / name, workspace / "lheanalyzer" / name)
            sample_name = "gg_h_eta0_2e2mu_pilot.lhe.gz"
            shutil.copy2(ROOT / "examples" / sample_name, workspace / "examples" / sample_name)
            for (stage, command), (source, observables, count) in zip(commands, steps, strict=True):
                with self.subTest(stage=stage):
                    (workspace / "lheanalyzer/lhe_four_lepton.py").write_text(source)
                    args = shlex.split(command)
                    args[0] = sys.executable
                    run = subprocess.run(args, cwd=workspace, capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    destination = workspace / "results" / args[3]
                    summary = json.loads((destination / "summary.json").read_text())
                    self.assertEqual(summary["selected_events"], count)
                    self.assertEqual([row["events"] for row in summary["cutflow"]],
                                     [100, 100, count])
                    for extension in ("png", "pdf"):
                        self.assertEqual({p.stem for p in destination.glob(f"*.{extension}")},
                                         observables)
                    self.assertIn(str(destination / "m_ee.png"), run.stdout)

    def test_mass_histogram_flow_and_squared_weights(self):
        _, selected, _, _ = analyze(self.sample.events, self.sample.weights, 10.)
        weights = np.asarray(selected) * self.sample.cross_section_pb / math.fsum(self.sample.weights)
        sumw, sumw2, density, error, flow = histogram([90., 120.], weights, [80., 100.])
        self.assertAlmostEqual(sumw[0], 3.2)
        self.assertAlmostEqual(sumw2[0], 3.2**2)
        self.assertAlmostEqual(error[0], 3.2 / 20)
        self.assertAlmostEqual(density[0] * 20 + flow["overflow_integral"], 1.6)

    def test_benchmark_widths_against_analytic_formulas(self):
        card = ROOT / "cards/param_card_gg_h_eta0_2e2mu.dat"
        widths, br = decay_tables(card.read_text())
        self.assertEqual(widths[6], 0.)
        self.assertEqual(widths[25], 0.)
        for pdg in (23, 99925):
            self.assertGreater(widths[pdg], 0.)
            self.assertAlmostEqual(sum(br[pdg].values()), 1., places=6)
        m, mh, mz, gf, stheta, kap112 = 400., 125., 91.188, 1.16639e-5, .2, 100.
        gamma_hh = (2 * kap112)**2 / (32 * math.pi * m) * math.sqrt(1 - 4 * mh**2 / m**2)
        x = mz**2 / m**2
        gamma_zz = (gf * m**3 * stheta**2 / (16 * math.pi * math.sqrt(2))
                    * math.sqrt(1 - 4*x) * (1 - 4*x + 12*x*x))
        self.assertAlmostEqual(widths[99925] * br[99925][(25, 25)] / gamma_hh,
                               1., delta=2e-5)
        self.assertAlmostEqual(widths[99925] * br[99925][(23, 23)] / gamma_zz,
                               1., delta=2e-5)

    def test_actual_decayed_pilot(self):
        path = ROOT / "examples/gg_h_eta0_2e2mu_pilot.lhe.gz"
        metadata = json.loads(path.with_name("gg_h_eta0_2e2mu_pilot.json").read_text())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), metadata["sha256"])
        sample = read_lhe(path)
        self.assertEqual(len(sample.events), 100)
        self.assertTrue(all(w > 0 for w in sample.weights))
        complete = completed_module()
        output, selected, checks, _ = complete.analyze(sample.events, sample.weights)
        self.assertEqual(len(selected), 100)
        np.testing.assert_allclose(output["m_4l"], 400., rtol=0, atol=1e-5)
        self.assertLess(checks["max_four_momentum_residual_GeV"], 1e-5)
        for event in sample.events:
            self.assertEqual(sorted(p.pdg for p in event if p.status == 1),
                             [-13, -11, 11, 13, 25])
            self.assertEqual(len([p for p in event if p.status == 2 and p.pdg == 99925]), 1)
            h = next(p for p in event if p.status == 1 and p.pdg == 25)
            self.assertAlmostEqual(invariant_mass(h.energy, h.px, h.py, h.pz),
                                   125., delta=1e-5)
        with gzip.open(path, "rt") as handle:
            text = handle.read()
        slha = re.search(r"<slha>(.*?)</slha>", text, re.S).group(1)
        widths, br = decay_tables(slha)
        self.assertEqual(widths[25], 0.)
        factorised_br = br[99925][(23, 23)] * 2 * br[23][(-11, 11)] * br[23][(-13, 13)]
        factor = sample.cross_section_pb / metadata["production_cross_section_pb"]
        self.assertAlmostEqual(factor, metadata["decay_branching_factor"], delta=1e-10)
        # A broad diagnostic includes finite-Z-width/BW-window effects and catches
        # a missing factor of two. It is not a precision decay prediction test.
        self.assertAlmostEqual(factor / factorised_br, 1., delta=.1)
        self.assertAlmostEqual(math.fsum(sample.weights) / sample.cross_section_pb,
                               1., delta=2e-6)
        _, cut, _, _ = complete.analyze(sample.events, sample.weights, 10.)
        self.assertEqual(len(cut), metadata["selected_events_pt10"])


if __name__ == "__main__":
    unittest.main()
