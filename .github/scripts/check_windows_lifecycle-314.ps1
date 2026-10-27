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
$LifecycleHelperDirectory = Split-Path -Parent $Helper
# Preserve the helper's repository-relative paths when invoked as source text.
# This supports the maintainer's script-block invocation without a nested .ps1
# invocation or any change to execution-policy settings.
$HelperSource = Get-Content -LiteralPath $Helper -Raw
# Build the token in parts so the caller's source replacement cannot rewrite it.
$HelperRootToken = '$' + 'PSScriptRoot'
$HelperBlock = [ScriptBlock]::Create($HelperSource.Replace($HelperRootToken, '$LifecycleHelperDirectory'))
$LASTEXITCODE = 0
& $HelperBlock -Python $Python -ExpectedMinor 14 -ReportDirectory $ReportDirectory
exit $LASTEXITCODE
