"""HwSim storage, jet selection, normalisation and student-code checks."""

import hashlib
from dataclasses import replace
import json
import math
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import types
import unittest

import numpy as np
import uproot

from jetanalyzer import hwsim_jets as jets
from jetanalyzer import compare_mbb_levels as levels
from jetanalyzer.compare_jets import compare
from lheanalyzer.lhe_tools import read_lhe
from scripts.prepare_herwig import prepare

ROOT = Path(__file__).resolve().parents[1]
EMPTY = np.empty((0, 4))
PAIR = np.array([[62.5, 60., 0., 0.], [62.5, -60., 0., 0.]])


def write_root(path, events):
    n = len(events)
    payload = {'evweight': np.array([e.weight for e in events]),
               'numJets': np.array([len(e.non_b_jets) for e in events], dtype=np.int32),
               'numbJets': np.array([len(e.b_jets) for e in events], dtype=np.int32),
               'theJets': np.full((n, 5, 100), -999.),
               'thebJets': np.full((n, 5, 100), -999.),
               'bHadronMultiplicity': np.full((n, 100), -1, dtype=np.int32)}
    for i, event in enumerate(events):
        for name, collection in [('theJets', event.non_b_jets), ('thebJets', event.b_jets)]:
            payload[name][i, :4, :len(collection)] = collection.T
        payload['bHadronMultiplicity'][i, :len(event.b_jets)] = 1
    with uproot.recreate(path) as f:
        f.mktree('Data', {k: np.dtype((v.dtype, v.shape[1:])) if v.ndim > 1 else v.dtype
                          for k, v in payload.items()})
        f['Data'].extend(payload)


def write_run_files(path, n):
    info = {'schema_version': 1, 'root_file': path.name, 'requested_events': n,
            'jet_algorithm': 'anti-kt', 'jet_radius': .4, 'b_tag': 'GhostBHadrons',
            'mpi': True, 'common_card_sha256': 'synthetic-test', 'cross_section_pb': 2.0}
    path.with_suffix('.json').write_text(json.dumps(info))
    path.with_suffix('.out').write_text(
        "Statistics for Les Houches event handler 'TutorialLHE':\n"
        " generated number of Cross-section\n events attempts (nb)\n"
        f"Total: {n} {n} 2.00000e-03\n")
    return info


def completed_module():
    source = (ROOT / 'jetanalyzer/hwsim_jets.py').read_text()
    snippets = re.findall(r'<!-- exercise: (calculation|plot) -->\n```python\n(.*?)\n```',
                          (ROOT / 'docs/jets.md').read_text(), re.S)
    if len(snippets) != 2:
        raise AssertionError('Expected the two exact HT additions.')
    for kind, text in snippets:
        marker = next(line for line in source.splitlines() if '# EXERCISE ' + kind.upper() + ':' in line)
        source = source.replace(marker, marker + '\n' + text)
    module = types.ModuleType('completed_jets')
    module.__file__ = str(ROOT / 'jetanalyzer/hwsim_jets.py')
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
    return module


class JetTests(unittest.TestCase):
    def test_two_collections_pair_and_merged_category(self):
        light = [np.array([50., 0., 50., 0.])]
        measured = jets.measure_jets(light, list(PAIR))
        self.assertEqual(measured, {'n_jets': 3, 'n_bjets': 2, 'm_bb': 125.})
        for b in ([], list(PAIR[:1]), list(PAIR) + [PAIR[0]]):
            self.assertIsNone(jets.measure_jets(light, b)['m_bb'])
        # Even a jet with two b-hadron markers is a single jet; the ROOT reader
        # counts its four-vector once, never expands hadron multiplicity.
        self.assertEqual(jets.measure_jets([], list(PAIR[:1]))['n_bjets'], 1)

    def test_acceptance_boundaries_and_same_cuts(self):
        on_pt = np.array([30., 25., 0., 0.])
        outside_eta = np.array([200., 25., 0., 25*math.sinh(2.51)])
        event = jets.JetEvent(np.array([on_pt, outside_eta]), np.array([on_pt, outside_eta]), 1.)
        out, _, flow = jets.analyze([event])
        self.assertEqual(out['n_jets'], [2])
        self.assertEqual(out['n_bjets'], [1])
        self.assertEqual(out['m_bb'], [])
        self.assertEqual(flow['exactly_two_bjets'], [])
        for pt, eta in ((9, 2.5), (math.nan, 2.5), (25, 0), (25, 7)):
            with self.assertRaises(ValueError):
                jets.analyze([event], pt, eta)

    def test_root_padding_and_weights(self):
        events = [jets.JetEvent(EMPTY, EMPTY, 2.), jets.JetEvent(EMPTY, PAIR, -0.5)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.root'
            write_root(path, events)
            read = list(jets.read_events(path))
            self.assertEqual(len(read), 2)
            self.assertEqual(read[0].b_jets.shape, (0, 4))
            np.testing.assert_array_equal(read[1].b_jets, PAIR)
            out, weights, flow = jets.analyze(read)
            self.assertEqual(out['n_jets'], [0, 2])
            self.assertEqual(weights['m_bb'], [-.5])
            self.assertEqual(flow['input'], [2., -.5])

    def test_bad_root_and_incomplete_statistics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.root'
            with uproot.recreate(path) as f:
                f.mktree('Data', {'evweight': 'float64'})
            with self.assertRaisesRegex(ValueError, 'Missing HwSim branches'):
                list(jets.read_events(path))
            invalid = PAIR.copy()
            invalid[0, 0] = -999
            write_root(path, [jets.JetEvent(EMPTY, invalid, 1.)])
            with self.assertRaisesRegex(ValueError, 'energy'):
                list(jets.read_events(path))
            stats = path.with_suffix('.out')
            stats.write_text('Herwig failed before final statistics\n')
            with self.assertRaisesRegex(ValueError, 'Finish the Herwig run'):
                jets.herwig_statistics(stats)
            write_run_files(path, 2)
            self.assertEqual(jets.herwig_statistics(stats)['cross_section_pb'], 2.)

    def test_rates_flow_and_empty_pair_selection(self):
        events = [jets.JetEvent(EMPTY, EMPTY, 1.), jets.JetEvent(EMPTY, PAIR, 2.),
                  jets.JetEvent(EMPTY, PAIR*8, -.5)]
        info = {'jet_algorithm': 'anti-kt', 'jet_radius': .4, 'b_tag': 'GhostBHadrons',
                'mpi': True, 'common_card_sha256': 'synthetic'}
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for normalization, sigma in [('cross-section', 2.), ('shape', 1.)]:
                out, weights, flow = jets.analyze(events)
                summary = jets.save_outputs(out, weights, flow, info, {'cross_section_pb': 2.},
                                            base / normalization, normalization, {})
                for name, expected in [('n_jets', sigma), ('n_bjets', sigma), ('m_bb', .6*sigma)]:
                    f = summary['histograms'][name]
                    integral = f['in_range_integral'] + f['underflow_integral'] + f['overflow_integral']
                    self.assertAlmostEqual(integral, expected)
                self.assertEqual(summary['histograms']['m_bb']['overflow_entries'], 1)
                self.assertAlmostEqual(summary['cutflow'][1]['weighted_efficiency'], .6)
            out, weights, flow = jets.analyze(events, min_jet_pt=10000)
            summary = jets.save_outputs(out, weights, flow, info, {'cross_section_pb': 2.},
                                        base / 'empty', 'cross-section', {})
            self.assertEqual(summary['histograms']['m_bb']['in_range_integral'], 0)
            self.assertEqual(summary['cutflow'][1]['events'], 0)

    def test_cli_compare_overwrite_and_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / 'input.root'
            write_root(root, [jets.JetEvent(EMPTY, EMPTY, 1.), jets.JetEvent(EMPTY, PAIR, 1.)])
            write_run_files(root, 2)
            cmd = [sys.executable, str(ROOT / 'jetanalyzer/hwsim_jets.py'), str(root),
                   'signal', '--output-dir', str(base)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(len(list((base / 'signal').glob('*.png'))), 3)
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            shutil.copytree(base / 'signal', base / 'background')
            report = compare(base / 'signal', base / 'background', base / 'shape')
            for integrals in report['integrals_including_flow'].values():
                np.testing.assert_allclose(integrals, [1, 1])
            report = compare(base / 'signal', base / 'background', base / 'rate', 'cross-section')
            self.assertEqual(report['integrals_including_flow']['m_bb'], [1, 1])
            summary_path = base / 'background/summary.json'
            summary = json.loads(summary_path.read_text())
            summary['selection']['min_jet_pt_GeV'] = 40
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError, 'same jet selections'):
                compare(base / 'signal', base / 'background', base / 'mismatch')
            info = json.loads(root.with_suffix('.json').read_text())
            info['requested_events'] = 3
            root.with_suffix('.json').write_text(json.dumps(info))
            result = subprocess.run(cmd + ['--overwrite'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Incomplete/mismatched run', result.stderr)

    def test_exact_ht_additions(self):
        completed = completed_module()
        light = np.array([[25., 0., 25., 0.]])
        out, weights, _ = completed.analyze([jets.JetEvent(light, PAIR, 1.),
                                            jets.JetEvent(EMPTY, EMPTY, 2.)])
        self.assertEqual(out['ht'], [145., 0.])
        self.assertEqual(weights['ht'], [1., 2.])
        with tempfile.TemporaryDirectory() as directory:
            _, _, flow = completed.analyze([jets.JetEvent(light, PAIR, 1.),
                                            jets.JetEvent(EMPTY, EMPTY, 2.)])
            completed.save_outputs(out, weights, flow, {}, {'cross_section_pb': 2.},
                                   Path(directory), 'cross-section', {})
            self.assertEqual(len(list(Path(directory).glob('*.png'))), 4)

    def test_preparation_refuses_wrong_samples_and_recycling(self):
        signal = ROOT / 'examples/gg_h_eta0_bb2e2mu_pilot.lhe.gz'
        with self.assertRaisesRegex(ValueError, 'contains 100'):
            prepare(signal, 'unwritten-test', events=101)
        with self.assertRaisesRegex(ValueError, 'fully decayed'):
            prepare(ROOT / 'examples/gg_h_eta0_2e2mu_pilot.lhe.gz', 'unwritten-test', events=10)
        with self.assertRaises(ValueError):
            prepare(signal, '../invalid', events=10)
        with self.assertRaises(ValueError):
            prepare(signal, 'unwritten-test', radius=math.nan)

    def test_lfs_manifest_and_effective_cards(self):
        manifest = json.loads((ROOT / 'samples/manifest.json').read_text())
        self.assertEqual([s['events'] for s in manifest['samples']], [10000, 10000, 10000, 50000])
        for sample in manifest['samples']:
            path = ROOT / 'samples' / sample['file']
            data = path.read_bytes()
            if data.startswith(b'version https://git-lfs.github.com/spec/'):
                self.assertIn(f"oid sha256:{sample['sha256']}".encode(), data)
                self.assertIn(f"size {sample['size_bytes']}".encode(), data)
            else:
                self.assertEqual(hashlib.sha256(data).hexdigest(), sample['sha256'])
                self.assertEqual(len(data), sample['size_bytes'])
            self.assertEqual(sample['events'], sample['unique_events'])
            for card in sample['cards'].values():
                self.assertTrue((ROOT / card).is_file())
            if sample['madspin_seed']:
                factor = math.prod(s['branching_factor'] for s in sample['decay_subruns'].values())
                self.assertAlmostEqual(factor, sample['decay_factor'])
                eta_br = sample['decay_subruns']['99925']['branching_factor']
                expected = sample['factorized_onshell_eta0_to_2e2mu_probability']
                self.assertLess(abs(eta_br / expected - 1), .15)


class MassLevelTests(unittest.TestCase):
    fixture = ROOT / 'tests/fixtures/gg_h_eta0_bb2e2mu_toy.lhe'

    def inputs(self, directory, events=None):
        path = Path(directory) / 'input.root'
        if events is None:
            events = [jets.JetEvent(EMPTY, EMPTY, 1.), jets.JetEvent(EMPTY, PAIR, 2.),
                      jets.JetEvent(EMPTY, PAIR*8, -.5)]
        write_root(path, events)
        info = write_run_files(path, len(events))
        info.update(lhe_sha256=hashlib.sha256(self.fixture.read_bytes()).hexdigest(), lhe_events=3)
        path.with_suffix('.json').write_text(json.dumps(info))
        return path

    def test_parton_four_vector_sum_status_and_acceptance(self):
        sample = read_lhe(self.fixture)
        event = sample.events[0]
        b = next(p for p in event if p.pdg == 5)._replace(px=30., py=0., pz=40., energy=50.)
        bbar = next(p for p in event if p.pdg == -5)._replace(px=-30., py=0., pz=0., energy=40.)
        # Intermediate b records and scalar masses must not enter the sum.
        event = [p for p in event if abs(p.pdg) != 5] + [b, bbar, b._replace(status=2, energy=500.)]
        sample = replace(sample, events=[event], weights=[2.])
        masses, weights = levels.parton_masses(sample, min_pt=30.)
        self.assertAlmostEqual(masses[0], math.sqrt(90.**2 - 40.**2))
        self.assertEqual(weights, [2.])  # A 5 GeV lepton does not impose another cut.
        self.assertEqual(levels.parton_masses(sample, min_pt=30.001), ([], []))
        self.assertEqual(levels.parton_masses(sample, max_eta=math.asinh(40./30.)), ([], []))
        self.assertEqual(levels.parton_masses(sample, max_eta=1.1)[1], [2.])

    def test_incompatible_lhe_topologies(self):
        sample = read_lhe(self.fixture)
        event = sample.events[0]
        b = next(p for p in event if p.pdg == 5)
        invalid = [
            [p for p in event if p.pdg != 5],
            event + [b],
            [p._replace(pdg=5) if p.pdg == -5 else p for p in event],
            [p._replace(status=2) if p.pdg == 5 else p for p in event],
            event + [b._replace(pdg=21)],
        ]
        for bad in invalid:
            with self.subTest(pdg=[(p.pdg, p.status) for p in bad]):
                with self.assertRaisesRegex(ValueError, 'fully decayed'):
                    levels.parton_masses(replace(sample, events=[bad], weights=[1.]))
        with self.assertRaisesRegex(ValueError, 'nominal weight'):
            levels.parton_masses(replace(sample, weights=[]))

    def test_separate_rate_normalizations_signed_weights_and_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.inputs(directory)
            for normalization in ('shape', 'cross-section'):
                destination = Path(directory) / normalization
                report = levels.compare(self.fixture, root, destination, normalization)
                for level, rate in (('parton', 8.), ('hadron', 1.2)):
                    row = report['levels'][level]
                    flow = row['histogram']
                    integral = sum(flow[key] for key in ('in_range_integral', 'underflow_integral',
                                                        'overflow_integral'))
                    self.assertAlmostEqual(integral, 1. if normalization == 'shape' else rate)
                    self.assertAlmostEqual(row['selected_cross_section_pb'], rate)
                self.assertEqual(report['levels']['hadron']['histogram']['overflow_entries'], 1)
                self.assertAlmostEqual(report['levels']['hadron']['weighted_efficiency'], .6)
                self.assertEqual(report['levels']['hadron']['selected_sumw2'], 4.25)
                self.assertEqual(report['levels']['parton']['selected_events'], 3)
                self.assertEqual(report['levels']['hadron']['selected_events'], 2)
                # The parton peak and its nominal +/- rounding lie in one bin.
                bins = levels.MASS_BINS
                self.assertEqual((bins[12] + bins[13])/2, 125.)
                self.assertEqual(np.searchsorted(bins, [124.99999, 125.00001]).tolist(), [13, 13])
                for filename in ('m_bb_levels.pdf', 'm_bb_levels.png', 'histograms.csv',
                                 'selection_table.csv', 'comparison.json'):
                    self.assertGreater((destination / filename).stat().st_size, 0)

    def test_empty_selection_and_nonpositive_selected_weight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.inputs(directory, [jets.JetEvent(EMPTY, EMPTY, 2.),
                                           jets.JetEvent(EMPTY, PAIR, -.5)])
            with self.assertRaisesRegex(ValueError, 'positive selected weight'):
                levels.compare(self.fixture, root, Path(directory) / 'bad_shape')
            rate = levels.compare(self.fixture, root, Path(directory) / 'rate', 'cross-section')
            self.assertAlmostEqual(rate['levels']['hadron']['selected_cross_section_pb'], -2./3.)
            for normalization in ('shape', 'cross-section'):
                report = levels.compare(self.fixture, root, Path(directory) / normalization,
                                        normalization, min_pt=10000)
                for row in report['levels'].values():
                    self.assertEqual(row['selected_events'], 0)
                    self.assertEqual(row['selected_cross_section_pb'], 0)
                    self.assertEqual(row['histogram']['in_range_integral'], 0)

    def test_source_identity_run_counts_and_cut_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.inputs(directory)
            info = json.loads(root.with_suffix('.json').read_text())
            for key, value, message in [('lhe_sha256', 'different', 'checksum differs'),
                                        ('lhe_events', 2, 'LHE event count'),
                                        ('requested_events', 4, 'Incomplete/mismatched'),
                                        ('b_tag', 'Other', 'truth-tagging setup')]:
                root.with_suffix('.json').write_text(json.dumps(dict(info, **{key: value})))
                with self.assertRaisesRegex(ValueError, message):
                    levels.compare(self.fixture, root, Path(directory) / 'unused')
            root.with_suffix('.json').write_text(json.dumps(info))
            pointer = Path(directory) / 'pointer.lhe.gz'
            pointer.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:dummy\n')
            with self.assertRaisesRegex(ValueError, 'git lfs pull'):
                levels.compare(pointer, root, Path(directory) / 'unused')
            for pt, eta in ((9., 2.5), (math.nan, 2.5), (25., 0), (25., 7.)):
                with self.assertRaisesRegex(ValueError, 'storage range'):
                    levels.compare(self.fixture, root, Path(directory) / 'unused', min_pt=pt, max_eta=eta)

    def test_guide_commands_and_cli_overwrite(self):
        guide = (ROOT / 'docs/jets.md').read_text()
        commands = re.findall(r'<!-- student-command: (mbb_levels|mbb_level_rates) -->\n```bash\n(.*?)\n```',
                              guide, re.S)
        self.assertEqual(len(commands), 2)
        with tempfile.TemporaryDirectory() as directory:
            root = self.inputs(directory)
            for _, command in commands:
                args = shlex.split(command)
                args[:4] = [sys.executable, str(ROOT / args[1]), str(self.fixture), str(root)]
                args += ['--output-dir', directory]
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('3/3 selected', result.stdout)
                self.assertIn('2/3 selected', result.stdout)
                repeated = subprocess.run(args, capture_output=True, text=True)
                self.assertNotEqual(repeated.returncode, 0)
                self.assertIn('Results already exist', repeated.stderr)
            result = subprocess.run(args + ['--overwrite'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
