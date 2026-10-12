"""Physics/normalisation regression checks; no MadGraph installation required."""

import gzip
import csv
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from lheanalyzer.lhe_analyzer import analyze, invariant_mass
from lheanalyzer.lhe_tools import Particle, histogram, read_lhe, readlhefile

FIXTURE = Path(__file__).parent / "fixtures/gg_h_eta0_toy.lhe"


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.sample = read_lhe(FIXTURE)

    def test_plain_gzip_and_upstream_interface(self):
        # The fixture includes a <generator> line after the numeric init rows,
        # as in an actual MadGraph 3.5.16 LHE v3 file.
        with tempfile.TemporaryDirectory() as directory:
            compressed = Path(directory) / "events.lhe.gz"
            with gzip.open(compressed, "wt") as handle:
                handle.write(FIXTURE.read_text())
            self.assertEqual(read_lhe(compressed), self.sample)
        events, weights, variations = readlhefile(FIXTURE)
        self.assertEqual(len(events), 3)
        self.assertEqual(weights, [2.0, 1.0, -0.5])
        self.assertAlmostEqual(variations[0]["scale_test"], 2.2)
        self.assertEqual(self.sample.cross_section_pb, 8.0)

    def test_kinematics_and_outgoing_status(self):
        # Intermediate copies must not be mistaken for outgoing Higgs bosons.
        events = [list(event) + [Particle(25, 2, 0, 0, 0, 125, 125)]
                  for event in self.sample.events]
        output, weights, checks = analyze(events, self.sample.weights)
        self.assertEqual(output["pt_h"], [50, 200, 100])
        self.assertEqual(output["pt_h"], output["pt_eta0"])
        np.testing.assert_allclose(output["delta_phi"], math.pi)
        self.assertTrue(all(m >= 525 for m in output["m_h_eta0"]))
        self.assertLess(checks["max_four_momentum_residual_GeV"], 1e-10)
        self.assertEqual(checks["max_pair_pt_GeV"], 0)
        self.assertEqual(weights, self.sample.weights)
        h = self.sample.events[0][2]
        self.assertAlmostEqual(invariant_mass(h.energy, h.px, h.py, h.pz), 125)

    def test_mismatched_event_weights_are_rejected(self):
        # Missing or extra weights must not silently drop events or alter rates.
        for weights in (self.sample.weights[:-1], self.sample.weights + [1.0]):
            with self.subTest(number_of_weights=len(weights)):
                with self.assertRaisesRegex(ValueError, "exactly one weight"):
                    analyze(self.sample.events, weights)

    def test_actual_madgraph_3516_pilot(self):
        pilot = read_lhe(FIXTURE.parents[2] / "examples/gg_h_eta0_pilot.lhe.gz")
        self.assertEqual(len(pilot.events), 100)
        self.assertEqual(pilot.weight_strategy, -3)
        self.assertEqual(pilot.process_id, 0)
        self.assertAlmostEqual(math.fsum(pilot.weights), pilot.cross_section_pb)
        output, weights, checks = analyze(pilot.events, pilot.weights)
        self.assertEqual(len(weights), 100)
        self.assertGreaterEqual(min(output["m_h_eta0"]), 525 - 1e-6)
        self.assertLess(checks["max_four_momentum_residual_GeV"], 1e-6)
        np.testing.assert_allclose(output["pt_h"], output["pt_eta0"])
        np.testing.assert_allclose(output["delta_phi"], math.pi)

    def test_signed_weights_sumw2_and_cut_normalisation(self):
        output, selected, _ = analyze(self.sample.events, self.sample.weights)
        edges = np.array([0., 100., 200., 300.])
        sumw, sumw2, density, error, flow = histogram(
            output["pt_h"], np.asarray(selected) * 8.0 / 2.5, edges)
        np.testing.assert_allclose(sumw, [6.4, -1.6, 3.2])
        np.testing.assert_allclose(sumw2, [40.96, 2.56, 10.24])
        np.testing.assert_allclose(error, np.sqrt(sumw2) / 100)
        self.assertAlmostEqual(np.dot(density, np.diff(edges)), 8.0)
        self.assertAlmostEqual(flow["in_range_integral"], 8.0)
        cut, cut_weights, _ = analyze(self.sample.events, self.sample.weights, 125)
        _, _, density, _, _ = histogram(cut["pt_h"], np.asarray(cut_weights) * 8.0 / 2.5, edges)
        self.assertAlmostEqual(np.dot(density, np.diff(edges)), 3.2)

    def test_bin_widths_and_flow_accounting(self):
        edges = np.array([60., 110., 180.])
        output, selected, _ = analyze(self.sample.events, self.sample.weights)
        _, _, density, _, flow = histogram(output["pt_h"], np.asarray(selected) / 2.5, edges)
        self.assertEqual(flow["underflow_entries"], 1)
        self.assertEqual(flow["overflow_entries"], 1)
        self.assertAlmostEqual(np.dot(density, np.diff(edges))
                               + flow["underflow_integral"] + flow["overflow_integral"], 1)
        # The rightmost edge is included, including Delta phi = pi.
        _, _, density, _, flow = histogram([math.pi], [1.], np.array([0., math.pi]))
        self.assertAlmostEqual(density[0] * math.pi, 1)
        self.assertEqual(flow["overflow_entries"], 0)

    def test_plot_command_preserves_cut_efficiency(self):
        # Exercise the actual normalisation in main(), the plot calls and exports.
        script = FIXTURE.parents[2] / "lheanalyzer/lhe_analyzer.py"
        with tempfile.TemporaryDirectory() as directory:
            for mode, expected in [("cross-section", 3.2), ("shape", 0.4)]:
                with self.subTest(normalization=mode):
                    subprocess.run([sys.executable, str(script), str(FIXTURE), mode,
                                    "--output-dir", directory, "--normalization", mode,
                                    "--min-pt-h", "125"], check=True, capture_output=True, text=True)
                    destination = Path(directory) / mode
                    summary = json.loads((destination / "summary.json").read_text())
                    self.assertEqual(summary["selected_events"], 1)
                    self.assertAlmostEqual(summary["selected_cross_section_pb"], 3.2)
                    self.assertEqual(len(list(destination.glob("*.pdf"))), 6)
                    with (destination / "histograms.csv").open() as handle:
                        rows = [row for row in csv.DictReader(handle) if row["observable"] == "pt_h"]
                    integral = sum(float(row["density"]) * (float(row["right"]) - float(row["left"])) for row in rows)
                    self.assertAlmostEqual(integral, expected)
                    self.assertAlmostEqual(sum(float(row["bin_integral"]) for row in rows), expected)

    def test_missing_student_append_gives_clear_error(self):
        with self.assertRaisesRegex(ValueError, "one value per selected event weight"):
            histogram([], [1, 2], np.array([0, 100, 200]))

    def assert_bad_file(self, text, message):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.lhe"
            path.write_text(text)
            with self.assertRaisesRegex(ValueError, message):
                read_lhe(path)

    def test_truncation_and_wrong_process_fail_clearly(self):
        text = FIXTURE.read_text()
        self.assert_bad_file(text.split("</event>")[0], "Truncated")
        self.assert_bad_file(text.replace("</LesHouchesEvents>", ""), "complete LHE")
        self.assert_bad_file(text.replace("-4 1", "-4 2", 1), "one subprocess")
        self.assert_bad_file(text.replace("4 1 2.000", "4 9 2.000", 1), "process ID")
        self.assert_bad_file(text.replace("4 1 2.000", "5 1 2.000", 1), "13 fields")

    def test_decayed_or_empty_selection(self):
        events = [[p._replace(status=2) if p.pdg == 99925 else p for p in event]
                  for event in self.sample.events]
        with self.assertRaisesRegex(ValueError, "undecayed"):
            analyze(events, self.sample.weights)
        with self.assertRaisesRegex(ValueError, "No selected"):
            analyze(self.sample.events, self.sample.weights, 1e6)


if __name__ == "__main__":
    unittest.main()
