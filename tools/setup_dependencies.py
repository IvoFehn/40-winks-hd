"""Fetch the published library commits and apply the matching release patches."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def git(folder, *args):
    subprocess.run(["git", "-C", str(folder), *args], check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("native", "web"))
    parser.add_argument("--verify-local", type=Path, help="Check patches against an existing configured source tree")
    args = parser.parse_args()
    project = ROOT / args.platform
    entries = json.loads((project / "dependencies.json").read_text())
    for item in entries:
        path = item["path"]
        if path == "lib/vcpkg" and (args.platform == "web" or os.environ.get("VCPKG_ROOT")):
            continue
        folder = (args.verify_local or project) / path
        if args.verify_local:
            if not (folder / ".git").exists():
                if "patch" in item or item.get("extras"):
                    raise RuntimeError(f"Missing changed library {path}")
                continue
            if "patch" in item:
                git(folder, "apply", "--check", "--reverse", str(project / item["patch"]))
            for extra in item.get("extras", []):
                expected = project / "dependency-extras" / path / extra
                if (folder / extra).read_bytes() != expected.read_bytes():
                    raise RuntimeError(f"Source differs: {path}/{extra}")
            continue
        marker = folder / ".winks-release-dependency"
        signature = json.dumps(item, sort_keys=True)
        if marker.is_file() and marker.read_text() == signature:
            continue
        if folder.exists() and any(folder.iterdir()):
            raise RuntimeError(f"Existing library requires review: {folder}")
        folder.mkdir(parents=True, exist_ok=True)
        git(folder, "init", "-q")
        git(folder, "remote", "add", "origin", item["url"])
        git(folder, "fetch", "--depth", "1", "origin", item["commit"])
        git(folder, "-c", "core.autocrlf=false", "checkout", "--detach", "FETCH_HEAD")
        if "patch" in item:
            git(folder, "apply", str(project / item["patch"]))
        for extra in item.get("extras", []):
            out = folder / extra
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project / "dependency-extras" / path / extra, out)
        marker.write_text(signature)
        print(path, item["commit"])
    print(args.platform, "dependencies verified" if args.verify_local else "dependencies ready")

if __name__ == "__main__":
    main()
