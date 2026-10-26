# Physics and numerical inputs

## The process

We consider the gluon-fusion contribution to `p p -> h eta0` at 13 TeV. In the
MadGraph process card the incoming partons are `g g`; the run card specifies
proton beams (`lpp1 = lpp2 = 1`), so the result includes the gluon PDFs in the
protons. It is not a fixed-energy scattering calculation with external gluon
beams, nor does it include all other possible partonic production channels.

```text
import model loop_sm_scalar
generate g g > h eta0 [noborn=QCD]
```

`[noborn=QCD]` explicitly requests the loop-induced calculation without a Born
tree amplitude. Squaring the one-loop amplitude gives the leading contribution
for this channel. A loop in the leading diagrams does not make this an NLO
calculation. Plain `[QCD]` is the general NLO syntax and should not be presented
as synonymous with loop-induced production. The explicit `noborn` form was
already available in earlier versions; here we use it consistently for 3.5.16.

The supplied default restriction card leaves the BSM couplings nonzero when
importing the model, so the generator retains both quark-box contributions and
scalar-mediated triangle contributions.
The model's nonzero quark masses and Yukawa couplings determine the active loops.
No heavy-top effective interaction is substituted for the full loop amplitude.

The model calls the particles `h` (PDG `25`) and `eta0` (PDG `99925`). We select
their **outgoing status-1 records**. This definition changes if the particles
are decayed or a shower is added; those samples are outside the original analyser.
The separate [four-lepton exercise](four_lepton.md) selects the stable Higgs and
the four outgoing charged leptons after the new scalar decays.

## A starting point for the exercise

The following is an **illustrative parameter choice for teaching**, not a fit,
an experimentally allowed benchmark, or a complete scalar-potential construction.
Students enter it by editing the cards as described in the README. The optional
instructor script `cards/run_gg_h_eta0.mg5` records the same settings.

| Input | Choice |
| --- | --- |
| Generator | MadGraph5_aMC@NLO 3.5.16 |
| Proton energies | 6500 GeV and 6500 GeV |
| Higgs mass | 125 GeV (`MASS 25`) |
| New scalar mass | 400 GeV (`MASS 99925`, model name `Meta`) |
| `ctheta`, `stheta` | `0.9797958971132712`, `0.2` (`BSM 13`, `14`) |
| `kap112`, `kap122` | 100 GeV each (`BSM 16`, `17`) |
| Remaining `kap` parameters | Zero (`BSM 15`, `18`–`23`) |
| Top, Higgs and new scalar widths | Zero for this on-shell, undecayed exercise |
| PDF | Built-in `nn23lo1`: NNPDF23 LO, alpha_s(MZ) = 0.130, QED member 0 |
| Scales | `dynamical_scale_choice = 3`: mu_R = mu_F = HT/2 |
| Scale factor | 1 |
| Matching/merging | Off (`ickkw = 0`) |
| Heavy-particle generation pT cut | 0 GeV (`ptheavy = 0`) |
| Shower, MadSpin, reweighting | Off |
| Automatic systematics | Off for the pilot |
| Event-weight convention | `event_norm = sum` |
| Pilot size and seed | 100 events, `12345` |

For these two outgoing particles, HT is the sum of their transverse masses,
so the scale is `(sqrt(m_h² + pT_h²) + sqrt(m_eta0² + pT_eta0²))/2`.
The built-in PDF keeps the exercise independent of an LHAPDF installation.
MadGraph sets the strong coupling consistently with that PDF; read the final
run banner instead of treating the UFO's initial `aS` value as the run value.
Other Standard Model parameters and inactive generation cuts retain the values
recorded in the generated cards. Save these cards to specify a run completely.

In this UFO, `ctheta` and `stheta` are independent external inputs. The chosen
values obey `ctheta² + stheta² = 1`. Update both when treating them as a mixing
angle. The quark Yukawa couplings to `h` and `eta0` carry `ctheta` and `stheta`,
respectively. Setting `ctheta = 0`, as in the old single-scalar exercise, removes
the corresponding Higgs Yukawa coupling and changes associated production.

The cubic parameters are dimensionful, and are not kappa modifiers normalised to
a Standard Model coupling. The supplied UFO defines the vertex factors
`h h eta0: -2 i kap112` and `h eta0 eta0: -2 i kap122`. Inspect `couplings.py`
and `vertices.py` after installing the model. In particular, box–triangle
interference means that rates do not generally scale as one squared parameter.

Import the model with its supplied restriction card, then change the run's
parameter card. Setting a coupling to zero at model-import time can remove
vertices permanently from generated code and spoil a later scan that turns it on.
The supplied restriction card leaves these BSM vertices available.

The zero scalar widths describe stable external scalars in this exercise.
Before studying physical decays, specify consistent total widths and branching
fractions and revisit the event selection. A branching fraction larger than one
is a configuration problem to investigate, not a warning to ignore.

## Observables and normalisation

For a four-vector `(E, px, py, pz)`, use

```text
pT = sqrt(px² + py²)
y  = (1/2) log((E + pz)/(E - pz))
m(h eta0)² = (E_h + E_eta0)² - |p_h + p_eta0|²
```

Rapidity `y` and pseudorapidity are different for massive particles. The
analyser uses rapidity. At this two-body, parton-level order, transverse momentum
conservation gives `pT_h = pT_eta0` and zero pair transverse momentum. For nonzero
transverse momenta, the azimuthal separation is pi. The pair invariant mass must
be at least `m_h + m_eta0` (525 GeV for the starting point), up to rounding.

Let `w_i` be the nominal event weights of the complete input file, `S = sum_i w_i`
and `sigma` the subprocess cross section from `<init>`, in pb. For a bin of width
`Delta x`, containing selected events `B`, the analyser reports

```text
dσ/dx ≈ (sigma / S) (sum_{i in B} w_i) / Delta x
bin error ≈ |sigma / S| sqrt(sum_{i in B} w_i²) / Delta x
```

For shape plots, replace `sigma` by 1. A cut keeps `S` unchanged: integrating
the selected distribution gives `sigma * sum_selected(w_i)/S`, rather than
restoring it to the inclusive cross section. This also accommodates MadGraph's
`sum` and `average` event-weight conventions, which differ by a common factor.
Flow bins are recorded in `summary.json`; add their integrals when checking
normalisation. The final upper bin edge is included, including `Delta phi = pi`.

The displayed bin errors assume a fixed overall normalisation and use squared
weights. They do not include the integration uncertainty on `sigma`, uncertainty
in the normalisation itself, scale/PDF variations or correlations. Variation
weights are read but are not used in the plots. The reader accepts a single
subprocess with IDWTUP `3`, `-3`, `4` or `-4` and a positive inclusive weight sum.
It rejects other normalisation strategies and multiple-subprocess files rather
than applying this formula to an ambiguous mixture.

Use a complete run file. Editing/truncating it or concatenating independent
runs changes the weight normalisation and cannot be repaired by its old header.

## Four-lepton decay exercise

The continuation studies `g g > h eta0`, followed by
`eta0 > z z, z > e+ e-, z > mu+ mu-`, with the associated Higgs stable.
Production uses the same masses, couplings, beams, PDF and scales as above,
but the new sample has nonzero, consistently calculated eta0 and Z widths.
The original undecayed pilot and its banner are unchanged.

The supplied parameter card uses approximate total widths calculated from all
kinematically open tree-level two-body channels in the installed UFO:

| Particle | Total width [GeV] | Channels included |
| --- | --- | --- |
| `eta0` | 1.864508 | `h h`, `w+ w-`, `z z`, `t t~`, `b b~`, `ta+ ta-` |
| `z` | 2.441756 | Five quark pairs, three charged-lepton pairs, three neutrino pairs |

The light-fermion Yukawa couplings set to zero by the model restriction do not
produce additional scalar modes. These totals exclude loop-induced decay modes,
off-shell multibody contributions and higher-order corrections. They are teaching
approximations, not precision physical widths. The top and Higgs widths remain
zero; calculating eta0's partial width into stable Higgs bosons does not cause
the associated Higgs in our chosen event sample to decay.

The instructor width card calls `compute_widths 99925 23 --body_decay=2`.
Copy the supplied teaching parameter card into the new process first and use
that same path for both input and output. In MadGraph 3.5.16 the numerical
integration can otherwise use an existing output card instead of the specified
input card. The generated partial widths were cross-checked against the analytic
tree-level formulas for eta0 to two Higgs bosons and to two Z bosons; see the
[validation record](validation.md).

MadSpin `spinmode none` generates the complete scalar decay chain separately
and combines it with each production event. It supports loop-induced production
and fixes the primary scalar mass at 400 GeV. No correlation between production
and decay spin states is imposed; the parent is a scalar. Specifying the full
chain in one command evaluates the decay matrix element with both Z decays,
including the correlations within that chain. The internal Z propagators have
finite widths. This is not the complete off-shell production-and-decay amplitude.
See the [MadSpin manual](https://cp3.irmp.ucl.ac.be/projects/madgraph/wiki/MadSpin).

For two on-shell Z bosons, the mixed-flavour branching probability is

```text
B(eta0 -> ZZ -> e+ e- mu+ mu-) = B(eta0 -> ZZ) * 2 * B(Z -> ee) * B(Z -> mumu).
```

The factor of two accounts for the two assignments of the electron and muon
pairs to the identical Z bosons. MadSpin's full-chain partial width includes
this combinatorial factor already. Its numerical result can differ from the
factorised expression through finite Z widths, the resonance mass window and
integration uncertainty. The formula is a cross-check, not an extra multiplier.

The decayed LHE `<init>` cross section and nominal weights have already been
scaled by MadSpin's branching factor. The new analyser uses that cross section
directly. Its shape normalisation uses the entire decayed sample as the reference:
after the lepton cut, the area is the efficiency within this decay channel.
Bin errors use squared weights as in the production lesson. They do not include
the decay-integration uncertainty, theory variations or detector effects.

The new selection requires exactly one outgoing Higgs and one each of PDGs
`11`, `-11`, `13`, `-13`. Intermediate status-2 records are excluded from the
reconstruction. The momentum check compares the incoming gluons with the five
outgoing particles before the lepton cut. There is no shower, lepton isolation,
detector simulation, background estimate or Higgs decay in this exercise.

## Higgs-decay continuation and background

The [next lesson](higgs_bb.md) adds `h -> b b~` to the signal and reconstructs
both scalar candidates from the six outgoing particles. It uses a separate
100-event production sample with a nonzero Higgs width and decays both scalars
in one MadSpin pass. The Higgs and eta0 masses remain fixed, so the sharp
reconstructed peaks do not describe detector mass resolution.

The approximate Higgs width is `0.005433204 GeV`, calculated from the open
two-body modes available in the supplied UFO: bottom and tau pairs, plus the
effective photon-pair vertex. It excludes off-shell vector-boson modes, the
gluon channel and higher-order corrections. The fixed 4.7 GeV bottom Yukawa
input and the missing channels give `B(h -> bb) = 0.952495`; this is not a
precision Standard Model branching fraction. The
[generation notes](higgs_bb_generation.md) describe the calculation and its inputs.

The optional background is the tree-level QCD contribution to `pp -> bbZZ`
with the two Z decay chains specified explicitly. It includes incoming gluons
and u/d/s/c quarks and antiquarks, with massive outgoing bottom quarks. It uses
the same 13 TeV beams, built-in PDF and HT/2 scale convention as the signal.
It is one background component, not the full `bb4l` prediction; the signal and
background are generated independently and their interference is omitted.

Both samples are analysed using exactly one status-1 bottom quark, one bottom
antiquark and the four specified leptons. Intermediate-particle truth records
are not needed for candidate reconstruction or selection. The bottom quarks
are not clustered jets, and no flavour-tagging efficiency is assumed. Rate
plots use each decayed LHE cross section directly. The comparison program's
shape mode divides by the selected cross section, giving unit area including
flow bins. Its plotted errors scale the squared-weight errors by that same
fixed denominator; they do not include normalisation correlations.

## Scope

This project studies generator-level kinematics. It provides neither an NLO
prediction nor an experimental sensitivity estimate. The pilot has deliberately
small statistics and no theory uncertainty evaluation. A phenomenological study
would require validated model inputs, scale/PDF variations, decay and shower
modelling as appropriate, and a specified background and detector treatment.

References: [MadGraph 3.5.16 source](https://github.com/mg5amcnlo/mg5amcnlo/tree/v3.5.16),
[automated loop-induced event generation](https://arxiv.org/abs/1507.00020),
[Les Houches event-file format](https://arxiv.org/abs/hep-ph/0609017).
