#!/usr/bin/env python3
"""Compare the LHE bottom-pair mass with the mass of two HwSim truth b-jets."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lheanalyzer.lhe_analyzer import invariant_mass
from lheanalyzer.lhe_tools import histogram, read_lhe
from jetanalyzer.hwsim_jets import analyze, herwig_statistics, read_events, selected_jets


# Common 10 GeV bins: 125 GeV lies at a bin centre, away from rounding boundaries.
MASS_BINS = np.linspace(0, 300, 31)


def parton_masses(sample, min_pt=25.0, max_eta=2.5):
    """Use outgoing b/bbar only; apply the same acceptance as for the jets."""
    if len(sample.events) != len(sample.weights):
        raise ValueError('Each LHE event needs one nominal weight.')
    masses, weights = [], []
    for event, weight in zip(sample.events, sample.weights):
        outgoing = [p for p in event if p.status == 1]
        if sorted(p.pdg for p in outgoing) != [-13, -11, -5, 5, 11, 13]:
            raise ValueError('Use a fully decayed bb2e2mu LHE sample with exactly one outgoing b and bbar.')
        bottoms = [np.array([p.energy, p.px, p.py, p.pz]) for p in outgoing if abs(p.pdg) == 5]
        accepted = selected_jets(bottoms, min_pt, max_eta)
        if len(accepted) == 2:
            masses.append(invariant_mass(*(accepted[0] + accepted[1])))
            weights.append(weight)
    return masses, weights


def compare(lhe_file, root_file, destination, normalization='shape', min_pt=25.0, max_eta=2.5):
    if normalization not in ('shape', 'cross-section'):
        raise ValueError('Choose shape or cross-section normalisation.')
    if not math.isfinite(min_pt) or min_pt < 10 or not math.isfinite(max_eta) or not 0 < max_eta <= 6:
        raise ValueError('Use min-pt >= 10 GeV and 0 < max-eta <= 6, within the HwSim storage range.')
    lhe_file, root_file, destination = map(Path, (lhe_file, root_file, destination))
    info = json.loads(root_file.with_suffix('.json').read_text())
    if Path(info['root_file']).name != root_file.name or info['b_tag'] != 'GhostBHadrons':
        raise ValueError('The run JSON does not describe this ROOT file and truth-tagging setup.')
    payload = lhe_file.read_bytes()
    if payload.startswith(b'version https://git-lfs.github.com/spec/'):
        raise ValueError('This is an LFS pointer. Run git lfs pull to download the events.')
    if hashlib.sha256(payload).hexdigest() != info['lhe_sha256']:
        raise ValueError('Use the same LHE file that was supplied to this Herwig run; its checksum differs.')
    sample = read_lhe(lhe_file)
    if len(sample.events) != info['lhe_events']:
        raise ValueError('The LHE event count does not match the run JSON.')
    parton_values, parton_weights = parton_masses(sample, min_pt, max_eta)
    stats = herwig_statistics(root_file.with_suffix('.out'))
    output, weights, cutflow = analyze(read_events(root_file), min_pt, max_eta)
    n = len(cutflow['input'])
    if n != info['requested_events'] or n != stats['generated_events']:
        raise ValueError('Incomplete/mismatched Herwig run: ROOT, requested and generated counts must agree.')
    distributions = {
        'parton': (parton_values, parton_weights, sample.weights, sample.cross_section_pb),
        'hadron': (output['m_bb'], weights['m_bb'], cutflow['input'], stats['cross_section_pb']),
    }
    report = {
        'normalization': normalization,
        'inputs': {'lhe': str(lhe_file), 'root': str(root_file)},
        'run': info, 'herwig': stats,
        'selection': {'min_pt_GeV': min_pt, 'max_abs_eta': max_eta,
                      'parton': 'both outgoing status-1 b/bbar pass acceptance',
                      'hadron': 'exactly two accepted truth b-jets',
                      'additional_lepton_selection': False},
        'event_scope': 'All events in the source LHE file versus all events in the completed '
                       'Herwig run. Selections are applied separately; records are not paired.',
        'error_note': 'sqrt(sum(w^2)), with each normalisation divisor fixed. '
                      'No inter-level correlations, integration or theory uncertainty included.',
        'mass_bins_GeV': MASS_BINS.tolist(), 'levels': {},
    }
    plots = {}
    for level, (values, selected, inclusive, cross_section) in distributions.items():
        sumw, selected_sumw = math.fsum(inclusive), math.fsum(selected)
        if sumw <= 0:
            raise ValueError(f'{level}: a positive inclusive weight sum is required.')
        if normalization == 'shape':
            if selected and selected_sumw <= 0:
                raise ValueError(f'{level}: unit-area shapes need a positive selected weight sum.')
            factor = 1.0 / selected_sumw if selected else 1.0
        else:
            factor = cross_section / sumw
        plots[level] = histogram(values, np.asarray(selected) * factor, MASS_BINS)
        report['levels'][level] = {
            'input_events': len(inclusive), 'selected_events': len(selected),
            'inclusive_sumw': sumw, 'selected_sumw': selected_sumw,
            'selected_sumw2': math.fsum(w*w for w in selected),
            'weighted_efficiency': selected_sumw / sumw,
            'cross_section_pb': cross_section,
            'selected_cross_section_pb': cross_section * selected_sumw / sumw,
            'histogram': plots[level][4],
        }

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    destination.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), layout='constrained')
    labels = {'parton': r'Parton level: LHE $b+\bar b$',
              'hadron': 'Hadron level: two truth b-jets'}
    with (destination / 'histograms.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['level', 'left', 'right', 'bin_integral', 'bin_sumw2', 'density', 'density_mc_error'])
        for (level, plot), color in zip(plots.items(), ('#1f77b4', '#ff7f0e')):
            sumw, sumw2, density, errors, _ = plot
            label = labels[level]
            if not report['levels'][level]['selected_events']:
                label += ' (no selected events)'
            ax.stairs(density, MASS_BINS, color=color, label=label)
            ax.errorbar((MASS_BINS[:-1]+MASS_BINS[1:])/2, density, yerr=errors,
                        fmt='none', ecolor=color, alpha=0.6)
            for i in range(len(MASS_BINS)-1):
                writer.writerow([level, MASS_BINS[i], MASS_BINS[i+1], sumw[i], sumw2[i], density[i], errors[i]])
    ax.set_xlabel(r'$m_{bb}$ [GeV]')
    ax.set_ylabel('Unit-area shape / GeV' if normalization == 'shape' else 'Cross section [pb/GeV]')
    ax.set_title('Bottom-pair mass before and after Herwig')
    ax.text(0.02, 0.97, rf'$p_T(b/\mathrm{{jet}}) \geq {min_pt:g}$ GeV'
            '\n' + rf'$|\eta| < {max_eta:g}$', transform=ax.transAxes,
            va='top', fontsize=10)
    ax.set_xlim(MASS_BINS[0], MASS_BINS[-1])
    ax.legend()
    fig.savefig(destination / 'm_bb_levels.pdf')
    fig.savefig(destination / 'm_bb_levels.png', dpi=160)
    plt.close(fig)
    with (destination / 'selection_table.csv').open('w', newline='') as handle:
        fields = ['level', 'input_events', 'selected_events', 'weighted_efficiency', 'selected_cross_section_pb']
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for level, row in report['levels'].items():
            writer.writerow(dict(level=level, **{key: row[key] for key in fields[1:]}))
    (destination / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lhe_file', type=Path, help='the original LHE input to this Herwig run')
    parser.add_argument('root_file', type=Path, help='HwSim ROOT file, with its .json and .out alongside')
    parser.add_argument('tag', help='name for this comparison results directory')
    parser.add_argument('--normalization', choices=['shape', 'cross-section'], default='shape')
    parser.add_argument('--min-pt', type=float, default=25.0, help='minimum pT of each b quark or jet [GeV]')
    parser.add_argument('--max-eta', type=float, default=2.5, help='maximum absolute eta for each b quark or jet')
    parser.add_argument('--output-dir', type=Path, default=Path('results'))
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', args.tag):
            raise ValueError('Use a simple results tag with no spaces or slashes.')
        destination = args.output_dir / args.tag
        if destination.exists() and any(destination.iterdir()) and not args.overwrite:
            raise ValueError('Results already exist; use a new tag or --overwrite.')
        report = compare(args.lhe_file, args.root_file, destination, args.normalization,
                         args.min_pt, args.max_eta)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    for level, row in report['levels'].items():
        print(f"{level:<8} {row['selected_events']}/{row['input_events']} selected  "
              f"efficiency={row['weighted_efficiency']:.4f}  "
              f"sigma={row['selected_cross_section_pb']:.6g} pb")
    print(f'Saved m_bb_levels.pdf/.png, histogram CSV, selection table and JSON in {destination.resolve()}')


if __name__ == '__main__':
    main()
