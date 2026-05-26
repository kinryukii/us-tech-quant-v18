[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [switch]$AllowScriptPatch
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R25A_source_script_repair_builder_selection_gate.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R25A_READ_FIRST.txt"

Write-Host "=== START V18.25A-R25A SOURCE SCRIPT REPAIR BUILDER SELECTION GATE ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "ALLOW_SCRIPT_PATCH: $($AllowScriptPatch.IsPresent)"
Write-Host "MODE: $(if ($AllowScriptPatch.IsPresent -and -not $DryRun.IsPresent) { 'SCRIPT_PATCH_AND_BUILDER_SELECTION_GATE' } else { 'DRYRUN_AUDIT_ONLY' })"

$argsList = @(
    $scriptPath,
    "--root", $Root
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($AllowScriptPatch.IsPresent) {
    $argsList += "--allow-script-patch"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R25A source script repair builder selection gate failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R25A SOURCE SCRIPT REPAIR BUILDER SELECTION GATE ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
