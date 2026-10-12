# Run only synthetic #27 qualification; production Windows writes remain gated.
[CmdletBinding()]
param(
    [string]$Python = 'python',
    [ValidateSet(12, 13, 14)][int]$ExpectedMinor = 13,
    [string]$ReportDirectory = (Join-Path $env:TEMP 'obfuscidian-27-private-reports')
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows is required.' }
$ReportDirectory = [IO.Path]::GetFullPath($ReportDirectory)
$Repository = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if ($ReportDirectory.StartsWith($Repository + [IO.Path]::DirectorySeparatorChar,
                              [StringComparison]::OrdinalIgnoreCase) -or $ReportDirectory -eq $Repository) {
    throw 'Keep raw host-identifying reports outside the checkout.'
}
New-Item -ItemType Directory -Force -Path $ReportDirectory | Out-Null
Set-Location $Repository
$Probe = @'
import ctypes, json, platform, struct, sys
assert sys.implementation.name == 'cpython', 'CPython required'
assert sys.version_info[:2] == (3, int(sys.argv[1])), 'Unexpected interpreter version'
assert struct.calcsize('P') == 8 and platform.machine().upper() == 'AMD64', 'AMD64/64-bit required'
assert not ctypes.windll.shell32.IsUserAnAdmin(), 'Use an existing unelevated token'
print(json.dumps({'implementation': platform.python_implementation(), 'version': platform.python_version(),
                  'architecture': platform.machine(), 'bits': struct.calcsize('P') * 8,
                  'store_package_path_detected': 'PythonSoftwareFoundation.Python.' in sys.executable,
                  'elevated': False}))
'@
$Metadata = & $Python -c $Probe $ExpectedMinor
if ($LASTEXITCODE -ne 0) { throw 'Interpreter/architecture/token validation failed.' }
$Metadata | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'selected-interpreter.json')
$Executable = & $Python -c 'import sys; print(sys.executable)'
if ($LASTEXITCODE -ne 0 -or -not $Executable) { throw 'Could not select the actual interpreter.' }
& poetry env use $Executable
if ($LASTEXITCODE -ne 0) { throw 'Poetry interpreter selection failed.' }
& poetry install --with dev,docs --no-interaction
if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
& poetry check --lock --strict
if ($LASTEXITCODE -ne 0) { throw 'Strict lock validation failed.' }
$Selected = & poetry run python -c $Probe $ExpectedMinor
if ($LASTEXITCODE -ne 0) { throw 'Poetry interpreter/architecture/token validation failed.' }
$Selected | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'poetry-interpreter.json')
if (($Metadata | ConvertFrom-Json).version -ne ($Selected | ConvertFrom-Json).version) {
    throw 'Poetry selected a different Python patch version.'
}
$NativeXml = Join-Path $ReportDirectory 'native-lifecycle.xml'
$NativeLog = Join-Path $ReportDirectory 'native-lifecycle.txt'
$DiagnosticXml = Join-Path $ReportDirectory 'diagnostic.xml'
$DiagnosticLog = Join-Path $ReportDirectory 'diagnostic.txt'
$OperatingSystem = Get-CimInstance Win32_OperatingSystem
@{ os = $OperatingSystem.Caption; build = $OperatingSystem.BuildNumber; git = (& git --version) } |
    ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'host-summary.json')
$SourceFiles = @(Get-ChildItem 'src/obfuscidian' -Filter '*.py' -File)
$SourceFiles += Get-ChildItem 'tests/unit' -Filter 'test_windows*.py' -File
$SourceFiles += Get-ChildItem 'tests/integration' -Filter 'test_windows*.py' -File
$SourceFiles += Get-Item '.github/scripts/check_windows_lifecycle.ps1'
$SourceFiles | Sort-Object FullName | ForEach-Object {
    $Relative = $_.FullName.Substring($Repository.Length + 1).Replace('\', '/')
    "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant())  $Relative"
} | Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'source-sha256.txt')
# This does not dispatch hosted CI or bypass the unsupported production CLI.
& poetry run python -m pytest -q -ra tests/unit/test_windows_transactions.py tests/integration/test_windows_lifecycle.py `
    tests/integration/test_windows_checkpoints.py tests/integration/test_windows_native.py `
    "--junitxml=$NativeXml" *> $NativeLog
$NativeExit = $LASTEXITCODE
# The mandatory real-owner fixture remains selected in both runs. Its known
# unavailable fixture failure must be reported; never filter, skip or xfail it.
& poetry run python -m pytest -q -ra "--junitxml=$DiagnosticXml" `
    *> $DiagnosticLog
$DiagnosticExit = $LASTEXITCODE
@{ native_exit = $NativeExit; diagnostic_exit = $DiagnosticExit } | ConvertTo-Json |
    Set-Content -Encoding UTF8 (Join-Path $ReportDirectory 'exit-codes.json')
Write-Output "Native qualification exit: $NativeExit; full diagnostic exit: $DiagnosticExit"
Write-Output 'Review private reports and disclose counts, fixture gaps and injected evidence separately.'
if ($NativeExit -ne 0 -or $DiagnosticExit -ne 0) { exit 1 }
