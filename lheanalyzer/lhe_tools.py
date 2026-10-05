"""LHE reading and report helpers for the undergraduate tutorial.

Students can begin with analyze(), plot_histogram() and make_plots() in
lhe_analyzer.py without editing this file. Reader adapted from Andreas
Papaefstathiou's lheanalyzer; see UPSTREAM.md for attribution.
"""

import argparse
import csv
from dataclasses import dataclass
import gzip
import json
import math
from pathlib import Path
import re
from typing import NamedTuple

import numpy as np


class Particle(NamedTuple):
    # Keep the upstream order: [PDG id, status, px, py, pz, E, mass].
    pdg: int
    status: int
    px: float
    py: float
    pz: float
    energy: float
    mass: float


@dataclass
class Sample:
    events: list
    weights: list
    multiweights: list
    cross_section_pb: float
    cross_section_error_pb: float
    weight_strategy: int
    process_id: int


def number(value):
    """LHE/Fortran numbers may use D as well as E for the exponent."""
    result = float(value.replace("D", "E").replace("d", "e"))
    if not math.isfinite(result):
        raise ValueError(f"Non-finite number in LHE file: {value}")
    return result


def block_lines(lines, closing):
    block = []
    for line in lines:
        if line.strip() == closing:
            return block
        block.append(line)
    raise ValueError(f"Truncated LHE file: missing {closing}")


def records(block):
    # Comments and blank lines do not count towards NUP or NPRUP.
    return [line.split("#", 1)[0].strip() for line in block
            if line.split("#", 1)[0].strip() and not line.lstrip().startswith("<!--")]


def read_momenta(line):
    fields = line.split()
    if len(fields) != 13:
        raise ValueError("An LHE particle record must have 13 fields.")
    return Particle(int(fields[0]), int(fields[1]),
                    *(number(value) for value in fields[6:11]))


def read_lhe(path):
    """Read standard MG5 plain/gzipped LHE with exactly one subprocess.

    Count NUP particle records explicitly; metadata such as <rwgt> cannot be
    mistaken for momenta. Nominal weights are used, variations are retained.
    Like upstream, the small classroom sample is held in memory.
    """
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    events, weights, multiweights = [], [], []
    init = None
    closed = False
    with opener(path, "rt", encoding="utf-8") as stream:
        lines = iter(stream)
        for line in lines:
            line = line.strip()
            if re.fullmatch(r"<init(?:\s[^>]*)?>", line):
                if init is not None or events:
                    raise ValueError("Duplicate or misplaced <init> block.")
                rows = records(block_lines(lines, "</init>"))
                # LHE v3 permits XML metadata (e.g. MG5's <generator>) after
                # the numeric header and NPRUP subprocess records.
                metadata_start = next((i for i, row in enumerate(rows)
                                       if row.startswith("<")), len(rows))
                rows = rows[:metadata_start]
                if not rows or len(rows[0].split()) != 10:
                    raise ValueError("Malformed LHE <init> header.")
                header = rows[0].split()
                strategy, nprocess = int(header[8]), int(header[9])
                if nprocess != 1:
                    raise ValueError("This tutorial supports one subprocess per file; "
                                     "analyse subprocess samples separately.")
                if strategy not in {3, -3, 4, -4}:
                    raise ValueError(f"Unsupported IDWTUP={strategy}; use MG5 LHE events.")
                if len(rows) != 2 or len(rows[1].split()) != 4:
                    raise ValueError("Malformed LHE subprocess cross-section record.")
                process = rows[1].split()
                xsec, error = number(process[0]), number(process[1])
                if xsec <= 0 or error < 0:
                    raise ValueError("Expected a positive cross section and non-negative error.")
                init = (xsec, error, strategy, int(process[3]))
            elif re.fullmatch(r"<event(?:\s[^>]*)?>", line):
                if init is None:
                    raise ValueError("An event appears before the LHE <init> block.")
                rows = records(block_lines(lines, "</event>"))
                if not rows or len(rows[0].split()) != 6:
                    raise ValueError(f"Malformed header for event {len(events) + 1}.")
                header = rows[0].split()
                nup, process = int(header[0]), int(header[1])
                if nup <= 0 or len(rows) < nup + 1:
                    raise ValueError("Truncated particle records in an LHE event.")
                if process != init[3]:
                    raise ValueError("An event process ID differs from its <init> record.")
                particles = [read_momenta(row) for row in rows[1:nup + 1]]
                extra = "\n".join(rows[nup + 1:])
                if any(len(row.split()) == 13 and not row.startswith("<")
                       for row in rows[nup + 1:]):
                    raise ValueError("Extra particle records beyond the declared NUP.")
                variations = {match[1]: number(match[2].strip()) for match in re.findall(
                    r"<wgt\s+id\s*=\s*(['\"])(.*?)\1\s*>(.*?)</wgt>", extra, re.S)}
                events.append(particles)
                weights.append(number(header[2]))
                multiweights.append(variations)
            elif line == "</LesHouchesEvents>":
                closed = True
    if not closed or init is None or not events:
        raise ValueError("Expected a complete LHE file with <init> and at least one event.")
    if not math.isfinite(math.fsum(weights)) or math.fsum(weights) <= 0:
        raise ValueError("The inclusive nominal weight sum must be finite and positive.")
    return Sample(events, weights, multiweights, *init)


def readlhefile(infile):
    """Compatibility with upstream's (events, weights, multiweights) interface."""
    sample = read_lhe(infile)
    return sample.events, sample.weights, sample.multiweights


def histogram(values, weights, edges):
    """Bin weights already normalised to pb (or inclusive fractions)."""
    values, weights = np.asarray(values), np.asarray(weights)
    if values.shape != weights.shape or values.ndim != 1:
        raise ValueError("Each plotted quantity needs one value per selected event weight; "
                         "check where its list is created and where append() is called.")
    sumw, _ = np.histogram(values, bins=edges, weights=weights)
    sumw2, _ = np.histogram(values, bins=edges, weights=weights**2)
    widths = np.diff(edges)
    flow = {
        "underflow_entries": int(np.count_nonzero(values < edges[0])),
        "overflow_entries": int(np.count_nonzero(values > edges[-1])),
        "underflow_integral": float(weights[values < edges[0]].sum()),
        "overflow_integral": float(weights[values > edges[-1]].sum()),
        "in_range_integral": float(sumw.sum()),
    }
    return sumw, sumw2, sumw / widths, np.sqrt(sumw2) / widths, flow


def check_momenta(particles, h, eta, checks):
    """Bookkeeping for the two-body momentum checks reported in summary.json."""
    checks["max_pt_imbalance_GeV"] = max(
        checks["max_pt_imbalance_GeV"], abs(math.hypot(h.px, h.py) - math.hypot(eta.px, eta.py)))
    checks["max_pair_pt_GeV"] = max(
        checks["max_pair_pt_GeV"], math.hypot(h.px + eta.px, h.py + eta.py))
    incoming = [p for p in particles if p.status == -1]
    if len(incoming) != 2 or any(p.pdg != 21 for p in incoming):
        raise ValueError("Expected two incoming gluons (PDG 21, status -1).")
    for component in ("energy", "px", "py", "pz"):
        residual = sum(getattr(p, component) for p in incoming) - sum(
            getattr(p, component) for p in (h, eta))
        checks["max_four_momentum_residual_GeV"] = max(
            checks["max_four_momentum_residual_GeV"], abs(residual))


def save_report(sample, selected_weights, checks, plots, destination, normalization,
                input_path, min_pt_h):
    inclusive_sumw = math.fsum(sample.weights)
    selected_sumw = math.fsum(selected_weights)
    summary = {
        "input": str(Path(input_path).resolve()),
        "normalization": normalization,
        "input_events": len(sample.events), "selected_events": len(selected_weights),
        "rejected_events": len(sample.events) - len(selected_weights),
        "negative_weight_events": sum(w < 0 for w in sample.weights),
        "inclusive_sumw": inclusive_sumw, "selected_sumw": selected_sumw,
        "weighted_acceptance": selected_sumw / inclusive_sumw,
        "cross_section_pb": sample.cross_section_pb,
        "cross_section_error_pb": sample.cross_section_error_pb,
        "selected_cross_section_pb": sample.cross_section_pb * selected_sumw / inclusive_sumw,
        "idwtup": sample.weight_strategy, "process_id": sample.process_id,
        "variation_weights_used": False,
        "events_with_variation_weights": sum(bool(w) for w in sample.multiweights),
        "min_pt_h_GeV": min_pt_h, "checks": checks, "histograms": {},
        "error_note": "Bin errors are sqrt(sum(w^2)) with fixed inclusive normalisation; "
                      "they exclude integration, scale/PDF and normalisation correlations.",
    }
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "histograms.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["observable", "left", "right", "bin_integral", "bin_sumw2",
                         "density", "density_mc_error"])
        for name, plot in plots.items():
            edges = plot["edges"]
            summary["histograms"][name] = plot["flow"]
            for i in range(len(edges) - 1):
                writer.writerow([name, edges[i], edges[i + 1], plot["sumw"][i],
                                 plot["sumw2"][i], plot["density"][i], plot["error"][i]])
    (destination / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def get_arguments():
    parser = argparse.ArgumentParser(description="Analyse undecayed g g > h eta0 LHE events.")
    parser.add_argument("lhe_file", type=Path)
    parser.add_argument("tag", nargs="?", default="baseline", help="output subdirectory name")
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--normalization", choices=["cross-section", "shape"],
                        default="cross-section")
    parser.add_argument("--min-pt-h", type=float, default=0.0, metavar="GEV")
    parser.add_argument("--overwrite", action="store_true", help="replace plots for this tag")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.tag):
        parser.error("tag must start with a letter/digit and contain no spaces or slashes")
    if not math.isfinite(args.min_pt_h) or args.min_pt_h < 0:
        parser.error("--min-pt-h must be finite and non-negative")
    destination = args.output_dir / args.tag
    if destination.exists() and any(destination.iterdir()) and not args.overwrite:
        parser.error(f"{destination} is non-empty; use another tag or --overwrite.")
    return args
