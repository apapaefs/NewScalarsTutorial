#!/usr/bin/env python3
"""Instructor aid: validate completed generation runs and package the LFS samples."""

import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_samples import inspect_sample
from lheanalyzer.lhe_tools import read_lhe

SPECS = [
    ('gg_h_eta0', 10000, 112345, None, [25, 99925],
     {'h': [[25], 125.0], 'eta0': [[99925], 400.0]}),
    ('gg_h_eta0_2e2mu', 10000, 123456, 134567, [-13, -11, 11, 13, 25],
     {'h': [[25], 125.0], 'four_leptons': [[-13, -11, 11, 13], 400.0]}),
    ('gg_h_eta0_bb2e2mu', 10000, 167890, 145678, [-13, -11, -5, 5, 11, 13],
     {'bb': [[-5, 5], 125.0], 'four_leptons': [[-13, -11, 11, 13], 400.0]}),
    ('pp_bbzz_2e2mu', 50000, 156789, None, [-13, -11, -5, 5, 11, 13], {}),
]


def header(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt') as handle:
        lines = []
        for line in handle:
            lines.append(line)
            if '</header>' in line:
                break
    return ''.join(lines)


def block(text, name):
    match = re.search(fr'<{name}>\s*\n(.*?)</{name}>', text, re.S | re.I)
    if not match:
        raise ValueError(f'Missing {name} card in run banner.')
    return '\n'.join(line.expandtabs(4).rstrip() for line in match[1].splitlines()) + '\n'


def decay_tables(text):
    tables = {}
    current = None
    for line in text.splitlines():
        fields = line.split('#')[0].split()
        if not fields:
            continue
        if fields[0].lower() == 'block':
            current = None
        elif fields[0].lower() == 'decay':
            current = int(fields[1])
            tables[current] = {'width': float(fields[2]), 'branches': {}}
        elif current is not None:
            tables[current]['branches'][tuple(sorted(map(int, fields[2:])))] = float(fields[0])
    return tables


def collect():
    destination = ROOT / 'samples'
    cards = ROOT / 'cards/large_samples/generated'
    destination.mkdir(exist_ok=True)
    cards.mkdir(exist_ok=True)
    entries = []
    for name, count, seed, spin_seed, pdgs, targets in SPECS:
        process = ROOT / 'Work' / name
        run_name = f'students_{count}' + ('_mc2' if count == 10000 else '')
        run = process / 'Events' / run_name
        final = run / ('unweighted_events_decayed.lhe.gz' if spin_seed else 'unweighted_events.lhe.gz')
        checked = inspect_sample(final, count, pdgs, targets)
        target = destination / f'{name}_{count}.lhe.gz'
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != checked['sha256']:
            raise ValueError(f'{target} already exists with different contents; do not overwrite it.')
        if not target.exists():
            shutil.copyfile(final, target)
        production_banner = (run / f'{run_name}_tag_1_banner.txt').read_text()
        final_header = header(final)
        entry = dict(checked, file=target.name, production_seed=seed, madspin_seed=spin_seed,
                     production_run=run_name, outgoing_pdgs=pdgs, mass_targets=targets,
                     process=('g g > h eta0 [noborn=QCD]' if count == 10000 else
                              'p p > b b~ z z QCD=2 QED=2, z > e+ e-, z > mu+ mu-'),
                     cards={})
        for label, tag in [('run', 'mgruncard'), ('parameters', 'slha'), ('process', 'mg5proccard')]:
            path = cards / f'{name}_{label}.dat'
            path.write_text(block(production_banner, tag))
            entry['cards'][label] = str(path.relative_to(ROOT))
        # The final file contains the same physical benchmark as production.
        tables = decay_tables(block(final_header, 'slha'))
        entry['widths_GeV'] = {str(pid): tables[pid]['width'] for pid in (6, 23, 25, 99925) if pid in tables}
        if spin_seed:
            production_file = run / 'unweighted_events.lhe'
            if not production_file.exists():
                production_file = run / 'unweighted_events.lhe.gz'
            production = read_lhe(production_file)
            entry['production_cross_section_pb'] = production.cross_section_pb
            entry['production_integration_error_pb'] = production.cross_section_error_pb
            entry['spinmode'] = 'none'
            entry['decay_subruns'] = {}
            factor = 1.0
            pids = (25, 99925) if 'bb2e2mu' in name else (99925,)
            for pid in pids:
                subrun = process / f'decay_{pid}_0/Events/run_01/run_01_tag_1_banner.txt'
                text = subrun.read_text()
                run_card = block(text, 'mgruncard')
                decay_seed = int(re.search(r'^\s*(\d+)\s*=\s*iseed', run_card, re.M)[1])
                width = float(re.search(r'Integrated weight \(pb\)\s*:\s*(\S+)', text)[1])
                partial_factor = width / tables[pid]['width']
                factor *= partial_factor
                path = cards / f'{name}_decay_{pid}_run.dat'
                path.write_text(run_card)
                entry['cards'][f'decay_{pid}'] = str(path.relative_to(ROOT))
                entry['decay_subruns'][str(pid)] = {'seed': decay_seed,
                    'partial_width_GeV': width, 'branching_factor': partial_factor}
            entry['decay_factor'] = factor
            measured = checked['cross_section_pb'] / production.cross_section_pb
            if not math.isclose(measured, factor, rel_tol=2e-6):
                raise ValueError(f'{name}: decay factor does not match the final LHE rate.')
            eta_br = tables[99925]['branches'][(23, 23)]
            e_br = tables[23]['branches'][(-11, 11)]
            mu_br = tables[23]['branches'][(-13, 13)]
            mixed = eta_br * 2 * e_br * mu_br
            entry['factorized_onshell_eta0_to_2e2mu_probability'] = mixed
            # Full chain uses finite-width Z propagators within bwcutoff=15.
            # This broad cross-check also catches a missing factor of two.
            eta_factor = entry['decay_subruns']['99925']['branching_factor']
            if not 0.85 < eta_factor / mixed < 1.15:
                raise ValueError(f'{name}: mixed-flavour branching-factor check failed.')
        entries.append(entry)
        print(f'Packaged {name}: {count:,} events, {checked["size_bytes"]/1e6:.2f} MB')
    manifest = {
        'schema_version': 1, 'generation_date': '2026-11-02',
        'generator': 'MadGraph5_aMC@NLO 3.5.16',
        'generator_commit': '3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7',
        'beam_energy_GeV': [6500, 6500], 'hard_pdf': 'nn23lo1',
        'scale': 'HT/2 (dynamical_scale_choice=3)', 'showered': False,
        'normalization_note': 'Use each final LHE cross section directly; specified decay factors '
                              'are already included. LHE errors exclude separate decay-integration errors.',
        'width_approximation': 'Same frozen cards as the pilot lessons. Open two-body UFO channels; '
                               'h gamma gamma is an effective vertex. No off-shell WW/ZZ Higgs decays, '
                               'loop h gg, running bottom Yukawa or higher-order corrections.',
        'samples': entries,
    }
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    collect()
