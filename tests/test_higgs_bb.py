"""Check the Higgs-decay lesson, its real samples and the exact student workflow."""

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

from lheanalyzer.lhe_tools import Particle, read_lhe
from lheanalyzer.lhe_analyzer import invariant_mass
from lheanalyzer.lhe_bb_four_lepton import analyze
from lheanalyzer.compare_bb_four_lepton import compare

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'docs/higgs_bb.md'
STARTER = ROOT / 'lheanalyzer/lhe_bb_four_lepton.py'
FIXTURE = ROOT / 'tests/fixtures/gg_h_eta0_bb2e2mu_toy.lhe'
SIGNAL = ROOT / 'examples/gg_h_eta0_bb2e2mu_pilot.lhe.gz'
BACKGROUND = ROOT / 'examples/pp_bbzz_2e2mu_pilot.lhe.gz'


def completed_source(additions=2):
    snippets = re.findall(r'<!-- exercise: (lists|calculations|plots) -->\n'
                          r'```python\n(.*?)\n```', GUIDE.read_text(), re.S)
    if len(snippets) != 6:
        raise AssertionError('Expected three snippets for each of the two additions.')
    source = STARTER.read_text()
    for kind, snippet in snippets[:3 * additions]:
        marker = next(line for line in source.splitlines()
                      if line.lstrip().startswith('# EXERCISE ' + kind.upper() + ':'))
        source = source.replace(marker, snippet + '\n' + marker, 1)
    return source


def completed_module():
    module = types.ModuleType('lheanalyzer.completed_bb_four_lepton')
    module.__package__ = 'lheanalyzer'
    exec(compile(completed_source(), str(STARTER), 'exec'), module.__dict__)
    return module


class HiggsBBTests(unittest.TestCase):
    def setUp(self):
        self.sample = read_lhe(FIXTURE)

    def test_reconstruction_and_truth_status(self):
        complete = completed_module()
        output, selected, checks, _ = complete.analyze(self.sample.events, self.sample.weights)
        self.assertEqual(set(output), {'m_ee', 'm_mumu', 'm_4l', 'm_bb', 'pt_bb'})
        np.testing.assert_allclose(output['m_bb'], 125, atol=1e-9)
        np.testing.assert_allclose(output['m_4l'], 400, atol=1e-9)
        np.testing.assert_allclose(output['pt_bb'], 0, atol=1e-9)
        self.assertEqual(selected, [2., 1., -.5])
        self.assertLess(checks['max_four_momentum_residual_GeV'], 1e-9)
        # Background reconstruction must not rely on parent records or incoming gg.
        event = [p for p in self.sample.events[0] if p.status != 2]
        event[0] = event[0]._replace(pdg=2)
        event[1] = event[1]._replace(pdg=-2)
        event.append(Particle(5, 2, 0, 0, 0, 1000, 1000))
        second, _, _, _ = complete.analyze([event], [1.])
        self.assertAlmostEqual(second['m_bb'][0], 125.)

    def test_incompatible_final_states_and_incoming_particles(self):
        event = self.sample.events[0]
        for changed in (event + [Particle(21, 1, 0, 0, 0, 0, 0)],
                        [p._replace(status=2) if p.pdg == -5 else p for p in event],
                        [p._replace(pdg=5) if p.pdg == -5 else p for p in event]):
            with self.assertRaisesRegex(ValueError, 'No compatible events'):
                analyze([changed], [1.])
        bad_beam = [p._replace(pdg=22) if p.status == -1 else p for p in event]
        with self.assertRaisesRegex(ValueError, 'two incoming'):
            analyze([bad_beam], [1.])
        # The stable-Higgs sample belongs to the earlier lesson.
        old = read_lhe(ROOT / 'examples/gg_h_eta0_2e2mu_pilot.lhe.gz')
        with self.assertRaisesRegex(ValueError, 'Higgs-decay sample'):
            analyze(old.events, old.weights)

    def test_cutflow_signed_weights_and_boundaries(self):
        _, selected, _, flow = analyze(self.sample.events, self.sample.weights,
                                      min_lepton_pt=10, min_b_pt=25,
                                      mbb_window=(125, 126), m4l_window=(399, 401))
        self.assertEqual([len(w) for w in flow.values()], [3, 3, 2, 2, 2, 2])
        self.assertEqual(selected, [1., -.5])
        self.assertAlmostEqual(math.fsum(selected) / math.fsum(self.sample.weights), .2)
        b = next(p for p in self.sample.events[0] if p.pdg == 5 and p.status == 1)
        _, selected, _, _ = analyze(self.sample.events, self.sample.weights, min_b_pt=abs(b.px))
        self.assertEqual(len(selected), 3)
        for kwargs in (dict(min_b_pt=1e6), dict(mbb_window=(130, 140)),
                       dict(m4l_window=(450, 500))):
            output, selected, _, flow = analyze(self.sample.events, self.sample.weights, **kwargs)
            self.assertEqual(output['m_ee'], [])
            self.assertEqual(selected, [])
            self.assertEqual(len(flow['correct_final_state']), 3)
            self.assertEqual(flow['m4l_window'], [])

    def test_invalid_selection_and_weight_lengths(self):
        for weights in ([], self.sample.weights + [1.]):
            with self.assertRaisesRegex(ValueError, 'exactly one weight'):
                analyze(self.sample.events, weights)
        for kwargs in (dict(min_b_pt=-1), dict(min_b_pt=float('nan')),
                       dict(min_lepton_pt=float('inf')), dict(mbb_window=(140, 130)),
                       dict(mbb_window=(-1, 130)), dict(m4l_window=(400, 400)),
                       dict(m4l_window=(0, float('nan')))):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                analyze(self.sample.events, self.sample.weights, **kwargs)

    def test_completed_cli_integrals_including_zero_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / 'completed.py'
            script.write_text(completed_source())
            env = dict(os.environ, PYTHONPATH=str(ROOT / 'lheanalyzer'))
            for i, (mode, cut, expected) in enumerate((('cross-section', 25, 1.6),
                                                      ('shape', 25, .2),
                                                      ('cross-section', 1e6, 0.))):
                command = [sys.executable, str(script), str(FIXTURE), str(i),
                           '--output-dir', directory, '--normalization', mode,
                           '--min-lepton-pt', '10', '--min-b-pt', str(cut)]
                run = subprocess.run(command, env=env, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                summary = json.loads((root / str(i) / 'summary.json').read_text())
                with (root / str(i) / 'histograms.csv').open() as handle:
                    rows = list(csv.DictReader(handle))
                for name, flow in summary['histograms'].items():
                    area = sum(float(r['density']) * (float(r['right']) - float(r['left']))
                               for r in rows if r['observable'] == name)
                    area += flow['underflow_integral'] + flow['overflow_integral']
                    self.assertAlmostEqual(area, expected)
                self.assertEqual(summary['cutflow'][-1]['events'], 0 if cut > 1e5 else 2)
                self.assertEqual(len(list((root / str(i)).glob('*.png'))), 5)

    def test_real_samples_and_decay_normalization(self):
        complete = completed_module()
        for path, count in ((SIGNAL, 100), (BACKGROUND, 500)):
            with self.subTest(sample=path.name):
                metadata = json.loads(path.with_suffix('').with_suffix('.json').read_text())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), metadata['sha256'])
                sample = read_lhe(path)
                self.assertEqual(len(sample.events), count)
                self.assertTrue(all(w > 0 for w in sample.weights))
                self.assertAlmostEqual(math.fsum(sample.weights) / sample.cross_section_pb, 1., delta=1e-6)
                output, selected, checks, _ = complete.analyze(sample.events, sample.weights)
                self.assertLess(checks['max_four_momentum_residual_GeV'], 2e-6)
                for event in sample.events:
                    self.assertEqual(sorted(p.pdg for p in event if p.status == 1),
                                     [-13, -11, -5, 5, 11, 13])
                for tag, kwargs in (('pt', dict(min_lepton_pt=10, min_b_pt=25)),
                                    ('windows', dict(min_lepton_pt=10, min_b_pt=25,
                                                     mbb_window=(105,145), m4l_window=(350,450)))):
                    _, weights, _, flow = complete.analyze(sample.events, sample.weights, **kwargs)
                    self.assertEqual({stage: len(w) for stage,w in flow.items()},
                                     metadata['cutflow_counts'][tag])
                    self.assertAlmostEqual(sample.cross_section_pb * math.fsum(weights) / math.fsum(sample.weights),
                                           metadata['selected_cross_sections_pb'][tag], delta=1e-15)
                if path == SIGNAL:
                    np.testing.assert_allclose(output['m_bb'], 125, rtol=0, atol=1e-5)
                    np.testing.assert_allclose(output['m_4l'], 400, rtol=0, atol=1e-5)
                    h_pt = [math.hypot(p.px, p.py) for event in sample.events for p in event
                            if p.pdg == 25 and p.status == 2]
                    np.testing.assert_allclose(output['pt_bb'], h_pt, rtol=0, atol=2e-6)
                    expected_factor = metadata['h_branching_factor'] * metadata['eta0_branching_factor']
                    self.assertAlmostEqual(sample.cross_section_pb / metadata['production_cross_section_pb'],
                                           expected_factor, delta=1e-10)
                    factorised_eta = .1653251 * 2 * .03438713**2
                    self.assertAlmostEqual(metadata['eta0_branching_factor'] / factorised_eta, 1., delta=.1)
                else:
                    self.assertGreater(np.std(output['m_bb']), 10.)
                    self.assertGreater(np.std(output['m_4l']), 10.)
                    beams = {p.pdg for event in sample.events for p in event if p.status == -1}
                    self.assertIn(21, beams)
                    self.assertTrue(beams.intersection({1, -1, 2, -2, 3, -3, 4, -4}))

    def test_higgs_width_and_unchanged_production_inputs(self):
        metadata = json.loads(SIGNAL.with_suffix('').with_suffix('.json').read_text())
        mh, mb, gf, ct = 125., 4.7, 1.16639e-5, .9797959
        expected = 3 * gf * mh * mb**2 * ct**2 / (4 * math.pi * math.sqrt(2)) * (1-4*mb**2/mh**2)**1.5
        self.assertAlmostEqual(metadata['h_decay_partial_width_GeV'] / expected, 1., delta=2e-5)
        # Compare all non-decay numeric blocks with the previous benchmark.
        def inputs(path):
            values, block = {}, None
            for line in path.read_text().splitlines():
                fields = line.split('#')[0].split()
                if not fields:
                    continue
                if fields[0].upper() == 'BLOCK':
                    block = ' '.join(fields[1:]).lower()
                elif fields[0].upper() == 'DECAY':
                    block = None
                elif block:
                    values[(block, tuple(fields[:-1]))] = float(fields[-1])
            return values
        self.assertEqual(inputs(ROOT / 'cards/param_card_gg_h_eta0_bb2e2mu.dat'),
                         inputs(ROOT / 'cards/param_card_gg_h_eta0_2e2mu.dat'))

    def test_exact_student_commands_and_comparison(self):
        commands = re.findall(r'<!-- student-command: (\w+) -->\n```bash\n(.*?)\n```',
                              GUIDE.read_text(), re.S)
        self.assertEqual([s for s,_ in commands], ['start', 'mass', 'complete', 'selected',
                         'background', 'shapes', 'signal_windows', 'background_windows', 'rates'])
        with tempfile.TemporaryDirectory(prefix='higgs_bb_lesson_') as directory:
            workspace = Path(directory)
            (workspace / 'lheanalyzer').mkdir()
            (workspace / 'examples').mkdir()
            for name in ('lhe_tools.py', 'lhe_analyzer.py', 'compare_bb_four_lepton.py'):
                shutil.copy2(ROOT / 'lheanalyzer' / name, workspace / 'lheanalyzer' / name)
            for sample in (SIGNAL, BACKGROUND):
                shutil.copy2(sample, workspace / 'examples' / sample.name)
            script = workspace / 'lheanalyzer/lhe_bb_four_lepton.py'
            for stage, command in commands:
                with self.subTest(stage=stage):
                    additions = 0 if stage == 'start' else (1 if stage == 'mass' else 2)
                    script.write_text(completed_source(additions))
                    args = shlex.split(command)
                    args[0] = sys.executable
                    run = subprocess.run(args, cwd=workspace, capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    destination = workspace / 'results' / args[3 if 'compare_' not in args[1] else 4]
                    self.assertEqual(len(list(destination.glob('*.png'))), 3 + additions)
                    self.assertEqual(len(list(destination.glob('*.pdf'))), 3 + additions)
                    if stage in ('shapes', 'rates'):
                        summary = json.loads((destination / 'comparison.json').read_text())
                        with (destination / 'histograms.csv').open() as handle:
                            rows = list(csv.DictReader(handle))
                        for name, samples in summary['histograms'].items():
                            for sample, flow in samples.items():
                                area = sum(float(r['density']) * (float(r['right']) - float(r['left']))
                                           for r in rows if r['observable'] == name and r['sample'] == sample)
                                area += flow['underflow_integral'] + flow['overflow_integral']
                                expected = 1. if stage == 'shapes' else summary[sample + '_cross_section_pb']
                                self.assertAlmostEqual(area, expected, delta=max(1e-15, abs(expected)*1e-9))
                        self.assertTrue((destination / 'selection_table.csv').is_file())
                    elif stage == 'selected':
                        summary = json.loads((destination / 'summary.json').read_text())
                        self.assertEqual(summary['selected_events'], 82)
            selected = workspace / 'results/bb_signal_selected'
            windows = workspace / 'results/bb_background_windows'
            with self.assertRaisesRegex(ValueError, 'selections differ'):
                compare(selected, windows, workspace / 'bad_comparison')
            # Existing outputs must be protected when a student repeats a command.
            run = subprocess.run(args, cwd=workspace, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('--overwrite', run.stderr)


if __name__ == '__main__':
    unittest.main()
