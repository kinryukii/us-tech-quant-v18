param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

chcp 65001 | Out-Null

Set-Location -LiteralPath $Root

Write-Host ""
Write-Host "=== RUN V16.2 CANDIDATE REVIEW PACK ==="
Write-Host ""

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
    $python = "python"
}

if (!(Test-Path ".\outputs\v16\latest\V16_FINAL_ACTION_LIST.csv")) {
    if (Test-Path ".\run_v16_1_time_risk_final_decision.ps1") {
        & ".\run_v16_1_time_risk_final_decision.ps1" -Root $Root
    } else {
        throw "Missing V16_FINAL_ACTION_LIST.csv and missing V16.1 runner. Run V16.1 first."
    }
}

& $python ".\scripts\run_v16_2_candidate_review_pack.py"

Write-Host ""
Write-Host "=== CHECK V16.2 FILES ==="
Write-Host ""

$files = @(
  "D:\us-tech-quant\outputs\v16\latest\V16_CANDIDATE_REVIEW_PACK.md",
  "D:\us-tech-quant\outputs\v16\latest\V16_CANDIDATE_REVIEW_PACK.csv",
  "D:\us-tech-quant\state\v16_manual_review_decisions.csv",
  "D:\us-tech-quant\outputs\v16\latest\V16_REVIEW_READ_THESE_FILES.txt"
)

foreach ($f in $files) {
  if (Test-Path $f) {
    Write-Host "OK   $f"
  } else {
    Write-Host "MISS $f"
  }
}

Write-Host ""
Write-Host "=== OPEN FILES ==="
Write-Host ""

Start-Process explorer.exe "D:\us-tech-quant\outputs\v16\latest"
Start-Process explorer.exe "D:\us-tech-quant\state"
Start-Process notepad.exe "D:\us-tech-quant\outputs\v16\latest\V16_CANDIDATE_REVIEW_PACK.md"
Start-Process notepad.exe "D:\us-tech-quant\state\v16_manual_review_decisions.csv"

Write-Host ""
Write-Host "=== V16.2 DONE ==="
Write-Host ""
