"""HwSim storage, jet selection, normalisation and student-code checks."""

import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

import numpy as np
import uproot

from jetanalyzer import hwsim_jets as jets
from jetanalyzer.compare_jets import compare
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


if __name__ == '__main__':
    unittest.main()
