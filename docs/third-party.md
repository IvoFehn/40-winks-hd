# Emulator components

The Windows ZIP includes the HD and UHD replacement PNGs, launcher, configuration and an unmodified Mupen64Plus-Next core archive. The launcher validates the SHA-256 of the selected emulator archive, extracts it locally and generates the compatible widescreen variant from the included patch data.

| Component | Build used | Upstream source |
| --- | --- | --- |
| Rosalie's Mupen GUI and bundled GLideN64 | RMG Windows x64 0.9.1 | [RMG release and source](https://github.com/Rosalie241/RMG/releases/tag/v0.9.1) |
| RetroArch | Windows x64 1.22.2, `69a4f0e` | [RetroArch source at 69a4f0e](https://github.com/libretro/RetroArch/tree/69a4f0ea1e8aaf442ae4858f2e7f2b31a1776576) |
| Mupen64Plus-Next | Windows x64 libretro core, `15bada8` | [Corresponding source archive](https://github.com/IvoFehn/40-winks-hd/releases/download/v0.1.1/mupen64plus-next-15bada8-source.zip) · [Upstream tree](https://github.com/libretro/mupen64plus-libretro-nx/tree/15bada85906593376e8fd697f1b0b3af3a20f512) |

The core's license accompanies its archive in the release ZIP. [License](mupen64plus-next-LICENSE.txt)

The local widescreen variants use the machine-code patches and checksum verification in the launcher repository. The patch adjusts horizontal scissor endpoints for adjusted widescreen views on the main color buffer. [Patch data](../game/profiles/widescreen-patches.json) · [Patch application](../game/Setup-Runtime.ps1)

## Building the launcher

Run `powershell.exe -NoProfile -File .\launcher\Build-Launcher.ps1` from the repository root on Windows with .NET Framework 4.x. The script uses the Windows C# compiler and creates `40 Winks HD.exe` at the repository root. The packaged game profiles, packs and core are in the Windows release ZIP.
