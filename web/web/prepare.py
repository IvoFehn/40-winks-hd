"""Prepare a ROM-free browser folder and version its downloadable assets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZIP_STORED, ZipFile

PROGRAM = "40WinksRecompiled"
RUNTIME = [f"{PROGRAM}.{ext}" for ext in ("html", "js", "wasm", "data")]

def build_mobile_pack(source: Path, destination: Path) -> None:
    # Keep the lighter replacement images at their original HD dimensions.
    # Entries outside this pack use the ROM artwork.
    with ZipFile(source) as hd, ZipFile(destination, "w", compression=ZIP_STORED) as mobile:
        mobile.writestr("rt64.json", hd.read("rt64.json"))
        for item in hd.infolist():
            if item.filename.endswith(".png") and item.file_size <= 48 * 1024:
                mobile.writestr(item.filename, hd.read(item))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packs", type=Path, help="Folder with Winks-HD.rtz and Winks-UHD.rtz")
    args = parser.parse_args()
    web = Path(__file__).resolve().parent
    source_build = args.build.resolve()
    build = args.output.resolve()
    if build == source_build:
        parser.error("Use a separate output folder for the public files.")
    build.mkdir(exist_ok=True,parents=True)
    assets = RUNTIME.copy()
    worker = f"{PROGRAM}.worker.js"
    if (source_build / worker).is_file():
        assets.append(worker)
    for name in assets:
        shutil.copy2(source_build / name, build / name)
    for name in ("web-assets.js", "coi_serviceworker.js"):
        shutil.copy2(web / name, build / name)
        assets.append(name)
    shutil.copy2(web.parent / "lib/N64Recomp-browser/site/touch_pad.js", build / "touch_pad.js")
    assets.append("touch_pad.js")

    packs = {}
    if args.packs:
        target = build / "packs"
        target.mkdir(exist_ok=True)
        for tier in ("HD", "UHD"):
            name = f"Winks-{tier}.rtz"
            source = args.packs / name
            if source.is_file():
                shutil.copy2(source, target / name)
                packs[tier] = f"packs/{name}"
        if "HD" in packs:
            mobile = target / "Winks-Mobile.rtz"
            build_mobile_pack(args.packs / "Winks-HD.rtz", mobile)
            packs["Mobile"] = "packs/Winks-Mobile.rtz"

    checksums = {}
    for name in assets + list(packs.values()):
        with (build / name).open("rb") as source:
            checksums[name] = hashlib.file_digest(source, "sha256").hexdigest()
    catalog = {
        "version": hashlib.sha256(json.dumps(checksums, sort_keys=True).encode()).hexdigest()[:20],
        "assets": assets,
        "packs": packs,
    }
    (build / "web-assets.json").write_text(json.dumps(catalog), encoding="utf-8")
    print("Browser assets", catalog["version"])

if __name__ == "__main__":
    main()
