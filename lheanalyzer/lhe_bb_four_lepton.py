#!/usr/bin/env python3
"""Continue the four-lepton lesson with h -> b bbar.

The three lepton masses are complete. Follow docs/higgs_bb.md at the three
EXERCISE comments to add m_bb and pt_bb. The same selection works for the
signal and the supplied Standard Model background, using outgoing particles.
"""

import argparse
import math
from pathlib import Path
import re
import sys

import numpy as np

if __package__:
    from . import lhe_tools
    from .lhe_analyzer import invariant_mass, plot_histogram
else:
    import lhe_tools
    from lhe_analyzer import invariant_mass, plot_histogram


def validate_selection(min_lepton_pt, min_b_pt, mbb_window, m4l_window):
    for name, threshold in (("lepton", min_lepton_pt), ("b-quark", min_b_pt)):
        if not math.isfinite(threshold) or threshold < 0:
            raise ValueError(f"The {name} pT threshold must be finite and non-negative.")
    for name, window in (("bb", mbb_window), ("four-lepton", m4l_window)):
        if window is not None:
            if (len(window) != 2 or not all(math.isfinite(x) for x in window)
                    or window[0] < 0 or window[0] >= window[1]):
                raise ValueError(f"The {name} mass window needs 0 <= LOW < HIGH in GeV.")


def in_mass_window(particles, window):
    """Provided selection helper: no mass requirement unless a window is given."""
    if window is None:
        return True
    mass = invariant_mass(sum(p.energy for p in particles),
                          sum(p.px for p in particles),
                          sum(p.py for p in particles),
                          sum(p.pz for p in particles))
    return window[0] <= mass <= window[1]


def analyze(events, weights, min_lepton_pt=0.0, min_b_pt=0.0,
            mbb_window=None, m4l_window=None):
    if len(events) != len(weights):
        raise ValueError("Each event must have exactly one weight.")
    validate_selection(min_lepton_pt, min_b_pt, mbb_window, m4l_window)

    # STEP 1: One empty list per observable, before the event loop.
    output = {}
    output["m_ee"] = []
    output["m_mumu"] = []
    output["m_4l"] = []
    # EXERCISE LISTS: add your new lists immediately above this comment.

    selected_weights = []
    cutflow = {name: [] for name in ("input", "correct_final_state", "lepton_pt",
                                    "b_pt", "mbb_window", "m4l_window")}
    checks = {"max_four_momentum_residual_GeV": 0.0}
    for particles, weight in zip(events, weights):
        cutflow["input"].append(weight)
        outgoing = [p for p in particles if p.status == 1]
        # Six outgoing particles now: b, bbar and the four leptons.
        # Do not count an intermediate Higgs, eta0 or Z as an extra particle.
        if sorted(p.pdg for p in outgoing) != [-13, -11, -5, 5, 11, 13]:
            continue
        b = next(p for p in outgoing if p.pdg == 5)
        bbar = next(p for p in outgoing if p.pdg == -5)
        electron = next(p for p in outgoing if p.pdg == 11)
        positron = next(p for p in outgoing if p.pdg == -11)
        muon = next(p for p in outgoing if p.pdg == 13)
        antimuon = next(p for p in outgoing if p.pdg == -13)
        leptons = [electron, positron, muon, antimuon]
        cutflow["correct_final_state"].append(weight)

        # Signal: incoming gluons. Background: gluons or light quarks.
        incoming = [p for p in particles if p.status == -1]
        allowed = {21, 1, -1, 2, -2, 3, -3, 4, -4}
        if len(incoming) != 2 or any(p.pdg not in allowed for p in incoming):
            raise ValueError("Expected two incoming gluons or u/d/s/c quarks and antiquarks.")
        for component in ("energy", "px", "py", "pz"):
            residual = (math.fsum(getattr(p, component) for p in incoming)
                        - math.fsum(getattr(p, component) for p in outgoing))
            checks["max_four_momentum_residual_GeV"] = max(
                checks["max_four_momentum_residual_GeV"], abs(residual))

        passes_lepton_cut = True
        for lepton in leptons:
            if math.sqrt(lepton.px**2 + lepton.py**2) < min_lepton_pt:
                passes_lepton_cut = False
        if not passes_lepton_cut:
            continue
        cutflow["lepton_pt"].append(weight)

        pt_b = math.sqrt(b.px**2 + b.py**2)
        pt_bbar = math.sqrt(bbar.px**2 + bbar.py**2)
        if pt_b < min_b_pt or pt_bbar < min_b_pt:
            continue
        cutflow["b_pt"].append(weight)
        if not in_mass_window([b, bbar], mbb_window):
            continue
        cutflow["mbb_window"].append(weight)
        if not in_mass_window(leptons, m4l_window):
            continue
        cutflow["m4l_window"].append(weight)

        # STEP 2: The completed calculations from the four-lepton exercise.
        m_ee = invariant_mass(
            electron.energy + positron.energy, electron.px + positron.px,
            electron.py + positron.py, electron.pz + positron.pz,
        )
        m_mumu = invariant_mass(
            muon.energy + antimuon.energy, muon.px + antimuon.px,
            muon.py + antimuon.py, muon.pz + antimuon.pz,
        )
        energy_4l = (electron.energy + positron.energy
                     + muon.energy + antimuon.energy)
        px_4l = electron.px + positron.px + muon.px + antimuon.px
        py_4l = electron.py + positron.py + muon.py + antimuon.py
        pz_4l = electron.pz + positron.pz + muon.pz + antimuon.pz
        m_4l = invariant_mass(energy_4l, px_4l, py_4l, pz_4l)
        output["m_ee"].append(m_ee)
        output["m_mumu"].append(m_mumu)
        output["m_4l"].append(m_4l)
        # EXERCISE CALCULATIONS: calculate and append your new observables here.

        selected_weights.append(weight)

    if not cutflow["correct_final_state"]:
        raise ValueError("No compatible events: expected b, bbar, e-, e+, mu-, mu+ "
                         "as the six status-1 particles. Use the Higgs-decay sample.")
    return output, selected_weights, checks, cutflow


def make_plots(output, weights, output_dir, normalization):
    per_gev = ("Cross section [pb/GeV]" if normalization == "cross-section"
               else "Weighted fraction / GeV")
    title = r"$b\bar b e^+e^-\mu^+\mu^-$ (parton level)"
    plots = {}
    plots["m_ee"] = plot_histogram(
        output["m_ee"], weights, bins=np.linspace(0, 200, 51),
        xlabel=r"$m(e^+e^-)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "m_ee", title=title,
    )
    plots["m_mumu"] = plot_histogram(
        output["m_mumu"], weights, bins=np.linspace(0, 200, 51),
        xlabel=r"$m(\mu^+\mu^-)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "m_mumu", title=title,
    )
    # A wider range also shows the continuum background; 400 is a bin centre.
    plots["m_4l"] = plot_histogram(
        output["m_4l"], weights, bins=np.linspace(150, 1150, 51),
        xlabel=r"$m(e^+e^-\mu^+\mu^-)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "m_4l", title=title,
    )
    # EXERCISE PLOTS: add new plot calls immediately above this comment.
    return plots


def get_arguments():
    parser = argparse.ArgumentParser(description="Analyse b bbar + four leptons at parton level.")
    parser.add_argument("lhe_file", type=Path, help="signal or background .lhe or .lhe.gz file")
    parser.add_argument("tag", help="name for this results folder")
    parser.add_argument("--min-lepton-pt", type=float, default=0.0, metavar="GEV",
                        help="minimum pT of each lepton (default: 0)")
    parser.add_argument("--min-b-pt", type=float, default=0.0, metavar="GEV",
                        help="minimum pT of EACH bottom quark (default: 0)")
    parser.add_argument("--mbb-window", type=float, nargs=2, metavar=("LOW", "HIGH"),
                        help="inclusive bb mass window in GeV (default: off)")
    parser.add_argument("--m4l-window", type=float, nargs=2, metavar=("LOW", "HIGH"),
                        help="inclusive four-lepton mass window in GeV (default: off)")
    parser.add_argument("--normalization", choices=["cross-section", "shape"],
                        default="cross-section", help="rates or fractions of all input events")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--overwrite", action="store_true", help="replace this run's existing outputs")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.tag):
        parser.error("tag must start with a letter/digit and contain no spaces or slashes")
    try:
        validate_selection(args.min_lepton_pt, args.min_b_pt, args.mbb_window, args.m4l_window)
    except ValueError as error:
        parser.error(str(error))
    destination = args.output_dir / args.tag
    if destination.exists() and any(destination.iterdir()) and not args.overwrite:
        parser.error(f"{destination} is non-empty; use another tag or --overwrite.")
    return args


def main():
    args = get_arguments()
    sample = lhe_tools.read_lhe(args.lhe_file)
    output, selected, checks, cutflow = analyze(
        sample.events, sample.weights, args.min_lepton_pt, args.min_b_pt,
        args.mbb_window, args.m4l_window)
    # Both event files already include the probabilities of their specified decays.
    total = sample.cross_section_pb if args.normalization == "cross-section" else 1.0
    plot_weights = np.asarray(selected) * total / math.fsum(sample.weights)
    destination = args.output_dir / args.tag
    destination.mkdir(parents=True, exist_ok=True)
    plots = make_plots(output, plot_weights, destination, args.normalization)
    summary = lhe_tools.save_report(
        sample, selected, checks, plots, destination, args.normalization, args.lhe_file,
        selection={"final_state": "b b~ e- e+ mu- mu+", "level": "parton",
                   "min_lepton_pt_GeV": args.min_lepton_pt, "min_b_pt_GeV": args.min_b_pt,
                   "mbb_window_GeV": args.mbb_window, "m4l_window_GeV": args.m4l_window},
        cutflow=cutflow,
    )
    labels = ["All input events", "Correct particles", "Lepton pT cut", "Bottom-quark pT cut",
              "bb mass window", "Four-lepton mass window"]
    print("Stage                       Events   Weighted efficiency   Cross section [pb]")
    for label, row in zip(labels, summary["cutflow"]):
        print(f"{label:<27} {row['events']:>6}   "
              f"{row['weighted_efficiency']:>19.6g}   {row['cross_section_pb']:.6g}")
    print("Mass windows are off unless supplied on the command line.")
    print(f"Saved {len(plots)} observable plots, each as PNG and PDF, in {destination.resolve()}")
    first = "m_bb" if "m_bb" in plots else "m_ee"
    print(f"Open this plot first: {destination.resolve() / (first + '.png')}")
    for name, flow in summary["histograms"].items():
        if flow["underflow_entries"] or flow["overflow_entries"]:
            print(f"{name}: {flow['underflow_entries']} underflow, "
                  f"{flow['overflow_entries']} overflow entries; consider wider bins.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, EOFError) as error:
        sys.exit(f"Analysis failed: {error}")
