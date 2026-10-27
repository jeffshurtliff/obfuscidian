# #29 explicit interactive two-standard-account synthetic VM fixture only.
# ARM results remain diagnostic evidence pending acceptance-scope approval.
[CmdletBinding()]
param(
    [ValidateSet(12, 13, 14)][int]$ExpectedMinor = 13,
    [string]$Poetry = 'poetry',
    [Parameter(Mandatory = $true)][string]$ReportDirectory
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required.' }
$Repository = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$ReportDirectory = [IO.Path]::GetFullPath($ReportDirectory)
if ($ReportDirectory.StartsWith($Repository + [IO.Path]::DirectorySeparatorChar,
                              [StringComparison]::OrdinalIgnoreCase) -or $ReportDirectory -eq $Repository) {
    throw 'Keep raw reports outside the source checkout.'
}
if (Test-Path -LiteralPath $ReportDirectory) { throw 'Use fresh report storage; preserve earlier evidence.' }
New-Item -ItemType Directory -Path $ReportDirectory | Out-Null
Push-Location $Repository
try {
    @{ owner_test_executed = $false; evidence_validated = $false; qualification_scope_approved = $false } |
        ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'exit-codes.json')
    # Record read-only observations, then require this actual Python process and A token.
    $EnvironmentSource = Get-Content -LiteralPath '.github/scripts/get_windows_vm_environment.ps1' -Raw
    & ([ScriptBlock]::Create($EnvironmentSource)) |
        Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'guest-observations.json')
    & $Poetry run python -m tests._windows_owner_vm probe --account ObfOwnerA *> (Join-Path $ReportDirectory 'account-a-preflight.json')
    $PreflightExit = $LASTEXITCODE
    if ($PreflightExit -ne 0) { throw 'Account/runtime preflight failed; do not test or elevate.' }
    $Runtime = Get-Content -Raw (Join-Path $ReportDirectory 'account-a-preflight.json') | ConvertFrom-Json
    if (-not $Runtime.python.StartsWith("3.$ExpectedMinor.")) { throw 'Unexpected Python version.' }
    if ($Runtime.elevated -or $Runtime.bits -ne 64) { throw 'Expected an unelevated 64-bit process.' }
    if (Test-Path -LiteralPath '.git') {
        & git rev-parse HEAD | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'base-commit.txt')
        if ($LASTEXITCODE -ne 0) { throw 'Cannot identify source base.' }
        & git status --porcelain=v1 | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'git-status.txt')
        if ($LASTEXITCODE -ne 0) { throw 'Cannot identify source changes.' }
    } elseif (Test-Path -LiteralPath 'qualification-manifest.json') {
        Copy-Item 'qualification-manifest.json' (Join-Path $ReportDirectory 'qualification-manifest.json')
        $Manifest = Get-Content -Raw 'qualification-manifest.json' | ConvertFrom-Json
        foreach ($File in $Manifest.files) {
            if ([IO.Path]::IsPathRooted($File.path) -or $File.path -match '(^|[\\/])\.\.([\\/]|$)') {
                throw 'Unsafe source manifest path.'
            }
            $SourcePath = [IO.Path]::GetFullPath((Join-Path $Repository $File.path))
            if (-not $SourcePath.StartsWith($Repository + [IO.Path]::DirectorySeparatorChar,
                                            [StringComparison]::OrdinalIgnoreCase)) {
                throw 'Source path escapes the candidate.'
            }
            if ((Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $File.sha256) {
                throw 'Candidate checksum mismatch.'
            }
        }
    } else { throw 'Require Git identity or the reviewed source manifest.' }
    $Sources = @(Get-ChildItem 'src/obfuscidian', 'tests', '.github/scripts' -Filter '*.py' -File -Recurse)
    $Sources += Get-Item 'pyproject.toml', 'poetry.lock', '.github/scripts/check_windows_owner_vm.ps1', `
        '.github/scripts/get_windows_vm_environment.ps1'
    $Sources | Sort-Object FullName | ForEach-Object {
        $Relative = $_.FullName.Substring($Repository.Length + 1).Replace('\', '/')
        '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $Relative
    } | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'source-sha256.txt')
    $GitVersion = 'unavailable; owner-only source snapshot is not Git qualification'
    if (Get-Command git -ErrorAction SilentlyContinue) { $GitVersion = ((& git --version) -join ' ') }
    @{ poetry = ((& $Poetry --version) -join ' '); git = $GitVersion } | ConvertTo-Json |
        Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'tool-versions.json')
    Write-Output 'A must stay signed in. Switch user only when pytest prints the exact peer command.'
    Write-Output ('Architecture evidence: ' + $Runtime.architecture_evidence)
    # Keep interactive stdin and visible peer instructions; do not redirect them to a hidden file.
    & $Poetry run python -m pytest -q -ra -s -o junit_family=xunit1 --owner-vm-two-account `
        tests/integration/test_windows_native.py::test_changed_native_owner_refused_without_privilege_activation `
        "--junitxml=$(Join-Path $ReportDirectory 'owner.xml')" | Tee-Object -FilePath (Join-Path $ReportDirectory 'owner.txt')
    $OwnerExit = $LASTEXITCODE
    @{ preflight_exit = $PreflightExit; owner_exit = $OwnerExit; owner_test_executed = $true;
       evidence_validated = $false; qualification_scope_approved = $false } | ConvertTo-Json |
        Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'exit-codes.json')
    if ($OwnerExit -ne 0) { throw 'Owner test failed; retain private reports and synthetic artifacts.' }
    [xml]$Evidence = Get-Content -Raw (Join-Path $ReportDirectory 'owner.xml')
    $Cases = @($Evidence.SelectNodes('//testcase'))
    if ($Cases.Count -ne 1 -or $Cases[0].name -ne 'test_changed_native_owner_refused_without_privilege_activation' -or
            $Cases[0].SelectSingleNode('skipped|failure|error')) {
        throw 'Require the actual original owner case to pass, with no skip/failure/error.'
    }
    foreach ($Required in @('owner_fixture_positive_setup', 'owner_fixture_positive_guarded_open',
            'actual_filesystem_owner_transition', 'retained_write_dac_restored_exact_original',
            'production_handle_owner_refused', 'production_guarded_open_owner_refused',
            'full_native_identity_preserved', 'original_bytes_preserved', 'exact_protected_dacl_preserved')) {
        $Property = $Cases[0].SelectSingleNode("properties/property[@name='$Required']")
        if (-not $Property -or $Property.value -ne 'True') { throw 'Mandatory actual-owner evidence missing.' }
    }
    $Before = $Cases[0].SelectSingleNode("properties/property[@name='actual_owner_before']")
    $After = $Cases[0].SelectSingleNode("properties/property[@name='actual_owner_after']")
    if (-not $Before -or -not $After -or $Before.value -eq $After.value) { throw 'Distinct actual owners required.' }
    @{ preflight_exit = $PreflightExit; owner_exit = $OwnerExit; owner_test_executed = $true;
       evidence_validated = $true; architecture_evidence = $Runtime.architecture_evidence;
       qualification_scope_approved = $false; scope = 'one VM owner case; no matrix or production qualification' } |
        ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'exit-codes.json')
    Write-Output 'Owner case properties validated. Keep reports private; acceptance-scope review and all other gates remain.'
} finally { Pop-Location }
