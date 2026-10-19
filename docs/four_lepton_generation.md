# Optional: generating the four-lepton sample

This is a separate extension for students working with an instructor.
The [main four-lepton exercise](four_lepton.md) uses the supplied sample;
you can finish all of its analysis tasks without installing or running MadGraph.

Complete the model installation from the main README first. The small supplied
sample is sufficient for the analysis lesson; this section explains how it is
made. Keep each new process/run under its own name.

**Terminal, from `NewScalarsTutorial`:**

```bash
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC
```

**MadGraph:**

```text
set auto_update 0
set automatic_html_opening False
set run_mode 0
set ninja None
set collier None
import model loop_sm_scalar
generate g g > h eta0 [noborn=QCD]
output Work/gg_h_eta0_2e2mu
quit
```

Copy the supplied teaching parameter card into the new process. **Terminal:**

```bash
cp cards/param_card_gg_h_eta0_2e2mu.dat Work/gg_h_eta0_2e2mu/Cards/param_card.dat
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC
```

**MadGraph:**

```text
set auto_update 0
set automatic_html_opening False
set run_mode 0
import model loop_sm_scalar
compute_widths 99925 23 --body_decay=2 --path=Work/gg_h_eta0_2e2mu/Cards/param_card.dat --output=Work/gg_h_eta0_2e2mu/Cards/param_card.dat
launch Work/gg_h_eta0_2e2mu -n four_lepton_pilot
```

The supplied parameter card contains the same teaching masses and couplings,
with consistent nonzero widths for the particles we decay. `compute_widths`
recalculates the widths from **all open tree-level two-body modes** in this model,
not just the desired leptonic channel. The Higgs and top widths stay zero.
Use the same path for the width input and output: when an output card already
exists, MadGraph 3.5.16 can otherwise use its previous parameters in the numerical
integration. Copying the inputs first avoids that mismatch.
Read the [decay physics notes](physics.md#four-lepton-decay-exercise) for the
approximation and normalisation checks. Never dismiss a branching fraction
larger than one: it signals a problem with the configuration.

At the first launch screen, set `shower=OFF`, `madspin=OFF` and `reweight=OFF`,
then enter `done`. We will run MadSpin separately below. At the card-editing
screen, keep the newly calculated parameter card. Edit the run card using the
settings in the main README, with **100 events and seed `23456`**. Keep the
13 TeV beams, built-in `nn23lo1` PDF, HT/2 scales, `ptheavy = 0`,
`event_norm = sum`, and matching/systematics off. These settings are also written
in `cards/run_gg_h_eta0_2e2mu.mg5`. Enter `done` to generate the events, then
`quit` to return to the terminal.

**Terminal, from `NewScalarsTutorial`:**

```bash
python Work/MG5_aMC_v3_5_16/MadSpin/madspin
```

**MadSpin:**

```text
set spinmode none
set seed 34567
set curr_dir Work/gg_h_eta0_2e2mu
import Work/gg_h_eta0_2e2mu/Events/four_lepton_pilot/unweighted_events.lhe.gz
decay eta0 > z z, z > e+ e-, z > mu+ mu-
launch
```

There is one complete decay-chain command and **no Higgs decay command**.
`spinmode none` supports loop-induced production. It generates the scalar decay
separately and combines it with each production event, leaving the parent mass
fixed. The complete decay chain is evaluated together, so correlations among
the leptons within the decay are included; the mode does not correlate production
and decay spin states. The parent here has spin zero.

MadSpin reports the output filename and branching factor. After it finishes,
enter `quit` if its prompt is still open. The standalone output is
`Work/gg_h_eta0_2e2mu/Events/four_lepton_pilot/unweighted_events_decayed.lhe.gz`.
Analyse that file with a new output label, keeping its banner and both sets of
cards. The new file's cross section includes the decay probability.

For instructors, these commands reproduce the workflow from the tutorial
root, provided the new process directory does not already exist:

```bash
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/generate_gg_h_eta0_2e2mu.mg5
cp cards/param_card_gg_h_eta0_2e2mu.dat Work/gg_h_eta0_2e2mu/Cards/param_card.dat
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/widths_gg_h_eta0_2e2mu.mg5
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/run_gg_h_eta0_2e2mu.mg5
python Work/MG5_aMC_v3_5_16/MadSpin/madspin cards/madspin_gg_h_eta0_2e2mu.dat
```

Check the recorded [validation results](validation.md) and
[sample provenance](../examples/README.md) before comparing numbers.
