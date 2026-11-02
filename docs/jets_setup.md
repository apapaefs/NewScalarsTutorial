# Instructor setup: Herwig and HwSim

The [student jet lesson](jets.md) assumes the software is already installed.
Its four exercises use pre-generated hard events, so compilation is not part
of the two-hour session.

## Tested software and plugin

The local end-to-end setup uses Herwig **7.3.0**, ThePEG **2.3.0**, FastJet
**3.5.1**, ROOT **6.40.04**, and Uproot **5.7.7**. The HwSim source is
[apapaefs/hwsim](https://gitlab.com/apapaefs/hwsim), commit
`51ba33aea55ddbee0df8309d425b6fbdde1ceee3`. Its reconstructed-object example,
`Contrib/hwsim/Analysis/HwSimPostAnalysis_reconstructed.cc`, shows how to read
`theJets`, `thebJets`, `numJets` and `numbJets`. Our Python analyser follows
that storage layout and uses the shared tutorial mass/plotting helpers.

Install Herwig using its [official installation instructions](https://herwig.hepforge.org/downloads.html)
with ROOT, FastJet and LHAPDF available. The **CT14lo** PDF set is needed for
this setup. With the Herwig environment active, check:

```bash
Herwig --version
fastjet-config --version
root-config --version
lhapdf list --installed
```

If necessary, an instructor with installation write access can install the PDF:

```bash
lhapdf install CT14lo
```

HwSim is a Herwig analysis plugin, loaded as `HwSim.so`. Following its README,
clone it into `Contrib` in the **configured Herwig source tree**, generate its
makefile there, and compile/install it with the same C++ compiler and ABI as
Herwig and FastJet. For a new installation, with `HERWIG_SRC` set to that tree:

```bash
cd "$HERWIG_SRC/Contrib"
git clone https://gitlab.com/apapaefs/hwsim.git hwsim
cd hwsim
git checkout 51ba33aea55ddbee0df8309d425b6fbdde1ceee3
cd ..
make
cd hwsim
make
make install
```

Do not clone over an existing working plugin checkout. On macOS, use the
installation's matching compiler; a ROOT `-stdlib=` option may need filtering
when building with GCC. The tested local installation already has this
makefile adjustment. Building a fresh installation on other platforms has
not been part of the tutorial validation.

`Herwig read` of a prepared tutorial input is the practical plugin check:
it must accept `BTaggingMethod GhostBHadrons`, `SaveReconstructed Yes` and
`SavePseudoJets No`. The ROOT tree must have `bHadronMultiplicity`. An older
plugin may lack these interfaces/branches; update it instead of changing to
the old stable-B-hadron tagging recipe.

## Shower and object definitions

`herwig/LHE-HwSim.in` uses the Herwig 7.3 default angular-ordered shower,
cluster hadronization, hadron decays and underlying-event model. MPI is on.
The shower uses the LHE `SCALUP` as a transverse-momentum veto scale, with
phase-space restriction enabled. There is no additional matrix-element jet
sample, matching or merging. Extra jets are described by the shower/MPI;
the high-pT tail does not acquire fixed-order multi-jet accuracy.

The hard events keep MadGraph's `nn23lo1` PDF and HT/2 scale. Herwig's hard
reader, shower, MPI and remnant PDF objects use the default **CT14lo** set.
`InitPDFs No` and `ReweightPDF No` avoid changing the supplied hard-event weights.
The shower couplings and nonperturbative parameters remain those of the Herwig
7.3 default tune; this is an educational LO-plus-shower setup, not a new tune
or a systematically matched prediction with identical hard/shower PDFs.

The scalar and Z decays are already in the LHE file. Herwig registers eta0 as
a neutral colour-singlet scalar; no extra decay is generated for it. Shower
spin correlations are off for the external BSM process. MadSpin's original
decay-chain kinematics/correlations are the starting point. The original
fixed scalar masses do not imply a sharp reconstructed jet-pair mass.

HwSim clusters visible particles with pT > 0 and |eta| < 6, excluding neutrinos
and isolated electrons/muons above 10 GeV. Isolation uses charged-particle pT
in a radius-0.2 cone, requiring the sum divided by lepton pT to be below 0.1.
Photons stay in the jet inputs; non-isolated decay leptons can contribute.
There is no lepton event selection in this lesson: both input samples already
describe the four-lepton process. The intended focus is jet reconstruction.

Jets use anti-kT, E-scheme recombination, R = 0.4 and a 10 GeV storage threshold.
The Python analysis applies pT >= 25 GeV and |eta| < 2.5 explicitly to both
stored collections; it does not depend on HwSim's `EtaCutJets` setting. A b-jet
is identified through a ghost of the last b hadron in a decay chain. Ordinary
hadron decays remain enabled. This label includes secondary b production and
does not identify the Higgs ancestor. Exactly two accepted b-jets are required
for the mass, while jet multiplicities are filled before this requirement.

The analysis uses particle momenta with no smearing, tagging efficiencies,
mistags or pileup. Do not interpret these plots as detector predictions.

## Weights and finite files

The preparation helper checks that the input has the correct six outgoing
particles and positive, equal event weights, as all supplied files do. It
records the LHE checksum, rate, seed and event count, and refuses to reuse an
existing run name or request more events than the input contains.
`AllowedToReOpen No` prevents silent input recycling.

HwSim's `evweight` supplies relative event weights. The analyser checks the ROOT
entry count against the request and Herwig's final `.out` statistics, then
normalises with **Herwig's final hard-process cross section** (converting nb to
pb), divided by the sum of all ROOT event weights. This allows Herwig's reported
generation efficiency to affect the rate. The LHE rate is also saved for a
cross-check; its decay factors are never applied again. Incomplete runs are
rejected. If the end of the LHE file is reached after shower failures, request
fewer events with a new run name and inspect the log; do not enable recycling.

The multiplicity histogram integrals, including flow bins, reproduce the full
analysed rate. The mass integral reproduces the exactly-two-b-jet rate. An empty
pair selection produces a zero mass histogram and a readable cutflow.
`--normalization shape` on the analyser divides by all input weight, so its mass
integral is the pair efficiency. The separate comparison program instead
normalises each plotted distribution to unit area, including flow bins.
Both conventions and the chosen cuts are recorded in the JSON output.

`jetanalyzer/compare_mbb_levels.py` compares the original outgoing LHE b/bbar
with exactly two accepted truth b-jets. The same pT and pseudorapidity cuts are
applied at each level, without another lepton cut. Both curves use 10 GeV bins
centred on 125 GeV, avoiding a bin edge at the fixed parton-level Higgs mass.
The default shapes each have unit area including flow bins; the rate option
uses the LHE rate divided by all LHE weight for the partons, and the final
Herwig rate divided by all ROOT weight for the jets. The selection table gives
each efficiency relative to its own inclusive sample.

The comparison checks the source LHE checksum against the Herwig run record.
It uses the entire LHE file and the completed ROOT run, which can have different
event counts. It does not match individual events, require them to pass both
selections, or measure a mass response for matched objects. Its error bars are
sqrt(sum(w^2)) with fixed normalisation divisors, without covariance between
the levels. An empty selection gives a zero curve. The broader jet mass includes
the combined effects of showering, hadronization, decays, MPI and reconstruction;
it does not isolate a hadronization correction or detector mass resolution.

The background remains the earlier massive-b tree-level QCD bbZZ component:
no incoming b partons, photon/nonresonant four-lepton diagrams, pure electroweak
component or other backgrounds. Its five-flavour hard PDF with massive final
b quarks is the same teaching approximation as the previous lesson.

The [sample manifest](../samples/manifest.json) contains the hard-generation
provenance. See [validation](validation.md#herwig-and-hwsim-jet-lesson) for the
checks actually run on the complete chain.
