"""Regenerate the prototype's CPU and RSP source using the player's ROM."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tomllib
import json

ROOT = Path(__file__).resolve().parents[1]
SHA256 = "899b866a45dfbebc8152a3122f28aa0ba906fb448dc6b2dc7c7442e7622b5442"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("native", "web"))
    parser.add_argument("rom", type=Path)
    parser.add_argument("cpu_tool", type=Path)
    parser.add_argument("rsp_tool", type=Path)
    args = parser.parse_args()
    rom_path = args.rom.resolve(strict=True)
    rom = rom_path.read_bytes()
    if hashlib.sha256(rom).hexdigest() != SHA256:
        parser.error("Use the original European N4WX prototype dated 1999-10-07 in .z64 byte order.")
    project = ROOT / args.platform
    work = project / "build" / "prototype"
    work.mkdir(parents=True, exist_ok=True)
    (project / "RecompiledFuncs").mkdir(exist_ok=True)
    (project / "rsp").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "tools/prototype-symbols.toml", work / "prototype-symbols.toml")
    cpu = (project / "40winks.toml").read_text(encoding="utf-8")
    cpu = re.sub(r'elf_path = "[^"]+"', lambda _: "rom_file_path = " + json.dumps(rom_path.as_posix()) + '\nsymbols_file_path = "prototype-symbols.toml"', cpu)
    cpu = cpu.replace('"RecompiledFuncs"', '"../../RecompiledFuncs"')
    cpu = re.sub(r"(?s)stubs = \[.*?\]", "stubs = []", cpu, count=1)
    (work / "cpu.toml").write_text(cpu, encoding="utf-8")
    subprocess.run([str(args.cpu_tool.resolve(strict=True)), "cpu.toml"], cwd=work, check=True)
    overlay = project / "RecompiledFuncs/recomp_overlays.inl"
    overlay.write_text(overlay.read_text().replace(", .got_ram_addr = std::nullopt", ""))
    rsp = (project / "aspMain.toml").read_text(encoding="utf-8")
    targets = tomllib.loads(rsp)["extra_indirect_branch_targets"]
    if list(struct.unpack_from(f">{len(targets)}H", rom, 0xA87E0)) != targets:
        raise ValueError("Unexpected audio microcode dispatch table")
    rsp = rsp.replace('"baserom.eur.z64"', json.dumps(rom_path.as_posix()))
    rsp = rsp.replace('"rsp/aspMain.cpp"', '"../../rsp/aspMain.cpp"')
    (work / "rsp.toml").write_text(rsp, encoding="utf-8")
    subprocess.run([str(args.rsp_tool.resolve(strict=True)), "rsp.toml"], cwd=work, check=True)

if __name__ == "__main__":
    main()
