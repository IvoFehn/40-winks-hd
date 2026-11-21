"""Generate private CPU and audio source from the supported 1999 PAL prototype."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tomllib


PROTOTYPE_SHA1 = "3774e87aa383220060d330314f2c5bbb872f72ce"
RAM_DELTA = 0x80000400 - 0x1000
PROJECT = Path(__file__).resolve().parents[1]


def write_symbols(split_dir, rom, target):
    functions = []
    for source in ("1000.s", "1050.s"):
        assembly = (split_dir / "asm" / source).read_text(encoding="utf-8")
        sizes = dict(re.findall(r"^nonmatching (\w+), (0x[\dA-Fa-f]+)$", assembly, re.M))
        labels = re.findall(
            r"^glabel (\w+)\s*(?:^[ \t]*\.[L\w]+:\s*)?^\s*/\* "
            r"([\da-f]+) ([\da-f]{8}) ([\da-f]{8}) \*/",
            assembly,
            re.M | re.I,
        )
        for name, offset_hex, address_hex, instruction in labels:
            if name not in sizes or name == "func_80080030":
                continue
            offset, address = int(offset_hex, 16), int(address_hex, 16)
            size = int(sizes[name], 16)
            if address - offset != RAM_DELTA or size % 4 or rom[offset:offset + 4] != bytes.fromhex(instruction):
                raise ValueError(f"Unexpected function address or first instruction for {name}")
            functions.append((name, address, size))

    functions.sort(key=lambda entry: entry[1])
    if not functions or functions[0][:2] != ("entrypoint", 0x80000400):
        raise ValueError("The prototype entrypoint is missing from the disassembly.")
    if any(a[1] + a[2] > b[1] for a, b in zip(functions, functions[1:])):
        raise ValueError("The prototype disassembly produced overlapping functions.")

    cpu_config = (PROJECT / "40winks.toml").read_text(encoding="utf-8")
    intervals = {name: (address, address + size) for name, address, size in functions}
    for hook in tomllib.loads(cpu_config)["patches"]["hook"]:
        start, end = intervals.get(hook["func"], (0, 0))
        if not start <= hook["before_vram"] < end:
            raise ValueError(f"Hook outside the matching prototype function: {hook['func']}")

    entries = "\n".join(
        f'    {{ name = "{name}", vram = 0x{address:X}, size = 0x{size:X} }},'
        for name, address, size in functions
    )
    target.write_text(
        '[[section]]\nname = ".main"\nrom = 0x1000\nvram = 0x80000400\nsize = 0xB8220\n'
        f"functions = [\n{entries}\n]\n",
        encoding="utf-8",
    )
    return cpu_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="Original 1999-10-07 prototype in .z64 byte order")
    parser.add_argument("cpu_tool", type=Path, help="Path to N64Recomp")
    parser.add_argument("rsp_tool", type=Path, help="Path to RSPRecomp")
    args = parser.parse_args()
    rom_path = args.rom.resolve(strict=True)
    rom = rom_path.read_bytes()
    if hashlib.sha1(rom).hexdigest() != PROTOTYPE_SHA1:
        parser.error(f"Expected the original European prototype N4WX with SHA-1 {PROTOTYPE_SHA1}.")

    decomp = PROJECT / "decomp"
    work = PROJECT / "build" / "prototype"
    split = work / "split"
    (split / "tools" / "splat_ext").mkdir(parents=True, exist_ok=True)
    quoted_rom = json.dumps(rom_path.as_posix(), ensure_ascii=False)
    splat_config = (decomp / "40winks.yaml").read_text(encoding="utf-8")
    splat_config = splat_config.replace("282b97c6a6eb79535e618fc2651b6156fff65ea4", PROTOTYPE_SHA1)
    splat_config = splat_config.replace(r"..\baserom.eur.z64", quoted_rom)
    # The final release injected code into a region that contains text in the prototype.
    splat_config = "\n".join(
        line for line in splat_config.splitlines() if "0xB7F78" not in line and "0xB7FA8" not in line
    ) + "\n"
    (split / "prototype.yaml").write_text(splat_config, encoding="utf-8")
    for name in ("symbol_addrs.txt", "reloc_addrs.txt"):
        shutil.copyfile(decomp / name, split / name)
    subprocess.run([sys.executable, "-m", "splat", "split", "prototype.yaml"], cwd=split, check=True)

    cpu_config = write_symbols(split, rom, work / "prototype-symbols.toml")
    cpu_config = re.sub(
        r'elf_path = "[^"]+"',
        lambda _: f'rom_file_path = {quoted_rom}\nsymbols_file_path = "prototype-symbols.toml"',
        cpu_config,
    )
    cpu_config = cpu_config.replace('"RecompiledFuncs"', '"../../RecompiledFuncs"')
    cpu_config = re.sub(r"(?s)stubs = \[.*?\]", "stubs = []", cpu_config, count=1)
    (work / "cpu.toml").write_text(cpu_config, encoding="utf-8")
    subprocess.run([str(args.cpu_tool.resolve(strict=True)), "cpu.toml"], cwd=work, check=True)

    # The upstream recompiler can emit a GOT field the pinned runtime predates.
    # This statically linked ROM has no GOT metadata.
    overlays = PROJECT / "RecompiledFuncs" / "recomp_overlays.inl"
    overlay_text = overlays.read_text(encoding="utf-8")
    compatible = overlay_text.replace(", .got_ram_addr = std::nullopt", "")
    if "got_ram_addr" in compatible:
        raise ValueError("Unexpected GOT relocation metadata in the prototype.")
    if compatible != overlay_text:
        overlays.write_text(compatible, encoding="utf-8")

    rsp_config = (PROJECT / "aspMain.toml").read_text(encoding="utf-8")
    table = tomllib.loads(rsp_config)["extra_indirect_branch_targets"]
    if list(struct.unpack_from(f">{len(table)}H", rom, 0xA87E0)) != table:
        raise ValueError("The audio microcode dispatch table differs from the expected layout.")
    rsp_config = rsp_config.replace('"baserom.eur.z64"', quoted_rom)
    rsp_config = rsp_config.replace('"rsp/aspMain.cpp"', '"../../rsp/aspMain.cpp"')
    (PROJECT / "rsp").mkdir(exist_ok=True)
    (work / "rsp.toml").write_text(rsp_config, encoding="utf-8")
    subprocess.run([str(args.rsp_tool.resolve(strict=True)), "rsp.toml"], cwd=work, check=True)


if __name__ == "__main__":
    main()
