#!/usr/bin/env python3
"""Overlay the student's signal/background histograms and compare their cutflows.

Read the CSV/JSON outputs, so this also uses observables added during the lesson.
Shape plots have unit area INCLUDING flow bins; rate plots keep the LHE rates.
"""

import argparse
import csv
import json
from pathlib import Path
import re
import sys

import numpy as np


LABELS = {
    "m_ee": r"$m(e^+e^-)$ [GeV]",
    "m_mumu": r"$m(\mu^+\mu^-)$ [GeV]",
    "m_4l": r"$m(e^+e^-\mu^+\mu^-)$ [GeV]",
    "m_bb": r"$m(b\bar b)$ [GeV]",
    "pt_bb": r"$p_T(b\bar b)$ [GeV]",
    "m_bb4l": r"$m(b\bar b e^+e^-\mu^+\mu^-)$ [GeV]",
    "delta_phi_bb": r"$\Delta\phi(b,\bar b)$ [rad]",
}


def load_result(directory):
    summary = json.loads((directory / "summary.json").read_text())
    if summary["normalization"] != "cross-section":
        raise ValueError("Use analyser outputs made with the default cross-section normalization; "
                         "this comparison program will make the shape plots.")
    histograms = {}
    with (directory / "histograms.csv").open() as handle:
        for row in csv.DictReader(handle):
            histograms.setdefault(row["observable"], []).append(row)
    if "m_bb" not in histograms:
        raise ValueError("Complete the m_bb exercise and rerun both samples before comparing them.")
    return summary, histograms


def compare(signal_dir, background_dir, destination, normalization="shape"):
    signal, signal_hist = load_result(signal_dir)
    background, background_hist = load_result(background_dir)
    if signal["selection"] != background["selection"]:
        raise ValueError("The selections differ. Rerun signal and background with the same cuts.")
    if set(signal_hist) != set(background_hist):
        raise ValueError("The observables differ. Use the same completed analyser for both samples.")
    for name in signal_hist:
        first = [(r["left"], r["right"]) for r in signal_hist[name]]
        second = [(r["left"], r["right"]) for r in background_hist[name]]
        if first != second:
            raise ValueError(f"The {name} bin edges differ; use identical binning for both samples.")
    if normalization == "shape" and min(signal["selected_cross_section_pb"],
                                        background["selected_cross_section_pb"]) <= 0:
        raise ValueError("Unit-area shapes need a positive selected weight sum in both samples. "
                         "Use --normalization cross-section or loosen the selection.")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    destination.mkdir(parents=True, exist_ok=True)
    plotted_rows, histogram_report = [], {}
    for name, signal_rows in signal_hist.items():
        histogram_report[name] = {}
        fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
        any_positive, any_negative = False, False
        for key, label, color, summary, rows in (
                ("signal", "Signal", "teal", signal, signal_rows),
                ("background", "SM bbZZ background", "darkorange", background, background_hist[name])):
            edges = np.array([float(r["left"]) for r in rows] + [float(rows[-1]["right"])])
            heights = np.array([float(r["density"]) for r in rows])
            errors = np.array([float(r["density_mc_error"]) for r in rows])
            divisor = summary["selected_cross_section_pb"] if normalization == "shape" else 1.0
            heights, errors = heights / divisor, errors / divisor
            histogram_report[name][key] = {
                field: summary["histograms"][name][field] / divisor
                for field in ("in_range_integral", "underflow_integral", "overflow_integral")}
            for i, height in enumerate(heights):
                plotted_rows.append([key, name, edges[i], edges[i + 1], height, errors[i]])
            any_positive |= bool(np.any(heights > 0))
            any_negative |= bool(np.any(heights < 0))
            ax.stairs(heights, edges, color=color, label=label)
            ax.errorbar((edges[:-1] + edges[1:]) / 2, heights, yerr=errors,
                        fmt="none", ecolor=color, alpha=0.65)
        unit = "rad" if name == "delta_phi_bb" else "GeV"
        ax.set_xlabel(LABELS.get(name, name))
        ax.set_ylabel(f"Selected-sample density [1/{unit}]" if normalization == "shape"
                      else f"Cross section [pb/{unit}]")
        if normalization == "cross-section" and any_positive and not any_negative:
            ax.set_yscale("log")
        ax.set_title(r"$b\bar b + 4\ell$ (parton level)")
        ax.legend()
        fig.savefig(destination / (name + ".pdf"))
        fig.savefig(destination / (name + ".png"), dpi=160)
        plt.close(fig)

    with (destination / "histograms.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample", "observable", "left", "right", "density", "density_mc_error"])
        writer.writerows(plotted_rows)
    rows = []
    for label, summary in (("signal", signal), ("background", background)):
        rows.extend(dict(sample=label, **row) for row in summary["cutflow"])
    with (destination / "selection_table.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    selected_s = signal["selected_cross_section_pb"]
    selected_b = background["selected_cross_section_pb"]
    result = {"signal": str(signal_dir.resolve()), "background": str(background_dir.resolve()),
              "normalization": normalization, "selection": signal["selection"],
              "histograms": histogram_report,
              "signal_cross_section_pb": selected_s,
              "background_cross_section_pb": selected_b,
              "signal_over_background": selected_s / selected_b if selected_b > 0 else None,
              "note": "Independent parton-level teaching samples; no interference or detector model. "
                      "Zero sampled background events do not establish zero physical background."}
    (destination / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Sample         Selected / input     Efficiency     Selected cross section [pb]")
    for label, summary in (("Signal", signal), ("Background", background)):
        print(f"{label:<14} {summary['selected_events']:>6} / {summary['input_events']:<6} "
              f"{summary['weighted_acceptance']:>13.6g}     {summary['selected_cross_section_pb']:.6g}")
    print(f"Saved comparison plots and selection_table.csv in {destination.resolve()}")
    if normalization == "shape":
        print("Each selected sample is normalized to unit area, including underflow and overflow.")
    else:
        print("These are the LHE cross sections after selection; no extra branching factors are applied.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("signal", type=Path, help="signal results folder")
    parser.add_argument("background", type=Path, help="background results folder with identical cuts")
    parser.add_argument("tag", help="name for the comparison results folder")
    parser.add_argument("--normalization", choices=["shape", "cross-section"], default="shape")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.tag):
        parser.error("tag must start with a letter/digit and contain no spaces or slashes")
    destination = args.output_dir / args.tag
    if destination.exists() and any(destination.iterdir()) and not args.overwrite:
        parser.error(f"{destination} is non-empty; use another tag or --overwrite.")
    compare(args.signal, args.background, destination, args.normalization)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"Comparison failed: {error}")
