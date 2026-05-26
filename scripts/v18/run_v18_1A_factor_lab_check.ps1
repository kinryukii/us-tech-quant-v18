$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"

$Files = @(
    "$Root\state\v18\factor_registry.csv",
    "$Root\state\v18\factor_promotion_policy.json",
    "$Root\configs\v18\v18_module_map.json",
    "$Root\outputs\v18\factor_lab\V18_1A_QUANT_FRAMEWORK_ARCHITECTURE.md",
    "$Root\outputs\v18\factor_lab\V18_1A_FACTOR_LAB_READ_FIRST.txt"
)

Write-Host ""
Write-Host "=== V18.1A FACTOR LAB CHECK START ==="
Write-Host ""

$Missing = @()

foreach ($File in $Files) {
    if (Test-Path $File) {
        Write-Host "OK: $File"
    } else {
        Write-Host "MISSING: $File"
        $Missing += $File
    }
}

Write-Host ""

if ($Missing.Count -eq 0) {
    Write-Host "V18_1A_STATUS: OK_FACTOR_LAB_BOOTSTRAP_READY"
    Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
    Write-Host ""
    Write-Host "READ_FIRST: $Root\outputs\v18\factor_lab\V18_1A_FACTOR_LAB_READ_FIRST.txt"
    Write-Host "ARCHITECTURE: $Root\outputs\v18\factor_lab\V18_1A_QUANT_FRAMEWORK_ARCHITECTURE.md"
    Write-Host "NEXT_STEP: V18.1B_FACTOR_VALUE_COMPUTE_SHADOW_ONLY"
} else {
    Write-Host "V18_1A_STATUS: FAIL_MISSING_FILES"
    Write-Host "MISSING_COUNT: $($Missing.Count)"
    exit 1
}

Write-Host ""
Write-Host "=== V18.1A FACTOR LAB CHECK DONE ==="
