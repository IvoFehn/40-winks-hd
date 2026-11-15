$releaseRoot = Split-Path $PSScriptRoot -Parent
$runtimeRoot = Join-Path $PSScriptRoot 'runtime'
$patches = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'profiles/widescreen-patches.json') -Raw | ConvertFrom-Json

function Get-Sha256([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $file = [IO.File]::OpenRead($Path)
        try { return [BitConverter]::ToString($sha.ComputeHash($file)).Replace('-', '') }
        finally { $file.Dispose() }
    } finally {
        $sha.Dispose()
    }
}

function Assert-Hash([string]$Path, [string]$Expected) {
    if ((Get-Sha256 $Path) -ine $Expected) {
        throw "Unexpected file checksum: $Path"
    }
}

function Convert-HexToBytes([string]$Hex) {
    $bytes = New-Object byte[] ($Hex.Length / 2)
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        $bytes[$i] = [Convert]::ToByte($Hex.Substring($i * 2, 2), 16)
    }
    return ,$bytes
}

function Install-WideRenderer([string]$From, [string]$To, $Patch) {
    Assert-Hash $From $Patch.original
    if ((Test-Path -LiteralPath $To -PathType Leaf) -and
        (Get-Sha256 $To) -ieq $Patch.patched) { return }
    $data = [IO.File]::ReadAllBytes($From)
    $extension = Convert-HexToBytes $Patch.extension
    $jump = Convert-HexToBytes $Patch.jump
    $size = [BitConverter]::ToUInt32($data, $Patch.sectionSizeAt) + $extension.Length
    $sizeBytes = [BitConverter]::GetBytes([uint32]$size)
    [Array]::Copy($sizeBytes, 0, $data, $Patch.sectionSizeAt, $sizeBytes.Length)
    [Array]::Copy($extension, 0, $data, $Patch.extensionAt, $extension.Length)
    [Array]::Copy($jump, 0, $data, $Patch.jumpAt, $jump.Length)
    $pending = $To + '.tmp'
    try {
        [IO.File]::WriteAllBytes($pending, $data)
        Assert-Hash $pending $Patch.patched
        Move-Item -LiteralPath $pending -Destination $To -Force
    } finally {
        [IO.File]::Delete($pending)
    }
}

function Use-SetupFolder([scriptblock]$Install) {
    $root = [IO.Path]::GetFullPath($runtimeRoot)
    $null = [IO.Directory]::CreateDirectory($root)
    $work = [IO.Path]::Combine($root, 'setup-' + [Guid]::NewGuid().ToString('N'))
    $null = [IO.Directory]::CreateDirectory($work)
    try { & $Install $work }
    finally {
        $item = Get-Item -LiteralPath $work
        if ($item.Parent.FullName -ne $root -or $item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Unexpected setup folder: $work"
        }
        [IO.Directory]::Delete($work, $true)
    }
}

function Expand-PinnedArchive([string]$Name, [string]$Url, [string]$Hash, [string]$Work) {
    $archive = Join-Path $releaseRoot "bootstrap/$Name"
    if (!(Test-Path -LiteralPath $archive -PathType Leaf)) {
        if (!$Url) { throw "Missing $Name. Extract the complete Windows release again." }
        $archive = Join-Path $Work $Name
        Write-Host "Downloading $Name for the selected mode..."
        $ProgressPreference = 'SilentlyContinue'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $Url -OutFile $archive -UseBasicParsing -TimeoutSec 180
    }
    Assert-Hash $archive $Hash
    $unpacked = Join-Path $Work 'unpacked'
    $null = [IO.Directory]::CreateDirectory($unpacked)
    if ($Name.EndsWith('.zip')) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::ExtractToDirectory($archive, $unpacked)
    } else {
        $tar = Join-Path ([Environment]::SystemDirectory) 'tar.exe'
        & $tar -xf $archive -C $unpacked
        if ($LASTEXITCODE -ne 0) { throw "Could not extract $Name." }
    }
    return $unpacked
}

function Initialize-Rmg {
    $dest = Join-Path $runtimeRoot 'rmg'
    if (!(Test-Path -LiteralPath $dest -PathType Container)) {
        Use-SetupFolder {
            param($work)
            $tree = Expand-PinnedArchive 'rmg.zip' 'https://github.com/Rosalie241/RMG/releases/download/v0.9.1/RMG-Portable-Windows64-v0.9.1.zip' '5C81292E5C17ED40381CBE1AEA1B6FD61D7EF6BE4307857F6135CBD3BACD297D' $work
            Assert-Hash (Join-Path $tree 'RMG.exe') '5C38B922BCD36211D783DC3F8C238A30CA6F7DE8DB730181E725E77525EF6628'
            $config = Join-Path $tree 'Config'
            $null = [IO.Directory]::CreateDirectory($config)
            Copy-Item -Path (Join-Path $PSScriptRoot 'profiles/rmg/*') -Destination $config -Recurse -Force
            [IO.File]::WriteAllBytes((Join-Path $tree 'portable.txt'), [byte[]]@())
            [IO.Directory]::Move($tree, $dest)
        }
    }
    $gfx = Join-Path $dest 'Plugin/GFX'
    Install-WideRenderer (Join-Path $gfx 'mupen64plus-video-GLideN64.dll') (Join-Path $gfx 'mupen64plus-video-GLideN64-WinksWide.dll') $patches.Rmg
}

function Initialize-RetroArch {
    $dest = Join-Path $runtimeRoot 'RetroArch-Win64'
    if (!(Test-Path -LiteralPath $dest -PathType Container)) {
        Use-SetupFolder {
            param($work)
            $tree = Expand-PinnedArchive 'retroarch.7z' 'https://buildbot.libretro.com/stable/1.22.2/windows/x86_64/RetroArch.7z' 'B2139B1D0F9D4526DC6B5CE23CBB3EFDC766096FA6F2C3DF016818B486AC6372' $work
            $tree = Join-Path $tree 'RetroArch-Win64'
            Assert-Hash (Join-Path $tree 'retroarch.exe') '81C11B6F24932BF7918F05EEE8928035BFF3887335FD2A081507C75E9D94D06A'
            [IO.Directory]::Move($tree, $dest)
        }
    }
    $cores = Join-Path $runtimeRoot 'core'
    if (!(Test-Path -LiteralPath $cores -PathType Container)) {
        Use-SetupFolder {
            param($work)
            $tree = Expand-PinnedArchive 'mupen64plus-next.zip' '' '21BF3974896DADED92DC9AF313E60A4F5419DB82761DAA68F3E28639ACF29372' $work
            Assert-Hash (Join-Path $tree 'mupen64plus_next_libretro.dll') $patches.Libretro.original
            [IO.Directory]::Move($tree, $cores)
        }
    }
    Install-WideRenderer (Join-Path $cores 'mupen64plus_next_libretro.dll') (Join-Path $cores 'mupen64plus_next_winkswide_libretro.dll') $patches.Libretro
}
