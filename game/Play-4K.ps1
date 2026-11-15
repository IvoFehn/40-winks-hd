[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RomPath,
    [ValidateSet('4:3', '16:9')]
    [string]$Aspect = '16:9',
    [switch]$ConfigureOnly
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Setup-Runtime.ps1')
Initialize-RetroArch
$runtime = Join-Path $PSScriptRoot 'runtime'
$retro = Join-Path $runtime 'RetroArch-Win64'
$executable = Join-Path $retro 'retroarch.exe'
$library = if ($Aspect -eq '16:9') { 'mupen64plus_next_winkswide_libretro.dll' } else { 'mupen64plus_next_libretro.dll' }
$core = Join-Path $runtime "core/$library"
$rom = (Get-Item -LiteralPath $RomPath -ErrorAction Stop).FullName
$pack = Join-Path $PSScriptRoot 'packs/uhd'
foreach ($path in @($executable, $core, $rom)) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing file $path" }
}
if (!(Test-Path -LiteralPath (Join-Path $pack '40 WINKS') -PathType Container)) {
    throw "Missing texture pack $pack"
}
if (Get-Process -Name retroarch -ErrorAction SilentlyContinue | Where-Object Path -EQ $executable) {
    throw 'Close this portable copy of RetroArch before switching profiles.'
}

$profile = Join-Path $runtime '4k-internal'
foreach ($directory in @('system/Mupen64plus', 'saves', 'states', 'screenshots', 'config')) {
    $null = [IO.Directory]::CreateDirectory((Join-Path $profile $directory))
}
$textureLink = Join-Path $profile 'system/Mupen64plus/hires_texture'
$existing = Get-Item -LiteralPath $textureLink -Force -ErrorAction SilentlyContinue
if ($existing) {
    if ($existing.LinkType -ne 'Junction') { throw "Texture link path is already occupied: $textureLink" }
    if ($existing.Target -notcontains $pack) {
        $existing.Delete()
        $existing = $null
    }
}
if (!$existing) {
    $null = New-Item -ItemType Junction -Path $textureLink -Target $pack
}

$portable = $profile.Replace('\', '/')
$encoding = [Text.UTF8Encoding]::new($false)
$settings = Join-Path $profile 'retroarch.cfg'
$options = Join-Path $profile 'mupen64plus.opt'
$coreAspect = if ($Aspect -eq '16:9') { '16:9 adjusted' } else { '4:3' }
$originalRomHash = '899B866A45DFBEBC8152A3122F28AA0BA906FB448DC6B2DC7C7442E7622B5442'
$gameCheats = if ((Get-Sha256 $rom) -eq $originalRomHash) {
    $cheatFolder = Join-Path $profile 'cheats/Mupen64Plus-Next'
    $null = [IO.Directory]::CreateDirectory($cheatFolder)
    $fileName = [IO.Path]::GetFileNameWithoutExtension($rom) + '.cht'
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'profiles/retroarch.cht') -Destination (Join-Path $cheatFolder $fileName) -Force
    "$portable/cheats"
} else { '' }
[IO.File]::WriteAllText($options, @"
mupen64plus-rdp-plugin = "gliden64"
mupen64plus-aspect = "$coreAspect"
mupen64plus-169screensize = "3840x2160"
mupen64plus-43screensize = "2880x2160"
mupen64plus-txHiresEnable = "True"
mupen64plus-txHiresFullAlphaChannel = "True"
mupen64plus-EnableTexCoordBounds = "True"
mupen64plus-EnableTextureCache = "False"
mupen64plus-EnableHiResAltCRC = "False"
"@, $encoding)
[IO.File]::WriteAllText($settings, @"
config_save_on_exit = "false"
history_list_enable = "false"
game_specific_options = "false"
global_core_options = "true"
core_options_path = "$portable/mupen64plus.opt"
system_directory = "$portable/system"
config_directory = "$portable/config"
cheat_database_path = "$gameCheats"
apply_cheats_after_load = "true"
notification_show_cheats_applied = "false"
savefile_directory = "$portable/saves"
savestate_directory = "$portable/states"
screenshot_directory = "$portable/screenshots"
video_driver = "gl"
video_fullscreen = "true"
video_windowed_fullscreen = "true"
video_gpu_screenshot = "false"
menu_driver = "rgui"
input_player1_start = "enter"
input_player1_a = "d"
input_player1_b = "x"
input_player1_y = "c"
input_player1_l2 = "z"
input_player1_l_x_minus = "left"
input_player1_l_x_plus = "right"
input_player1_l_y_minus = "up"
input_player1_l_y_plus = "down"
input_exit_emulator = "escape"
"@, $encoding)

Write-Host "4K internal rendering, $Aspect, texture pack uhd"
if ($ConfigureOnly) { return }
Push-Location -LiteralPath $retro
try { & $executable --config $settings --libretro $core $rom | Out-Host }
finally { Pop-Location }
exit $LASTEXITCODE
