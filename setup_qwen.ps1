[CmdletBinding()]
param(
    [switch]$Preflight,
    [switch]$RuntimeOnly,
    [switch]$ModelOnly,
    [string]$ModelPreset = ""
)

# Compatibility entry point; preserve named parameters and exit status.
$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $ProjectDir "setup_localharness.ps1") @PSBoundParameters
exit $LASTEXITCODE
