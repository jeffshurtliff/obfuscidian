# Run the shared synthetic #27 qualification with Store or explicit CPython 3.14.
# Production Windows writes remain gated; the shared helper validates the actual
# version, AMD64/64-bit architecture and unelevated token and retains all failures.
[CmdletBinding()]
param(
    [string]$Python = 'python',
    [string]$ReportDirectory = (Join-Path $env:TEMP 'obfuscidian-27-private-reports-314')
)
$ErrorActionPreference = 'Stop'
$Helper = Join-Path $PSScriptRoot 'check_windows_lifecycle.ps1'
$LASTEXITCODE = 0
& $Helper -Python $Python -ExpectedMinor 14 -ReportDirectory $ReportDirectory
exit $LASTEXITCODE
