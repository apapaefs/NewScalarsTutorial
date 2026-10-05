# Validation and troubleshooting

## What was checked

On 5 October 2026, the tutorial was tested locally on macOS/Apple Silicon with
Python 3.12.14, GNU Fortran 16.2.0, NumPy 2.5.3, Matplotlib 3.11.2 and six 1.17.0.
The full generation test used MadGraph's official 3.5.16 Git tag, commit
`3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7`. The UFO was installed from the original
archive, excluding obsolete caches. A separate check of the manual installation
and plotting lesson is recorded below.

- Model installation and a second, idempotent installation both succeeded.
- MadGraph imported the model and generated `g g > h eta0 [noborn=QCD]` with
  0 Born, 20 loop and 6 R2 diagrams in its generation log.
- The bundled CutTools and IREGI libraries compiled, and MadLoop initialisation
  completed. Optional Ninja and Collier were disabled by the generation card.
- The supplied run card produced 100 undecayed events, using seed `12345` as
  recorded in the run banner. The generated cards were checked against the
  beam, PDF, scale, mass, coupling and weight settings in the tutorial.
- The analyser read that actual gzipped LHE v3 output, including its `<generator>`
  metadata, selected all 100 events and produced all six plots plus CSV/JSON.
- The maximum four-momentum residual was about `8.2e-8 GeV`, consistent with
  rounding of the written momenta. Pair pT and the difference of the two scalar
  transverse momenta were zero at the stored precision.
- The nominal weights summed to the `<init>` cross section, `2.980640e-4 pb`.
  Each uncut histogram integrated to that value, with no flow entries for this
  small sample. The integration uncertainty in `<init>` was `1.347514e-6 pb`.
- With `pT(h) >= 100 GeV`, 59 events passed and the selected cross section was
  `1.7585776e-4 pb`, exactly 59% of the inclusive value for these equal-weight
  events. The histogram normalisation retained that efficiency.
- The synthetic signed-weight fixture and the actual pilot passed the original
  seven regression tests covering kinematics, gzip, nominal/variation weights,
  init metadata, `sum(w²)`, bin widths/flow, selection normalisation and invalid
  input handling.
- Representative PNG output was visually inspected for labels and layout.

The small real sample is available in `examples/gg_h_eta0_pilot.lhe.gz`. The
fixture under `tests/fixtures/` is synthetic and has no physical cross section.

These checks establish a working generation-to-analysis path for the stated
inputs. They are not a validation of the model against a second calculation,
a gauge-invariance study, a survey of other platforms, or a theory uncertainty
assessment. The cross section above is a recorded smoke-test result, not a
published reference prediction.

## Checks of the manual workflow and plotting lesson

The revised student instructions and simpler plotting interface were checked
on the same machine and date:

- The official `MG5_aMC_v3.5.16.tar.gz` release archive was downloaded, copied
  into a fresh `Work/` directory and extracted. Its top-level directory was
  `MG5_aMC_v3_5_16`, and its `VERSION` reported `3.5.16`, dated `2026-07-03`.
- `loop_sm_scalar_source.tar.gz` was copied into that installation's `models/`
  directory and extracted using the README's commands. All 24 included files
  were compared with the original model archive and were byte-for-byte equal.
- The settings, model import and process-generation commands from the README
  ran in that release, again giving 0 Born, 20 loop and 6 R2 diagrams. This
  separate check stopped at diagram generation; the compiler and complete
  event-generation checks above used the Git distribution.
- All nine current regression tests passed. The two additional checks run the
  actual plotting command with a selection in both normalisation modes, and
  check the explanatory error for a missing per-event list entry.
- The six revised plots were compared numerically with the original analyser's
  output for the same 100-event sample. Bin edges, densities and statistical
  errors agreed to numerical precision.
- The three pair-rapidity snippets were taken directly from the README and
  inserted into a temporary copy of the student script. Running that copy
  produced seven PDF and seven PNG plots. The new rapidities agreed with
  `0.5 * log(E_gluon_plus / E_gluon_minus)` calculated from the incoming gluons.
  The new histogram integrated to the inclusive cross section; after the
  100 GeV Higgs-pT cut it retained the expected 59% efficiency.
- Representative pT and pair-rapidity PNGs were inspected for labels and layout.

The pair-rapidity solution is deliberately left as a student exercise in the
distributed script. The CSV now labels its weighted bin contents `bin_integral`
and `bin_sumw2`: these use the normalised plotting weights, in pb and pb² for
cross-section plots, or inclusive fractions and their squares for shape plots.

## Reproduce the analysis checks

```bash
python -m unittest discover -s tests -v
python lheanalyzer/lhe_analyzer.py examples/gg_h_eta0_pilot.lhe.gz check
python lheanalyzer/lhe_analyzer.py examples/gg_h_eta0_pilot.lhe.gz check_pt100 --min-pt-h 100
```

Inspect `results/check/summary.json` and the CSV, and repeat the generation
commands in the README to test your local generator/compiler combination.
Different platforms or integration histories can change the sampled events;
compare conserved quantities and statistically compatible results, not a
byte-for-byte event-file match.

## Common problems

**The model cannot be imported.** Check that the directory is named
`models/loop_sm_scalar` inside the actual 3.5.16 installation being executed.
Use the source-only archive and the manual copy/extraction commands in the
README. The original archive includes caches made by older Python/MadGraph
versions; the source-only copy omits those caches. If a previous installation
of this model is present, ask your instructor to check it before replacing it.

**Compilation takes several minutes.** The first run builds loop libraries.
In this test, the IREGI complex-matrix source took several minutes to compile.
Wait for the compiler to finish, and read its diagnostics if it fails. Check
that `gfortran`, a C/C++ compiler and `make` are available. A successful model
import alone does not test compilation or event generation.

**A source checkout prints a development-version banner.** The Git checkout
used for the initial validation includes `bin/create_release.py`, which triggers
that generic banner in 3.5.16. The README uses the packaged release instead.
If using Git, check the exact commit and `VERSION`.

**The output directory/run name already exists.** Keep prior runs and choose
a different name in the MadGraph `launch` command, or a different analysis label
when running the Python script. A run should be identified by its saved banner
and cards.
MadGraph may reset `iseed` to zero in the working run card after consuming it;
use the saved run banner for the seed actually used.

**MadGraph exits but there is no LHE file.** Inspect the full log for the first
error and look for the final cross-section/event-count summary. MadGraph can
return shell status zero after a command error; file existence and a readable,
complete LHE sample are part of the test.

**No events pass the analyser.** The initial exercise requires exactly one
outgoing `h` and one outgoing `eta0`. Decayed samples, extra partons or a very
hard selection need a different analysis or looser cuts. Do not select an
intermediate resonance as if it were an outgoing particle.

**A plotted integral is too small.** Include bin widths, inspect underflow and
overflow integrals, and account for the selection efficiency. Enlarge the range
of `bins=np.linspace(...)` in the appropriate `make_plots()` call when a changed
mass or collider energy extends the plotted range.
Negative weights must be retained; their errors use squared weights.

**The reader reports a malformed/truncated file.** Check that the run and
compression finished. Do not analyse a file while it is being written or simply
concatenate independent LHE runs. Multiple-subprocess files and weight strategies
other than those described in the physics notes require an extended reader and
an explicit normalisation prescription.
