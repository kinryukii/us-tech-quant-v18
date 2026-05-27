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

function Invoke-ChildCommand {
    param(
        [string]$Name,
        [string[]]$CommandArgs
    )

    $Start = Get-Date
    Write-Host ""
    Write-Host "=== STEP START: $Name ==="

    try {
        $Output = & powershell @CommandArgs 2>&1
        $ExitCode = $LASTEXITCODE

        foreach ($Line in $Output) {
            Write-Host $Line
        }

        if ($ExitCode -ne 0) {
            throw "Child command failed with exit code $ExitCode"
        }

        $End = Get-Date
        $Seconds = [Math]::Round(($End - $Start).TotalSeconds, 3)
        Write-Host "=== STEP OK: $Name | ${Seconds}s ==="

        return [PSCustomObject]@{
            step = $Name
            status = "OK"
            seconds = $Seconds
            error = ""
        }
    }
    catch {
        $End = Get-Date
        $Seconds = [Math]::Round(($End - $Start).TotalSeconds, 3)
        $ErrText = $_.Exception.Message

        Write-Host "=== STEP FAIL: $Name | ${Seconds}s ==="
        Write-Host $ErrText

        return [PSCustomObject]@{
            step = $Name
            status = "FAIL"
            seconds = $Seconds
            error = $ErrText
        }
    }
}

Write-Host ""
Write-Host "=== V18.10D OFFICIAL DAILY WITH FACTOR + WEIGHT RESEARCH START ==="
Write-Host "ROOT: $Root"
Write-Host "SKIP_OFFICIAL_DAILY: $SkipOfficialDaily"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "MIN_COUNT: $MinCount"
Write-Host "TOP_FRACTION: $TopFraction"

$OutReadCenter = Join-Path $Root "outputs\v18\read_center"
$OutOps = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OutReadCenter | Out-Null
New-Item -ItemType Directory -Force -Path $OutOps | Out-Null

$StepsPath = Join-Path $OutOps "V18_10D_CURRENT_OFFICIAL_DAILY_WITH_FACTOR_WEIGHT_RESEARCH_STEPS.csv"
$ProfilePath = Join-Path $OutOps "V18_10D_CURRENT_OFFICIAL_DAILY_WITH_FACTOR_WEIGHT_RESEARCH_PROFILE.csv"
$ReportPath = Join-Path $OutReadCenter "V18_10D_CURRENT_OFFICIAL_DAILY_WITH_FACTOR_WEIGHT_RESEARCH.md"
$ReadFirstPath = Join-Path $OutReadCenter "V18_10D_READ_FIRST.txt"

$OfficialDaily = Join-Path $Root "scripts\v18\run_v18_current_official_daily.ps1"
$ResearchChain = Join-Path $Root "scripts\v18\run_v18_10C_R1_factor_weight_research_daily_chain.ps1"

foreach ($Required in @($OfficialDaily, $ResearchChain)) {
    if (-not (Test-Path $Required)) {
        throw "Missing required script: $Required"
    }
}

$StepResults = @()

$OfficialArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $OfficialDaily)
if ($SkipOfficialDaily) {
    $OfficialArgs += "-SkipOfficialDaily"
}
if ($UseYFinance) {
    $OfficialArgs += "-UseYFinance"
}

$StepResults += Invoke-ChildCommand "Current official daily wrapper" $OfficialArgs

$ResearchArgs = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $ResearchChain,
    "-MinCount",
    "$MinCount",
    "-TopFraction",
    "$TopFraction"
)

if ($UseYFinance) {
    $ResearchArgs += "-UseYFinance"
}

$StepResults += Invoke-ChildCommand "V18.10C-R1 factor + weight research chain" $ResearchArgs

$StepResults | Export-Csv -Path $StepsPath -NoTypeInformation -Encoding UTF8

$FailCount = @($StepResults | Where-Object { $_.status -ne "OK" }).Count
$TotalSeconds = [Math]::Round((@($StepResults | Measure-Object -Property seconds -Sum).Sum), 3)

$OfficialReadFirstCandidates = @(
    (Join-Path $Root "outputs\v18\read_center\V18_9C_READ_FIRST.txt"),
    (Join-Path $Root "outputs\v18\read_center\V18_8C_READ_FIRST.txt"),
    (Join-Path $Root "outputs\v18\read_center\V18_6E_READ_FIRST.txt")
)

$OfficialReadFirst = ""
foreach ($p in $OfficialReadFirstCandidates) {
    if (Test-Path $p) {
        $OfficialReadFirst = $p
        break
    }
}

$ResearchReadFirst = Join-Path $Root "outputs\v18\weight_research\V18_10C_R1_READ_FIRST.txt"

$OfficialStatus = Get-ReadFirstValue $OfficialReadFirst "STATUS:"
if ($OfficialStatus -eq "") {
    $OfficialStatus = Get-ReadFirstValue $OfficialReadFirst "V18_9C_STATUS:"
}
$FinalAction = Get-ReadFirstValue $OfficialReadFirst "FINAL_ACTION:"
$BuyPermission = Get-ReadFirstValue $OfficialReadFirst "BUY_PERMISSION:"
$VixRegime = Get-ReadFirstValue $OfficialReadFirst "VIX_REGIME:"
$OfficialDecisionImpact = Get-ReadFirstValue $OfficialReadFirst "OFFICIAL_DECISION_IMPACT:"
$SimStatus = Get-ReadFirstValue $OfficialReadFirst "SIM_STATUS:"
$CandidateTrackerStatus = Get-ReadFirstValue $OfficialReadFirst "CANDIDATE_TRACKER_STATUS:"
$ForwardFillerStatusFromOfficial = Get-ReadFirstValue $OfficialReadFirst "FORWARD_FILLER_STATUS:"

$ResearchStatus = Get-ReadFirstValue $ResearchReadFirst "STATUS:"
$ResearchPermission = Get-ReadFirstValue $ResearchReadFirst "RESEARCH_PERMISSION:"
$ForwardStatus = Get-ReadFirstValue $ResearchReadFirst "FORWARD_FILLER_STATUS:"
$YFinanceStatus = Get-ReadFirstValue $ResearchReadFirst "YFINANCE_STATUS:"
$TrackerRows = Get-ReadFirstValue $ResearchReadFirst "TRACKER_ROWS:"
$FilledCells = Get-ReadFirstValue $ResearchReadFirst "FILLED_CELLS_THIS_RUN:"
$PendingCells = Get-ReadFirstValue $ResearchReadFirst "PENDING_CELLS_THIS_RUN:"
$ReadyHorizonCount = Get-ReadFirstValue $ResearchReadFirst "READY_HORIZON_COUNT:"
$TotalLabelNonblank = Get-ReadFirstValue $ResearchReadFirst "TOTAL_LABEL_NONBLANK_COUNT:"
$FactorOkRows = Get-ReadFirstValue $ResearchReadFirst "FACTOR_OK_EVALUATED_ROWS:"
$FactorNoDataRows = Get-ReadFirstValue $ResearchReadFirst "FACTOR_NO_DATA_ROWS:"
$WeightStatus = Get-ReadFirstValue $ResearchReadFirst "WEIGHT_RESEARCH_STATUS:"
$WeightCandidateCount = Get-ReadFirstValue $ResearchReadFirst "WEIGHT_CANDIDATE_COUNT:"
$WeightOkRows = Get-ReadFirstValue $ResearchReadFirst "WEIGHT_OK_EVALUATED_ROWS:"
$WeightNoDataRows = Get-ReadFirstValue $ResearchReadFirst "WEIGHT_NO_DATA_ROWS:"
$WeightPromotionPermission = Get-ReadFirstValue $ResearchReadFirst "WEIGHT_PROMOTION_PERMISSION:"

if ($FailCount -eq 0) {
    $Status = "OK_OFFICIAL_DAILY_WITH_FACTOR_WEIGHT_RESEARCH_READY"
}
else {
    $Status = "FAIL_OFFICIAL_DAILY_WITH_FACTOR_WEIGHT_RESEARCH"
}

$CombinedOfficialImpact = "NONE"
$AutoWeightChange = "DISABLED"
$AutoPromotion = "DISABLED"
$AutoTrade = "DISABLED"

$ProfileRows = @(
    [PSCustomObject]@{ key = "STATUS"; value = $Status },
    [PSCustomObject]@{ key = "TOTAL_SECONDS"; value = $TotalSeconds },
    [PSCustomObject]@{ key = "FAIL_COUNT"; value = $FailCount },
    [PSCustomObject]@{ key = "SKIP_OFFICIAL_DAILY"; value = $SkipOfficialDaily },
    [PSCustomObject]@{ key = "USE_YFINANCE"; value = $UseYFinance },
    [PSCustomObject]@{ key = "OFFICIAL_STATUS"; value = $OfficialStatus },
    [PSCustomObject]@{ key = "FINAL_ACTION"; value = $FinalAction },
    [PSCustomObject]@{ key = "BUY_PERMISSION"; value = $BuyPermission },
    [PSCustomObject]@{ key = "VIX_REGIME"; value = $VixRegime },
    [PSCustomObject]@{ key = "RESEARCH_STATUS"; value = $ResearchStatus },
    [PSCustomObject]@{ key = "RESEARCH_PERMISSION"; value = $ResearchPermission },
    [PSCustomObject]@{ key = "READY_HORIZON_COUNT"; value = $ReadyHorizonCount },
    [PSCustomObject]@{ key = "WEIGHT_CANDIDATE_COUNT"; value = $WeightCandidateCount }
)

$ProfileRows | Export-Csv -Path $ProfilePath -NoTypeInformation -Encoding UTF8

$ReadFirstLines = @(
    "V18.10D OFFICIAL DAILY WITH FACTOR + WEIGHT RESEARCH READ FIRST",
    "",
    "STATUS:",
    $Status,
    "",
    "MODE:",
    "OFFICIAL_DAILY_PLUS_SHADOW_FACTOR_WEIGHT_RESEARCH",
    "",
    "OFFICIAL_DECISION_IMPACT:",
    $CombinedOfficialImpact,
    "",
    "AUTO_WEIGHT_CHANGE:",
    $AutoWeightChange,
    "",
    "AUTO_PROMOTION:",
    $AutoPromotion,
    "",
    "AUTO_TRADE:",
    $AutoTrade,
    "",
    "SKIP_OFFICIAL_DAILY:",
    "$SkipOfficialDaily",
    "",
    "USE_YFINANCE:",
    "$UseYFinance",
    "",
    "TOTAL_SECONDS:",
    "$TotalSeconds",
    "",
    "FAIL_COUNT:",
    "$FailCount",
    "",
    "OFFICIAL_READ_FIRST:",
    "$OfficialReadFirst",
    "",
    "OFFICIAL_STATUS:",
    "$OfficialStatus",
    "",
    "FINAL_ACTION:",
    "$FinalAction",
    "",
    "BUY_PERMISSION:",
    "$BuyPermission",
    "",
    "VIX_REGIME:",
    "$VixRegime",
    "",
    "SIM_STATUS:",
    "$SimStatus",
    "",
    "CANDIDATE_TRACKER_STATUS:",
    "$CandidateTrackerStatus",
    "",
    "OFFICIAL_FORWARD_FILLER_STATUS:",
    "$ForwardFillerStatusFromOfficial",
    "",
    "RESEARCH_READ_FIRST:",
    "$ResearchReadFirst",
    "",
    "RESEARCH_STATUS:",
    "$ResearchStatus",
    "",
    "RESEARCH_PERMISSION:",
    "$ResearchPermission",
    "",
    "FORWARD_FILLER_STATUS:",
    "$ForwardStatus",
    "",
    "YFINANCE_STATUS:",
    "$YFinanceStatus",
    "",
    "TRACKER_ROWS:",
    "$TrackerRows",
    "",
    "FILLED_CELLS_THIS_RUN:",
    "$FilledCells",
    "",
    "PENDING_CELLS_THIS_RUN:",
    "$PendingCells",
    "",
    "READY_HORIZON_COUNT:",
    "$ReadyHorizonCount",
    "",
    "TOTAL_LABEL_NONBLANK_COUNT:",
    "$TotalLabelNonblank",
    "",
    "FACTOR_OK_EVALUATED_ROWS:",
    "$FactorOkRows",
    "",
    "FACTOR_NO_DATA_ROWS:",
    "$FactorNoDataRows",
    "",
    "WEIGHT_RESEARCH_STATUS:",
    "$WeightStatus",
    "",
    "WEIGHT_CANDIDATE_COUNT:",
    "$WeightCandidateCount",
    "",
    "WEIGHT_OK_EVALUATED_ROWS:",
    "$WeightOkRows",
    "",
    "WEIGHT_NO_DATA_ROWS:",
    "$WeightNoDataRows",
    "",
    "WEIGHT_PROMOTION_PERMISSION:",
    "$WeightPromotionPermission",
    "",
    "STEPS:",
    "$StepsPath",
    "",
    "PROFILE:",
    "$ProfilePath",
    "",
    "REPORT:",
    "$ReportPath",
    "",
    "READ_FIRST:",
    "$ReadFirstPath",
    "",
    "NEXT_STEP:",
    "If STATUS is OK, this wrapper can be used as a shadow research extension.",
    "Do not point run_v18_current_official_daily.ps1 here until separately approved.",
    "Do not adjust weights until forward-return labels mature and research rows become OK_EVALUATED."
)

Set-Content -Path $ReadFirstPath -Value $ReadFirstLines -Encoding UTF8

$ReportLines = @(
    "# V18.10D Official Daily With Factor + Weight Research",
    "",
    "Generated: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"),
    "",
    "## 1. Status",
    "",
    "- STATUS: " + $Status,
    "- MODE: OFFICIAL_DAILY_PLUS_SHADOW_FACTOR_WEIGHT_RESEARCH",
    "- OFFICIAL_DECISION_IMPACT: " + $CombinedOfficialImpact,
    "- AUTO_WEIGHT_CHANGE: " + $AutoWeightChange,
    "- AUTO_PROMOTION: " + $AutoPromotion,
    "- AUTO_TRADE: " + $AutoTrade,
    "- TOTAL_SECONDS: " + $TotalSeconds,
    "- FAIL_COUNT: " + $FailCount,
    "",
    "## 2. Official daily",
    "",
    "- OFFICIAL_READ_FIRST: " + $OfficialReadFirst,
    "- OFFICIAL_STATUS: " + $OfficialStatus,
    "- FINAL_ACTION: " + $FinalAction,
    "- BUY_PERMISSION: " + $BuyPermission,
    "- VIX_REGIME: " + $VixRegime,
    "- SIM_STATUS: " + $SimStatus,
    "",
    "## 3. Shadow factor + weight research",
    "",
    "- RESEARCH_READ_FIRST: " + $ResearchReadFirst,
    "- RESEARCH_STATUS: " + $ResearchStatus,
    "- RESEARCH_PERMISSION: " + $ResearchPermission,
    "- FORWARD_FILLER_STATUS: " + $ForwardStatus,
    "- YFINANCE_STATUS: " + $YFinanceStatus,
    "- TRACKER_ROWS: " + $TrackerRows,
    "- FILLED_CELLS_THIS_RUN: " + $FilledCells,
    "- PENDING_CELLS_THIS_RUN: " + $PendingCells,
    "- READY_HORIZON_COUNT: " + $ReadyHorizonCount,
    "- FACTOR_OK_EVALUATED_ROWS: " + $FactorOkRows,
    "- FACTOR_NO_DATA_ROWS: " + $FactorNoDataRows,
    "- WEIGHT_RESEARCH_STATUS: " + $WeightStatus,
    "- WEIGHT_CANDIDATE_COUNT: " + $WeightCandidateCount,
    "- WEIGHT_PROMOTION_PERMISSION: " + $WeightPromotionPermission,
    "",
    "## 4. Guardrail",
    "",
    "The factor + weight research chain is shadow-only. It cannot change official daily decisions or weights.",
    "",
    "## 5. Step results",
    "",
    "| step | status | seconds | error |",
    "|---|---|---:|---|"
)

foreach ($s in $StepResults) {
    $safeErr = "$($s.error)".Replace("|", "/")
    $ReportLines += "| $($s.step) | $($s.status) | $($s.seconds) | $safeErr |"
}

$ReportLines += @(
    "",
    "## 6. Outputs",
    "",
    "- STEPS: " + $StepsPath,
    "- PROFILE: " + $ProfilePath,
    "- REPORT: " + $ReportPath,
    "- READ_FIRST: " + $ReadFirstPath
)

Set-Content -Path $ReportPath -Value $ReportLines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.10D OFFICIAL DAILY WITH FACTOR + WEIGHT RESEARCH READY ==="
Write-Host "STATUS: $Status"
Write-Host "MODE: OFFICIAL_DAILY_PLUS_SHADOW_FACTOR_WEIGHT_RESEARCH"
Write-Host "OFFICIAL_DECISION_IMPACT: $CombinedOfficialImpact"
Write-Host "AUTO_WEIGHT_CHANGE: $AutoWeightChange"
Write-Host "AUTO_PROMOTION: $AutoPromotion"
Write-Host "AUTO_TRADE: $AutoTrade"
Write-Host "TOTAL_SECONDS: $TotalSeconds"
Write-Host "FAIL_COUNT: $FailCount"
Write-Host "OFFICIAL_STATUS: $OfficialStatus"
Write-Host "FINAL_ACTION: $FinalAction"
Write-Host "BUY_PERMISSION: $BuyPermission"
Write-Host "VIX_REGIME: $VixRegime"
Write-Host "RESEARCH_STATUS: $ResearchStatus"
Write-Host "RESEARCH_PERMISSION: $ResearchPermission"
Write-Host "FORWARD_FILLER_STATUS: $ForwardStatus"
Write-Host "YFINANCE_STATUS: $YFinanceStatus"
Write-Host "READY_HORIZON_COUNT: $ReadyHorizonCount"
Write-Host "FACTOR_OK_EVALUATED_ROWS: $FactorOkRows"
Write-Host "WEIGHT_RESEARCH_STATUS: $WeightStatus"
Write-Host "WEIGHT_CANDIDATE_COUNT: $WeightCandidateCount"
Write-Host "WEIGHT_PROMOTION_PERMISSION: $WeightPromotionPermission"
Write-Host "STEPS: $StepsPath"
Write-Host "PROFILE: $ProfilePath"
Write-Host "REPORT: $ReportPath"
Write-Host "READ_FIRST: $ReadFirstPath"
Write-Host ""

if ($FailCount -gt 0) {
    throw "V18.10D completed with failing step(s). Check: $StepsPath"
}
