"""Package the v0.1.1 Rice-named PNGs for the native renderer."""

import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_STORED, ZipFile

PACK_DATABASE = {
    "configuration": {
        "configurationVersion": 3,
        "hashVersion": 5,
        "autoPath": "rice",
        "defaultOperation": "stream",
        "defaultShift": "none",
    },
    "textures": [],
}


def package_texture_pack(source: Path, target: Path) -> int:
    images = sorted(source.rglob("*.png"))
    if not images:
        raise ValueError(f"No replacement textures in {source}")

    texture_keys: set[str] = set()
    for image in images:
        prefix, separator, name = image.stem.partition("#")
        key, suffix_separator, image_type = name.rpartition("_")
        if prefix.upper() != "40 WINKS" or not separator or not suffix_separator:
            raise ValueError(f"Unexpected texture filename: {image.name}")
        if image_type not in {"all", "ciByRGBA", "allciByRGBA"}:
            raise ValueError(f"Unsupported texture encoding: {image.name}")
        if key.lower() in texture_keys:
            raise ValueError(f"Ambiguous texture ID: {image.name}")
        texture_keys.add(key.lower())

    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=target.parent, suffix=".rtz.tmp", delete=False) as file:
        temporary = Path(file.name)
    try:
        with ZipFile(temporary, "w", compression=ZIP_STORED) as archive:
            archive.writestr("rt64.json", json.dumps(PACK_DATABASE, indent=2))
            for image in images:
                archive.write(image, image.relative_to(source).as_posix())
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)

    return len(images)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packs", type=Path, help="Folder containing hd/40 WINKS and uhd/40 WINKS")
    parser.add_argument("destination", type=Path, help="Directory for the two RTZ archives")
    args = parser.parse_args()

    for name in ("HD", "UHD"):
        source = args.packs / name.lower() / "40 WINKS"
        target = args.destination / f"Winks-{name}.rtz"
        count = package_texture_pack(source, target)
        print(f"{target.name}: {count} textures")


if __name__ == "__main__":
    main()
