param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplySafeReferencePatches
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_35C_candidate_source_dependency_role_review.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_35C_READ_FIRST.txt"

Write-Host "=== START V18.35C CANDIDATE SOURCE DEPENDENCY ROLE REVIEW ==="
Write-Host "ROOT: $Root"
Write-Host "APPLY_SAFE_REFERENCE_PATCHES: $ApplySafeReferencePatches"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_FAILED"
    throw "Missing script: $Script"
}

$Args35C = @("--root", $Root)
if ($ApplySafeReferencePatches) {
    $Args35C += "--apply-safe-reference-patches"
}

& $Python $Script @Args35C
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.35C READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.35C CANDIDATE SOURCE DEPENDENCY ROLE REVIEW ==="
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
