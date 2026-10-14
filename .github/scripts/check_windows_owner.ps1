# #29 mandatory real-owner proof only. No privilege/account/policy changes.
[CmdletBinding()]
param(
    [ValidateSet(12, 13, 14)][int]$ExpectedMinor = 13,
    [string]$ReportDirectory = (Join-Path $env:TEMP 'obfuscidian-29-owner-proof')
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows is required.' }
$Repository = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$ReportDirectory = [IO.Path]::GetFullPath($ReportDirectory)
if ($ReportDirectory.StartsWith($Repository + [IO.Path]::DirectorySeparatorChar,
                              [StringComparison]::OrdinalIgnoreCase) -or $ReportDirectory -eq $Repository) {
    throw 'Keep raw reports outside the checkout.'
}
if (Test-Path -LiteralPath $ReportDirectory) { throw 'Use fresh storage; preserve previous evidence.' }
New-Item -ItemType Directory -Path $ReportDirectory | Out-Null
Push-Location $Repository
try {
    # The maintainer selects/installs the requested Poetry interpreter beforehand.
    # This never runs pytest on the known unavailable token merely to obtain a total.
    & poetry run python -m tests._windows_owner *> (Join-Path $ReportDirectory 'token-preflight.txt')
    $PreflightExit = $LASTEXITCODE
    @{ preflight_exit = $PreflightExit; owner_test_executed = $false } | ConvertTo-Json |
        Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'exit-codes.json')
    if ($PreflightExit -ne 0) { throw 'Owner setup unavailable. Stop; do not elevate, skip, inject or rerun unchanged setup.' }
    $Token = Get-Content -Raw (Join-Path $ReportDirectory 'token-preflight.txt') | ConvertFrom-Json
    if (-not $Token.version.StartsWith("3.$ExpectedMinor.")) { throw 'Unexpected Poetry interpreter.' }
    $OperatingSystem = Get-CimInstance Win32_OperatingSystem
    @{ os = $OperatingSystem.Caption; build = $OperatingSystem.BuildNumber;
       powershell = $PSVersionTable.PSVersion.ToString(); poetry = ((& poetry --version) -join ' ');
       git = ((& git --version) -join ' ') } | ConvertTo-Json |
        Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'host-summary.json')
    if (Test-Path -LiteralPath '.git') {
        & git rev-parse HEAD | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'base-commit.txt')
        if ($LASTEXITCODE -ne 0) { throw 'Cannot record source base.' }
        & git status --porcelain=v1 | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'git-status.txt')
    } elseif (Test-Path -LiteralPath 'qualification-manifest.json') {
        Copy-Item 'qualification-manifest.json' (Join-Path $ReportDirectory 'qualification-manifest.json')
        $Manifest = Get-Content -Raw 'qualification-manifest.json' | ConvertFrom-Json
        foreach ($File in $Manifest.files) {
            if ((Get-FileHash -LiteralPath $File.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $File.sha256) {
                throw 'Source snapshot checksum mismatch.'
            }
        }
    } else { throw 'Require Git source identity or a reviewed snapshot manifest.' }
    $Sources = @(Get-ChildItem 'src/obfuscidian' -Filter '*.py' -File)
    $Sources += Get-Item 'tests/_windows_owner.py', 'tests/_windows_support.py', 'tests/conftest.py', `
        'tests/integration/test_windows_native.py', 'pyproject.toml', 'poetry.lock', '.github/scripts/check_windows_owner.ps1'
    $Sources | Sort-Object FullName | ForEach-Object {
        $Relative = $_.FullName.Substring($Repository.Length + 1).Replace('\', '/')
        '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $Relative
    } | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'source-sha256.txt')
    & poetry run python -m pytest -q -ra -o junit_family=xunit1 `
        tests/integration/test_windows_native.py::test_changed_native_owner_refused_without_privilege_activation `
        "--junitxml=$(Join-Path $ReportDirectory 'owner.xml')" *> (Join-Path $ReportDirectory 'owner.txt')
    $OwnerExit = $LASTEXITCODE
    @{ preflight_exit = $PreflightExit; owner_exit = $OwnerExit; owner_test_executed = $true;
       evidence_validated = $false } | ConvertTo-Json |
        Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'exit-codes.json')
    Write-Output "Actual owner proof exit: $OwnerExit. Keep reports private; inspect all required properties."
    if ($OwnerExit -ne 0) { exit 1 }
    [xml]$Evidence = Get-Content -Raw (Join-Path $ReportDirectory 'owner.xml')
    $Cases = @($Evidence.SelectNodes('//testcase'))
    if ($Cases.Count -ne 1 -or $Cases[0].SelectSingleNode('skipped|failure|error')) {
        throw 'Require exactly one real passing owner case, with no skips, failures or errors.'
    }
    foreach ($Required in @('assignable_owner_group_available', 'owner_fixture_positive_setup', `
            'actual_filesystem_owner_transition', 'production_handle_owner_refused', `
            'full_native_identity_preserved', 'original_bytes_preserved', 'exact_protected_dacl_preserved')) {
        $Property = $Cases[0].SelectSingleNode("properties/property[@name='$Required']")
        if (-not $Property -or $Property.value -ne 'True') { throw 'Required actual owner evidence property missing.' }
    }
    $Before = $Cases[0].SelectSingleNode("properties/property[@name='actual_owner_before']")
    $After = $Cases[0].SelectSingleNode("properties/property[@name='actual_owner_after']")
    if (-not $Before -or -not $After -or $Before.value -eq $After.value) { throw 'Actual owner transition missing.' }
    @{ preflight_exit = $PreflightExit; owner_exit = $OwnerExit; owner_test_executed = $true;
       evidence_validated = $true } | ConvertTo-Json |
        Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'exit-codes.json')
} finally { Pop-Location }
