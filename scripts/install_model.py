#!/usr/bin/env python3
"""Install the supplied UFO source, excluding old Python/MadGraph caches."""

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile

MODEL_SHA256 = "f0531ad6e701d35cc55ba6c6799a07f1b99eb29f7bc8a029c663d4d8b144441f"
ROOT = Path(__file__).resolve().parents[1]


def install(mg5):
    mg5 = mg5.resolve()
    version_file = mg5 / "VERSION"
    if not version_file.is_file() or not re.search(
        r"^version\s*=\s*3\.5\.16\s*$", version_file.read_text(), re.MULTILINE
    ):
        raise ValueError("The target must be a MadGraph 3.5.16 installation.")
    archive = ROOT / "Model/loop_sm_scalar_180521_withaa_py3.tar.gz"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != MODEL_SHA256:
        raise ValueError("The supplied model archive has changed; check its provenance.")

    sources = {}
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            path = PurePosixPath(member.name)
            if (member.isfile() and len(path.parts) == 2
                    and path.parts[0] == "loop_sm_scalar"
                    and not path.name.startswith(".")
                    and path.suffix in {".py", ".dat"}):
                sources[path.name] = tar.extractfile(member).read()
    if not {"particles.py", "parameters.py", "restrict_default.dat"} <= sources.keys():
        raise ValueError("The model archive is incomplete.")

    target = mg5 / "models/loop_sm_scalar"
    if target.exists():
        if all((target / name).is_file() and (target / name).read_bytes() == data
               for name, data in sources.items()):
            print(f"Model source already installed: {target}")
            return
        raise ValueError(f"Refusing to overwrite a different model at {target}")
    with tempfile.TemporaryDirectory(dir=mg5 / "models") as temporary:
        staging = Path(temporary) / "loop_sm_scalar"
        staging.mkdir()
        for name, data in sources.items():
            (staging / name).write_bytes(data)
        shutil.move(str(staging), target)
    print(f"Installed {len(sources)} source/card files in {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mg5_dir", type=Path)
    args = parser.parse_args()
    try:
        install(args.mg5_dir)
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.exit(1, f"Model installation failed: {error}\n")
