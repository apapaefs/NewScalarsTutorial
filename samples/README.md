# Larger classroom event samples

These independent MadGraph 3.5.16 samples contain **100 times as many events**
as each corresponding pilot in `examples/`. The 13 TeV benchmark, masses,
couplings, hard PDFs, scales, cuts and decay-width approximations are unchanged.
The files are unshowered LHE inputs. Students run Herwig themselves in
[the jet lesson](../docs/jets.md).

| Sample | Events | Compressed size | Cross section [pb] |
| --- | ---: | ---: | ---: |
| `gg_h_eta0_10000.lhe.gz` | 10,000 | 0.92 MB | 2.962420e-4 |
| `gg_h_eta0_2e2mu_10000.lhe.gz` | 10,000 | 3.05 MB | 1.1155781e-7 |
| `gg_h_eta0_bb2e2mu_10000.lhe.gz` | 10,000 | 3.74 MB | 1.0628676e-7 |
| `pp_bbzz_2e2mu_50000.lhe.gz` | 50,000 | 15.96 MB | 4.369310e-4 |

The cross sections are Monte Carlo estimates and differ slightly from the
independent pilots. The decayed rates already include the requested branching
factors. Do not multiply by them again. The Higgs branching fraction follows
the [two-body model approximation](../docs/higgs_bb_generation.md#higgs-width-used-here),
not a precision Standard Model prediction.

## Download and verify

Install [Git LFS](https://git-lfs.com/), then, from the tutorial repository:

```bash
git lfs install --local
git lfs pull
python scripts/verify_samples.py
```

A successful check reports 80,000 events across four files. Without Git LFS,
a clone or source ZIP may contain tiny text pointers instead of event data.
Use a Git clone and `git lfs pull`; do not rename a pointer or pass it to Herwig.
Only `samples/*.lhe.gz` uses LFS. The old pilots remain ordinary Git files.

The [manifest](manifest.json) records the SHA-256 checksums, seeds, event counts,
cross sections and errors, widths, decay factors, effective cards and numerical
validation. It also records unique final-state momenta: these are newly generated
events, not repeated copies of the pilots. The collection script checks the
mixed electron/muon branching probability including the two assignments to the Zs.

## Reproduce with MadGraph (instructor)

Use the installation/model instructions in the main README and the process
generation cards in `cards/`. For the decayed signal processes, copy the matching
frozen `cards/param_card_*.dat` into each process's `Cards/param_card.dat`, as in
the earlier generation guides. No pilot run is required. Then run:

```bash
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/large_samples/run_gg_h_eta0.mg5
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/large_samples/run_gg_h_eta0_2e2mu.mg5
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/large_samples/run_gg_h_eta0_bb2e2mu.mg5
python Work/MG5_aMC_v3_5_16/bin/mg5_aMC cards/large_samples/run_pp_bbzz_2e2mu.mg5
python Work/MG5_aMC_v3_5_16/MadSpin/madspin cards/large_samples/madspin_gg_h_eta0_2e2mu.dat
python Work/MG5_aMC_v3_5_16/MadSpin/madspin cards/large_samples/madspin_higgs_bb.dat
python scripts/collect_student_samples.py
python scripts/verify_samples.py
```

The three loop-induced runs explicitly use two cores. MadGraph 3.5.16's
single-core survey/refinement combination failed here when refinement needed
an `ftn25` grid; the two-core path completed without changes to MadGraph source.
The two scalar decays are specified in **one** MadSpin pass with `spinmode none`.
The background includes its Z decays in the matrix element.

The collection script refuses to replace an existing sample with different
contents. For a new campaign, use a separate checkout or a deliberately new
sample version. Seeds and physics cards specify reproducible runs; exact
compressed-file bytes can differ with software/build/platform details.

## Updating the student download

Run the sample verifier and the Python tests before committing. Install Git LFS
locally and stage `.gitattributes`, the manifest, the effective cards and the
four `.lhe.gz` files. `git lfs ls-files` must show all four payloads. Push the
commit normally: Git LFS uploads its objects through the pre-push hook. Check
a fresh clone with `git lfs pull` and the verifier before announcing the update.
Do not migrate old Git history or add generated shower ROOT files to LFS.
