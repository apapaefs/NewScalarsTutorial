# NewScalarsTutorial

Some code and instructions for studying the production of a Higgs boson together
with a new scalar particle at a proton collider. We will generate events with
**MadGraph5_aMC@NLO 3.5.16** and then write a small Python analysis to examine
their momenta.

The process we will study is

```text
g g > h eta0 [noborn=QCD]
```

Here `g` is a gluon, `h` is the Higgs boson, and `eta0` is the new neutral scalar.
The aim is to understand the steps between specifying a physics process and
making a distribution from the simulated events. You will copy and unpack the
model yourself, enter commands in MadGraph, edit its input files, and add a new
plot to the analysis code.

## Before we start

- These instructions assume a Linux or macOS terminal. On Windows, use the Linux
  environment provided for the course, for example WSL. You will need Python
  3.12, GNU Fortran (`gfortran`), Make, a C/C++ compiler and a text editor. Your
  instructor can help prepare these programs before the exercise.
- Begin in the `NewScalarsTutorial` directory. This is the directory containing
  this `README.md`, `Model`, `lheanalyzer` and `examples`. In the terminal, `pwd`
  prints your current directory and `ls` lists its contents. `cd` changes
  directory; `..` means the directory one level above your current location.
- We will use **two different command prompts**. Commands labelled **Terminal**
  go in your ordinary terminal. Commands labelled **MadGraph** go inside
  MadGraph after it has started. The contents of a parameter card are edited in
  a text editor. Do not type card entries at either command prompt.
- Follow the directory changes in order. Paths such as `../../Model` are
  relative to the directory you are in at that step. Do not type the triple
  backticks surrounding a command block; they are only formatting in this page.

First prepare the Python environment. **Terminal, from `NewScalarsTutorial`:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The first command creates a local environment for the Python packages used in
this exercise. The second activates it: your prompt will usually gain a
`(.venv)` prefix. The third installs NumPy for numerical work, Matplotlib for
plotting, and a small compatibility package required by MadGraph. In this
environment, `python` refers to the Python version we have just selected.
In a new terminal, return to `NewScalarsTutorial` and run
`source .venv/bin/activate` again before continuing.

## Getting started with MadGraph5_aMC and the new scalar model

- Download [MG5_aMC_v3.5.16.tar.gz](https://launchpad.net/mg5amcnlo/3.0/3.5.x/+download/MG5_aMC_v3.5.16.tar.gz)
  from the official MadGraph downloads. The commands below assume it is in your
  `Downloads` directory. If you saved it elsewhere, change the source path in
  the `cp` command. A `.tar.gz` file is a compressed archive containing a
  directory and its files.
- Create a working directory and copy the archive into it. **Terminal, from
  `NewScalarsTutorial`:**

```bash
mkdir -p Work
cp ~/Downloads/MG5_aMC_v3.5.16.tar.gz Work/
cd Work
tar -xzf MG5_aMC_v3.5.16.tar.gz
ls
```

`mkdir` creates a directory, `cp` copies a file, and `tar -xzf` extracts this
compressed archive. You should now see a directory named `MG5_aMC_v3_5_16`.
If your instructor has already installed this version there, use that
installation and skip the download and extraction. Do not extract over a
different existing installation.

- The tutorial's `Model` directory contains `loop_sm_scalar_source.tar.gz`.
  It contains the model's Python source files, which describe the particles,
  masses and interactions that MadGraph will use. The old Python caches have
  been left out; the physics source is unchanged from the original NewScalars
  model. We now copy this archive into MadGraph's `models` directory.
  **Terminal, currently in `Work`:**

```bash
cd MG5_aMC_v3_5_16
cat VERSION
cp ../../Model/loop_sm_scalar_source.tar.gz models/
cd models
tar -xzf loop_sm_scalar_source.tar.gz
ls loop_sm_scalar
cd ..
```

Check that `VERSION` reports `3.5.16`. The `ls` command should show files such as
`particles.py`, `parameters.py` and `vertices.py`. The final `cd ..` returns you
to `Work/MG5_aMC_v3_5_16`. If the same model is already installed there, you can
skip its copy and extraction as well.

- Start MadGraph. **Terminal, in `Work/MG5_aMC_v3_5_16`:**

```bash
python bin/mg5_aMC
```

You should see a welcome message and a prompt such as `MG5_aMC>`.
**From this point, enter the following commands in MadGraph, one at a time.**
First choose a few settings for the exercise:

```text
set auto_update 0
set automatic_html_opening False
set run_mode 0
set ninja None
set collier None
set text_editor nano
```

These keep the chosen version fixed, stop browser windows opening automatically,
and run jobs on this computer in serial mode. The two library settings use the
loop-calculation tools supplied with MadGraph, without requesting optional
downloads. The final command chooses `nano` as the editor for the input files.
Use your instructor's preferred editor instead if necessary.

- To import the new scalar model, type **in MadGraph**:

```text
import model loop_sm_scalar
```

Importing a model tells MadGraph which particles and interactions are available.
To generate our process, type:

```text
generate g g > h eta0 [noborn=QCD]
```

The particles before `>` are incoming; the particles after it are outgoing.
`[noborn=QCD]` explicitly asks for a loop-induced process: its leading
contribution contains a loop. For this exercise use this complete form, rather
than the plain `[QCD]` used in the older page. A loop-induced leading-order
calculation is not the same as a next-to-leading-order calculation.

- Once the process has been generated, examine the diagrams:

```text
display diagrams
```

Identify diagrams with a quark loop. Some have a box shape; others contain a
triangle and an intermediate scalar. The viewer depends on your computer;
the diagrams are also saved with the generated process.

- Write the generated code into a directory for this process:

```text
output ../gg_h_eta0
```

The `..` puts this directory in `Work`, next to the MadGraph installation.
On the first use, the supplied loop libraries are compiled; this may take
several minutes. Wait for MadGraph to report that the output is complete.
If `gg_h_eta0` already exists from a previous exercise, keep it and use `launch`
on that saved process, or choose a new output name for a different process.

## Choosing the model parameters and generating events

- Start a run called `pilot`. **MadGraph:**

```text
launch ../gg_h_eta0 -n pilot
```

The run name distinguishes this sample from later samples. On the first screen,
leave the shower, particle decays (`madspin`) and reweighting switched off. You
can enter these settings explicitly at that screen:

```text
shower=OFF
madspin=OFF
reweight=OFF
done
```

We will initially study the two scalars before either decays. A parton shower
adds radiation to the hard collision; it is also outside this first exercise.
The next screen asks whether you want to edit the input cards. Do not finish
this second screen until you have checked both cards below.

- Choose the entry for **`param_card.dat`**, normally option `1`. This file
  contains masses, widths and couplings. In nano, use the arrow keys to move,
  type to edit, **Ctrl+O**, then **Enter** to save, and **Ctrl+X** to exit.
  Saving and exiting returns you to MadGraph's card-editing menu.
- Find the block headed `BLOCK BSM`. Replace its numbered entries with the
  following values. Keep one `BLOCK BSM` heading: do not add a second copy of
  the block elsewhere in the file.

**Contents of `param_card.dat`, not prompt commands:**

```text
BLOCK BSM
   13  0.9797958971132712  # ctheta
   14  0.2                 # stheta
   15  0.0                 # kap111
   16  100.0               # kap112
   17  100.0               # kap122
   18  0.0                 # kap222
   19  0.0                 # kap1111
   20  0.0                 # kap1112
   21  0.0                 # kap1122
   22  0.0                 # kap1222
   23  0.0                 # kap2222
```

`ctheta` and `stheta` control the couplings of the two scalars to Standard Model
particles. Here they are chosen as the cosine and sine of a mixing angle, so
their squares add to one. Both must be nonzero for the box contribution in
this example. `kap112` and `kap122` set interactions involving three scalars;
their values are in GeV in this model. Use these illustrative inputs for the
first run; we will vary them later. They are teaching inputs, not a claim that
this point satisfies all experimental constraints.

- In `BLOCK MASS`, find the entries with particle codes `25` and `99925` and
  set their values as follows. Keep the other mass entries in the block.

```text
   25     125.0   # Higgs mass, MH, in GeV
   99925  400.0   # new scalar mass, Meta, in GeV
```

The integer codes identify particle species. Thus `99925` identifies `eta0`;
it is not a mass. We will use the same codes to identify particles in Python.

- Find the `DECAY` entries for codes `6`, `25` and `99925` and change their
  widths to zero for this exercise:

```text
DECAY 6      0.0
DECAY 25     0.0
DECAY 99925  0.0
```

The number following the particle code is its total width in GeV. We use a
stable top in the loop calculation and keep the outgoing scalars undecayed.
These are settings for the production exercise, not physical decay-width
predictions. Leave other entries unchanged. Save the file and exit the editor.

- Now choose **`run_card.dat`**, normally option `2`. This file specifies the
  beams, event count and generation settings. Find the entries below and edit
  their values. Notice that this card uses **`value = name`**, whereas the mass
  block above uses **`particle code  value`**.

**Entries in `run_card.dat`:**

```text
100       = nevents
12345     = iseed
1         = lpp1
1         = lpp2
6500.0    = ebeam1
6500.0    = ebeam2
nn23lo1   = pdlabel
False     = fixed_ren_scale
False     = fixed_fac_scale
3         = dynamical_scale_choice
1.0       = scalefact
0.0       = ptheavy
False     = use_syst
sum       = event_norm
```

`nevents` requests 100 events for a small first test. `iseed` starts the random
number sequence; record it with your results. `lpp1 = lpp2 = 1` selects two
proton beams. Each proton has energy 6500 GeV, giving a proton collision energy
of 13000 GeV, or 13 TeV. MadGraph samples gluons from those protons using a
parton distribution function (PDF); `nn23lo1` selects a built-in PDF set.
The gluon energies vary from event to event.

The scale settings choose a standard momentum scale that varies with the event.
`ptheavy = 0` avoids a minimum transverse-momentum requirement on the scalars at
generation. We turn automatic uncertainty calculations off for this first run.
`event_norm = sum` makes the sum of the event weights represent the cross
section. The [physics notes](docs/physics.md) explain the PDF and scale choices
in more detail.

- Save and exit the run-card editor. Still at **MadGraph's card-editing menu**,
  enter the following two commands. These options may be hidden in the short
  version of the run card:

```text
set ickkw 0
set systematics_program none
```

These leave matching/merging and additional systematics programs off. You can
reopen either card to check your changes. When you are ready, type `done` at
the card-editing menu. MadGraph will now integrate the cross section and
generate the events. Even 100 loop-induced events require an integration step,
so the run may take a few minutes.

- At the end, record the reported cross section, its integration uncertainty,
  and the number of events. Our 100-event check with these inputs gave about
  `2.98e-4 pb`; this is only a check of the example setup. Your differential
  plots will have substantial statistical fluctuations with so few events.
  The complete settings and test result are in the
  [validation record](docs/validation.md).
- The event file is `Work/gg_h_eta0/Events/pilot/unweighted_events.lhe.gz`.
  The same run directory contains a banner with the input cards. Keep it: a
  cross section without the model and run settings does not specify a result.
  Type **`quit` in MadGraph** to return to the terminal.

## Looking at the events

You should now be back in the terminal in `Work/MG5_aMC_v3_5_16`. Return to the
tutorial directory and copy the event file into a directory for analysis.
**Terminal:**

```bash
cd ../..
mkdir -p Work/events
cp Work/gg_h_eta0/Events/pilot/unweighted_events.lhe.gz Work/events/gg_h_eta0_pilot.lhe.gz
zless Work/events/gg_h_eta0_pilot.lhe.gz
```

The final command lets you read the compressed file without extracting it.
Press `/`, type `<event>`, and press Enter to search for the first event. Press
`q` to leave the viewer and return to the terminal.

This is a **Les Houches event (LHE) file**. After its header, each `<event>`
block contains one simulated collision. The first numeric line gives the
number of particle records and the event weight, among other information.
The particle lines contain the particle code, its status, its parents, colour
information, and the momentum components `px py pz E m` in GeV.

Find the two gluons (code `21`, status `-1`) and the Higgs and new scalar
(codes `25` and `99925`, status `1`). Status `-1` means incoming; status `1`
means outgoing. These are **parton-level events**: the two scalars come from
the hard collision and have not been decayed, showered or passed through a
detector simulation.

If you are waiting for a generator installation, a small completed sample is
provided in `examples/gg_h_eta0_pilot.lhe.gz`. You can analyse that file by
using its path in the next command. It contains 100 real MadGraph events;
the separate files under `tests/` are for checking the software.

## Running the Python analysis

- The analyser is also tested with Python 3.9. If your course computer uses
  that version, you can use it for this section; the MadGraph setup above was
  tested separately with Python 3.12. Activate your course or tutorial Python
  environment, then check and install the required packages. **Terminal, from
  `NewScalarsTutorial`:**

```bash
python --version
python -m pip install -r requirements.txt
python -m pip check
```

Using `python -m pip` installs packages for the same interpreter that will run
the analysis. Keep NumPy and Matplotlib consistent with `requirements.txt`:
some older Matplotlib packages cannot load alongside NumPy 2. The required
Matplotlib version is now at least 3.9.4. If an import or plotting error occurs,
see the [troubleshooting notes](docs/validation.md#common-problems).

- Our starting analysis is in `lheanalyzer/lhe_analyzer.py`, adapted from
  [lheanalyzer](https://gitlab.com/apapaefs/lheanalyzer). The code reads the
  event file, calculates quantities for each event and draws histograms.
  **Terminal, from `NewScalarsTutorial`:**

```bash
python lheanalyzer/lhe_analyzer.py Work/events/gg_h_eta0_pilot.lhe.gz pilot
```

The first argument is the event file. The final word, `pilot`, is an output
label: your plots are written in `results/pilot/`. It does not change the
events. Open that directory in your file manager and look at the PDF or PNG
files. Both formats contain the same plots.

- There are initially six plots: `pt_h`, `pt_eta0`, `m_h_eta0`, `y_h`,
  `y_eta0` and `delta_phi`. We will understand one of them before adding another.
  `pt_h` is the Higgs transverse momentum, defined by

```text
pT = sqrt(px² + py²).
```

"Transverse" refers to the plane perpendicular to the beam, which we call the
z direction. Each selected event contributes one Higgs pT value. A histogram
groups these values into intervals called **bins**. Its horizontal axis gives
the pT interval; its vertical axis gives the cross section per GeV in that bin.

- You should find equal transverse momenta for the two scalars, a pair mass
  above `125 + 400 = 525 GeV`, and an azimuthal separation close to pi for
  nonzero pT. Explain these observations using momentum conservation.
- `summary.json` records the selected-event count and numerical checks.
  `histograms.csv` contains the plot data: bin edges, bin integrals, squared
  normalised weight sums, densities and statistical errors. You can inspect
  these as text, but you do not need to edit them to add a plot.

## Understanding the analysis code

- Make a backup before editing, then open the analysis file in your text editor.
  **Terminal:**

```bash
cp lheanalyzer/lhe_analyzer.py Work/lhe_analyzer_before_edits.py
nano lheanalyzer/lhe_analyzer.py
```

Edit the file inside `lheanalyzer`; the copy in `Work` is only a backup. The
file reader and report-writing details are in `lheanalyzer/lhe_tools.py`, which
you can leave alone for this exercise. We will work in three functions:

| Function | What it does |
| --- | --- |
| `analyze()` | Loops over events and calculates the quantities to plot. |
| `plot_histogram()` | Draws one histogram, labels it and saves PDF/PNG files. |
| `make_plots()` | Calls `plot_histogram()` once for each plot we want. |

- Near the start of `analyze()`, find:

```python
    output = {}
    output["pt_h"] = []
```

`output` is a Python **dictionary**: it associates a name with some data.
The name `"pt_h"` is a string, and `[]` creates an empty list. We will put one
Higgs pT value in this list for each selected event.

- Inside the event loop, `h` and `eta` refer to the outgoing particles selected
  by their codes and status. `h.px` means the x component of the Higgs momentum;
  `h.energy` means its energy. The same notation applies to `eta`. Find:

```python
        pt_h = math.sqrt(h.px**2 + h.py**2)
        output["pt_h"].append(pt_h)
```

These lines occur in the calculation and list-filling parts of the loop.
`**2` means "squared", `math.sqrt()` takes a square root, and `.append()` adds
one number to the end of a list. After 100 selected events, the list has 100
entries. The indentation is important: these lines must be **inside** the
event loop to run for every event.

- In `make_plots()`, find the existing call for the Higgs pT:

```python
    plots["pt_h"] = plot_histogram(
        output["pt_h"], weights,
        bins=np.linspace(0, 600, 31),
        xlabel=r"$p_T(h)$ [GeV]", ylabel=per_gev,
        filename=output_dir / "pt_h",
    )
```

Read this as "plot the numbers in `output["pt_h"]`, using the event weights".
The remaining arguments specify the bin edges, horizontal label, vertical
label and filename. `np.linspace(0, 600, 31)` makes **31 edges**, giving
**30 bins** between 0 and 600 GeV. Each bin is 20 GeV wide. The `r` before the
label allows the mathematical notation to be written conveniently; a plain
label such as `"Higgs transverse momentum [GeV]"` also works.

`per_gev` is the vertical-axis label for a quantity measured in GeV. `per_unit`
is used for rapidity and `per_radian` for an angle in radians. These labels
are already defined at the start of `make_plots()`. `output_dir / "pt_h"`
constructs the output path; the plotting function adds `.pdf` and `.png`.

As a first small change, replace `31` by `16`. Save the file and rerun the
analysis with a new label, for example `pilot_widebins`. You now have 15 bins,
each 40 GeV wide. Compare the resolution and fluctuations with the original
plot. The plot is divided by the bin width, so doubling that width does not
simply double its vertical scale.

## Adding a new plot: the rapidity of the two-scalar system

We will now make a new plot in three steps. The example is the **pair rapidity**,
which describes the longitudinal motion of the Higgs and new scalar together.
For any system with energy `E` and longitudinal momentum `pz`,

```text
y = (1/2) log((E + pz)/(E - pz)).
```

For the pair, add the energies and longitudinal momenta first:
`E_pair = E_h + E_eta0`, `pz_pair = pz_h + pz_eta0`. The pair rapidity is not
the sum of the individual rapidities. This variable is dimensionless.

### Step 1: create a list

At the start of `analyze()`, immediately after the existing lines that create
the lists, add:

```python
    output["y_pair"] = []
```

Use four spaces before this line, like the other list declarations. It belongs
**before the event loop**, so the list is created once rather than being emptied
on every event. The name `"y_pair"` is our label for this new quantity.

### Step 2: calculate one value for each selected event

Inside the event loop, after the existing `.append()` lines and before
`selected_weights.append(weight)`, add:

```python
        energy_pair = h.energy + eta.energy
        pz_pair = h.pz + eta.pz
        y_pair = 0.5 * math.log(
            (energy_pair + pz_pair) / (energy_pair - pz_pair)
        )
        output["y_pair"].append(y_pair)
```

These statements start with eight spaces, matching the calculations for `pt_h`
and `y_h`. `math.log()` is the natural logarithm. The final line stores this
event's value. It must use exactly the same dictionary name as Step 1, including
the underscore. Keep the calculation after the selection cut so its list has
one entry for every selected weight.

### Step 3: ask for a histogram

In `make_plots()`, after the existing plot calls and **before `return plots`**,
add:

```python
    plots["y_pair"] = plot_histogram(
        output["y_pair"], weights,
        bins=np.linspace(-6, 6, 31),
        xlabel=r"$y(h\eta_0)$", ylabel=per_unit,
        filename=output_dir / "y_pair",
    )
```

Here we choose 30 bins from -6 to 6. Their width is 0.4. The label has no GeV
unit because rapidity is dimensionless. Keep `weights` as it is: the program
has already calculated the correct weight for each selected event.
Giving the plot its own entry in `plots` also includes it in the CSV and summary.

Save your changes and exit the editor. **Terminal, from `NewScalarsTutorial`:**

```bash
python lheanalyzer/lhe_analyzer.py Work/events/gg_h_eta0_pilot.lhe.gz pilot_y_pair
```

Open `results/pilot_y_pair/y_pair.pdf`. You should now have seven plots.
Does the pair rapidity have to vanish in every event? Consider whether the two
incoming gluons necessarily carry equal fractions of the proton momenta.
With a large sample, the distribution should be symmetric about zero for
identical proton beams; 100 events can still fluctuate visibly.

If something goes wrong, check the following:

- **`KeyError: 'y_pair'`:** check the spelling in all three steps and make sure
  the list was declared inside `analyze()` before the event loop.
- **`IndentationError`:** compare the spaces with the neighbouring lines. Use
  spaces consistently, not a mixture of tabs and spaces.
- **A values/weights length error:** initialise the list once, then append once
  per selected event. Do not put `.append()` outside the event loop.
- **No new plot:** check that the call is inside `make_plots()` and before its
  `return plots` line, and that you saved the file you are actually running.
- **The output directory already exists:** choose a new label. To replace plots
  deliberately, add `--overwrite` to the command. This changes the plot files,
  not the input events.

## Event weights, selection cuts and further exercises

An event weight tells us how much that simulated event contributes to the
predicted cross section. For the equal-weight pilot sample, every event has
the same contribution. The analysis also retains weights if a sample has
unequal or negative ones. It does not replace them with unweighted counts.

Before plotting, the program uses the cross section in the LHE header and the
sum of all input weights to set the overall normalisation. The histogram then
divides each bin's contribution by its width. Thus the area of an uncut
histogram gives the inclusive cross section, provided the plotted range covers
all events. The error bars describe the finite sample statistics; they are not
a complete estimate of the theoretical uncertainty.

- Try a selection requiring `pT(h) >= 100 GeV`. **Terminal:**

```bash
python lheanalyzer/lhe_analyzer.py Work/events/gg_h_eta0_pilot.lhe.gz pilot_pt100 --min-pt-h 100
```

Compare the selected-event count and cross section with the original result.
Rejecting events must reduce the rate for this positive-weight sample. The
normalisation still uses all input events; it does not rescale the surviving
events back to the original cross section. Find the corresponding `if` and
`continue` statements in `analyze()`.

- For a comparison of shapes, repeat a run with `--normalization shape`. The
  uncut distribution then has unit area. After a cut its area is the weighted
  selection efficiency. Check the vertical label when comparing plots.
- Add a distribution of `y_h - y_eta0`, or of the pair transverse momentum
  `sqrt((px_h + px_eta0)² + (py_h + py_eta0)²)`, following the same three steps.
  Predict the second result for this two-body process before running the code.
- Change a plotting range or number of bins. If the program reports overflow
  or underflow, some values lie outside your range; enlarge it and compare.
- Once the pilot is understood, start MadGraph again from its installation
  directory and type `launch ../gg_h_eta0 -n sample_01`. Edit `nevents` to
  `10000` and use a different seed. Check the runtime with your instructor
  before making larger samples. Keep each run under a different name.
- For a second physics sample, change the new-scalar mass from 400 to 600 GeV
  in the parameter card. Predict the new pair-mass threshold. Generate and
  analyse the new run under different names, and compare both rates and shapes.
  A further exercise is to vary the cubic scalar couplings and study interference.

In your report, state the process, generator version, beam energy, masses,
couplings, PDF, scales, seed and event count. Explain how you calculated your
new quantity, how you checked the result, and what the plot tells you about
the collision. The [project questions](docs/tutorial.md) provide further prompts.

## Next exercise: reconstructing the new scalar

Continue with [the four-lepton exercise](docs/four_lepton.md). We leave the
associated Higgs stable and decay `eta0 -> Z Z -> e+ e- mu+ mu-`. A separate
starter analyser plots the electron-pair mass. You will add the muon-pair and
four-lepton masses, then compare the plots and selection efficiency after a
lepton transverse-momentum cut. The guide explains each code addition, shows
every run command and gives a checkpoint after each step. A small decayed sample
is provided, so you only need the Python setup to begin; running MadGraph is
an [optional extension](docs/four_lepton_generation.md).

Then continue with [reconstructing the Higgs from bottom quarks](docs/higgs_bb.md).
The next starter includes the completed lepton analysis. You will add the
bottom-pair mass and transverse momentum, try your own observable, and apply
simple selections. An optional Standard Model background sample lets you compare
shapes, rates and the effect of mass windows using the same analysis code.

## Reference material

The manual steps above are the student exercise. The files in `cards/` and
`scripts/install_model.py` are optional instructor/reproducibility aids and
are not needed to follow it. Additional details are available in the
[physics notes](docs/physics.md), [validation and troubleshooting](docs/validation.md),
[source attribution](docs/provenance.md), and [GitHub publishing instructions](docs/publishing.md).
The model and original tutorial come from
[NewScalars](https://gitlab.com/apapaefs/NewScalars).

Software installations, generated processes, event samples made during the
exercise, and plots belong in `Work/` or `results/`; these directories are
excluded from Git. The small provided example is kept separately in `examples/`.
