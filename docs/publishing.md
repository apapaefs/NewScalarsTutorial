# Maintaining the GitHub repository

The tutorial repository is
[apapaefs/NewScalarsTutorial](https://github.com/apapaefs/NewScalarsTutorial).
A clone already has its `origin` remote configured. Before publishing changes,
check that you are inside this repository and that `origin` points to it:

```bash
git rev-parse --show-toplevel
git remote -v
```

From the tutorial repository root, review and commit the source:

```bash
git status --short
git lfs install --local
git add README.md .gitignore .gitattributes requirements*.txt Model cards docs examples samples herwig lheanalyzer jetanalyzer scripts tests
git lfs ls-files
git diff --cached --stat
git diff --cached --check
git commit -m "Update the scalar-production tutorial"
```

`Work/`, `results/` and virtual environments are ignored. Synthetic LHE fixtures
and the small real pilots in `examples/` are ordinary Git files. The four larger
classroom LHE files under `samples/` use **Git LFS**; their checksums and provenance
are in `samples/manifest.json`. Run `python scripts/verify_samples.py` before
publishing them. The LFS pre-push hook uploads the data when the commit is pushed.
Validate a fresh clone with `git lfs pull` and the verifier before announcing
an update. See the [sample instructions](../samples/README.md) for details.
Generated shower ROOT files and the MadGraph installation are not published.

With write access to this repository, push the reviewed commit from `main`:

```bash
git push origin main
```

Use your own fork and a pull request if you do not have write access. The
inherited sources and their licence status are recorded in
[provenance](provenance.md).
