#!/usr/bin/env python3
"""Prepare a separate Herwig run from a checked b bbar + four-lepton LHE file."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lheanalyzer.lhe_tools import read_lhe


def prepare(lhe, tag, events=1000, seed=22001, radius=0.4, mpi=True):
    if Path.cwd().resolve() != ROOT:
        raise ValueError("Run this command from the NewScalarsTutorial directory.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", tag):
        raise ValueError("Use a tag containing letters, digits, underscores or hyphens.")
    if events < 1 or not 0 < seed < 900000000:
        raise ValueError("Use a positive event count and a seed between 1 and 899999999.")
    if not math.isfinite(radius) or not 0.1 <= radius <= 1.5:
        raise ValueError("Use a jet radius between 0.1 and 1.5.")
    lhe = Path(lhe).resolve()
    try:
        relative = lhe.relative_to(ROOT)
    except ValueError:
        raise ValueError("Place the LHE file inside this repository, e.g. in Work/events/.")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", str(relative)):
        raise ValueError("The input path must not contain spaces or command characters.")
    if lhe.read_bytes()[:42].startswith(b"version https://git-lfs.github.com/spec/"):
        raise ValueError("This is an LFS pointer. Run git lfs pull to download the events.")
    sample = read_lhe(lhe)
    if events > len(sample.events):
        raise ValueError(f"Requested {events} events, but this file contains {len(sample.events)}.")
    expected = [-13, -11, -5, 5, 11, 13]
    if any(sorted(p.pdg for p in event if p.status == 1) != expected
           for event in sample.events):
        raise ValueError("Use the fully decayed bb2e2mu signal or background sample.")
    # This lesson's rate normalisation assumes positive, equal-weight input.
    if any(w <= 0 or not math.isclose(w, sample.weights[0], rel_tol=1e-6)
           for w in sample.weights):
        raise ValueError("This shower lesson requires positive, equal-weight LHE events.")
    destination = ROOT / 'Work/herwig'
    destination.mkdir(parents=True, exist_ok=True)
    prefix = destination / tag
    if list(destination.glob(tag + '.*')):
        raise ValueError(f"Run {tag!r} already exists. Choose a new tag.")
    text = ('read herwig/LHE-HwSim.in\n'
            f'set /Herwig/EventHandlers/TutorialReader:FileName {relative}\n'
            f'set /Herwig/Analysis/TutorialHwSim:RParameter {radius}\n'
            f'set /Herwig/Generators/EventGenerator:NumberOfEvents {events}\n'
            f'set /Herwig/Generators/EventGenerator:RandomNumberGenerator:Seed {seed}\n')
    if not mpi:
        text += 'set /Herwig/Shower/ShowerHandler:MPIHandler NULL\n'
    text += f'saverun Work/herwig/{tag} /Herwig/Generators/EventGenerator\n'
    Path(str(prefix) + '.in').write_text(text)
    info = {
        'schema_version': 1, 'tag': tag, 'lhe_file': str(relative),
        'lhe_sha256': hashlib.sha256(lhe.read_bytes()).hexdigest(),
        'lhe_events': len(sample.events), 'requested_events': events, 'seed': seed,
        'cross_section_pb': sample.cross_section_pb,
        'cross_section_error_pb': sample.cross_section_error_pb,
        'jet_algorithm': 'anti-kt', 'jet_radius': radius,
        'b_tag': 'GhostBHadrons', 'mpi': mpi,
        'root_file': f'Work/herwig/{tag}.root',
        'common_card_sha256': hashlib.sha256((ROOT / 'herwig/LHE-HwSim.in').read_bytes()).hexdigest(),
        'normalization_note': 'Use the LHE rate once; includes the specified decays. '
                              'No branching-factor multiplication or hard-PDF reweighting.',
    }
    Path(str(prefix) + '.json').write_text(json.dumps(info, indent=2) + '\n')
    return prefix.relative_to(ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lhe_file', type=Path)
    parser.add_argument('tag')
    parser.add_argument('--events', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=22001)
    parser.add_argument('--radius', type=float, default=0.4)
    parser.add_argument('--no-mpi', action='store_true')
    args = parser.parse_args()
    try:
        path = prepare(args.lhe_file, args.tag, args.events, args.seed, args.radius, not args.no_mpi)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f'Prepared {path}.in and {path}.json. Next run:')
    print(f'Herwig read {path}.in')
    print(f'Herwig run {path}.run')


if __name__ == '__main__':
    main()
