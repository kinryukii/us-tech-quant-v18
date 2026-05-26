param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

chcp 65001 | Out-Null

Set-Location -LiteralPath $Root

Write-Host ""
Write-Host "=== RUN V16.1 TIME RISK + FINAL DECISION ==="
Write-Host ""

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
    $python = "python"
}

& $python ".\scripts\run_v16_1_time_risk_final_decision.py" --root $Root

Write-Host ""
Write-Host "=== V16.1 DONE ==="
Write-Host ""
