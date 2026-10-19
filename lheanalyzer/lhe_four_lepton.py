#!/usr/bin/env python3
"""Reconstruct eta0 -> Z Z -> e+ e- mu+ mu- with the associated Higgs stable.

The starter plots m_ee. Follow docs/four_lepton.md to add m_mumu and m_4l.
Start at the three EXERCISE comments in analyze() and make_plots().
The file-reading, checks and report-writing code is already provided.
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


def analyze(events, weights, min_lepton_pt=0.0):
    """Select the five outgoing particles, apply a cut, and reconstruct m_ee."""
    # Each event needs one weight. Check the lengths before pairing them below.
    if len(events) != len(weights):
        raise ValueError("Each event must have exactly one weight; "
                         "the event and weight lists have different lengths.")
    if not math.isfinite(min_lepton_pt) or min_lepton_pt < 0:
        raise ValueError("The lepton pT threshold must be finite and non-negative.")

    # STEP 1: Create one list per observable, BEFORE the event loop.
    output = {}             # A dictionary: a name attached to each list.
    output["m_ee"] = []     # An empty list; append one mass per selected event.
    # EXERCISE LISTS: add your new lists here.

    selected_weights = []
    cutflow = {"input": [], "correct_final_state": [], "lepton_pt": []}
    checks = {"max_four_momentum_residual_GeV": 0.0}

    # Work through one event and its weight at a time.
    for particles, weight in zip(events, weights):
        cutflow["input"].append(weight)
        # Status 2 denotes intermediate particles; counting them here would
        # double-count their decay products. The stable Higgs has status 1.
        outgoing = [p for p in particles if p.status == 1]
        # Compare the particle codes, including duplicates, with the five we need.
        if sorted(p.pdg for p in outgoing) != [-13, -11, 11, 13, 25]:
            continue
        # next(...) finds the one outgoing particle with the requested code.
        h = next(p for p in outgoing if p.pdg == 25)
        electron = next(p for p in outgoing if p.pdg == 11)
        positron = next(p for p in outgoing if p.pdg == -11)
        muon = next(p for p in outgoing if p.pdg == 13)
        antimuon = next(p for p in outgoing if p.pdg == -13)
        leptons = [electron, positron, muon, antimuon]
        cutflow["correct_final_state"].append(weight)

        # Check every event with the correct final state, even if the pT cut
        # below rejects it. Only incoming and outgoing records enter this sum.
        incoming = [p for p in particles if p.status == -1]
        if len(incoming) != 2 or any(p.pdg != 21 for p in incoming):
            raise ValueError("Expected two incoming gluons (PDG 21, status -1).")
        for component in ("energy", "px", "py", "pz"):
            residual = math.fsum(getattr(p, component) for p in incoming) - math.fsum(
                getattr(p, component) for p in [h] + leptons)
            checks["max_four_momentum_residual_GeV"] = max(
                checks["max_four_momentum_residual_GeV"], abs(residual))

        # Check each lepton in turn. The whole event must pass the selection.
        passes_lepton_cut = True
        for lepton in leptons:
            pt_lepton = math.sqrt(lepton.px**2 + lepton.py**2)
            if pt_lepton < min_lepton_pt:
                passes_lepton_cut = False
        if not passes_lepton_cut:
            # continue means: skip the rest of this event and start the next one.
            continue
        cutflow["lepton_pt"].append(weight)

        # STEP 2: Add four-momenta first, then calculate an invariant mass.
        m_ee = invariant_mass(
            electron.energy + positron.energy,
            electron.px + positron.px,
            electron.py + positron.py,
            electron.pz + positron.pz,
        )
        output["m_ee"].append(m_ee)   # Store this event's electron-pair mass.
        # EXERCISE CALCULATIONS: calculate and append your new masses here.

        selected_weights.append(weight)

    if not cutflow["correct_final_state"]:
        raise ValueError("No compatible events: expected one stable Higgs and "
                         "e- e+ mu- mu+ (status 1), with no other outgoing particles.")
    # A valid sample can have no events passing the cut: empty histograms and
    # a zero last cutflow row are useful results, not an incompatible file.
    return output, selected_weights, checks, cutflow


def make_plots(output, weights, output_dir, normalization):
    """STEP 3: Copy the m_ee call to add your two new plots."""
    per_gev = ("Cross section [pb/GeV]" if normalization == "cross-section"
               else "Weighted fraction / GeV")
    plots = {}
    plots["m_ee"] = plot_histogram(
        output["m_ee"], weights,
        bins=np.linspace(0, 200, 51),
        xlabel=r"$m(e^+e^-)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "m_ee",
    )
    # EXERCISE PLOTS: add your new plot calls here, before return.
    return plots


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Reconstruct eta0 -> Z Z -> e+ e- mu+ mu- with a stable Higgs.")
    parser.add_argument("lhe_file", type=Path, help="path to the decayed .lhe or .lhe.gz sample")
    parser.add_argument("tag", nargs="?", default="four_lepton",
                        help="name for your results folder (default: four_lepton)")
    parser.add_argument("--min-lepton-pt", type=float, default=0.0, metavar="GEV",
                        help="minimum pT of each of the four leptons (default: 0)")
    parser.add_argument("--normalization", choices=["cross-section", "shape"],
                        default="cross-section", help="plot rates or fractions of the input sample")
    parser.add_argument("--output-dir", type=Path, default=Path("results"),
                        help="parent folder for results (default: results)")
    parser.add_argument("--overwrite", action="store_true",
                        help="replace existing plots and reports for this results name")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.tag):
        parser.error("tag must start with a letter/digit and contain no spaces or slashes")
    if not math.isfinite(args.min_lepton_pt) or args.min_lepton_pt < 0:
        parser.error("--min-lepton-pt must be finite and non-negative")
    destination = args.output_dir / args.tag
    if destination.exists() and any(destination.iterdir()) and not args.overwrite:
        parser.error(f"{destination} is non-empty; use another tag or --overwrite.")
    return args


def main():
    args = get_arguments()
    sample = lhe_tools.read_lhe(args.lhe_file)
    output, selected, checks, cutflow = analyze(
        sample.events, sample.weights, args.min_lepton_pt)
    # The decayed LHE cross section ALREADY includes the decay branching factor.
    # All input weights stay in the denominator after selection.
    total = sample.cross_section_pb if args.normalization == "cross-section" else 1.0
    plot_weights = np.asarray(selected) * total / math.fsum(sample.weights)
    destination = args.output_dir / args.tag
    destination.mkdir(parents=True, exist_ok=True)
    plots = make_plots(output, plot_weights, destination, args.normalization)
    summary = lhe_tools.save_report(
        sample, selected, checks, plots, destination, args.normalization, args.lhe_file,
        selection={"final_state": "h e- e+ mu- mu+", "higgs_stable": True,
                   "min_lepton_pt_GeV": args.min_lepton_pt}, cutflow=cutflow,
    )
    print("Stage                    Events   Weighted efficiency   Cross section [pb]")
    stage_labels = {"input": "All input events", "correct_final_state": "Correct particles",
                    "lepton_pt": "Lepton pT cut"}
    for row in summary["cutflow"]:
        print(f"{stage_labels[row['stage']]:<24} {row['events']:>6}   "
              f"{row['weighted_efficiency']:>19.6g}   {row['cross_section_pb']:.6g}")
    print(f"Output: {destination.resolve()}")
    print(f"Saved {len(plots)} mass plot(s), each as PNG and PDF.")
    print(f"Open this plot first: {destination.resolve() / 'm_ee.png'}")
    for name, flow in summary["histograms"].items():
        if flow["underflow_entries"] or flow["overflow_entries"]:
            print(f"{name}: {flow['underflow_entries']} underflow, "
                  f"{flow['overflow_entries']} overflow entries; consider wider bins.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, EOFError) as error:
        sys.exit(f"Analysis failed: {error}")
