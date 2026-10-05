# Student project: associated production of two scalars

## Aim

We will generate `g g > h eta0 [noborn=QCD]` events, identify the outgoing
particles in the event record, and construct distributions of their momenta.
We will then change a model parameter and distinguish a change in the production
rate from a change in the shape of a distribution.

The [main README](../README.md) is the step-by-step guide: follow its commands
and explanations first. This page collects questions for your project report.
The [physics notes](physics.md) give the definitions and input choices in more
detail. Keep a short record of commands, input cards, seeds, event counts and
cross sections throughout the exercise.

## 1. Inspect the process

After importing the model and entering the generation command in the MadGraph
prompt, use `display diagrams` to inspect the diagrams. Identify quark boxes and
scalar-mediated triangles. Explain why this channel starts at one loop and why
its leading prediction is still called LO. Keep the Higgs and new scalar stable
for the initial study.

Generate the pilot by entering the MadGraph commands and editing the two cards
as described in the README. At the end, record the integration cross section
and its uncertainty, and check the requested number of events against the
output. The masses and couplings are specified in `param_card.dat`; the beam
energy and number of events are specified in `run_card.dat`.

**Checkpoint:** the outgoing PDG IDs should be `25` and `99925`, with the masses
125 GeV and 400 GeV. The beam energy should be 6500 GeV per proton. If these do
not agree with the banner, resolve the difference before plotting.

## 2. Read an event record

After copying the event file as described in the README, inspect it from the
tutorial's top-level directory. **Terminal:**

```bash
zless Work/events/gg_h_eta0_pilot.lhe.gz
```

Type `/<event>` and press Enter to find the first event. Press `q` to quit
the viewer when you have finished. The first numeric line **after `<event>`**
contains `NUP IDPRUP XWGTUP SCALUP AQEDUP AQCDUP`.
`NUP` is the number of particle records; `XWGTUP` is the nominal event weight.
Each particle line gives its PDG ID, status, mother indices, colour labels,
`px py pz E m`, lifetime and spin information. Momenta and masses are in GeV.

Identify the two incoming gluons (`status = -1`) and the two outgoing scalars
(`status = 1`). Sum the incoming and outgoing four-vectors by hand for one event.
Do the gluon energies have to be equal? Explain the role of the proton PDFs and
the longitudinal boost of the partonic collision.

## 3. Follow the Python analysis

Read `analyze()` in `lheanalyzer/lhe_analyzer.py`. The particle tuples have named
fields, for example `particle.pdg`, `particle.status`, `particle.px` and
`particle.energy`. They retain the upstream list order for comparison with the
original `lheanalyzer`.

Run the analyser and inspect the six plots, the CSV and the summary. Explain:

1. Why the Higgs and new-scalar transverse-momentum distributions coincide in
   this setup even though the masses differ.
2. Why the pair mass starts at 525 GeV, and what sets its distribution above
   threshold.
3. Why the azimuthal separation is concentrated at pi. What happens to its
   histogram height when the bin width is halved?
4. Why the rapidity distributions need not have the same shape for the two
   particles, and why the ensemble is symmetric under a common reversal of the
   longitudinal axis for identical proton beams.

**Checkpoint:** inspect `max_pair_pt_GeV`, `max_pt_imbalance_GeV` and
`max_four_momentum_residual_GeV` in `summary.json`. These should be close to zero,
allowing for the precision of the written LHE momenta. Check normalisation by
integrating the CSV densities over their bin widths and adding any flow bins.

## 4. Make a selection and add an observable

Apply `--min-pt-h 100` under a new output tag. Compute the weighted efficiency
and compare it with the ratio of selected to inclusive cross sections. The
selected result must not be rescaled to the inclusive rate.

Work through the README's pair-rapidity example: create a list before the
event loop, calculate and append one value per selected event inside the loop,
then add a `plot_histogram()` call in `make_plots()`. Explain why the first two
steps have different indentation. Check that your seventh plot appears and
that its bin integrals, including any flow entries, add up to the expected rate.

Then add a different observable yourself. Start with `y_h - y_eta0` or the pair
transverse momentum. Write its definition on paper first and predict what the
plot should look like. For a more advanced extension, consider the cosine of a
scattering angle in the pair rest frame; show how you perform and check the
Lorentz boost, and define the axis with respect to which you measure the angle.

Explain what would break if all particles with PDG `25` were selected without
checking their status. Also explain why counting two entries per event in a
single-particle distribution would change its integral.

## 5. Increase statistics and vary the inputs

After validating the pilot, start MadGraph again. **Terminal, from the
tutorial's top-level directory:**

```bash
cd Work/MG5_aMC_v3_5_16
python bin/mg5_aMC
```

**MadGraph:**

```text
launch ../gg_h_eta0 -n sample_01
```

Keep the shower, decays and reweighting off. In the card-editing menu, open
`run_card.dat`, change `nevents` to `10000`, and choose a different nonzero
`iseed`. Save, exit the editor and type `done` at the card-editing menu. The
new run keeps its own banner and events in `Events/sample_01`; do not reuse
the name `pilot`. Loop-induced samples can take time, so choose the size with
your instructor.

When generation finishes, type `quit` in MadGraph. Copy and analyse the new
file yourself, using the new run name in both places. **Terminal:**

```bash
cd ../..
cp Work/gg_h_eta0/Events/sample_01/unweighted_events.lhe.gz Work/events/gg_h_eta0_sample_01.lhe.gz
python lheanalyzer/lhe_analyzer.py Work/events/gg_h_eta0_sample_01.lhe.gz sample_01
```

Now generate a second physics sample changing **one parameter at a time** in
`param_card.dat`, keeping separate cards, banners, event files and analysis
tags. For example:

- Increase `Meta` from 400 to 600 GeV. Predict the new invariant-mass threshold
  before running and discuss the role of gluon luminosities in the rate change.
- Set both `kap112` and `kap122` to zero to remove the scalar-triangle terms
  while retaining the quark boxes. Compare both rate and shape with the starting
  point. Do not add separate box and triangle cross sections to infer the total:
  their amplitudes interfere.
- Change `stheta` and update `ctheta = sqrt(1 - stheta²)`. Explain why the
  full result need not follow a single simple power of the mixing parameter.

For every comparison, show one plot in pb per unit observable and another using
`--normalization shape`. Use the same bin edges for both samples. You can read
`histograms.csv` in a short plotting script and overlay matching bins, or add an
overlay function to the analyser as an extension.

## 6. Write a short report

Include the process and its perturbative accuracy, generator/model versions,
beam energy, masses/couplings, PDF, scales, seed and sample size. Present one
event-record check, your normalisation check, your new observable and one
parameter comparison. Explain which conclusions concern rates and which concern
shapes, and identify the uncertainty you have actually measured.

An optional extension is to vary renormalisation and factorisation scales with
the instructor. A second extension is to decay the particles and redesign the
selection. Neither a statistical error bar nor a sample of undecayed scalars
accounts for theory uncertainties or detector reconstruction.
