$ErrorActionPreference = "Stop"
$Root = "D:\us-tech-quant"
$Python = if (Test-Path "$Root\.venv\Scripts\python.exe") { "$Root\.venv\Scripts\python.exe" } else { "python" }
$ReadFirst = "$Root\outputs\v18\factor_shadow\V18_3C_READ_FIRST.txt"
New-Item -ItemType Directory -Force "$Root\outputs\v18\factor_shadow" | Out-Null
Write-Host ""
Write-Host "=== V18.3C FACTOR SHADOW DAILY WRAPPER START ==="
Write-Host ""
$Step1 = "$Root\scripts\v18\run_v18_1B_factor_value_compute.ps1"
if (!(Test-Path $Step1)) { throw "MISSING_STEP1_V18_1B_WRAPPER: $Step1" }
Write-Host "STEP 1: V18.1B factor value compute"
& powershell -NoProfile -ExecutionPolicy Bypass -File $Step1
if ($LASTEXITCODE -ne 0) { throw "V18_1B_FAILED" }
$Py3A = "$Root\src\v18\factor_lab\run_v18_3A_factor_shadow_daily.py"
$Py3B = "$Root\src\v18\factor_lab\run_v18_3B_R2_strict_fallback_compare.py"
foreach ($Py in @($Py3A, $Py3B)) {
    if (!(Test-Path $Py)) { throw "MISSING_PY_SCRIPT: $Py" }
    Write-Host ""
    Write-Host "PARSE CHECK: $Py"
    & $Python -m py_compile $Py
    if ($LASTEXITCODE -ne 0) { throw "PY_PARSE_FAILED: $Py" }
    Write-Host "RUN: $Py"
    & $Python $Py
    if ($LASTEXITCODE -ne 0) { throw "PY_RUN_FAILED: $Py" }
}
$Lines = @(
    "=== V18.3C FACTOR SHADOW DAILY READ FIRST ===",
    "",
    "STATUS:",
    "V18_3C_STATUS: OK_FACTOR_SHADOW_DAILY_WRAPPER_READY",
    "",
    "OFFICIAL_DECISION_IMPACT:",
    "NONE",
    "",
    "PROMOTION_ACTION:",
    "NONE",
    "",
    "READ:",
    "$Root\outputs\v18\factor_shadow\V18_3A_READ_FIRST.txt",
    "$Root\outputs\v18\factor_shadow\V18_3B_R2_READ_FIRST.txt",
    "$Root\outputs\v18\factor_shadow\V18_3B_R2_SHADOW_OFFICIAL_COMPARE_REPORT.md",
    "$Root\state\v18\factor_shadow_outcome_tracker.csv",
    "",
    "NEXT_STEP:",
    "Run this wrapper after each V17.8D official daily run. Run V18.4A only after forward trading days are available.",
    "",
    "IMPORTANT:",
    "This wrapper refreshes shadow factors only. It does not promote factors and does not change official BUY / NO_BUY."
)
Set-Content -Path $ReadFirst -Value $Lines -Encoding UTF8
Write-Host ""
Write-Host "=== V18.3C FACTOR SHADOW DAILY WRAPPER READY ==="
Write-Host "V18_3C_STATUS: OK_FACTOR_SHADOW_DAILY_WRAPPER_READY"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "PROMOTION_ACTION: NONE"
Write-Host ""
Write-Host "READ_FIRST:"
Write-Host $ReadFirst
Write-Host ""
Write-Host "=== DONE ==="
