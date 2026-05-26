param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplyCanonicalAliasRepair
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_35B_current_candidate_source_normalization.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_35B_READ_FIRST.txt"

Write-Host "=== START V18.35B CURRENT CANDIDATE SOURCE NORMALIZATION ==="
Write-Host "ROOT: $Root"
Write-Host "APPLY_CANONICAL_ALIAS_REPAIR: $ApplyCanonicalAliasRepair"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_35B_CANDIDATE_SOURCE_NORMALIZATION_FAILED"
    throw "Missing script: $Script"
}

$Args35B = @("--root", $Root)
if ($ApplyCanonicalAliasRepair) {
    $Args35B += "--apply-canonical-alias-repair"
}

& $Python $Script @Args35B
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.35B READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.35B CURRENT CANDIDATE SOURCE NORMALIZATION ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) {
        exit 1
    }
}

exit 0
