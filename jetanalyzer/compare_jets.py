#!/usr/bin/env python3
"""Overlay two saved jet analyses, using either rates or unit-area shapes."""

import argparse
import csv
import json
from pathlib import Path
import re

import numpy as np

try:
    from .hwsim_jets import OBSERVABLES
except ImportError:
    from hwsim_jets import OBSERVABLES


def read_result(path):
    summary = json.loads((path / 'summary.json').read_text())
    if summary['normalization'] != 'cross-section':
        raise ValueError('Use cross-section-normalised analyser outputs as the comparison inputs.')
    with (path / 'histograms.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    data = {name: [r for r in rows if r['observable'] == name]
            for name in summary['histograms']}
    return summary, data


def compare(first, second, destination, normalization='shape'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    a, b = read_result(first), read_result(second)
    if a[0]['selection'] != b[0]['selection']:
        raise ValueError('Apply the same jet selections to both samples before comparing them.')
    for field in ('jet_algorithm', 'jet_radius', 'b_tag', 'mpi', 'common_card_sha256'):
        if a[0]['run'][field] != b[0]['run'][field]:
            raise ValueError(f'Different shower/object settings: {field}.')
    if set(a[1]) != set(b[1]):
        raise ValueError('Both analyses must contain the same observables; rerun both after an edit.')
    report = {'normalization': normalization, 'inputs': [str(first), str(second)],
              'integrals_including_flow': {}, 'selection': a[0]['selection']}
    # Validate binning before writing any plot.
    for name in a[1]:
        if [(r['left'], r['right']) for r in a[1][name]] != [(r['left'], r['right']) for r in b[1][name]]:
            raise ValueError(f'Different bins for {name}.')
    destination.mkdir(parents=True, exist_ok=True)
    for name in a[1]:
        fig, ax = plt.subplots(figsize=(7, 5), layout='constrained')
        report['integrals_including_flow'][name] = []
        for (summary, data), label, color in zip((a, b), ('Signal', 'Background'),
                                                ('#1f77b4', '#ff7f0e')):
            rows = data[name]
            edges = np.array([float(r['left']) for r in rows] + [float(rows[-1]['right'])])
            flow = summary['histograms'][name]
            total = sum(float(r['bin_integral']) for r in rows) + flow['underflow_integral'] + flow['overflow_integral']
            divisor = total if normalization == 'shape' and total > 0 else 1.0
            y = np.array([float(r['density']) for r in rows]) / divisor
            err = np.array([float(r['density_mc_error']) for r in rows]) / abs(divisor)
            ax.stairs(y, edges, label=label, color=color)
            ax.errorbar((edges[:-1]+edges[1:])/2, y, yerr=err, fmt='none', ecolor=color, alpha=0.6)
            report['integrals_including_flow'][name].append(total / divisor)
        xlabel, _, gev = OBSERVABLES[name]
        ax.set_xlabel(xlabel)
        ylabel = 'Unit-area shape' if normalization == 'shape' else 'Cross section [pb]'
        ax.set_ylabel(ylabel + (' / GeV' if gev else ' / bin'))
        if normalization == 'cross-section':
            ax.set_yscale('log')
        ax.legend()
        ax.set_xlim(edges[0], edges[-1])
        fig.savefig(destination / f'{name}.pdf')
        fig.savefig(destination / f'{name}.png', dpi=160)
        plt.close(fig)
    with (destination / 'selection_table.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['sample', 'stage', 'events', 'weighted_efficiency', 'cross_section_pb'])
        for result, label in zip((a, b), ('signal', 'background')):
            for row in result[0]['cutflow']:
                writer.writerow([label, row['stage'], row['events'], row['weighted_efficiency'], row['cross_section_pb']])
    (destination / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('signal', type=Path)
    parser.add_argument('background', type=Path)
    parser.add_argument('tag')
    parser.add_argument('--normalization', choices=['shape', 'cross-section'], default='shape')
    parser.add_argument('--output-dir', type=Path, default=Path('results'))
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', args.tag):
            raise ValueError('Use a simple results tag with no spaces or slashes.')
        destination = args.output_dir / args.tag
        if destination.exists() and any(destination.iterdir()) and not args.overwrite:
            raise ValueError('Results already exist; use a new tag or --overwrite.')
        compare(args.signal, args.background, destination, args.normalization)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    print(f'Saved overlays and selection_table.csv in {destination.resolve()}')


if __name__ == '__main__':
    main()
