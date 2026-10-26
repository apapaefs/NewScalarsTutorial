#!/usr/bin/env python3
"""Student analysis of g g > h eta0 events.

Start with analyze() and make_plots(). The README works through adding a plot.
Adapted from Andreas Papaefstathiou's lheanalyzer; see UPSTREAM.md.
"""

import math
import sys

import numpy as np

# This allows both "python lheanalyzer/lhe_analyzer.py ..." and Python imports.
if __package__:
    from . import lhe_tools
else:
    import lhe_tools


def invariant_mass(energy, px, py, pz):
    """Calculate m from m^2 = E^2 - px^2 - py^2 - pz^2, in GeV."""
    mass2 = energy**2 - px**2 - py**2 - pz**2
    if mass2 < -1e-9 * max(energy**2, px**2 + py**2 + pz**2, 1.0):
        raise ValueError("A selected four-vector is spacelike; inspect the event.")
    # Small negative values can arise from rounding a nearly massless momentum.
    return math.sqrt(max(0.0, mass2))


def rapidity(particle):
    """Calculate y = (1/2) log((E + pz)/(E - pz))."""
    if particle.energy <= abs(particle.pz):
        raise ValueError("Rapidity is undefined for this selected four-vector.")
    return 0.5 * math.log((particle.energy + particle.pz)
                          / (particle.energy - particle.pz))


def analyze(events, weights, min_pt_h=0.0):
    """Loop over events and return the quantities we want to plot."""

    # Each event needs one weight. Check this before zip, which would otherwise
    # silently stop at the end of the shorter list.
    if len(events) != len(weights):
        raise ValueError("Each event must have exactly one weight; "
                         "the event and weight lists have different lengths.")

    # STEP 1: Make an empty list for each quantity. Each list will receive one
    # number per selected event. Add the list for your own quantity here.
    output = {}
    output["pt_h"] = []
    output["pt_eta0"] = []
    output["m_h_eta0"] = []
    output["y_h"] = []
    output["y_eta0"] = []
    output["delta_phi"] = []

    selected_weights = []
    checks = {"max_pt_imbalance_GeV": 0.0, "max_pair_pt_GeV": 0.0,
              "max_four_momentum_residual_GeV": 0.0}

    # zip gives us an event and its weight together on each pass through the loop.
    for particles, weight in zip(events, weights):
        # Select particles leaving the hard collision: LHE status 1.
        outgoing = [p for p in particles if p.status == 1]
        higgs = [p for p in outgoing if p.pdg == 25]
        etas = [p for p in outgoing if p.pdg == 99925]
        if len(outgoing) != 2 or len(higgs) != 1 or len(etas) != 1:
            continue
        h = higgs[0]
        eta = etas[0]

        # STEP 2: Calculate quantities for THIS event. Components are in GeV.
        pt_h = math.sqrt(h.px**2 + h.py**2)
        pt_eta0 = math.sqrt(eta.px**2 + eta.py**2)
        if pt_h < min_pt_h:
            continue

        m_h_eta0 = invariant_mass(h.energy + eta.energy, h.px + eta.px,
                                  h.py + eta.py, h.pz + eta.pz)
        y_h = rapidity(h)
        y_eta0 = rapidity(eta)
        phi_h = math.atan2(h.py, h.px)
        phi_eta0 = math.atan2(eta.py, eta.px)
        delta_phi = abs(math.remainder(phi_h - phi_eta0, 2 * math.pi))

        # append adds one number to the end of a list. Keep these lines INSIDE
        # the event loop, so that every selected event contributes an entry.
        output["pt_h"].append(pt_h)
        output["pt_eta0"].append(pt_eta0)
        output["m_h_eta0"].append(m_h_eta0)
        output["y_h"].append(y_h)
        output["y_eta0"].append(y_eta0)
        output["delta_phi"].append(delta_phi)
        # Add your new calculation and append its value here.

        selected_weights.append(weight)
        lhe_tools.check_momenta(particles, h, eta, checks)

    if not selected_weights:
        raise ValueError("No selected events. Use undecayed g g > h eta0 events "
                         "with outgoing PDGs 25 and 99925, or loosen the cut.")
    return output, selected_weights, checks


def plot_histogram(values, weights, bins, xlabel, ylabel, filename, *,
                   title=r"$g g \rightarrow h\,\eta_0$ (parton level)"):
    """Draw ONE histogram. Copy a call in make_plots() to create another plot.

    values: one measured number per event; weights: one normalised event weight.
    bins: bin edges, e.g. np.linspace(0, 600, 31) gives 30 bins of width 20 GeV.
    filename: output path without .pdf or .png; both files will be written.
    """
    import matplotlib
    matplotlib.use("Agg")   # Save plots to files, including on a remote computer.
    import matplotlib.pyplot as plt

    # The helper adds weights in each bin and divides by the bin width.
    # Statistical errors use the sum of SQUARED weights in that bin.
    sumw, sumw2, heights, errors, flow = lhe_tools.histogram(values, weights, bins)
    centres = (bins[:-1] + bins[1:]) / 2

    fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
    ax.stairs(heights, bins, color="teal")
    ax.errorbar(centres, heights, yerr=errors, fmt="none", ecolor="teal")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xlim(bins[0], bins[-1])
    fig.savefig(str(filename) + ".pdf")
    fig.savefig(str(filename) + ".png", dpi=160)
    plt.close(fig)

    # These numbers are also saved to histograms.csv and summary.json.
    return {"edges": bins, "sumw": sumw, "sumw2": sumw2, "density": heights,
            "error": errors, "flow": flow}


def make_plots(output, weights, output_dir, normalization):
    """STEP 3: One explicit call per plot. Add your new call before return."""
    if normalization == "cross-section":
        per_gev = "Cross section [pb/GeV]"
        per_unit = "Cross section [pb]"
        per_radian = "Cross section [pb/rad]"
    else:
        per_gev = "Weighted fraction / GeV"
        per_unit = "Weighted fraction / unit rapidity"
        per_radian = "Weighted fraction / rad"

    plots = {}
    plots["pt_h"] = plot_histogram(
        output["pt_h"], weights,
        bins=np.linspace(0, 600, 31),
        xlabel=r"$p_T(h)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "pt_h",
    )
    plots["pt_eta0"] = plot_histogram(
        output["pt_eta0"], weights,
        bins=np.linspace(0, 600, 31),
        xlabel=r"$p_T(\eta_0)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "pt_eta0",
    )
    plots["m_h_eta0"] = plot_histogram(
        output["m_h_eta0"], weights,
        bins=np.linspace(0, 2000, 41),
        xlabel=r"$m(h\eta_0)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "m_h_eta0",
    )
    plots["y_h"] = plot_histogram(
        output["y_h"], weights,
        bins=np.linspace(-6, 6, 31),
        xlabel=r"$y(h)$", ylabel=per_unit,
        filename=output_dir / "y_h",
    )
    plots["y_eta0"] = plot_histogram(
        output["y_eta0"], weights,
        bins=np.linspace(-6, 6, 31),
        xlabel=r"$y(\eta_0)$", ylabel=per_unit,
        filename=output_dir / "y_eta0",
    )
    plots["delta_phi"] = plot_histogram(
        output["delta_phi"], weights,
        bins=np.linspace(0, math.pi, 33),
        xlabel=r"$\Delta\phi(h,\eta_0)$ [rad]", ylabel=per_radian,
        filename=output_dir / "delta_phi",
    )
    # Add your new plot here.
    return plots


def main():
    args = lhe_tools.get_arguments()
    sample = lhe_tools.read_lhe(args.lhe_file)
    output, selected, checks = analyze(sample.events, sample.weights, args.min_pt_h)

    # Convert the nominal LHE weights into contributions to the cross section.
    # Keep ALL input weights in the denominator, even when a cut rejects events.
    total = sample.cross_section_pb if args.normalization == "cross-section" else 1.0
    plot_weights = np.asarray(selected) * total / math.fsum(sample.weights)

    destination = args.output_dir / args.tag
    destination.mkdir(parents=True, exist_ok=True)
    plots = make_plots(output, plot_weights, destination, args.normalization)
    summary = lhe_tools.save_report(sample, selected, checks, plots, destination,
                                    args.normalization, args.lhe_file, args.min_pt_h)
    print(f"Selected {len(selected)}/{len(sample.events)} events")
    print(f"Inclusive cross section: {sample.cross_section_pb:.6g} pb (LHE init)")
    print(f"Selected cross section: {summary['selected_cross_section_pb']:.6g} pb")
    print(f"Output: {destination.resolve()}")
    for name, flow in summary["histograms"].items():
        if flow["underflow_entries"] or flow["overflow_entries"]:
            print(f"{name}: {flow['underflow_entries']} underflow, "
                  f"{flow['overflow_entries']} overflow entries; consider wider bins.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, EOFError) as error:
        sys.exit(f"Analysis failed: {error}")
