# Origin of the analyser

This is a teaching adaptation of Andreas Papaefstathiou's
[lheanalyzer](https://gitlab.com/apapaefs/lheanalyzer), based on commit
[`51150cde5f628d597b5a75fbb2a7e360f444fd39`](https://gitlab.com/apapaefs/lheanalyzer/-/tree/51150cde5f628d597b5a75fbb2a7e360f444fd39)
(30 November 2023).

The upstream `lhe_analyzer.py` had SHA-256
`692850ba8b7990df520c5fa2e6ce35174bbd67106fe0f1e790f3b3643211c65d`.
The upstream repository and original example remain available at that commit.
Its unrelated 7.8 MB muon-collider event sample is not included here.

The adaptation retains `analyze()` in the student script, and `read_momenta()`
and `readlhefile()` in the supporting `lhe_tools.py` module, along with the
particle tuple order `[PDG, status, px, py, pz, E, mass]`.
Named fields make the same objects easier for students to read.
The working tutorial script is `lheanalyzer/lhe_analyzer.py`.

Changes for this tutorial:

- Select the outgoing Higgs (`25`) and new scalar (`99925`) in undecayed events.
- Add transverse momenta, pair invariant mass, rapidities and azimuthal separation.
- Use nominal LHE weights, the `<init>` cross section, bin widths and `sum(w²)`.
- Count particle records using `NUP` and reject truncated/unsupported inputs.
- Support plain and gzipped LHE, Fortran exponents and nominal/variation weights.
- Fix the single-file plotting call and implement the optional output tag.
- Replace hard-coded example cross sections and two-file behaviour with an explicit
  one-sample command; analyse comparisons under separate tags.
- Write CSV, JSON, PDF and PNG outputs without opening a GUI.
- Keep the student-facing analysis, one `plot_histogram()` routine and explicit
  plot calls together; put the LHE reader and report-writing code in `lhe_tools.py`.
- Explain list creation, per-event calculation and adding a plot in the README.
  Histogram inputs are normalised event weights; CSV bin integrals use those
  weights, in pb or inclusive fractions according to the chosen mode.

No explicit licence was present in the upstream snapshot. Existing authorship is
preserved; this adaptation does not declare a new licence for upstream code.
