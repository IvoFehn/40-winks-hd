# Building the static recompilation

Use Python 3.11+, Git, CMake 3.20+ and Ninja. Windows builds require Visual Studio Build Tools with the Windows SDK and clang-cl. Run native commands in a Visual Studio Developer terminal with clang-cl on PATH.

## Windows

```sh
python tools/setup_dependencies.py native
cmake -S native/lib/N64Recomp -B native/build-tools -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl
cmake --build native/build-tools --target N64RecompCLI RSPRecomp -j 8
python tools/recompile.py native /path/to/your-game.z64 native/build-tools/N64Recomp.exe native/build-tools/RSPRecomp.exe
cmake -S native -B native/build-release -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl
cmake --build native/build-release --target 40WinksRecompiled -j 8
```

If VCPKG_ROOT points to an existing vcpkg installation, setup uses it. Otherwise setup fetches the pinned vcpkg tool. Bootstrap that copy with `native/lib/vcpkg/bootstrap-vcpkg.bat` before configuring.

Copy the resulting EXE, required DLLs, native/assets and native/recompcontrollerdb.txt into one folder. Put Winks-HD.rtz and Winks-UHD.rtz from the release under assets/textures. Rename the EXE to 40 Winks HD.exe if desired. The ROM is supplied by the player.

## Browser

Use Emscripten **6.0.12**, Naga CLI **30.0.1** with WGSL output support, and a native host compiler for the recompiler tools. Enable Emscripten in the shell where you build.

```sh
python tools/setup_dependencies.py web
cmake -S web/lib/N64ModernRuntime/N64Recomp -B web/build-tools -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build web/build-tools --target N64RecompCLI RSPRecomp -j 8
python tools/recompile.py web /path/to/your-game.z64 web/build-tools/N64Recomp.exe web/build-tools/RSPRecomp.exe
emcmake cmake -S web -B web/build-release -G Ninja -DCMAKE_BUILD_TYPE=Release -DN64RECOMP_BROWSER_FAST_LINK=ON -DRT64_NAGA_EXECUTABLE=/path/to/naga
cmake --build web/build-release --target 40WinksRecompiled -j 8
python web/web/prepare.py web/build-release dist/web --packs /path/to/release/assets/textures
python web/web/serve.py dist/web
```

On Linux the recompiler tools have no .exe extension. The browser preview reserves 1 GiB of WebAssembly memory. GPU and browser allocations add to that budget. Mobile reduces texture downloads and residency.

prepare.py selects the public runtime files and creates the cache manifest. It builds Mobile from HD images of at most 48 KiB each. Larger assets use their ROM versions.

## Source provenance

Each platform's dependencies.json records public repository URLs and exact commits. dependency-patches contains changes against those commits. dependency-extras supplies new library files. tools/setup_dependencies.py fetches those versions and applies the changes.

The game source is adapted from [DreaXer/40WinksRecomp at c1dea09](https://github.com/DreaXer/40WinksRecomp/tree/c1dea09). Web integration uses [N64Recomp-browser at 6ae3a7d](https://github.com/n64hub/N64Recomp-browser/tree/6ae3a7d14919dcd1992298642d05a7ad1f47200b).

The prototype's function metadata is in tools/prototype-symbols.toml. tools/recompile.py validates the ROM, generates CPU source with the platform's pinned recompiler, and recompiles audio microcode. Generated game files, ROMs, saves, build trees and texture packs are excluded from Git.

Source files retain their upstream licenses. The application is GPL-3.0. See the root LICENSE, library licenses at their pinned commits, and docs/third-party.md.
