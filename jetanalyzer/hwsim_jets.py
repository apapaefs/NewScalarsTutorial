#!/usr/bin/env python3
"""Make weighted jet plots from HwSim's reconstructed-object ROOT tree."""

import argparse
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lheanalyzer.lhe_analyzer import invariant_mass, plot_histogram


# One entry per plot: (axis label, bin edges, whether the x axis is in GeV).
OBSERVABLES = {
    'n_jets': (r'Number of jets, $N_j$ (including b-jets)', np.arange(-0.5, 16), False),
    'n_bjets': (r'Number of truth b-jets, $N_b$', np.arange(-0.5, 7), False),
    'm_bb': (r'$m_{bb}$ from two truth b-jets [GeV]', np.linspace(0, 300, 61), True),
    # EXERCISE PLOT: add the HT entry here.
}


@dataclass
class JetEvent:
    # HwSim stores four-vectors in the order (E, px, py, pz), in GeV.
    non_b_jets: np.ndarray
    b_jets: np.ndarray
    weight: float


def selected_jets(jets, min_pt, max_eta):
    """Apply the same pT and pseudorapidity cuts to BOTH jet collections."""
    selected = []
    for jet in jets:
        pt = math.hypot(jet[1], jet[2])
        eta = math.asinh(jet[3] / pt) if pt > 0 else math.inf
        if pt >= min_pt and abs(eta) < max_eta:
            selected.append(jet)
    return sorted(selected, key=lambda j: math.hypot(j[1], j[2]), reverse=True)


def measure_jets(non_b_jets, b_jets):
    """STUDENT CODE: all jets have already passed the pT and eta cuts."""
    jets = non_b_jets + b_jets
    values = {}
    values['n_jets'] = len(jets)       # HwSim's numJets alone excludes b-jets!
    values['n_bjets'] = len(b_jets)
    # EXERCISE CALCULATION: add HT here, before the two-b-jet requirement.

    # A missing mass is not zero: it means this event has no chosen pair.
    values['m_bb'] = None
    if len(b_jets) == 2:
        pair = b_jets[0] + b_jets[1]   # Add (E, px, py, pz), component by component.
        values['m_bb'] = invariant_mass(*pair)
    return values


def read_events(path):
    """Read only populated array slots; -999 padding is not a physical jet."""
    import uproot
    branches = ['theJets', 'numJets', 'thebJets', 'numbJets',
                'bHadronMultiplicity', 'evweight']
    with uproot.open(path) as root_file:
        if 'Data' not in root_file:
            raise ValueError("No HwSim Data tree. Use SaveReconstructed Yes.")
        tree = root_file['Data']
        missing = set(branches) - set(tree.keys())
        if missing:
            raise ValueError(f"Missing HwSim branches: {', '.join(sorted(missing))}. "
                             "Use the current HwSim plugin and the supplied card.")
        for batch in tree.iterate(branches, step_size=1000, library='np'):
            for i, weight in enumerate(batch['evweight']):
                nj, nb = int(batch['numJets'][i]), int(batch['numbJets'][i])
                if not (0 <= nj < 100 and 0 <= nb < 100):
                    raise ValueError("Invalid or full HwSim jet array; cannot exclude truncation.")
                non_b = batch['theJets'][i, :4, :nj].T.copy()
                b = batch['thebJets'][i, :4, :nb].T.copy()
                if (not np.isfinite(weight) or not np.isfinite(non_b).all()
                        or not np.isfinite(b).all()
                        or np.any(non_b[:, 0] < 0) or np.any(b[:, 0] < 0)):
                    raise ValueError("Non-finite weight/momentum or invalid HwSim jet energy.")
                if np.any(batch['bHadronMultiplicity'][i, :nb] < 1):
                    raise ValueError("A truth b-jet has no associated b hadron. Check BTaggingMethod.")
                yield JetEvent(non_b, b, float(weight))


def analyze(events, min_jet_pt=25.0, max_jet_eta=2.5):
    if not math.isfinite(min_jet_pt) or min_jet_pt < 10:
        raise ValueError("min-jet-pt must be at least the 10 GeV HwSim storage threshold.")
    if not math.isfinite(max_jet_eta) or not 0 < max_jet_eta <= 6:
        raise ValueError("max-jet-eta must be positive and at most 6.")
    output = {name: [] for name in OBSERVABLES}
    weights = {name: [] for name in OBSERVABLES}
    cutflow = {'input': [], 'exactly_two_bjets': []}
    for event in events:
        cutflow['input'].append(event.weight)
        non_b = selected_jets(event.non_b_jets, min_jet_pt, max_jet_eta)
        b = selected_jets(event.b_jets, min_jet_pt, max_jet_eta)
        values = measure_jets(non_b, b)
        if set(values) != set(OBSERVABLES):
            raise ValueError("Each observable needs a calculation and an OBSERVABLES entry.")
        if len(b) == 2:
            cutflow['exactly_two_bjets'].append(event.weight)
        for name, value in values.items():
            if value is not None:
                if not math.isfinite(value):
                    raise ValueError(f"Non-finite observable: {name}.")
                output[name].append(value)
                weights[name].append(event.weight)
    if not cutflow['input'] or math.fsum(cutflow['input']) <= 0:
        raise ValueError("Expected at least one event and a positive total event weight.")
    return output, weights, cutflow


def herwig_statistics(path):
    """Use Herwig's final hard-process rate, including any generator rejection."""
    text = Path(path).read_text()
    match = re.search(r"Statistics for Les Houches event handler 'TutorialLHE':"
                      r".*?Cross-section\s*.*?\(nb\).*?"
                      r"^Total:\s+(\d+)\s+(\d+)\s+([\d.eE+-]+)", text, re.S | re.M)
    if not match:
        raise ValueError("No completed TutorialLHE statistics in the .out file. Finish the Herwig run.")
    generated, attempts = map(int, match.group(1, 2))
    xsec = float(match[3]) * 1000.0   # ThePEG prints nb; this tutorial uses pb.
    if not math.isfinite(xsec) or xsec <= 0 or attempts < generated:
        raise ValueError("Invalid Herwig event statistics or cross section.")
    return {'generated_events': generated, 'attempts': attempts, 'cross_section_pb': xsec}


def save_outputs(output, weights, cutflow, info, stats, destination, normalization, selection):
    sumw = math.fsum(cutflow['input'])
    total = stats['cross_section_pb'] if normalization == 'cross-section' else 1.0
    factor = total / sumw
    rows = []
    for stage, stage_weights in cutflow.items():
        stage_sumw = math.fsum(stage_weights)
        rows.append({'stage': stage, 'events': len(stage_weights), 'sumw': stage_sumw,
                     'sumw2': math.fsum(w*w for w in stage_weights),
                     'weighted_efficiency': stage_sumw / sumw,
                     'cross_section_pb': stats['cross_section_pb'] * stage_sumw / sumw})
    summary = {'input_events': len(cutflow['input']), 'inclusive_sumw': sumw,
               'normalization': normalization, 'selection': selection,
               'run': info, 'herwig': stats, 'cutflow': rows, 'histograms': {},
               'error_note': 'sqrt(sum(w^2)), treating the inclusive normalisation as fixed; '
                             'no integration or theory uncertainty included.'}
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / 'cutflow.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (destination / 'histograms.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['observable', 'left', 'right', 'bin_integral', 'bin_sumw2',
                         'density', 'density_mc_error'])
        for name, (xlabel, bins, gev) in OBSERVABLES.items():
            ylabel = 'Cross section [pb]' if normalization == 'cross-section' else 'Weighted fraction'
            ylabel += ' / GeV' if gev else ' / bin'
            plot = plot_histogram(output[name], np.asarray(weights[name]) * factor,
                                  bins, xlabel, ylabel, destination / name,
                                  title='Herwig + HwSim (particle level)')
            summary['histograms'][name] = plot['flow']
            for i in range(len(bins) - 1):
                writer.writerow([name, bins[i], bins[i+1], plot['sumw'][i], plot['sumw2'][i],
                                 plot['density'][i], plot['error'][i]])
    (destination / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root_file', type=Path)
    parser.add_argument('tag', help='name for the results directory')
    parser.add_argument('--min-jet-pt', type=float, default=25.0)
    parser.add_argument('--max-jet-eta', type=float, default=2.5)
    parser.add_argument('--normalization', choices=['cross-section', 'shape'], default='cross-section')
    parser.add_argument('--output-dir', type=Path, default=Path('results'))
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', args.tag):
            raise ValueError('Use a simple tag with no spaces or slashes.')
        destination = args.output_dir / args.tag
        if destination.exists() and any(destination.iterdir()) and not args.overwrite:
            raise ValueError(f'{destination} already contains results; choose a new tag or --overwrite.')
        info = json.loads(args.root_file.with_suffix('.json').read_text())
        if Path(info['root_file']).name != args.root_file.name or info['b_tag'] != 'GhostBHadrons':
            raise ValueError('The run JSON does not describe this ROOT file and truth-tagging setup.')
        stats = herwig_statistics(args.root_file.with_suffix('.out'))
        output, weights, cutflow = analyze(read_events(args.root_file), args.min_jet_pt, args.max_jet_eta)
        n = len(cutflow['input'])
        if n != info['requested_events'] or n != stats['generated_events']:
            raise ValueError(f'Incomplete/mismatched run: ROOT has {n} events, requested '
                             f"{info['requested_events']}, Herwig reports {stats['generated_events']}.")
        selection = {'level': 'particle', 'min_jet_pt_GeV': args.min_jet_pt,
                     'max_abs_jet_eta': args.max_jet_eta, 'b_pair': 'exactly two accepted truth b-jets',
                     'multiplicities': 'all input events, before the b-pair requirement',
                     'additional_lepton_selection': False}
        summary = save_outputs(output, weights, cutflow, info, stats, destination,
                               args.normalization, selection)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    for row in summary['cutflow']:
        print(f"{row['stage']:<24} {row['events']:>7} events  "
              f"efficiency={row['weighted_efficiency']:.4f}  sigma={row['cross_section_pb']:.6g} pb")
    print(f'Saved {len(output)} plots (PDF/PNG), histogram CSV and cutflow in {destination.resolve()}')
    print('Multiplicity plots include every event. The mass plot requires exactly two accepted b-jets.')


if __name__ == '__main__':
    main()
