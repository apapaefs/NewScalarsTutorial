# Finding the Higgs in a bottom-quark pair

In the [four-lepton exercise](four_lepton.md), we reconstructed the new scalar
from four leptons and left the Higgs undecayed. We now let that Higgs decay:

```text
Signal:       g g -> h + eta0
Higgs decay:  h -> b + bbar
Other decay:  eta0 -> Z Z -> e+ e- mu+ mu-
```

`b` is a bottom quark and `bbar` is its antiparticle. MadGraph writes the latter
as `b~`. There is **one Higgs in each signal event**. Our final state now has
six outgoing particles: two bottom quarks and four leptons.

We will find the Higgs mass from the bottom-quark pair, then measure how fast
the pair moves across the beam direction. An optional final section adds a
Standard Model background with the same outgoing particles.

| Observable | What it measures | Status in the new starter |
| --- | --- | --- |
| `m_ee`, `m_mumu`, `m_4l` | The masses from the previous exercise | Already complete |
| `m_bb` | The mass of the bottom-quark pair | You will add this |
| `pt_bb` | The transverse momentum of the pair | You will add this |

These are **quark momenta from the event generator**. A quark in an experiment
produces a jet of particles. We have not yet simulated that process or a detector,
so we are not reconstructing or tagging experimental b jets in this lesson.

## 1. Start from the completed lepton analysis

Use the same terminal and Python environment as before. All commands below
start in `NewScalarsTutorial`. **Terminal:**

```bash
source .venv/bin/activate
```

A new starter includes the completed three lepton masses, so you do not have
to copy your previous solution. Your earlier analyser and samples stay available.
Run the new starter on the new signal file. **Terminal:**

<!-- student-command: start -->
```bash
python lheanalyzer/lhe_bb_four_lepton.py examples/gg_h_eta0_bb2e2mu_pilot.lhe.gz bb_signal_start
```

**Checkpoint:** `results/bb_signal_start` contains three PNG and three PDF plots.
The electron and muon pairs peak near 91 GeV; the four-lepton mass peaks at
400 GeV. All 100 events pass the default selection. The program prints a
cutflow and saves `cutflow.csv`, `histograms.csv` and `summary.json` as before.
The optional cuts are initially switched off.

Look at one event with `zless examples/gg_h_eta0_bb2e2mu_pilot.lhe.gz`.
Type `/<event>` and Enter to search, then `q` to leave. The first numeric line
is the event summary; the next lines are particle records.

| Particle | PDG code | Status |
| --- | --- | --- |
| Bottom quark | `5` | `1`: outgoing |
| Bottom antiquark | `-5` | `1`: outgoing |
| Four leptons | `11`, `-11`, `13`, `-13` | `1`: outgoing |
| Higgs, new scalar and Z bosons | `25`, `99925`, `23` | `2`: intermediate |

The Higgs now has status `2`. We reconstruct its mass using the two status-1
bottom quarks. Including the intermediate Higgs momentum as well would count
its energy twice. The analysis also works for the background, which need not
contain an intermediate Higgs or new scalar.

## 2. Add the bottom-pair mass

Make a backup and open the new file. **Terminal:**

```bash
mkdir -p Work
cp -n lheanalyzer/lhe_bb_four_lepton.py Work/lhe_bb_four_lepton_before_edits.py
nano lheanalyzer/lhe_bb_four_lepton.py
```

In `nano`, Ctrl+W searches, Ctrl+O followed by Enter saves, and Ctrl+X exits.
Edit the file inside `lheanalyzer`; the file in `Work` is a backup.

Use the same three steps as in the previous exercise: **make a list, calculate
one value per event, ask for a plot**. Keep all existing code. Paste each addition
once, immediately above its matching `# EXERCISE` comment. Use spaces, not tabs.

### A. Make a list

Find `# EXERCISE LISTS:`. Add this immediately above it, with **four spaces**
at the start. **Python — edit the file:**

<!-- exercise: lists -->
```python
    output["m_bb"] = []
```

### B. Calculate and store the mass

The variables `b` and `bbar` already refer to the two outgoing particles.
Add their energies and each momentum component before calculating the mass.
Immediately above `# EXERCISE CALCULATIONS:`, with **eight spaces** at the
start of each instruction. **Python — edit the file:**

<!-- exercise: calculations -->
```python
        m_bb = invariant_mass(
            b.energy + bbar.energy,
            b.px + bbar.px,
            b.py + bbar.py,
            b.pz + bbar.pz,
        )
        output["m_bb"].append(m_bb)
```

This is exactly the electron-pair calculation with different particles.
`append` stores this event's answer in the list. The pair's mass is not the
sum of the two individual bottom-quark masses.

### C. Ask for a plot

Immediately above `# EXERCISE PLOTS:`, with **four spaces** before the first
line. Keep this before `return plots`. **Python — edit the file:**

<!-- exercise: plots -->
```python
    plots["m_bb"] = plot_histogram(
        output["m_bb"], weights,
        bins=np.linspace(0, 500, 51),
        xlabel=r"$m(b\bar b)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "m_bb", title=title,
    )
```

This gives 50 bins of width 10 GeV, with 125 GeV at a bin centre. Save the file,
leave the editor and run it with a new results name. **Terminal:**

<!-- student-command: mass -->
```bash
python lheanalyzer/lhe_bb_four_lepton.py examples/gg_h_eta0_bb2e2mu_pilot.lhe.gz bb_signal_mass
```

**Checkpoint:** there are now **four** plots in each format. Open
`results/bb_signal_mass/m_bb.png`: its peak is at **125 GeV**, the Higgs mass.
Like the 400 GeV peak, it is sharp because MadSpin keeps the parent mass fixed.
Its plotted width comes from our binning, not detector resolution.

## 3. Add the Higgs transverse momentum

Open the file again with `nano lheanalyzer/lhe_bb_four_lepton.py` and keep your
mass additions. The pair's transverse momentum is

```text
px_pair = px_b + px_bbar
py_pair = py_b + py_bbar
pT_pair = sqrt(px_pair² + py_pair²)
```

Add the components first. Adding the two individual pT values would calculate
a different quantity. For example, two particles moving in opposite transverse
directions can have nonzero individual pT values but zero pair pT.

At the same three locations, add the following. **Python — edit the file.**
First, immediately above `# EXERCISE LISTS:` (**four spaces**):

<!-- exercise: lists -->
```python
    output["pt_bb"] = []
```

Immediately above `# EXERCISE CALCULATIONS:` (**eight spaces**):

<!-- exercise: calculations -->
```python
        px_bb = b.px + bbar.px
        py_bb = b.py + bbar.py
        pt_bb = math.sqrt(px_bb**2 + py_bb**2)
        output["pt_bb"].append(pt_bb)
```

Immediately above `# EXERCISE PLOTS:` (**four spaces**):

<!-- exercise: plots -->
```python
    plots["pt_bb"] = plot_histogram(
        output["pt_bb"], weights,
        bins=np.linspace(0, 600, 31),
        xlabel=r"$p_T(b\bar b)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "pt_bb", title=title,
    )
```

Save, exit and run. **Terminal:**

<!-- student-command: complete -->
```bash
python lheanalyzer/lhe_bb_four_lepton.py examples/gg_h_eta0_bb2e2mu_pilot.lhe.gz bb_signal_complete
```

**Checkpoint:** you now have **five PNG and five PDF plots**. `pt_bb` is spread
over a range of values, although `m_bb` is fixed. Different events produce the
same-mass Higgs with different momenta. In this sample, the reconstructed pair
pT equals the intermediate Higgs pT, up to numerical rounding.

## 4. Select particles with enough transverse momentum

Require every lepton to have pT of at least 10 GeV and **each** bottom quark
to have pT of at least 25 GeV. **Terminal:**

<!-- student-command: selected -->
```bash
python lheanalyzer/lhe_bb_four_lepton.py examples/gg_h_eta0_bb2e2mu_pilot.lhe.gz bb_signal_selected --min-lepton-pt 10 --min-b-pt 25
```

Open `results/bb_signal_selected/cutflow.csv`. The `lepton_pt` row applies the
lepton requirement; the next `b_pt` row also applies the bottom-quark requirement.
If either bottom quark fails, the whole event fails. `--min-b-pt` cuts on the
individual quarks, not on the pair pT you just plotted.

Calculate the efficiency by dividing the selected count by 100. The supplied
events have equal, positive weights, so this agrees with the reported weighted
efficiency. **Checkpoint:** 96 events pass the lepton cut and 82 also pass the
bottom-quark cut, giving an overall efficiency of 82%.
Compare the five plots before and after selection. Which shapes
change? Does either reconstructed signal mass move?

You can stop here with a complete reconstruction exercise. The next section
uses the same code to investigate a background.

## 5. Optional: add a Standard Model background

A **background** is another process that can give us the same outgoing
particles. We provide a small Standard Model sample of

```text
p p -> b bbar Z Z,  Z Z -> e+ e- mu+ mu-
```

Here `p p` means proton–proton collisions. The generator includes incoming
gluons and light quarks. We use the tree-level QCD contribution with two
resonant Z bosons. It does not need a new scalar or a Higgs decaying into the
bottom pair, so we can ask whether its mass distributions differ from the signal.

This is **one background component**. It is enough for this comparison exercise;
other contributions, misidentified particles and detector effects would be needed
for an experimental analysis. The [generation notes](higgs_bb_generation.md)
state the precise approximation and inputs.

Run your completed analyser on the background, with the **same cuts**.
**Terminal:**

<!-- student-command: background -->
```bash
python lheanalyzer/lhe_bb_four_lepton.py examples/pp_bbzz_2e2mu_pilot.lhe.gz bb_background_selected --min-lepton-pt 10 --min-b-pt 25
```

**Checkpoint:** 66 of the 500 background events pass these cuts. There are five
plots, just as for the signal. The bottom-pair and four-lepton masses are spread
out rather than fixed at 125 and 400 GeV.

### Compare shapes first

The supplied comparison program reads your saved histograms. It checks that
both runs used identical cuts and binning. **Terminal:**

<!-- student-command: shapes -->
```bash
python lheanalyzer/compare_bb_four_lepton.py results/bb_signal_selected results/bb_background_selected bb_shapes
```

Open `results/bb_shapes/m_bb.png` and `m_4l.png`. Each selected sample is
normalised to unit area, including any contribution outside the plotting range.
This lets us compare **shapes** even when the predicted rates differ. The
program also writes `selection_table.csv` with both cutflows.

If the analyser reports overflow, some events lie beyond the plotted range.
Their contributions are still included in the normalisation and recorded in
the JSON report. To show them, widen the bins and rerun **both** samples.

The signal has two known mass peaks. That suggests keeping events close to
both masses. Before trying it, predict which sample will lose a larger fraction.

### Apply two mass windows

A **mass window** keeps events between a lower and upper mass. The following
commands require `105 <= m_bb <= 145 GeV` and `350 <= m_4l <= 450 GeV`, as well
as the momentum cuts. Apply the same windows to both samples. **Terminal:**

<!-- student-command: signal_windows -->
```bash
python lheanalyzer/lhe_bb_four_lepton.py examples/gg_h_eta0_bb2e2mu_pilot.lhe.gz bb_signal_windows --min-lepton-pt 10 --min-b-pt 25 --mbb-window 105 145 --m4l-window 350 450
```

<!-- student-command: background_windows -->
```bash
python lheanalyzer/lhe_bb_four_lepton.py examples/pp_bbzz_2e2mu_pilot.lhe.gz bb_background_windows --min-lepton-pt 10 --min-b-pt 25 --mbb-window 105 145 --m4l-window 350 450
```

**Checkpoint:** the background cutflow goes from 66 events after the pT cuts
to seven after the bottom-pair mass window, then three after the four-lepton
window. The signal mass windows should remove no additional events, because
both parent masses are fixed in this simulation. The cutflow efficiencies are
always measured relative to all input events, not just the preceding row.

Three background events are very few: expect large Monte Carlo fluctuations.
A cut that leaves zero sampled events would not prove that the physical
background is zero. Do not tune increasingly narrow windows around the exact
signal masses and interpret the result as detector performance.

### Compare predicted rates

100 signal events and 500 background events are sizes of simulation samples,
not expected numbers of events in an experiment. Each sample's cross section
and weights determine its predicted rate. Use the same comparison program with
rate normalisation. **Terminal:**

<!-- student-command: rates -->
```bash
python lheanalyzer/compare_bb_four_lepton.py results/bb_signal_windows results/bb_background_windows bb_rates --normalization cross-section
```

The vertical axis now shows cross section per GeV on a logarithmic scale, so
both rates can be seen. `comparison.json` gives the selected cross sections and
the signal-to-background ratio. The histogram area, including flow bins, is the
selected cross section. **Do not multiply by branching fractions again:** both
LHE files already include their specified decays.

The signal uses the UFO's approximate Higgs decay table, whose bottom-pair
branching fraction is about 0.9525. It omits important Higgs decay contributions
and is not a precision Standard Model branching fraction. Treat these rates as
a calculation exercise with the stated inputs, not a discovery prediction.
Signal–background interference, showers, jet reconstruction and detector effects
are outside this exercise.

## Try another observable

Choose one extension and use the same list–calculation–plot pattern:

- **The six-particle mass, `m_bb4l`:** add all six four-momenta and call
  `invariant_mass`. For signal this reconstructs the Higgs–new-scalar system.
  Predict its minimum mass using 125 GeV and 400 GeV before making the plot.
- **The bottom-pair azimuthal separation, `delta_phi_bb`:** use
  `math.atan2(py, px)` for each particle and
  `abs(math.remainder(phi_b - phi_bbar, 2 * math.pi))` for their separation.
  Plot between zero and pi. In the default rate mode, use
  `ylabel="Cross section [pb/rad]"` for this angular plot.
  Does a fast-moving Higgs always give back-to-back
  bottom quarks in the laboratory?

The comparison program can also overlay these named observables once you
have produced them for both samples with identical bins and selections.

## What to hand in

1. Your `m_bb` and `pt_bb` plots, explaining why one has a sharp peak and the
   other does not.
2. The signal cutflow and efficiency for the lepton and bottom-quark pT cuts.
3. One extra observable, its calculation, and a sentence interpreting it.
4. If you do the background extension: the shape comparison and the two
   cutflows, explaining the difference between reducing a background and
   proving that it is absent.

If a plot is missing, check that all three additions are present and saved,
with matching names and indentation, and that its plotting call comes before
`return plots`. An old stable-Higgs sample gives `No compatible events`; use
the new `bb2e2mu` file. A non-empty results folder needs a new name, or an
explicit `--overwrite` if you intend to replace it.

The supplied samples let you finish everything above without running MadGraph.
[Optional generation instructions](higgs_bb_generation.md) are provided for
work with your instructor.
