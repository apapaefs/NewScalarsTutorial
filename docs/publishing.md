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
git add README.md .gitignore requirements.txt Model cards docs examples lheanalyzer scripts tests
git diff --cached --stat
git diff --cached --check
git commit -m "Update the scalar-production tutorial"
```

`Work/`, `results/`, virtual environments and generated event files are ignored.
The small LHE file under `tests/fixtures/` is synthetic test data. The 100-event
file under `examples/` is a real tutorial pilot. These two small samples are
intended to be tracked. The old MadGraph installation archive is not part of
this repo.

With write access to this repository, push the reviewed commit from `main`:

```bash
git push origin main
```

Use your own fork and a pull request if you do not have write access. The
inherited sources and their licence status are recorded in
[provenance](provenance.md).
