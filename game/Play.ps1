[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RomPath,
    [ValidateSet('1080p', '1440p', '2160p')]
    [string]$Resolution = '1080p',
    [ValidateSet('4:3', '16:9')]
    [string]$Aspect = '4:3',
    [switch]$Windowed,
    [switch]$Fullscreen,
    [switch]$ConfigureOnly,
    [switch]$ShowResolution,
    [switch]$DumpTextures,
    [switch]$OriginalTextures,
    [switch]$OriginalFiltering
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Setup-Runtime.ps1')
if ($Windowed -and $Fullscreen) { throw 'Choose one window mode.' }
Initialize-Rmg
$runtime = Join-Path $PSScriptRoot 'runtime/rmg'
$executable = Join-Path $runtime 'RMG.exe'
$config = Join-Path $runtime 'Config/GLideN64.ini'
$coreConfig = Join-Path $runtime 'Config/mupen64plus.cfg'
$rom = (Get-Item -LiteralPath $RomPath -ErrorAction Stop).FullName
foreach ($path in @($executable, $config, $coreConfig, $rom)) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing file $path" }
}
if (Get-Process -Name RMG -ErrorAction SilentlyContinue | Where-Object Path -EQ $executable) {
    throw 'Close this portable copy of RMG before switching profiles.'
}

$width, $height, $tier = switch ($Resolution) {
    '1080p' { 1920, 1080, 'hd' }
    '1440p' { 2560, 1440, 'hd' }
    '2160p' { 3840, 2160, 'uhd' }
}
# Expand the scene around the game's 4:3 projection and UI proportions.
$aspectMode = if ($Aspect -eq '16:9') { 3 } else { 1 }
$packRoot = Join-Path $PSScriptRoot ('packs/' + $tier)
$pack = Join-Path $packRoot '40 WINKS'
if (!(Test-Path -LiteralPath $pack -PathType Container)) { throw "Missing texture pack $pack" }

# The wide profile uses the 40 Winks scissor correction when running GLideN64.
$coreText = [IO.File]::ReadAllText($coreConfig)
$stockRenderer = 'mupen64plus-video-GLideN64.dll'
$wideRenderer = 'mupen64plus-video-GLideN64-WinksWide.dll'
$bundledRenderer = '(?m)^GFX_Plugin = "mupen64plus-video-GLideN64(?:-WinksWide)?\.dll"(?=\r?$)'
$nextCoreText = $coreText
if ($coreText -match $bundledRenderer) {
    $renderer = if ($Aspect -eq '16:9') { $wideRenderer } else { $stockRenderer }
    if (!(Test-Path -LiteralPath (Join-Path $runtime "Plugin/GFX/$renderer") -PathType Leaf)) {
        throw "Missing graphics plugin $renderer"
    }
    $nextCoreText = $coreText -replace $bundledRenderer, ('GFX_Plugin = "' + $renderer + '"')
}

$settings = [ordered]@{
    'video\fullscreenWidth' = $width
    'video\fullscreenHeight' = $height
    'video\windowedWidth' = $width
    'video\windowedHeight' = $height
    'video\fxaa' = if ($OriginalFiltering) { 0 } else { 1 }
    'texture\anisotropy' = if ($OriginalFiltering) { 0 } else { 8 }
    'graphics2D\correctTexrectCoords' = if ($OriginalFiltering) { 0 } else { 1 }
    'graphics2D\enableTexCoordBounds' = if ($OriginalFiltering) { 0 } else { 1 }
    'frameBufferEmulation\aspect' = $aspectMode
    'frameBufferEmulation\nativeResFactor' = 0
    'textureFilter\txHiresEnable' = 1
    # Keep the hi-res lookup enabled for CRC calculation even when dumping originals.
    'textureFilter\txPath' = if ($OriginalTextures) {
        (Join-Path $PSScriptRoot 'runtime/original-textures').Replace('\', '/')
    } else { $packRoot.Replace('\', '/') }
    'textureFilter\txSaveCache' = 0
    'textureFilter\txDump' = [int]$DumpTextures.IsPresent
    'hotkeys\hkTexDumpEnabled' = if ($DumpTextures) { 7 } else { 0 }
    'onScreenDisplay\showRenderingResolution' = [int]$ShowResolution.IsPresent
}
$userProfile = $false
$updated = @{}
$configLines = foreach ($line in [IO.File]::ReadAllLines($config)) {
    if ($line.StartsWith('[')) { $userProfile = $line -ceq '[User]' }
    $key = $line.Split('=')[0]
    if ($userProfile -and $settings.Contains($key)) {
        $updated[$key] = $true
        $key + '=' + $settings[$key]
    } else {
        $line
    }
}
foreach ($key in $settings.Keys) {
    if (!$updated.ContainsKey($key)) { throw "Expected GLideN64 setting $key" }
}
$pendingConfig = $config + '.tmp'
try {
    [IO.File]::WriteAllLines($pendingConfig, [string[]]$configLines, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $pendingConfig -Destination $config -Force
} finally {
    [IO.File]::Delete($pendingConfig)
}
if ($nextCoreText -cne $coreText) {
    $pendingCoreConfig = $coreConfig + '.tmp'
    try {
        [IO.File]::WriteAllText($pendingCoreConfig, $nextCoreText, [Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $pendingCoreConfig -Destination $coreConfig -Force
    } finally {
        [IO.File]::Delete($pendingCoreConfig)
    }
}

Write-Host "$Resolution ($($width)x$height), $Aspect, texture pack $tier"
if ($ConfigureOnly) { return }
$emulatorArgs = @('--quit-after-emulation')
if ($Fullscreen -or (!$Windowed -and $Resolution -ne '1080p')) {
    $emulatorArgs += '--fullscreen'
}
Push-Location -LiteralPath $runtime
try { & $executable @emulatorArgs $rom | Out-Host; exit $LASTEXITCODE }
finally { Pop-Location }
