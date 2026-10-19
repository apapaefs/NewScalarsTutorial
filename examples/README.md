# A small sample for the first analysis

`gg_h_eta0_pilot.lhe.gz` contains 100 undecayed `g g > h eta0 [noborn=QCD]`
events generated with MadGraph 3.5.16 on 5 October 2026, using the supplied
generation and pilot-run cards. Its compressed size is about 14 kB.

The proton collision energy is 13 TeV, the scalar masses are 125 and 400 GeV,
the PDF is built-in `nn23lo1`, the scales are HT/2, and the seed is `12345`.
The mixing and cubic couplings are the illustrative choices in
[the physics notes](../docs/physics.md). No decay, shower or detector simulation
is included. The full run and parameter cards are embedded in the LHE header.

From the repository root:

```bash
python lheanalyzer/lhe_analyzer.py examples/gg_h_eta0_pilot.lhe.gz example
```

The recorded inclusive cross section is `2.980640e-4 pb`, with integration
uncertainty `1.347514e-6 pb`. This is a software smoke-test result for the
specified teaching inputs, not an independently validated phenomenological
benchmark. A 100-event sample gives only coarse differential distributions.
See the [validation record](../docs/validation.md) for the checks performed.

SHA-256 of the compressed file:

```text
42ae85113e111669c20d8a2226ba37f47ba97a7cee64f0e270ac08e425f88d0c
```

This file is deliberately tracked as a small classroom example. Store new,
larger generated samples under the ignored `Work/` directory.

## Four leptons with a stable associated Higgs

`gg_h_eta0_2e2mu_pilot.lhe.gz` contains 100 real MadGraph/MadSpin events generated
on 19 October 2026 for `g g > h eta0 [noborn=QCD]`, followed by
`eta0 > z z, z > e+ e-, z > mu+ mu-`. The Higgs remains a status-1 outgoing
particle with mass 125 GeV. There is no shower or detector simulation.
The [guided exercise](../docs/four_lepton.md) starts with:

```bash
python lheanalyzer/lhe_four_lepton.py examples/gg_h_eta0_2e2mu_pilot.lhe.gz four_lepton_start
```

The masses, mixing, cubic couplings, 13 TeV beams, PDF and scales match the
production lesson. The separate production run uses seed `23456` and nonzero
eta0/Z widths, calculated from all open tree-level two-body modes in the model.
The Higgs and top widths are zero. MadSpin uses `spinmode none` and input seed
`34567`; its internal decay-generation seed is `750713659`, derived from that
seed. The complete decay chain is specified together, with only the parent
scalar constrained to its original on-shell mass.

| Quantity | Recorded value |
| --- | --- |
| Production cross section | `2.956610e-4 pb` |
| Production integration uncertainty | `1.454767e-6 pb` |
| eta0 total width in this approximation | `1.864508 GeV` |
| Z total width in this approximation | `2.441756 GeV` |
| Full-chain partial width | `(6.9886e-4 +/- 1.1999e-5) GeV` |
| MadSpin branching factor | `3.7482275e-4` |
| Decayed LHE cross section | `1.1082047e-7 pb` |
| Decayed LHE reported uncertainty | `5.4527976e-10 pb` |
| Events with all four lepton pT values at least 10 GeV | `95 / 100` |

The reported decayed-file uncertainty is the production integration uncertainty
scaled by the branching factor. It does not include the separate decay-integration
uncertainty listed above. The cross section already contains the branching
factor; the analyser must not apply it again.

The two-on-shell-Z estimate, including the factor of two for the electron/muon
assignments, is `3.9098550e-4`. The full-chain integration is about 4.1% lower,
with finite Z widths and the `bwcutoff = 15` resonance windows. Its numerical
integration also has a 1.7% uncertainty. The internal decay run applies no lepton
momentum, angular-separation or pair-mass cuts beyond those resonance windows.

The generated file contains the production cards and MadSpin commands in its
header. `gg_h_eta0_2e2mu_decay_run_card.dat` records the internal decay run card;
`gg_h_eta0_2e2mu_pilot.json` records the seeds, rates, checks and software versions.
The reproducible input cards are in `cards/`, and the detailed checks are in
[the validation record](../docs/validation.md#four-lepton-exercise-validation).
These numbers validate the teaching workflow, not a precision phenomenological
prediction. This 100-event sample is suitable for the reconstruction lesson.

The compressed file is 37,066 bytes. Its SHA-256 is:

```text
df5174e87f0f0485461d98d739f994e0eb88ab5d40a196fcc6ca1692881002c9
```
