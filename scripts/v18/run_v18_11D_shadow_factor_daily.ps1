param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$UseYFinance
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

$Start = Get-Date
$FailCount = 0

$OutResearch = Join-Path $Root "outputs\v18\factor_research"
$OutOps = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OutResearch | Out-Null
New-Item -ItemType Directory -Force -Path $OutOps | Out-Null

$Report = Join-Path $OutResearch "V18_11D_CURRENT_SHADOW_FACTOR_DAILY.md"
$ReadFirst = Join-Path $OutResearch "V18_11D_READ_FIRST.txt"
$StepsCsv = Join-Path $OutOps "V18_11D_CURRENT_SHADOW_FACTOR_DAILY_STEPS.csv"

$StepRows = New-Object System.Collections.Generic.List[object]

$Runner = Join-Path $Root "scripts\v18\run_v18_11_calendar_vwap_rv_shadow_factors.ps1"

Write-Host ""
Write-Host "=== V18.11D SHADOW FACTOR DAILY START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SHADOW_ONLY"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_WEIGHT_CHANGE: DISABLED"
Write-Host "AUTO_PROMOTION: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

if (-not (Test-Path $Runner)) {
    throw "MISSING_V18_11_RUNNER: $Runner"
}

$StepStart = Get-Date
$StepStatus = "OK"
$StepNote = "Ran V18.11 calendar/OPEX/RV/VWAP-proxy shadow factor layer."
try {
    $ArgsList = @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $Runner,
        "-Root",
        $Root
    )
    if ($UseYFinance) {
        $ArgsList += "-UseYFinance"
    }

    & powershell @ArgsList
    if ($LASTEXITCODE -ne 0) {
        throw "V18_11_FACTOR_LAYER_FAILED"
    }
}
catch {
    $FailCount += 1
    $StepStatus = "FAIL"
    $StepNote = $_.Exception.Message
}
$StepSeconds = [math]::Round(((Get-Date) - $StepStart).TotalSeconds, 3)
$StepRows.Add([pscustomobject]@{
    step_name = "RUN_V18_11_SHADOW_FACTOR_LAYER"
    status = $StepStatus
    seconds = $StepSeconds
    output_path = Join-Path $OutResearch "V18_11C_READ_FIRST.txt"
    note = $StepNote
}) | Out-Null

$V11ARead = Join-Path $Root "outputs\v18\factor_registry\V18_11A_READ_FIRST.txt"
$V11BRead = Join-Path $Root "outputs\v18\factor_registry\V18_11B_READ_FIRST.txt"
$V11CRead = Join-Path $Root "outputs\v18\factor_research\V18_11C_READ_FIRST.txt"

$FactorCount = Get-ReadFirstValue -Path $V11CRead -Key "FACTOR_COUNT"
$ComputableCount = Get-ReadFirstValue -Path $V11CRead -Key "COMPUTABLE_COUNT"
$ProxyOnlyCount = Get-ReadFirstValue -Path $V11CRead -Key "PROXY_ONLY_COUNT"
$DataUnavailableCount = Get-ReadFirstValue -Path $V11CRead -Key "DATA_UNAVAILABLE_COUNT"
$CandidateRowCount = Get-ReadFirstValue -Path $V11CRead -Key "CANDIDATE_ROW_COUNT"
$YFinanceStatus = Get-ReadFirstValue -Path $V11CRead -Key "YFINANCE_STATUS"

$OfficialDecisionImpact = "NONE"
$AutoWeightChange = "DISABLED"
$AutoPromotion = "DISABLED"
$AutoTrade = "DISABLED"
$StateRegistryModified = "False"
$CandidateTrackerStateModified = "False"
$Mode = "SHADOW_ONLY"
$Status = if ($FailCount -eq 0) { "OK_V18_11D_SHADOW_FACTOR_DAILY_READY" } else { "FAIL_V18_11D_SHADOW_FACTOR_DAILY" }
$TotalSeconds = [math]::Round(((Get-Date) - $Start).TotalSeconds, 3)

$csvLines = New-Object System.Collections.Generic.List[string]
$csvLines.Add("step_name,status,seconds,output_path,note") | Out-Null
foreach ($row in $StepRows) {
    $csvLines.Add(
        ((CsvEscape $row.step_name), (CsvEscape $row.status), (CsvEscape ([string]$row.seconds)), (CsvEscape $row.output_path), (CsvEscape $row.note) -join ",")
    ) | Out-Null
}
$csvLines | Set-Content -Path $StepsCsv -Encoding UTF8

$ReportText = @"
# V18.11D Shadow Factor Daily

- STATUS: `$Status`
- MODE: `$Mode`
- USE_YFINANCE: `$UseYFinance`
- OFFICIAL_DECISION_IMPACT: `$OfficialDecisionImpact`
- AUTO_WEIGHT_CHANGE: `$AutoWeightChange`
- AUTO_PROMOTION: `$AutoPromotion`
- AUTO_TRADE: `$AutoTrade`
- STATE_REGISTRY_MODIFIED: `$StateRegistryModified`
- CANDIDATE_TRACKER_STATE_MODIFIED: `$CandidateTrackerStateModified`
- FACTOR_COUNT: `$FactorCount`
- COMPUTABLE_COUNT: `$ComputableCount`
- PROXY_ONLY_COUNT: `$ProxyOnlyCount`
- DATA_UNAVAILABLE_COUNT: `$DataUnavailableCount`
- CANDIDATE_ROW_COUNT: `$CandidateRowCount`
- YFINANCE_STATUS: `$YFinanceStatus`
- TOTAL_SECONDS: `$TotalSeconds`
- FAIL_COUNT: `$FailCount`

## Outputs

- V18.11A_READ_FIRST: `$V11ARead`
- V18.11B_READ_FIRST: `$V11BRead`
- V18.11C_READ_FIRST: `$V11CRead`
- STEPS_CSV: `$StepsCsv`

## Safety

This wrapper runs only `scripts\v18\run_v18_11_calendar_vwap_rv_shadow_factors.ps1`.
It does not run official daily, shadow research daily, V18.10D, or cleanup delete tools.
"@
$ReportText | Set-Content -Path $Report -Encoding UTF8

$ReadFirstText = @"
V18.11D SHADOW FACTOR DAILY READ FIRST

STATUS:
$Status

MODE:
$Mode

OFFICIAL_DECISION_IMPACT:
$OfficialDecisionImpact

AUTO_WEIGHT_CHANGE:
$AutoWeightChange

AUTO_PROMOTION:
$AutoPromotion

AUTO_TRADE:
$AutoTrade

STATE_REGISTRY_MODIFIED:
$StateRegistryModified

CANDIDATE_TRACKER_STATE_MODIFIED:
$CandidateTrackerStateModified

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

YFINANCE_STATUS:
$YFinanceStatus

TOTAL_SECONDS:
$TotalSeconds

FAIL_COUNT:
$FailCount

REPORT:
$Report

STEPS_CSV:
$StepsCsv
"@
$ReadFirstText | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host "STATUS: $Status"
Write-Host "MODE: $Mode"
Write-Host "OFFICIAL_DECISION_IMPACT: $OfficialDecisionImpact"
Write-Host "AUTO_WEIGHT_CHANGE: $AutoWeightChange"
Write-Host "AUTO_PROMOTION: $AutoPromotion"
Write-Host "AUTO_TRADE: $AutoTrade"
Write-Host "STATE_REGISTRY_MODIFIED: $StateRegistryModified"
Write-Host "CANDIDATE_TRACKER_STATE_MODIFIED: $CandidateTrackerStateModified"
Write-Host "FACTOR_COUNT: $FactorCount"
Write-Host "COMPUTABLE_COUNT: $ComputableCount"
Write-Host "PROXY_ONLY_COUNT: $ProxyOnlyCount"
Write-Host "DATA_UNAVAILABLE_COUNT: $DataUnavailableCount"
Write-Host "CANDIDATE_ROW_COUNT: $CandidateRowCount"
Write-Host "YFINANCE_STATUS: $YFinanceStatus"
Write-Host "TOTAL_SECONDS: $TotalSeconds"
Write-Host "FAIL_COUNT: $FailCount"
Write-Host "REPORT: $Report"
Write-Host "READ_FIRST: $ReadFirst"
Write-Host "STEPS_CSV: $StepsCsv"

Write-Host ""
Write-Host "=== V18.11D SHADOW FACTOR DAILY DONE ==="

if ($FailCount -ne 0) {
    throw "V18_11D_SHADOW_FACTOR_DAILY_FAILED"
}
