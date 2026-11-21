"""Make the Windows and web release ZIPs from the verified distribution folders."""
import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def package(source, target):
    files = sorted(file for file in source.rglob("*") if file.is_file())
    forbidden = {".z64", ".v64", ".n64", ".elf", ".srm", ".sav", ".mpk", ".bin"}
    if any(file.suffix.lower() in forbidden or "saves" in file.relative_to(source).parts for file in files):
        raise ValueError(f"Private game or save data in {source}")
    with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for file in files:
            archive.write(file, file.relative_to(source).as_posix())
    return hashlib.file_digest(target.open("rb"), "sha256").hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("windows", type=Path)
    parser.add_argument("web", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--version", default="0.2.0-preview")
    args = parser.parse_args()
    args.output.mkdir(exist_ok=True, parents=True)
    sums = []
    for suffix, source in (("Windows-x64", args.windows), ("Web", args.web)):
        target = args.output / f"40-Winks-HD-v{args.version}-{suffix}.zip"
        digest = package(source, target)
        sums.append(f"{digest}  {target.name}")
        print(target.name, target.stat().st_size)
    (args.output / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")

if __name__ == "__main__":
    main()
