param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

chcp 65001 | Out-Null

Set-Location -LiteralPath $Root

Write-Host ""
Write-Host "=== RUN V16.3 PULLBACK TRIGGER LAYER ==="
Write-Host ""

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
    $python = "python"
}

if (!(Test-Path ".\outputs\v16\latest\V16_CANDIDATE_REVIEW_PACK.csv")) {
    if (Test-Path ".\run_v16_2_candidate_review_pack.ps1") {
        & ".\run_v16_2_candidate_review_pack.ps1" -Root $Root
    } else {
        throw "Missing V16_CANDIDATE_REVIEW_PACK.csv and missing V16.2 runner. Run V16.2 first."
    }
}

& $python ".\scripts\run_v16_3_pullback_trigger_layer.py"

Write-Host ""
Write-Host "=== CHECK V16.3 FILES ==="
Write-Host ""

$files = @(
  "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_TRIGGER_PLAN.md",
  "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_TRIGGER_PLAN.csv",
  "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_READ_THESE_FILES.txt"
)

foreach ($f in $files) {
  if (Test-Path $f) {
    Write-Host "OK   $f"
  } else {
    Write-Host "MISS $f"
  }
}

Write-Host ""
Write-Host "=== OPEN V16.3 FILES ==="
Write-Host ""

Start-Process explorer.exe "D:\us-tech-quant\outputs\v16\latest"
Start-Process notepad.exe "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_TRIGGER_PLAN.md"
Start-Process notepad.exe "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_TRIGGER_PLAN.csv"

Write-Host ""
Write-Host "=== V16.3 DONE ==="
Write-Host ""
