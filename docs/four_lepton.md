# Finding the new scalar's mass from four leptons

How can we find the mass of a particle that has already decayed? We use the
energies and momenta of the particles it produced. This is called
**reconstructing** its mass.

In this exercise, two gluons (`g`) produce a Higgs boson (`h`) and the new scalar
(`eta0`). The new scalar decays into two Z bosons. One Z decays into an electron
and a positron; the other decays into a muon and an antimuon:

```text
The collision:       g g -> h + eta0
The scalar decay:    eta0 -> Z + Z
The two Z decays:    Z -> e+ + e-     and     Z -> mu+ + mu-
```

Electrons and muons, together with their antiparticles, are examples of
**leptons**. Here `e-` is an electron, `e+` a positron, `mu-` a muon and `mu+`
an antimuon. The associated Higgs stays **stable in this simulation**: we leave
it undecayed. This does not mean that a real Higgs boson is stable.

You will start with a working plot, add two more, and then count how many events
pass a simple selection. An **event** is one simulated collision.

| Plot | What goes into the mass calculation? | Your task | Expected peak |
| --- | --- | --- | --- |
| `m_ee` | Electron + positron | Run the supplied example | About 91 GeV, the Z mass |
| `m_mumu` | Muon + antimuon | Add a similar calculation | About 91 GeV, the Z mass |
| `m_4l` | All four leptons | Add the new scalar's mass | 400 GeV |

The supplied file contains 100 events at the same 13 TeV proton collision energy
as the first exercise, with a 125 GeV Higgs and a 400 GeV new scalar. It describes
the production and decay of particles, without a parton shower or detector
simulation.

## Before you start

You need a terminal, a text editor and the Python environment prepared in
[Before we start in the main tutorial](../README.md#before-we-start).
**You can complete this whole exercise with the supplied event file. You do not
need to install or run MadGraph.** If you have not prepared Python yet, follow
the three Python setup commands in that section, then return here.

Run every terminal command below from the `NewScalarsTutorial` directory.
To check where you are, type these commands in your **terminal**:

```bash
pwd
ls
```

The directory should contain `README.md`, `lheanalyzer`, `examples` and
`requirements.txt`. If you are inside its `docs` or `lheanalyzer` directory,
`cd ..` takes you back one level. If you are elsewhere, use `cd` to go to your
own copy of `NewScalarsTutorial`.

Activate the Python environment. **Terminal:**

```bash
source .venv/bin/activate
```

Your prompt will usually start with `(.venv)`. Repeat this activation whenever
you open a new terminal.

Throughout this guide, **Terminal** blocks are commands to run. **Python — edit
the file** blocks belong in the text editor. Copy only what is inside a block,
without the surrounding backticks. The decay diagram above is an explanation,
not a command.

## 1. Make your first plot

Run the supplied analyser. **Terminal:**

<!-- student-command: start -->
```bash
python lheanalyzer/lhe_four_lepton.py examples/gg_h_eta0_2e2mu_pilot.lhe.gz four_lepton_start
```

Here is what each part means:

| Part | Meaning |
| --- | --- |
| `python` | Run a Python program using the active environment |
| `lheanalyzer/lhe_four_lepton.py` | The program to run |
| `examples/gg_h_eta0_2e2mu_pilot.lhe.gz` | The compressed file of simulated events to read |
| `four_lepton_start` | A name for this set of results |

Open `results/four_lepton_start/m_ee.png` with your file manager. The program
also prints its full path. The PDF version contains the same plot.

This is a **histogram**: we group events into mass intervals, called **bins**.
The horizontal axis shows the electron-pair mass in GeV. Look for a peak near
91 GeV. The vertical axis includes the predicted collision rate; we will return
to its units in step 6. With only 100 events, the detailed shape will be uneven.

**Checkpoint:** you have one PNG plot and one PDF plot. The terminal table
shows 100 events in each of its three rows. The starter makes only `m_ee`;
you will add the other two masses.

The results folder also contains `histograms.csv` (the numbers behind the
plot), `cutflow.csv` (the selection table) and `summary.json` (a text record of
the run). CSV files can be opened in a text editor or spreadsheet program.
You do not need to edit any of these output files.

## 2. Look inside one event

An LHE file is a text file of simulated events. The `.gz` ending means it has
been compressed. This command lets you read it without unpacking it yourself.
**Terminal:**

```bash
zless examples/gg_h_eta0_2e2mu_pilot.lhe.gz
```

Type `/<event>` and press Enter to find the first event. The first numeric line
below `<event>` is a summary of that event. The lines after it describe the
particles. Their first two columns are the **particle code** and **status**:

| Particle | PDG code | Status in this sample |
| --- | --- | --- |
| Incoming gluons | `21` | `-1` |
| Stable Higgs | `25` | `1` |
| New scalar | `99925` | `2` |
| Intermediate Z bosons | `23` | `2` |
| Electron, positron | `11`, `-11` | `1` |
| Muon, antimuon | `13`, `-13` | `1` |

A **PDG code** is a number identifying a particle. For these leptons, the
negative code identifies the antiparticle; it does not mean negative energy.
Status `1` identifies an outgoing particle. Status `2` identifies an
intermediate particle whose decay products are also listed.

**Checkpoint:** find the five status-1 particles: one Higgs and the four
leptons. Press `q` to leave the viewer and return to the terminal.

We reconstruct masses from the leptons. Adding the intermediate Z or `eta0`
momentum as well would count the same energy twice.

### How do two particles give us a mass?

Each particle has an energy `E` and three momentum components, `px`, `py` and
`pz`. Together, these four numbers are its **four-momentum**. Add the two
particles' energies, then add each momentum component separately:

```text
E_pair  = E_1  + E_2
px_pair = px_1 + px_2
py_pair = py_1 + py_2
pz_pair = pz_1 + pz_2
m_pair  = sqrt(E_pair² - px_pair² - py_pair² - pz_pair²)
```

Here `sqrt` means square root. We use the particle-physics convention `c = 1`,
so energies, momenta and masses are all written in GeV.

Try these simple, invented four-momenta as a practice calculation:

```text
Particle 1: (E, px, py, pz) = (50,  30, 0,  40) GeV
Particle 2: (E, px, py, pz) = (50, -30, 0, -40) GeV
```

Their total energy is 100 GeV and their total momentum is zero, so the pair
has mass 100 GeV. Each individual particle has zero mass in this example.
This shows why we add four-momenta before calculating the pair's mass.

## 3. Find the three places you will edit

First make a backup and open the starter. **Terminal:**

```bash
mkdir -p Work
cp -n lheanalyzer/lhe_four_lepton.py Work/lhe_four_lepton_before_edits.py
nano lheanalyzer/lhe_four_lepton.py
```

`mkdir -p` creates the backup directory if needed. `cp -n` copies the file
without overwriting an existing backup. Edit the file inside `lheanalyzer`;
the copy in `Work` is only a backup. You may use another plain-text code editor
instead of `nano`.

If using `nano`, these are the controls you need:

- **Find text:** press Ctrl+W, type the text to find, then press Enter.
- **Save:** press Ctrl+O (the letter O), then Enter to confirm the filename.
- **Exit:** press Ctrl+X.

Here Ctrl means hold the **Control** key while pressing the letter. On a Mac,
use Control for these shortcuts, rather than Command.

The code has three comments marking where your additions go. Search for each
comment to find its position:

| Search for | What you will add immediately above it | Indentation |
| --- | --- | --- |
| `# EXERCISE LISTS:` | An empty list to store the new masses | 4 spaces |
| `# EXERCISE CALCULATIONS:` | The calculation for one event | 8 spaces |
| `# EXERCISE PLOTS:` | The instruction to draw the histogram | 4 spaces |

Keep the comments and all existing code. **Paste each addition once, immediately
above its comment.** Use spaces, not tabs. Python uses this indentation to tell
which instructions belong together. The lists are created before the event
loop; the calculations run inside the loop, once per selected event.

A few pieces of Python are enough for this exercise:

- `output` is a **dictionary**: it connects names such as `"m_ee"` to lists.
- `output["m_ee"] = []` creates an empty list for the electron-pair masses.
- `.append(m_ee)` adds one calculated mass to the end of that list.
- `electron.energy` means the electron's energy; `.px`, `.py` and `.pz` give
  its momentum components.
- A line starting with `#` is a comment for the reader. Python does not run it.

Find this working example in `analyze()`. **Read this existing Python code;
you do not need to paste it:**

```python
        m_ee = invariant_mass(
            electron.energy + positron.energy,
            electron.px + positron.px,
            electron.py + positron.py,
            electron.pz + positron.pz,
        )
        output["m_ee"].append(m_ee)
```

`invariant_mass(...)` calls a function that implements the square-root formula
from step 2. Give it the total energy and the three total momentum components,
in that order. The variables `electron`, `positron`, `muon` and `antimuon`
already refer to the right particles. The file reading and particle selection
are provided; your edits start from those variables.

## 4. Add the muon-pair mass

You will make three small additions. This is the same calculation as for the
electron pair, using the muon and antimuon instead.

### A. Make a list

Immediately above `# EXERCISE LISTS:`, add this line with **four spaces** at
the start. **Python — edit the file:**

<!-- exercise: lists -->
```python
    output["m_mumu"] = []
```

### B. Calculate and store the mass

Immediately above `# EXERCISE CALCULATIONS:`, add the following. The first and
last lines have **eight spaces** at the start; the arguments inside the function
call have twelve. **Python — edit the file:**

<!-- exercise: calculations -->
```python
        m_mumu = invariant_mass(
            muon.energy + antimuon.energy,
            muon.px + antimuon.px,
            muon.py + antimuon.py,
            muon.pz + antimuon.pz,
        )
        output["m_mumu"].append(m_mumu)
```

### C. Ask for a plot

Immediately above `# EXERCISE PLOTS:`, add this call with **four spaces** at
the start of its first line. It must be before `return plots`.
That instruction ends the function, so code placed after it would not run.
**Python — edit the file:**

<!-- exercise: plots -->
```python
    plots["m_mumu"] = plot_histogram(
        output["m_mumu"], weights,
        bins=np.linspace(0, 200, 51),
        xlabel=r"$m(\mu^+\mu^-)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "m_mumu",
    )
```

`np.linspace(0, 200, 51)` makes 51 evenly spaced bin edges, giving 50 bins
of width 4 GeV. `xlabel` gives the horizontal-axis label; `filename` gives
the plot's name. The supplied plotting function handles `weights` and the
vertical-axis units for you.

Save the file and leave the editor. Run it again with a new results name.
**Terminal:**

<!-- student-command: two_masses -->
```bash
python lheanalyzer/lhe_four_lepton.py examples/gg_h_eta0_2e2mu_pilot.lhe.gz four_lepton_two_masses
```

**Checkpoint:** `results/four_lepton_two_masses` contains `m_ee.png` and
`m_mumu.png`, together with their PDF versions. Both should peak near 91 GeV.
Both pairs come from Z bosons, although their bins need not contain identical
numbers of events. If you still have only one plot, check that you saved the
file you edited and placed the new plotting call before `return plots`.

## 5. Reconstruct the new scalar

Open the file again. **Terminal:**

```bash
nano lheanalyzer/lhe_four_lepton.py
```

Keep your muon-pair additions. Now use the same three locations to add the
four-lepton mass. The new scalar's four-momentum is the sum of all four lepton
four-momenta. Leave the Higgs out of this sum: it was produced alongside the
new scalar and is not one of its decay products.

### A. Make a list

Immediately above `# EXERCISE LISTS:`, with **four spaces** at the start:
**Python — edit the file:**

<!-- exercise: lists -->
```python
    output["m_4l"] = []
```

### B. Calculate and store the mass

Immediately above `# EXERCISE CALCULATIONS:`, with **eight spaces** at the
start of each instruction. **Python — edit the file:**

<!-- exercise: calculations -->
```python
        energy_4l = (electron.energy + positron.energy
                     + muon.energy + antimuon.energy)
        px_4l = electron.px + positron.px + muon.px + antimuon.px
        py_4l = electron.py + positron.py + muon.py + antimuon.py
        pz_4l = electron.pz + positron.pz + muon.pz + antimuon.pz
        m_4l = invariant_mass(energy_4l, px_4l, py_4l, pz_4l)
        output["m_4l"].append(m_4l)
```

Each sum has four terms, one for each lepton. The parentheses around the
energy sum let us write that long expression on two lines.

### C. Ask for a plot

Immediately above `# EXERCISE PLOTS:`, with **four spaces** at the start of
the first line. **Python — edit the file:**

<!-- exercise: plots -->
```python
    plots["m_4l"] = plot_histogram(
        output["m_4l"], weights,
        bins=np.linspace(302.5, 502.5, 41),
        xlabel=r"$m(e^+e^-\mu^+\mu^-)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "m_4l",
    )
```

These 40 bins have width 5 GeV, with 400 GeV at a bin centre. Save the file and
leave the editor. **Terminal:**

<!-- student-command: complete -->
```bash
python lheanalyzer/lhe_four_lepton.py examples/gg_h_eta0_2e2mu_pilot.lhe.gz four_lepton_complete
```

**Checkpoint:** `results/four_lepton_complete` contains **three PNG and three
PDF plots**. The new `m_4l.png` has a sharp peak at 400 GeV.

Why is this peak so sharp? The generator keeps the parent `eta0` **on shell**:
its mass is fixed at 400 GeV for every event. Your reconstructed masses should
therefore agree with 400 GeV up to numerical rounding. The histogram bin width
makes the plotted spike look finite. It does not measure detector mass
resolution or the scalar's physical decay width. There is no detector simulation
here. The internal Z masses can vary in this calculation; the
[physics notes](physics.md#four-lepton-decay-exercise) explain the approximation.

## 6. Select events using the lepton momenta

A **selection**, also called a **cut**, is a rule for deciding which events
enter our plots. We will require every lepton to have transverse momentum of
at least 10 GeV.

The beam direction is the z direction. **Transverse momentum**, written `pT`,
is the size of the momentum perpendicular to that direction:

```text
pT = sqrt(px² + py²)
```

You can change this requirement using a command option, without editing the
code. **Terminal, after completing both new mass plots:**

<!-- student-command: cut -->
```bash
python lheanalyzer/lhe_four_lepton.py examples/gg_h_eta0_2e2mu_pilot.lhe.gz four_lepton_pt10 --min-lepton-pt 10
```

`--min-lepton-pt 10` applies the 10 GeV threshold to **all four leptons**. If
any one of them falls below it, the whole event is excluded from the plots.
Without this option, the threshold is zero.

To see how the code does this, find `for lepton in leptons:` in `analyze()`.
It checks the particles one at a time. If the event fails, `continue` skips
the remaining calculations for that event and moves to the next one.

**Checkpoint:** compare the terminal tables, or the two `cutflow.csv` files.
For the supplied sample, you should find:

| Selection stage | Baseline: no pT cut | Every lepton has pT ≥ 10 GeV |
| --- | ---: | ---: |
| All input events | 100 | 100 |
| Correct particles | 100 | 100 |
| Lepton pT cut | 100 | 95 |

This table is called a **cutflow**: it shows how many events pass each step.
The selection efficiency here is `95 / 100 = 0.95`, or **95%**. These exact
counts apply to the supplied file; a newly generated sample can give different
counts. In the CSV, the three rows are named `input`, `correct_final_state`
and `lepton_pt`, in the same order as this table.

Compare the three plots in `results/four_lepton_complete` with those in
`results/four_lepton_pt10`. The peak positions should stay similar, while
fewer events contribute after the cut. The cut chooses events; it does not
change a particle's momentum within an event.

### What do the rates and weights mean?

An event's **weight** describes how much it contributes to the predicted rate.
All events in this file have equal, positive weights, so keeping 95% of the
events also keeps 95% of the predicted rate. A **cross section** measures how
likely the process is to occur in a collision. The calculation is:

```text
selected cross section = input cross section × selection efficiency
```

The table reports cross sections in **pb**, short for picobarns. A number such
as `1.1082e-07` means `1.1082 × 10⁻⁷`. The analyser handles these small numbers
and the units for you. The event file's cross section already includes the
probability of the specified decays; you do not need another branching-fraction
factor.

The histogram's vertical axis is cross section **per GeV**. Multiply each bin
height by its width and add the results to obtain the plotted cross section.
Any events below or above the plotted range are called **underflow** or
**overflow**; their contributions are recorded in `summary.json`.
The [normalisation notes](physics.md#observables-and-normalisation) give more
detail about weights, uncertainties and the optional `--normalization shape`
setting.

## What to hand in

1. Your three baseline mass plots, with a sentence identifying each peak.
2. The selection table before and after the 10 GeV cut, and your calculation
   of the selection efficiency.
3. A sentence explaining why the Higgs momentum is left out of `m_4l`.
4. A sentence explaining why the sharp 400 GeV peak is not a measurement of
   detector resolution.

**Optional challenge:** predict whether more or fewer events will pass a
20 GeV threshold, then try `--min-lepton-pt 20` with a new results name.
Explain what changes in the selection table.

## If something goes wrong

Read the last line of the error first. Most editing errors in this exercise
come from a filename, indentation or a missing line.

| What you see | What to check |
| --- | --- |
| `No such file or directory` | Run `pwd` and `ls`. All commands start in `NewScalarsTutorial`, not inside `docs`, `Work` or `lheanalyzer`. |
| `.venv/bin/activate` is missing | Check your directory. If the environment has not been created, follow the Python setup in the main tutorial. |
| `No module named numpy` or `matplotlib` | Activate `.venv`, then run `python -m pip install -r requirements.txt`. |
| `IndentationError` | Match the spaces shown in the snippets: four for the list and plot, eight for the calculation. Avoid tabs. |
| `SyntaxError` | Check quotation marks, commas and parentheses. Do not paste the Markdown backticks into Python. |
| `KeyError: 'm_mumu'` or `'m_4l'` | Add the matching empty list before the event loop, and check that its name is spelled the same in all three places. |
| A message about different numbers of values and weights | Put each mass calculation and `.append(...)` inside the event loop, at the calculation marker after the cut. |
| There is still only one plot | Save the edited file, put plotting calls before `return plots`, and open the results folder from your new run. |
| `No compatible events` | Use `gg_h_eta0_2e2mu_pilot.lhe.gz`. The older undecayed sample does not contain the four leptons. |
| The results folder is non-empty | Choose a new results name, for example `four_lepton_complete_2`. To replace that run's existing outputs deliberately, add `--overwrite`. |
| Zero events pass a very high pT cut | This is a valid result. Try a lower threshold with a new results name. |

The analysis exercise ends here. [Generating a new sample](four_lepton_generation.md)
is a separate, optional extension to work through with your instructor.
The [physics notes](physics.md#four-lepton-decay-exercise) and
[validation notes](validation.md#four-lepton-exercise-validation) give the
technical details behind the supplied sample.
