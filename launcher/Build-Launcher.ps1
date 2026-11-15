$ErrorActionPreference = 'Stop'
$framework = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319'
$csc = Join-Path $framework 'csc.exe'
$source = Join-Path $PSScriptRoot 'Launcher.cs'
$output = Join-Path (Split-Path $PSScriptRoot -Parent) '40 Winks HD.exe'
& $csc /nologo /target:exe /platform:x64 /optimize+ "/out:$output" $source
if ($LASTEXITCODE -ne 0) { throw 'The launcher build failed.' }
