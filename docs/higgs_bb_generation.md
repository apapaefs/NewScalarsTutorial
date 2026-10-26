# Optional: generating the Higgs-decay and background samples

The [student lesson](higgs_bb.md) uses two supplied files. This page is for
students working with an instructor who want to reproduce them. Install the
model and MadGraph as described in the main README, activate the Python
environment, and start every terminal command in `NewScalarsTutorial`.

## Signal: decay both scalars in one pass

The production process and benchmark are unchanged: loop-induced
`g g > h eta0`, 13 TeV proton collisions, `m_h = 125 GeV`, `m_eta0 = 400 GeV`,
the same mixing and cubic couplings, built-in `nn23lo1` PDF and HT/2 scales.
The new production sample uses a nonzero Higgs width, needed for its decay.
It has its own process directory, production seed `67890` and 100 events.

MadSpin 3.5.16 refuses to import a file it has already decayed for another
pass. Start from an **undecayed production file** and specify both scalar decays
in a single MadSpin run. The old stable-Higgs four-lepton sample remains an
independent input for the earlier lesson.

### Higgs width used here

The frozen parameter card is `cards/param_card_gg_h_eta0_bb2e2mu.dat`.
Its non-decay parameters agree with the preceding benchmark. The Higgs width
was calculated with `compute_widths 25 --body_decay=2`, including all open
two-body channels supplied by this UFO:

| Channel | Partial width [GeV] | Branching fraction |
| --- | ---: | ---: |
| `h -> b b~` | 0.00517510 | 0.952495 |
| `h -> ta+ ta-` | 0.000248400 | 0.0457189 |
| `h -> a a` | 0.00000970420 | 0.00178609 |
| Total | 0.005433204 | 1, up to rounding |

The photon channel comes from the UFO's **effective** `h a a` vertex. This is
not an explicit loop decay calculation. The bottom mass and bottom Yukawa
input are both fixed at 4.7 GeV. The model restriction has zero charm Yukawa.
The table excludes off-shell `WW*` and `ZZ*`, the loop-induced gluon channel,
and higher-order corrections, including the running-bottom-mass treatment
used in precision Higgs predictions. Its large bottom branching fraction is
therefore a teaching approximation, not a precision Standard Model value.
Do not combine this tree-level partial width with an unrelated physical total
width: the resulting branching fraction can be inconsistent.

The eta0 and Z widths remain `1.864508 GeV` and `2.441756 GeV`, with the
approximations documented in the [four-lepton physics notes](physics.md#four-lepton-decay-exercise).
The top width remains zero. The event generator uses these widths to normalise
the chosen decay probabilities; the externally produced Higgs and eta0 still
have fixed masses in the `spinmode none` decay procedure.

### Reproduce the signal

Use a fresh process directory; the commands do not overwrite an existing one.
These are **terminal commands**, using the instructor cards:

```bash
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/generate_gg_h_eta0_bb2e2mu.mg5
cp cards/param_card_gg_h_eta0_bb2e2mu.dat Work/gg_h_eta0_bb2e2mu/Cards/param_card.dat
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/widths_higgs_bb.mg5
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/run_gg_h_eta0_bb2e2mu.mg5
python Work/MG5_aMC_v3_5_16/MadSpin/madspin cards/madspin_higgs_bb.dat
```

The width command recalculates the Higgs table using the same input/output
path. To reproduce the frozen benchmark without recalculating that table,
omit only the width command after copying the supplied parameter card.
The 100-event pilot distributed here used that frozen card.

For orientation, the generation card contains these **MadGraph commands**:

```text
import model loop_sm_scalar
generate g g > h eta0 [noborn=QCD]
output Work/gg_h_eta0_bb2e2mu
```

The decay card contains these **MadSpin commands**:

```text
set spinmode none
set seed 45678
import Work/gg_h_eta0_bb2e2mu/Events/bb_four_lepton_pilot/unweighted_events.lhe.gz
decay eta0 > z z, z > e+ e-, z > mu+ mu-
decay h > b b~
launch
```

The complete eta0 chain is evaluated together, including its internal decay
correlations. The Higgs is a scalar; its two-body decay has no preferred direction
in its rest frame. `spinmode none` keeps the parent masses fixed and does not
impose production–decay spin correlations. It supports loop-induced production;
see the [MadSpin manual](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/MadSpin).
Showering is off.

The final signal file is
`Work/gg_h_eta0_bb2e2mu/Events/bb_four_lepton_pilot/unweighted_events_decayed.lhe.gz`.
Its cross section includes **both** decay factors. In particular, the full eta0
chain includes the two possible electron/muon assignments to the Z bosons.
Do not apply either branching factor again in the analysis.

## Background: a tree-level QCD bbZZ component

We generate the Standard Model process using decay-chain syntax directly:

```text
import model sm
define p = g u c d s u~ c~ d~ s~
generate p p > b b~ z z QCD=2 QED=2, z > e+ e-, z > mu+ mu-
output Work/pp_bbzz_2e2mu
```

These are **MadGraph commands**, not terminal commands. `p` includes gluons
and u, d, s, c quarks and antiquarks; there is no incoming bottom quark.
The outgoing bottom mass and Yukawa input are 4.7 GeV. `QCD=2 QED=2` selects
the QCD contribution to the production of the bottom pair and two Z bosons;
with both leptonic decays its squared amplitude is of order
`alpha_s^2 alpha^4`. The Z decay chains include their correlations and the
mixed-flavour assignments. The [MadGraph syntax guide](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/InputEx)
explains coupling orders and decay chains.

This includes two resonant Z bosons with `bwcutoff = 15`. It excludes photon
and non-resonant four-lepton contributions outside those chains, the purely
electroweak contribution, loop corrections, other backgrounds and interference
with the new-scalar signal. It is not a complete background calculation for
an experimental search.

The beam energy, built-in `nn23lo1` PDF and HT/2 scale choice match the signal.
The Z width is set to the same approximate value, `2.441756 GeV`. We use massive
final-state bottom quarks and omit incoming bottom partons while keeping this
built-in five-flavour PDF for the teaching comparison. This should not be
presented as a precision calculation using a consistently matched four-flavour
PDF and coupling scheme.

No final-state momentum or angular generation cuts are applied; `cut_decays`
is false and the Z resonance windows remain in place. The nonzero bottom mass
regulates the bottom-pair collinear region. The students apply pT and mass cuts
later, in the common analyser. There is no shower, matching, merging, hadronisation,
jet clustering, flavour tagging or detector simulation.

Generate a fresh 500-event pilot with seed `56789`. **Terminal:**

```bash
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/generate_pp_bbzz_2e2mu.mg5
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/run_pp_bbzz_2e2mu.mg5
```

Its output is
`Work/pp_bbzz_2e2mu/Events/bbzz_pilot/unweighted_events.lhe.gz`.
No separate MadSpin step is needed. The LHE cross section already includes
both leptonic Z decays. Use the same completed analyser, cuts and plotting
bins for signal and background; use each sample's own cross section and total
input weight for normalisation.

The [sample notes](../examples/README.md) record the measured rates, seeds,
checksums and cutflows. The [validation notes](validation.md#higgs-decay-and-background-exercise)
list the checks actually completed. Keep new runs under new names; different
platforms and integration histories can change individual events.
