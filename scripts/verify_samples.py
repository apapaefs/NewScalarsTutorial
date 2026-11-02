#!/usr/bin/env python3
"""Verify the downloaded classroom LHE files against samples/manifest.json."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lheanalyzer.lhe_tools import read_lhe
from lheanalyzer.lhe_analyzer import invariant_mass


def inspect_sample(path, expected_events, outgoing_pdgs, mass_targets):
    with Path(path).open('rb') as handle:
        if handle.read(80).startswith(b'version https://git-lfs.github.com/spec/'):
            raise ValueError(f'{path}: only an LFS pointer is present. Run git lfs pull.')
    sample = read_lhe(path)
    if len(sample.events) != expected_events:
        raise ValueError(f'{path}: expected {expected_events} events, found {len(sample.events)}.')
    if any(w <= 0 or not math.isclose(w, sample.weights[0], rel_tol=1e-6) for w in sample.weights):
        raise ValueError(f'{path}: expected equal, positive event weights.')
    sumw = math.fsum(sample.weights)
    if not math.isclose(sumw, sample.cross_section_pb, rel_tol=2e-6):
        raise ValueError(f'{path}: weight sum does not reproduce the LHE cross section.')
    residual = 0.0
    mass_errors = {name: 0.0 for name in mass_targets}
    unique = set()
    for event in sample.events:
        outgoing = [p for p in event if p.status == 1]
        incoming = [p for p in event if p.status == -1]
        if sorted(p.pdg for p in outgoing) != sorted(outgoing_pdgs) or len(incoming) != 2:
            raise ValueError(f'{path}: incorrect incoming/outgoing particle records.')
        if any(p.pdg not in (21, 1, -1, 2, -2, 3, -3, 4, -4) for p in incoming):
            raise ValueError(f'{path}: unexpected incoming flavour.')
        if mass_targets and any(p.pdg != 21 for p in incoming):
            raise ValueError(f'{path}: the signal must have two incoming gluons.')
        unique.add(tuple(tuple(p) for p in outgoing))
        for component in ('energy', 'px', 'py', 'pz'):
            residual = max(residual, abs(math.fsum(getattr(p, component) for p in incoming)
                                         - math.fsum(getattr(p, component) for p in outgoing)))
        for name, (pdgs, target) in mass_targets.items():
            particles = [p for p in outgoing if p.pdg in pdgs]
            mass = invariant_mass(*(math.fsum(getattr(p, c) for p in particles)
                                    for c in ('energy', 'px', 'py', 'pz')))
            mass_errors[name] = max(mass_errors[name], abs(mass-target))
    if residual > 5e-5 or any(error > 1e-4 for error in mass_errors.values()):
        raise ValueError(f'{path}: momentum conservation or mass check failed.')
    if len(unique) != expected_events:
        raise ValueError(f'{path}: duplicate final-state momentum records found.')
    return {'events': len(sample.events), 'unique_events': len(unique),
            'cross_section_pb': sample.cross_section_pb,
            'cross_section_error_pb': sample.cross_section_error_pb,
            'sum_weights': sumw, 'negative_weight_events': 0,
            'max_four_momentum_residual_GeV': residual,
            'max_mass_errors_GeV': mass_errors,
            'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'size_bytes': Path(path).stat().st_size}


def verify(manifest_path):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    total = 0
    for entry in manifest['samples']:
        path = manifest_path.parent / entry['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            if path.read_bytes()[:80].startswith(b'version https://git-lfs.github.com/spec/'):
                raise ValueError(f'{path}: LFS pointer only. Run git lfs pull.')
            raise ValueError(f'{path}: checksum mismatch. Download the sample again.')
        checked = inspect_sample(path, entry['events'], entry['outgoing_pdgs'], entry['mass_targets'])
        for key in ('size_bytes', 'unique_events', 'cross_section_pb', 'cross_section_error_pb'):
            if checked[key] != entry[key]:
                raise ValueError(f'{path}: {key} differs from the manifest.')
        if 'decay_factor' in entry:
            ratio = checked['cross_section_pb'] / entry['production_cross_section_pb']
            if not math.isclose(ratio, entry['decay_factor'], rel_tol=2e-6):
                raise ValueError(f'{path}: inconsistent decay normalisation.')
        total += checked['events']
        print(f"{entry['file']}: {checked['events']:,} events; checksum, momenta and normalisation OK")
    print(f'Total: {total:,} events in {len(manifest["samples"])} independent samples.')
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'samples/manifest.json')
    args = parser.parse_args()
    try:
        verify(args.manifest)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
