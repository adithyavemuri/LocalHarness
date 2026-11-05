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

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Arguments = @((Join-Path $ProjectDir "run_server.py"), "--setup-if-needed",
    "--port", "$Port", "--thinking", $Thinking, "--backend", $Backend)
$ServerClient = if ($Client -eq "browser") { "server" } else { $Client }
$Arguments += @("--client", $ServerClient, "--interface", $Interface)
if ($Workspace) { $Arguments += @("--workspace", $Workspace) }
if ($PSBoundParameters.ContainsKey("Prompt")) { $Arguments += @("--prompt", $Prompt) }
if ($NoBrowser -and $Client -eq "opencode") { $Arguments += @("--interface", "terminal") }
if ($Context -lt 0) { throw "Context must not be negative." }
if ($Context -gt 0) { $Arguments += @("--context", "$Context") }
if ($ModelPreset) { $Arguments += @("--preset", $ModelPreset) }
if ($Router) { $Arguments += "--router" }
if ($Threads -lt 0) { throw "Threads must not be negative." }
if ($Threads -gt 0) { $Arguments += @("--threads", "$Threads") }
if (-not $NoBrowser) { $Arguments += "--open-browser" }
& python @Arguments
exit $LASTEXITCODE
