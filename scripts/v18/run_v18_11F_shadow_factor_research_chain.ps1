param(
    [string]$Root = "D:\us-tech-quant"
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

    $Lines = Get-Content -Path $Path -Encoding UTF8
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $Line = $Lines[$i].Trim()
        if ($Line -eq $Target) {
            for ($j = $i + 1; $j -lt $Lines.Count; $j++) {
                $Next = $Lines[$j].Trim()
                if ($Next -ne "") {
                    return $Next
                }
            }
        }
        if ($Line.StartsWith($Target)) {
            $Value = $Line.Substring($Target.Length).Trim()
            if ($Value -ne "") {
                return $Value
            }
        }
    }
    return ""
}

function CsvEscape {
    param([string]$Value)
    $Text = [string]$Value
    return '"' + $Text.Replace('"', '""') + '"'
}

function Add-Step {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$StepName,
        [string]$Status,
        [double]$Seconds,
        [string]$OutputPath,
        [string]$Note
    )

    $Rows.Add([pscustomobject]@{
        step_name = $StepName
        status = $Status
        seconds = $Seconds
        output_path = $OutputPath
        note = $Note
    }) | Out-Null
}

$Start = Get-Date
$FailCount = 0
$Mode = "SHADOW_ONLY"
$OfficialDecisionImpact = "NONE"
$AutoWeightChange = "DISABLED"
$AutoPromotion = "DISABLED"
$AutoTrade = "DISABLED"
$OfficialTradingImpact = "NONE"
$StateRegistryModified = "False"
$CandidateTrackerStateModified = "False"
$FactorWeightsModified = "False"

$OutResearch = Join-Path $Root "outputs\v18\factor_research"
$OutOps = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OutResearch | Out-Null
New-Item -ItemType Directory -Force -Path $OutOps | Out-Null

$Report = Join-Path $OutResearch "V18_11F_CURRENT_SHADOW_FACTOR_RESEARCH_CHAIN.md"
$ReadFirst = Join-Path $OutResearch "V18_11F_READ_FIRST.txt"
$StepsCsv = Join-Path $OutOps "V18_11F_CURRENT_SHADOW_FACTOR_RESEARCH_CHAIN_STEPS.csv"

$Runner11D = Join-Path $Root "scripts\v18\run_v18_11D_shadow_factor_daily.ps1"
$Runner11E = Join-Path $Root "scripts\v18\run_v18_11E_shadow_factor_summary.ps1"
$Read11D = Join-Path $OutResearch "V18_11D_READ_FIRST.txt"
$Read11E = Join-Path $OutResearch "V18_11E_READ_FIRST.txt"

$StepRows = New-Object System.Collections.Generic.List[object]

Write-Host ""
Write-Host "=== V18.11F SHADOW FACTOR RESEARCH CHAIN START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $Mode"
Write-Host "OFFICIAL_DECISION_IMPACT: $OfficialDecisionImpact"
Write-Host "AUTO_WEIGHT_CHANGE: $AutoWeightChange"
Write-Host "AUTO_PROMOTION: $AutoPromotion"
Write-Host "AUTO_TRADE: $AutoTrade"
Write-Host "OFFICIAL_TRADING_IMPACT: $OfficialTradingImpact"

if (-not (Test-Path $Runner11D)) {
    throw "MISSING_V18_11D_RUNNER: $Runner11D"
}
if (-not (Test-Path $Runner11E)) {
    throw "MISSING_V18_11E_RUNNER: $Runner11E"
}

$StepStart = Get-Date
$StepStatus = "OK"
$StepNote = "Ran V18.11D shadow factor daily with -UseYFinance."
try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Runner11D -Root $Root -UseYFinance
    if ($LASTEXITCODE -ne 0) {
        throw "V18_11D_FAILED"
    }
}
catch {
    $FailCount += 1
    $StepStatus = "FAIL"
    $StepNote = $_.Exception.Message
}
$StepSeconds = [math]::Round(((Get-Date) - $StepStart).TotalSeconds, 3)
Add-Step -Rows $StepRows -StepName "RUN_V18_11D_SHADOW_FACTOR_DAILY" -Status $StepStatus -Seconds $StepSeconds -OutputPath $Read11D -Note $StepNote

$StepStart = Get-Date
$StepStatus = "OK"
$StepNote = "Ran V18.11E shadow factor summary."
try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Runner11E -Root $Root
    if ($LASTEXITCODE -ne 0) {
        throw "V18_11E_FAILED"
    }
}
catch {
    $FailCount += 1
    $StepStatus = "FAIL"
    $StepNote = $_.Exception.Message
}
$StepSeconds = [math]::Round(((Get-Date) - $StepStart).TotalSeconds, 3)
Add-Step -Rows $StepRows -StepName "RUN_V18_11E_SHADOW_FACTOR_SUMMARY" -Status $StepStatus -Seconds $StepSeconds -OutputPath $Read11E -Note $StepNote

$Status = if ($FailCount -eq 0) { "OK_V18_11F_SHADOW_FACTOR_RESEARCH_CHAIN_READY" } else { "FAIL_V18_11F_SHADOW_FACTOR_RESEARCH_CHAIN" }
$TotalSeconds = [math]::Round(((Get-Date) - $Start).TotalSeconds, 3)

$Status11D = Get-ReadFirstValue -Path $Read11D -Key "STATUS"
$Status11E = Get-ReadFirstValue -Path $Read11E -Key "STATUS"
$FactorCount = Get-ReadFirstValue -Path $Read11D -Key "FACTOR_COUNT"
$ComputableCount = Get-ReadFirstValue -Path $Read11D -Key "COMPUTABLE_COUNT"
$ProxyOnlyCount = Get-ReadFirstValue -Path $Read11D -Key "PROXY_ONLY_COUNT"
$DataUnavailableCount = Get-ReadFirstValue -Path $Read11D -Key "DATA_UNAVAILABLE_COUNT"
$CandidateRowCount = Get-ReadFirstValue -Path $Read11D -Key "CANDIDATE_ROW_COUNT"
$UniqueTickerCount = Get-ReadFirstValue -Path $Read11E -Key "UNIQUE_TICKER_COUNT"
$UniqueTickerBaseDateCount = Get-ReadFirstValue -Path $Read11E -Key "UNIQUE_TICKER_BASE_DATE_COUNT"
$YFinanceStatus = Get-ReadFirstValue -Path $Read11D -Key "YFINANCE_STATUS"
$TopHighRvTickers = Get-ReadFirstValue -Path $Read11E -Key "TOP_HIGH_RV_TICKERS"
$TopPositiveVwapTickers = Get-ReadFirstValue -Path $Read11E -Key "TOP_POSITIVE_VWAP_PROXY_DEVIATION_TICKERS"
$TopNegativeVwapTickers = Get-ReadFirstValue -Path $Read11E -Key "TOP_NEGATIVE_VWAP_PROXY_DEVIATION_TICKERS"
$VwapReclaimCandidates = Get-ReadFirstValue -Path $Read11E -Key "VWAP_RECLAIM_CANDIDATES"
$OpexRaw = Get-ReadFirstValue -Path $Read11E -Key "OPEX_PRESSURE_ACTIVE_RAW_ROW_COUNT"
$OpexUnique = Get-ReadFirstValue -Path $Read11E -Key "OPEX_PRESSURE_ACTIVE_UNIQUE_TICKER_BASE_DATE_COUNT"
$MonthEndActive = Get-ReadFirstValue -Path $Read11E -Key "MONTH_END_ACTIVE_COUNT"
$QuarterEndActive = Get-ReadFirstValue -Path $Read11E -Key "QUARTER_END_ACTIVE_COUNT"
$PostOpexReliefActive = Get-ReadFirstValue -Path $Read11E -Key "POST_OPEX_RELIEF_ACTIVE_COUNT"

$csvLines = New-Object System.Collections.Generic.List[string]
$csvLines.Add("step_name,status,seconds,output_path,note") | Out-Null
foreach ($row in $StepRows) {
    $csvLines.Add(
        ((CsvEscape $row.step_name), (CsvEscape $row.status), (CsvEscape ([string]$row.seconds)), (CsvEscape $row.output_path), (CsvEscape $row.note) -join ",")
    ) | Out-Null
}
$csvLines | Set-Content -Path $StepsCsv -Encoding UTF8

$ReportText = @"
# V18.11F Shadow Factor Research Chain

- STATUS: `$Status`
- MODE: `$Mode`
- TOTAL_SECONDS: `$TotalSeconds`
- FAIL_COUNT: `$FailCount`
- OFFICIAL_DECISION_IMPACT: `$OfficialDecisionImpact`
- AUTO_WEIGHT_CHANGE: `$AutoWeightChange`
- AUTO_PROMOTION: `$AutoPromotion`
- AUTO_TRADE: `$AutoTrade`
- OFFICIAL_TRADING_IMPACT: `$OfficialTradingImpact`
- STATE_REGISTRY_MODIFIED: `$StateRegistryModified`
- CANDIDATE_TRACKER_STATE_MODIFIED: `$CandidateTrackerStateModified`
- FACTOR_WEIGHTS_MODIFIED: `$FactorWeightsModified`
- V18_11D_STATUS: `$Status11D`
- V18_11E_STATUS: `$Status11E`
- FACTOR_COUNT: `$FactorCount`
- COMPUTABLE_COUNT: `$ComputableCount`
- PROXY_ONLY_COUNT: `$ProxyOnlyCount`
- DATA_UNAVAILABLE_COUNT: `$DataUnavailableCount`
- CANDIDATE_ROW_COUNT: `$CandidateRowCount`
- UNIQUE_TICKER_COUNT: `$UniqueTickerCount`
- UNIQUE_TICKER_BASE_DATE_COUNT: `$UniqueTickerBaseDateCount`
- YFINANCE_STATUS: `$YFinanceStatus`

## Research Highlights

- TOP_HIGH_RV_TICKERS: `$TopHighRvTickers`
- TOP_POSITIVE_VWAP_PROXY_DEVIATION_TICKERS: `$TopPositiveVwapTickers`
- TOP_NEGATIVE_VWAP_PROXY_DEVIATION_TICKERS: `$TopNegativeVwapTickers`
- VWAP_RECLAIM_CANDIDATES: `$VwapReclaimCandidates`

## OPEX Warning Summary

- OPEX_PRESSURE_ACTIVE_RAW_ROW_COUNT: `$OpexRaw`
- OPEX_PRESSURE_ACTIVE_UNIQUE_TICKER_BASE_DATE_COUNT: `$OpexUnique`
- MONTH_END_ACTIVE_COUNT: `$MonthEndActive`
- QUARTER_END_ACTIVE_COUNT: `$QuarterEndActive`
- POST_OPEX_RELIEF_ACTIVE_COUNT: `$PostOpexReliefActive`
- OPEX_METHOD: `CALENDAR_PROXY_ONLY; No options chain / OI / IV used`
- VWAP_METHOD: `PROXY_ONLY_DAILY_OHLCV; Not true intraday VWAP`

## Outputs

- V18.11D_READ_FIRST: `$Read11D`
- V18.11E_READ_FIRST: `$Read11E`
- STEPS_CSV: `$StepsCsv`

## Safety

This wrapper runs only V18.11D and V18.11E. It does not run official daily, current shadow research daily, V18.10D, or cleanup delete tools.
"@
$ReportText | Set-Content -Path $Report -Encoding UTF8

$ReadFirstText = @"
V18.11F SHADOW FACTOR RESEARCH CHAIN READ FIRST

STATUS:
$Status

MODE:
$Mode

TOTAL_SECONDS:
$TotalSeconds

FAIL_COUNT:
$FailCount

OFFICIAL_DECISION_IMPACT:
$OfficialDecisionImpact

AUTO_WEIGHT_CHANGE:
$AutoWeightChange

AUTO_PROMOTION:
$AutoPromotion

AUTO_TRADE:
$AutoTrade

OFFICIAL_TRADING_IMPACT:
$OfficialTradingImpact

STATE_REGISTRY_MODIFIED:
$StateRegistryModified

CANDIDATE_TRACKER_STATE_MODIFIED:
$CandidateTrackerStateModified

FACTOR_WEIGHTS_MODIFIED:
$FactorWeightsModified

V18_11D_STATUS:
$Status11D

V18_11E_STATUS:
$Status11E

FACTOR_COUNT:
$FactorCount

COMPUTABLE_COUNT:
$ComputableCount

PROXY_ONLY_COUNT:
$ProxyOnlyCount

DATA_UNAVAILABLE_COUNT:
$DataUnavailableCount

CANDIDATE_ROW_COUNT:
$CandidateRowCount

UNIQUE_TICKER_COUNT:
$UniqueTickerCount

UNIQUE_TICKER_BASE_DATE_COUNT:
$UniqueTickerBaseDateCount

YFINANCE_STATUS:
$YFinanceStatus

TOP_HIGH_RV_TICKERS:
$TopHighRvTickers

TOP_POSITIVE_VWAP_PROXY_DEVIATION_TICKERS:
$TopPositiveVwapTickers

TOP_NEGATIVE_VWAP_PROXY_DEVIATION_TICKERS:
$TopNegativeVwapTickers

VWAP_RECLAIM_CANDIDATES:
$VwapReclaimCandidates

OPEX_PRESSURE_ACTIVE_RAW_ROW_COUNT:
$OpexRaw

OPEX_PRESSURE_ACTIVE_UNIQUE_TICKER_BASE_DATE_COUNT:
$OpexUnique

MONTH_END_ACTIVE_COUNT:
$MonthEndActive

QUARTER_END_ACTIVE_COUNT:
$QuarterEndActive

POST_OPEX_RELIEF_ACTIVE_COUNT:
$PostOpexReliefActive

REPORT:
$Report

STEPS_CSV:
$StepsCsv
"@
$ReadFirstText | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host "STATUS: $Status"
Write-Host "MODE: $Mode"
Write-Host "TOTAL_SECONDS: $TotalSeconds"
Write-Host "FAIL_COUNT: $FailCount"
Write-Host "OFFICIAL_DECISION_IMPACT: $OfficialDecisionImpact"
Write-Host "AUTO_WEIGHT_CHANGE: $AutoWeightChange"
Write-Host "AUTO_PROMOTION: $AutoPromotion"
Write-Host "AUTO_TRADE: $AutoTrade"
Write-Host "OFFICIAL_TRADING_IMPACT: $OfficialTradingImpact"
Write-Host "STATE_REGISTRY_MODIFIED: $StateRegistryModified"
Write-Host "CANDIDATE_TRACKER_STATE_MODIFIED: $CandidateTrackerStateModified"
Write-Host "FACTOR_WEIGHTS_MODIFIED: $FactorWeightsModified"
Write-Host "V18_11D_STATUS: $Status11D"
Write-Host "V18_11E_STATUS: $Status11E"
Write-Host "FACTOR_COUNT: $FactorCount"
Write-Host "COMPUTABLE_COUNT: $ComputableCount"
Write-Host "PROXY_ONLY_COUNT: $ProxyOnlyCount"
Write-Host "DATA_UNAVAILABLE_COUNT: $DataUnavailableCount"
Write-Host "CANDIDATE_ROW_COUNT: $CandidateRowCount"
Write-Host "UNIQUE_TICKER_COUNT: $UniqueTickerCount"
Write-Host "UNIQUE_TICKER_BASE_DATE_COUNT: $UniqueTickerBaseDateCount"
Write-Host "YFINANCE_STATUS: $YFinanceStatus"
Write-Host "REPORT: $Report"
Write-Host "READ_FIRST: $ReadFirst"
Write-Host "STEPS_CSV: $StepsCsv"

Write-Host ""
Write-Host "=== V18.11F SHADOW FACTOR RESEARCH CHAIN DONE ==="

if ($FailCount -ne 0) {
    throw "V18_11F_SHADOW_FACTOR_RESEARCH_CHAIN_FAILED"
}
