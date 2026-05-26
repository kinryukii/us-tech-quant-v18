param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$SkipOfficialDaily,
    [switch]$UseYFinance,
    [int]$MinCount = 20,
    [double]$TopFraction = 0.30
)

$ErrorActionPreference = "Stop"

function Get-ReadFirstValue {
    param(
        [string]$Path,
        [string]$Key
    )

    if (-not (Test-Path $Path)) {
        return ""
    }

    $Target = $Key.Trim()
    if (-not $Target.EndsWith(":")) {
        $Target = $Target + ":"
    }

    $Lines = Get-Content $Path -Encoding UTF8

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $Line = $Lines[$i].Trim()

        if ($Line.StartsWith($Target)) {
            $Value = $Line.Substring($Target.Length).Trim()
            if ($Value -ne "") {
                return $Value
            }
        }

        if ($Line -eq $Target) {
            for ($j = $i + 1; $j -lt $Lines.Count; $j++) {
                $Next = $Lines[$j].Trim()
                if ($Next -ne "") {
                    return $Next
                }
            }
        }
    }

    return ""
}

Write-Host ""
Write-Host "=== V18 CURRENT SHADOW RESEARCH DAILY ENTRY ==="
Write-Host "ROOT: $Root"
Write-Host "SKIP_OFFICIAL_DAILY: $SkipOfficialDaily"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "MIN_COUNT: $MinCount"
Write-Host "TOP_FRACTION: $TopFraction"

$Target = Join-Path $Root "scripts\v18\run_v18_10D_official_daily_with_factor_weight_research.ps1"

if (-not (Test-Path $Target)) {
    throw "Missing V18.10D wrapper: $Target"
}

$ArgsList = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $Target,
    "-MinCount",
    "$MinCount",
    "-TopFraction",
    "$TopFraction"
)

if ($SkipOfficialDaily) {
    $ArgsList += "-SkipOfficialDaily"
}

if ($UseYFinance) {
    $ArgsList += "-UseYFinance"
}

& powershell @ArgsList

if ($LASTEXITCODE -ne 0) {
    throw "V18_CURRENT_SHADOW_RESEARCH_DAILY_FAILED"
}

$SourceReadFirst = Join-Path $Root "outputs\v18\read_center\V18_10D_READ_FIRST.txt"
$OutReadCenter = Join-Path $Root "outputs\v18\read_center"
New-Item -ItemType Directory -Force -Path $OutReadCenter | Out-Null

$CurrentReadFirst = Join-Path $OutReadCenter "V18_CURRENT_SHADOW_RESEARCH_DAILY_READ_FIRST.txt"
$CurrentReport = Join-Path $OutReadCenter "V18_CURRENT_SHADOW_RESEARCH_DAILY.md"

$Status = Get-ReadFirstValue $SourceReadFirst "STATUS:"
$OfficialImpact = Get-ReadFirstValue $SourceReadFirst "OFFICIAL_DECISION_IMPACT:"
$AutoWeight = Get-ReadFirstValue $SourceReadFirst "AUTO_WEIGHT_CHANGE:"
$AutoPromotion = Get-ReadFirstValue $SourceReadFirst "AUTO_PROMOTION:"
$AutoTrade = Get-ReadFirstValue $SourceReadFirst "AUTO_TRADE:"
$FinalAction = Get-ReadFirstValue $SourceReadFirst "FINAL_ACTION:"
$BuyPermission = Get-ReadFirstValue $SourceReadFirst "BUY_PERMISSION:"
$VixRegime = Get-ReadFirstValue $SourceReadFirst "VIX_REGIME:"
$ResearchStatus = Get-ReadFirstValue $SourceReadFirst "RESEARCH_STATUS:"
$ResearchPermission = Get-ReadFirstValue $SourceReadFirst "RESEARCH_PERMISSION:"
$ReadyHorizonCount = Get-ReadFirstValue $SourceReadFirst "READY_HORIZON_COUNT:"
$FactorOkRows = Get-ReadFirstValue $SourceReadFirst "FACTOR_OK_EVALUATED_ROWS:"
$WeightOkRows = Get-ReadFirstValue $SourceReadFirst "WEIGHT_OK_EVALUATED_ROWS:"
$WeightPromotionPermission = Get-ReadFirstValue $SourceReadFirst "WEIGHT_PROMOTION_PERMISSION:"

$ReadFirstLines = @(
    "V18 CURRENT SHADOW RESEARCH DAILY READ FIRST",
    "",
    "STATUS:",
    $Status,
    "",
    "ENTRY_MODE:",
    "INDEPENDENT_SHADOW_RESEARCH_DAILY_ENTRY",
    "",
    "TARGET:",
    $Target,
    "",
    "IMPORTANT:",
    "This entry does not replace run_v18_current_official_daily.ps1.",
    "",
    "OFFICIAL_DECISION_IMPACT:",
    $OfficialImpact,
    "",
    "AUTO_WEIGHT_CHANGE:",
    $AutoWeight,
    "",
    "AUTO_PROMOTION:",
    $AutoPromotion,
    "",
    "AUTO_TRADE:",
    $AutoTrade,
    "",
    "FINAL_ACTION:",
    $FinalAction,
    "",
    "BUY_PERMISSION:",
    $BuyPermission,
    "",
    "VIX_REGIME:",
    $VixRegime,
    "",
    "RESEARCH_STATUS:",
    $ResearchStatus,
    "",
    "RESEARCH_PERMISSION:",
    $ResearchPermission,
    "",
    "READY_HORIZON_COUNT:",
    $ReadyHorizonCount,
    "",
    "FACTOR_OK_EVALUATED_ROWS:",
    $FactorOkRows,
    "",
    "WEIGHT_OK_EVALUATED_ROWS:",
    $WeightOkRows,
    "",
    "WEIGHT_PROMOTION_PERMISSION:",
    $WeightPromotionPermission,
    "",
    "SOURCE_READ_FIRST:",
    $SourceReadFirst,
    "",
    "CURRENT_READ_FIRST:",
    $CurrentReadFirst,
    "",
    "CURRENT_REPORT:",
    $CurrentReport,
    "",
    "DAILY_COMMAND:",
    "powershell -NoProfile -ExecutionPolicy Bypass -File `"D:\us-tech-quant\scripts\v18\run_v18_current_shadow_research_daily.ps1`" -UseYFinance"
)

Set-Content -Path $CurrentReadFirst -Value $ReadFirstLines -Encoding UTF8

$ReportLines = @(
    "# V18 Current Shadow Research Daily",
    "",
    "Generated: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"),
    "",
    "## Status",
    "",
    "- STATUS: " + $Status,
    "- ENTRY_MODE: INDEPENDENT_SHADOW_RESEARCH_DAILY_ENTRY",
    "- TARGET: " + $Target,
    "- OFFICIAL_DECISION_IMPACT: " + $OfficialImpact,
    "- AUTO_WEIGHT_CHANGE: " + $AutoWeight,
    "- AUTO_PROMOTION: " + $AutoPromotion,
    "- AUTO_TRADE: " + $AutoTrade,
    "",
    "## Official decision",
    "",
    "- FINAL_ACTION: " + $FinalAction,
    "- BUY_PERMISSION: " + $BuyPermission,
    "- VIX_REGIME: " + $VixRegime,
    "",
    "## Shadow research",
    "",
    "- RESEARCH_STATUS: " + $ResearchStatus,
    "- RESEARCH_PERMISSION: " + $ResearchPermission,
    "- READY_HORIZON_COUNT: " + $ReadyHorizonCount,
    "- FACTOR_OK_EVALUATED_ROWS: " + $FactorOkRows,
    "- WEIGHT_OK_EVALUATED_ROWS: " + $WeightOkRows,
    "- WEIGHT_PROMOTION_PERMISSION: " + $WeightPromotionPermission,
    "",
    "## Guardrail",
    "",
    "This wrapper is an independent shadow research entry. It does not replace the official daily entry.",
    "",
    "## Outputs",
    "",
    "- SOURCE_READ_FIRST: " + $SourceReadFirst,
    "- CURRENT_READ_FIRST: " + $CurrentReadFirst
)

Set-Content -Path $CurrentReport -Value $ReportLines -Encoding UTF8

Write-Host ""
Write-Host "=== V18 CURRENT SHADOW RESEARCH DAILY READY ==="
Write-Host "STATUS: $Status"
Write-Host "ENTRY_MODE: INDEPENDENT_SHADOW_RESEARCH_DAILY_ENTRY"
Write-Host "OFFICIAL_DECISION_IMPACT: $OfficialImpact"
Write-Host "AUTO_WEIGHT_CHANGE: $AutoWeight"
Write-Host "AUTO_PROMOTION: $AutoPromotion"
Write-Host "AUTO_TRADE: $AutoTrade"
Write-Host "FINAL_ACTION: $FinalAction"
Write-Host "BUY_PERMISSION: $BuyPermission"
Write-Host "VIX_REGIME: $VixRegime"
Write-Host "RESEARCH_STATUS: $ResearchStatus"
Write-Host "RESEARCH_PERMISSION: $ResearchPermission"
Write-Host "READY_HORIZON_COUNT: $ReadyHorizonCount"
Write-Host "FACTOR_OK_EVALUATED_ROWS: $FactorOkRows"
Write-Host "WEIGHT_OK_EVALUATED_ROWS: $WeightOkRows"
Write-Host "WEIGHT_PROMOTION_PERMISSION: $WeightPromotionPermission"
Write-Host "READ_FIRST: $CurrentReadFirst"
Write-Host "REPORT: $CurrentReport"
Write-Host ""
