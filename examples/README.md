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
