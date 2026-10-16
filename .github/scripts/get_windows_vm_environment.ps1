# #29 read-only VM readiness observations; never qualification or permission repair.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required.' }
if (-not ('Obf29EnvironmentNative' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Obf29EnvironmentNative {
    [DllImport("kernel32.dll")] public static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsWow64Process2(IntPtr process, out ushort processMachine, out ushort nativeMachine);
}
'@
}
[UInt16]$ProcessMachine = 0
[UInt16]$NativeMachine = 0
if (-not [Obf29EnvironmentNative]::IsWow64Process2(
        [Obf29EnvironmentNative]::GetCurrentProcess(), [ref]$ProcessMachine, [ref]$NativeMachine)) {
    throw 'Cannot establish native and process architectures. Do not infer native AMD64.'
}
$Machines = @{ 0 = 'native process'; 34404 = 'AMD64'; 43620 = 'ARM64'; 332 = 'I386' }
$OperatingSystem = Get-CimInstance Win32_OperatingSystem
$Processors = @(Get-CimInstance Win32_Processor)
$Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = [Security.Principal.WindowsPrincipal]::new($Identity)
$AdministratorSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
$AdministratorGroupPresent = @($Identity.Groups | Where-Object { $_.Value -eq $AdministratorSid.Value }).Count -ne 0
$Volume = Get-Volume -DriveLetter C
$Tools = @{}
foreach ($Tool in @('python', 'py', 'git', 'poetry')) {
    $Tools[$Tool] = [bool](Get-Command $Tool -ErrorAction SilentlyContinue)
}
[ordered]@{
    scope = 'read-only readiness observations; no owner fixture or qualification'
    edition = $OperatingSystem.Caption
    os_version = $OperatingSystem.Version
    build = $OperatingSystem.BuildNumber
    os_architecture_observation = $OperatingSystem.OSArchitecture
    processor_architecture_codes = @($Processors | ForEach-Object { [int]$_.Architecture })
    native_machine_code = ('0x{0:X4}' -f $NativeMachine)
    native_machine = $Machines[[int]$NativeMachine]
    powershell_process_machine_code = ('0x{0:X4}' -f $ProcessMachine)
    powershell_process_machine = $Machines[[int]$ProcessMachine]
    powershell_bits = [IntPtr]::Size * 8
    powershell_version = $PSVersionTable.PSVersion.ToString()
    elevated = $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    administrator_group_present_in_token = $AdministratorGroupPresent
    approved_test_account = ($Identity.Name.Split('\')[-1] -in @('ObfOwnerA', 'ObfOwnerB'))
    system_volume_filesystem = $Volume.FileSystem
    system_volume_drive_type = [string]$Volume.DriveType
    system_volume_free_bytes = $Volume.SizeRemaining
    command_names_available = $Tools
    python_architecture = 'not probed; Python must be checked separately with IsWow64Process2'
    utm_version_and_virtualization_mode = 'not established by this guest probe'
} | ConvertTo-Json -Depth 4
