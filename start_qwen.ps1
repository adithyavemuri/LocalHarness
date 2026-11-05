[CmdletBinding()]
param(
    [int]$Port = 8080,
    [string]$ModelPreset = "",
    [int]$Context = 0,
    [int]$Threads = 0,
    [ValidateSet("auto", "cpu", "vulkan")][string]$Backend = "auto",
    [switch]$Router,
    [ValidateSet("opencode", "cline", "browser")][string]$Client = "opencode",
    [ValidateSet("web", "terminal")][string]$Interface = "web",
    [string]$Workspace = "",
    [string]$Prompt = "",
    [ValidateSet("auto", "on", "off")][string]$Thinking = "auto",
    [switch]$NoBrowser
)

# Compatibility entry point; preserve named parameters and exit status.
$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $ProjectDir "start_localharness.ps1") @PSBoundParameters
exit $LASTEXITCODE
