param(
    [switch]$SkipUpstream
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"

$UpstreamWrapper = Join-Path $Root "scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1"
$PromotionMergeWrapper = Join-Path $Root "scripts\v18\run_v18_4I_backtest_forward_promotion_merge.ps1"

$DailyOutDir = Join-Path $Root "outputs\v18\daily_integrated"
$PromotionOutDir = Join-Path $Root "outputs\v18\promotion_merge"

New-Item -ItemType Directory -Force -Path $DailyOutDir | Out-Null
New-Item -ItemType Directory -Force -Path $PromotionOutDir | Out-Null

$ReadFirst = Join-Path $DailyOutDir "V18_4I_R1_READ_FIRST.txt"
$PromotionReadFirst = Join-Path $PromotionOutDir "V18_4I_READ_FIRST.txt"
$PromotionReport = Join-Path $PromotionOutDir "V18_4I_CURRENT_BACKTEST_FORWARD_PROMOTION_REPORT.md"
$PromotionCurrent = Join-Path $PromotionOutDir "V18_CURRENT_BACKTEST_FORWARD_PROMOTION.md"
$IntegratedCurrent = Join-Path $DailyOutDir "V18_CURRENT_FINAL_DAILY_PROMOTION_MERGE.md"

Write-Host ""
Write-Host "=== V18.4I-R1 FINAL DAILY PROMOTION MERGE WRAPPER START ==="

if (!(Test-Path $PromotionMergeWrapper)) {
    throw "Missing V18.4I merge wrapper: $PromotionMergeWrapper"
}

if ($SkipUpstream) {
    Write-Host ""
    Write-Host "STEP 1: skipped upstream wrapper by -SkipUpstream"
}
else {
    if (!(Test-Path $UpstreamWrapper)) {
        throw "Missing upstream V18.4G-R1 wrapper: $UpstreamWrapper"
    }

    Write-Host ""
    Write-Host "STEP 1: run upstream V18.4G-R1 final daily factor audit wrapper"

    powershell -NoProfile -ExecutionPolicy Bypass -File $UpstreamWrapper

    if ($LASTEXITCODE -ne 0) {
        throw "Upstream V18.4G-R1 wrapper failed with exit code $LASTEXITCODE"
    }
}

Write-Host ""
Write-Host "STEP 2: run V18.4I backtest-forward promotion merge"

powershell -NoProfile -ExecutionPolicy Bypass -File $PromotionMergeWrapper

if ($LASTEXITCODE -ne 0) {
    throw "V18.4I promotion merge failed with exit code $LASTEXITCODE"
}

if (!(Test-Path $PromotionReadFirst)) {
    throw "Missing V18.4I read first output: $PromotionReadFirst"
}

if (!(Test-Path $PromotionReport)) {
    throw "Missing V18.4I promotion report: $PromotionReport"
}

if (!(Test-Path $PromotionCurrent)) {
    throw "Missing V18 current promotion report: $PromotionCurrent"
}

$PromotionReadText = Get-Content $PromotionReadFirst -Raw -Encoding UTF8
$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$ReadFirstLines = @()
$ReadFirstLines += "V18_4I_R1_STATUS: OK_FINAL_DAILY_PROMOTION_MERGE_READY"
$ReadFirstLines += "GENERATED_AT: $Now"
$ReadFirstLines += ""
$ReadFirstLines += "FINAL_DAILY_COMMAND:"
$ReadFirstLines += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"'
$ReadFirstLines += ""
$ReadFirstLines += "UPSTREAM_WRAPPER: $UpstreamWrapper"
$ReadFirstLines += "PROMOTION_MERGE_WRAPPER: $PromotionMergeWrapper"
$ReadFirstLines += ""
$ReadFirstLines += "OFFICIAL_DECISION_IMPACT: NONE"
$ReadFirstLines += "PROMOTION_ACTION: NONE"
$ReadFirstLines += "DIRECT_PROMOTION: NO"
$ReadFirstLines += ""
$ReadFirstLines += "V18_4I_PROMOTION_READ_FIRST: $PromotionReadFirst"
$ReadFirstLines += "V18_4I_PROMOTION_REPORT: $PromotionReport"
$ReadFirstLines += "V18_CURRENT_BACKTEST_FORWARD_PROMOTION: $PromotionCurrent"
$ReadFirstLines += "INTEGRATED_CURRENT: $IntegratedCurrent"
$ReadFirstLines += ""
$ReadFirstLines += "PROMOTION_CONTEXT:"
$ReadFirstLines += $PromotionReadText

Set-Content -Path $ReadFirst -Value $ReadFirstLines -Encoding UTF8

$IntegratedLines = @()
$IntegratedLines += "# V18.4I-R1 Final Daily Promotion Merge"
$IntegratedLines += ""
$IntegratedLines += "Generated at: $Now"
$IntegratedLines += ""
$IntegratedLines += "## 1. Status"
$IntegratedLines += ""
$IntegratedLines += "- V18_4I_R1_STATUS: OK_FINAL_DAILY_PROMOTION_MERGE_READY"
$IntegratedLines += "- DIRECT_PROMOTION: NO"
$IntegratedLines += "- OFFICIAL_DECISION_IMPACT: NONE"
$IntegratedLines += "- PROMOTION_ACTION: NONE"
$IntegratedLines += ""
$IntegratedLines += "## 2. Final Daily Command"
$IntegratedLines += ""
$IntegratedLines += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"'
$IntegratedLines += ""
$IntegratedLines += "## 3. Run Chain"
$IntegratedLines += ""
$IntegratedLines += "V18.4G-R1 final daily factor audit wrapper"
$IntegratedLines += "-> V18.4I backtest-forward promotion merge"
$IntegratedLines += "-> V18.4I-R1 final daily promotion summary"
$IntegratedLines += ""
$IntegratedLines += "## 4. Promotion Conclusion"
$IntegratedLines += ""
$IntegratedLines += "F007_PULLBACK_IN_UPTREND:"
$IntegratedLines += "- CORE_ALPHA_WATCH"
$IntegratedLines += "- STRONG_ALPHA"
$IntegratedLines += "- VERY_HIGH_DRAWDOWN_RISK"
$IntegratedLines += "- NOT_PROMOTED_DD_AND_FORWARD_BLOCKED"
$IntegratedLines += ""
$IntegratedLines += "F009_VOLUME_PRICE_CONFIRM:"
$IntegratedLines += "- PRIMARY_CONFIRMATION_WATCH"
$IntegratedLines += "- HIGH_ALPHA"
$IntegratedLines += "- HIGH_DRAWDOWN_RISK"
$IntegratedLines += "- NOT_PROMOTED_DD_AND_FORWARD_BLOCKED"
$IntegratedLines += ""
$IntegratedLines += "F010 / F011 / F008 / F006:"
$IntegratedLines += "- AUXILIARY_EVIDENCE_ONLY"
$IntegratedLines += ""
$IntegratedLines += "## 5. Risk Control Conclusion"
$IntegratedLines += ""
$IntegratedLines += "No factor is allowed to bypass:"
$IntegratedLines += "- event gate"
$IntegratedLines += "- budget lock"
$IntegratedLines += "- behavior guard"
$IntegratedLines += "- official daily decision"
$IntegratedLines += "- position cap"
$IntegratedLines += ""
$IntegratedLines += "Therefore:"
$IntegratedLines += "- OFFICIAL_DECISION_IMPACT: NONE"
$IntegratedLines += "- PROMOTION_ACTION: NONE"
$IntegratedLines += "- DIRECT_PROMOTION: NO"
$IntegratedLines += ""
$IntegratedLines += "## 6. Read Files"
$IntegratedLines += ""
$IntegratedLines += "- Read first: $ReadFirst"
$IntegratedLines += "- Promotion report: $PromotionReport"
$IntegratedLines += "- Current promotion: $PromotionCurrent"

Set-Content -Path $IntegratedCurrent -Value $IntegratedLines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4I-R1 FINAL DAILY PROMOTION MERGE WRAPPER READY ==="
Write-Host "V18_4I_R1_STATUS: OK_FINAL_DAILY_PROMOTION_MERGE_READY"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "PROMOTION_ACTION: NONE"
Write-Host "DIRECT_PROMOTION: NO"
Write-Host "READ_FIRST: $ReadFirst"
Write-Host "INTEGRATED_CURRENT: $IntegratedCurrent"
Write-Host "PROMOTION_CURRENT: $PromotionCurrent"

Write-Host ""
Write-Host "=== V18.4I-R1 FINAL DAILY PROMOTION MERGE WRAPPER DONE ==="