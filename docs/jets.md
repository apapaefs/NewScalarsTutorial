# From bottom quarks to b-jets with Herwig

In the [previous exercise](higgs_bb.md), two bottom-quark momenta gave a sharp
Higgs mass. We now pass the same hard process to **Herwig** for parton showering,
hadronization, hadron decays and the underlying event. **HwSim** groups the
resulting particles into jets and writes a ROOT file. You will reconstruct
the Higgs from b-jets and compare with the supplied background.

There are four exercises, about **two hours in total**, after software setup.
All commands below go in a **terminal**, from the `NewScalarsTutorial` directory.

## Before the session

Ask your instructor for a working **Herwig 7.3 + FastJet + ROOT + HwSim**
installation. Building these packages is outside the two-hour exercise.
The [setup notes](jets_setup.md) give the tested versions and installation checks.
Activate Herwig, then select the tutorial's Python interpreter:

```bash
source /path/to/Herwig/bin/activate
export PATH="$PWD/.venv/bin:$PATH"
python -m pip install -r requirements-jets.txt
Herwig --version
```

Replace `/path/to/Herwig` with the installation path supplied by your instructor.
The `PATH` line makes `python` use your existing `.venv` while keeping Herwig
available; sourcing both activation scripts can undo the first activation.
Python reads the ROOT file through Uproot; you do not need to learn ROOT or C++.

The larger samples use [Git LFS](https://git-lfs.com/). Install Git LFS before
downloading them, then run:

```bash
git lfs install --local
git lfs pull
python scripts/verify_samples.py
```

The verification should report **10,000 + 10,000 + 10,000 + 50,000 events**.
The first two files extend the earlier lessons; this lesson uses the last two:

| File in `samples/` | Process | Events |
| --- | --- | ---: |
| `gg_h_eta0_10000.lhe.gz` | Undecayed Higgs and eta0 | 10,000 |
| `gg_h_eta0_2e2mu_10000.lhe.gz` | Four leptons, stable Higgs | 10,000 |
| `gg_h_eta0_bb2e2mu_10000.lhe.gz` | Higgs to bb, eta0 to four leptons | 10,000 |
| `pp_bbzz_2e2mu_50000.lhe.gz` | QCD bbZZ background, Z decays to four leptons | 50,000 |

These are new independent simulation samples, **100 times the size** of each
earlier pilot. They are not expected event yields for a particular experiment.
The small files in `examples/` still work for quick checks.

## 1. Shower the signal and make three plots (25 minutes)

Begin with **1,000 events**, so you can test the whole sequence quickly:

<!-- student-command: signal_prepare -->
```bash
python scripts/prepare_herwig.py samples/gg_h_eta0_bb2e2mu_10000.lhe.gz signal --events 1000 --seed 22001
```

This writes `Work/herwig/signal.in` and a small file recording the run settings.
Open the `.in` file: it names the LHE input, event count, random seed and jet
radius. `read` prepares a run; `run` actually simulates events:

<!-- student-command: signal_read -->
```bash
Herwig read Work/herwig/signal.in
```

<!-- student-command: signal_run -->
```bash
Herwig run Work/herwig/signal.run
```

<!-- student-command: signal_analyze -->
```bash
python jetanalyzer/hwsim_jets.py Work/herwig/signal.root signal_jets
```

**Checkpoint:** `results/signal_jets/` contains `m_bb`, `n_jets` and `n_bjets`,
each as PDF and PNG, plus `histograms.csv`, `cutflow.csv` and `summary.json`.
The first cutflow row should contain 1,000 events. If Herwig fails or the event
count differs, fix the run before interpreting the plots; the analyser checks this.

Explain why there can be more than two jets even though the hard signal has only
two outgoing quarks. Identify the contributions of radiation and additional
parton interactions. No detector simulation or pileup has been added.

## 2. Compare partons with jets and change a cut (35 minutes)

Our jets use **anti-kT with radius R = 0.4**. The analysis accepts jets with
**pT at least 25 GeV and |eta| below 2.5**. Here eta measures how close a jet
points to the beam. Both b-jets and other jets must pass the same cuts.

A **truth b-jet** contains a b hadron associated by HwSim's ghost method:
an almost zero-momentum marker follows that hadron's direction into the jet.
The marker labels the jet without changing its momentum. Physical b hadrons
decay normally. This is a simulation label, with no experimental tagging
efficiency or mistag probability applied.

Open `jetanalyzer/hwsim_jets.py` and find `measure_jets()`. Its key lines are:

```python
jets = non_b_jets + b_jets
values['n_jets'] = len(jets)
values['n_bjets'] = len(b_jets)
```

HwSim stores **non-b jets and b-jets separately**. Counting only the `numJets`
branch would miss every b-jet. Both multiplicity plots include all input events,
including events with zero or one accepted b-jet.

The mass plot then requires **exactly two accepted truth b-jets**:

```python
if len(b_jets) == 2:
    pair = b_jets[0] + b_jets[1]
    values['m_bb'] = invariant_mass(*pair)
```

Each jet is `(E, px, py, pz)` in GeV. NumPy adds the four components; `*pair`
passes them to the same mass formula used in the LHE lesson. An event without
two accepted b-jets has no mass entry. A merged jet containing two b hadrons
still counts as **one jet**. Extra b-jets can also arise from gluon splitting;
a truth b label does not guarantee that the jet came from the Higgs.

### Put the parton and hadron levels on one plot

Reuse your Herwig output to compare the two stages:

<!-- student-command: mbb_levels -->
```bash
python jetanalyzer/compare_mbb_levels.py samples/gg_h_eta0_bb2e2mu_10000.lhe.gz Work/herwig/signal.root signal_mbb_levels
```

Open `results/signal_mbb_levels/m_bb_levels.pdf`. The blue curve uses the
outgoing b and bbar in the **original LHE file**; the orange curve uses the
two accepted truth b-jets **after Herwig**. Both use pT >= 25 GeV, |eta| < 2.5
and common 10 GeV mass bins. The parton-level Higgs mass is fixed at 125 GeV,
at the centre of one bin. Explain why the jet curve spreads out and develops
a low-mass tail.

Each curve has unit area, including entries outside the plotted range, so this
first plot compares **shapes**. For rates and selection efficiencies, also run:

<!-- student-command: mbb_level_rates -->
```bash
python jetanalyzer/compare_mbb_levels.py samples/gg_h_eta0_bb2e2mu_10000.lhe.gz Work/herwig/signal.root signal_mbb_level_rates --normalization cross-section
```

Read `selection_table.csv` beside the plot. The same numerical cuts select
different objects at the two levels. The parton curve uses all 10,000 LHE events;
the hadron curve uses your 1,000-event shower run. These are separately selected
distributions, not pairs of matched event records. The program checks that the
LHE file is the one used for your Herwig run.

Here, **hadron level** includes showering, hadronization, hadron decays and
multiple parton interactions (MPI). This comparison shows their combined effect
on reconstruction and selection.
Radiation outside the jets and neutrinos from hadron decays can lower the
reconstructed mass; extra particles can add energy. No detector resolution
has been applied.

Raise the jet threshold without repeating Herwig:

<!-- student-command: harder_jets -->
```bash
python jetanalyzer/hwsim_jets.py Work/herwig/signal.root signal_pt40 --min-jet-pt 40
```

Record the two-b-jet efficiencies at 25 and 40 GeV. Explain the change in
`n_bjets` and `m_bb`. You can repeat the level comparison with `--min-pt 40`
and a new tag; this changes the cut on both the quarks and the jets.

## 3. Add an observable: total jet transverse momentum (25 minutes)

Define **HT** as the sum of pT over all accepted jets. It measures the transverse
activity in the event. This time there are only two code additions.

In `measure_jets()`, immediately below `# EXERCISE CALCULATION`, insert:

<!-- exercise: calculation -->
```python
    values['ht'] = sum(math.hypot(jet[1], jet[2]) for jet in jets)
```

Near the top of the file, inside `OBSERVABLES`, below `# EXERCISE PLOT`, add:

<!-- exercise: plot -->
```python
    'ht': (r'$H_T$ [GeV]', np.linspace(0, 1000, 51), True),
```

Keep the four-space indentation and the final comma in the second addition.
The last `True` tells the plotter that the horizontal axis is in GeV.
Save the file and run:

<!-- student-command: ht -->
```bash
python jetanalyzer/hwsim_jets.py Work/herwig/signal.root signal_with_ht
```

**Checkpoint:** four plots now appear, including `ht.pdf`. Explain why HT is
not the transverse momentum of the vector sum of the jets. What value should
an event with no accepted jets contribute?

## 4. Shower the background and compare (35 minutes)

Use a different seed and output name. The same settings and analysis must be
used for both samples:

<!-- student-command: background_prepare -->
```bash
python scripts/prepare_herwig.py samples/pp_bbzz_2e2mu_50000.lhe.gz background --events 1000 --seed 22002
```

<!-- student-command: background_read -->
```bash
Herwig read Work/herwig/background.in
```

<!-- student-command: background_run -->
```bash
Herwig run Work/herwig/background.run
```

<!-- student-command: background_analyze -->
```bash
python jetanalyzer/hwsim_jets.py Work/herwig/background.root background_with_ht
```

<!-- student-command: shapes -->
```bash
python jetanalyzer/compare_jets.py results/signal_with_ht results/background_with_ht jet_shapes
```

The default overlays give each distribution unit area, including events outside
the plotted range. For `m_bb`, this compares shapes **among events with exactly
two accepted b-jets**. To compare the predicted rates instead:

<!-- student-command: rates -->
```bash
python jetanalyzer/compare_jets.py results/signal_with_ht results/background_with_ht jet_rates --normalization cross-section
```

Use `selection_table.csv` and the plots to suggest a Higgs mass window. Explain
why its signal efficiency is now below 100%, and why a small background count
has a large statistical uncertainty. The rates already include the specified
decays: **do not multiply by branching fractions again**. This is one QCD
background component, not a complete experimental background estimate.

If time permits, prepare a new signal run with `--radius 0.6` and a new tag,
then repeat `Herwig read`, `Herwig run` and the analysis. Changing the radius
requires reclustering, so it cannot be done by changing the plotting script.
Predict how the mass peak and two-b-jet efficiency might respond.

For better statistics later, use `--events 10000` for signal and `--events 50000`
for background, with new tags. Keep each `.json` and `.out` beside its `.root`:
they record the setup and the final Herwig cross section. The generator stops
at the end of the input file instead of recycling events.

**Hand in:** the three jet plots plus HT, the parton/hadron mass overlay, the two
efficiencies from exercise 2, the signal/background selection table, and a few
sentences answering the questions.
