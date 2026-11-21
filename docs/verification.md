# v0.2.0-preview verification

Release preparation on 21 November 2026.

- Fresh Windows Release build completed with Visual Studio Build Tools, clang-cl, CMake and Ninja.
- The packaged Windows executable started from an isolated portable directory with the supported ROM and rendered using the HD replacement pack.
- The published dependency patches passed reverse-application checks against both configured source trees. Added dependency files matched their working copies.
- The published recompilation command regenerated both platforms' 29 CPU C files exactly as in the corresponding tested source trees.
- The browser checks cover local ROM selection, active HD replacement rendering, keyboard input and a cold page reload with networking disabled.
- Earlier touch checks used a simulated mobile viewport and the Mobile replacement pack.

The release is a preview. Real iPhone and Android performance, listening checks for audio, save/load gameplay and later levels require further playtesting. Some tiled menu backgrounds can still show seams. The ZIPs provide Windows and static web builds.
