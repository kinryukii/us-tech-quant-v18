param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$SkipBaseCommandCenter,
    [switch]$RunSingleTickerExplainer,
    [string]$ExplainTicker = "",
    [int]$ExplainNeighborWindow = 3,
    [switch]$RunTopNRankingExplainer,
    [int]$TopNRankingExplainerCount = 20,
    [int]$TopNRankingExplainerNeighborWindow = 2,
    [switch]$RunDailyOperatorHomepageV2,
    [ValidateSet("Rolling", "Full")]
    [string]$RefreshMode = "Rolling"
)

$ErrorActionPreference = "Stop"

Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Missing Python executable: $Python"
}

$StepResults = @()

function Invoke-PipelineStep {
    param(
        [string]$Name,
        [string]$Script,
        [string[]]$Arguments = @(),
        [bool]$Required = $true
    )
    Write-Host ""
    Write-Host "=== V18.41A STEP: $Name ==="
    Write-Host "SCRIPT: $Script"
    if (-not (Test-Path $Script)) {
        $Status = if ($Required) { "FAIL_REQUIRED_MISSING" } else { "SKIPPED_OPTIONAL_MISSING" }
        Write-Host "STEP_STATUS: $Status"
        $script:StepResults += [pscustomobject]@{ step = $Name; status = $Status; exit_code = ""; required = $Required }
        if ($Required) { throw "Missing required step wrapper: $Script" }
        return
    }

    & powershell -NoProfile -ExecutionPolicy Bypass -File $Script @Arguments
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        $Status = if ($Required) { "FAIL_REQUIRED_NONZERO_$ExitCode" } else { "WARN_OPTIONAL_NONZERO_$ExitCode" }
        Write-Host "STEP_STATUS: $Status"
        $script:StepResults += [pscustomobject]@{ step = $Name; status = $Status; exit_code = $ExitCode; required = $Required }
        if ($Required) { exit $ExitCode }
    }
    else {
        Write-Host "STEP_STATUS: OK"
        $script:StepResults += [pscustomobject]@{ step = $Name; status = "OK"; exit_code = 0; required = $Required }
    }
}

Write-Host "=== START V18.41A DAILY CLEAN OPERATOR PIPELINE ==="
Write-Host "ROOT: $Root"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "BROKER_API_USED: FALSE"
Write-Host "ORDER_EXECUTION_USED: FALSE"
Write-Host "REFRESH_MODE: $RefreshMode"

if (-not $SkipBaseCommandCenter) {
    Invoke-PipelineStep `
        -Name "Optional base current daily command center read-center refresh" `
        -Script (Join-Path $Root "scripts\v18\run_v18_current_daily_command_center.ps1") `
        -Arguments @("-ReadCenterRefreshOnly") `
        -Required $false
}

Invoke-PipelineStep -Name "V18.35F next signal freeze expansion apply" -Script (Join-Path $Root "scripts\v18\run_v18_35F_next_signal_freeze_expansion.ps1") -Arguments @("-Root", $Root, "-ApplyNextSignalFreezeExpansion") -Required $true
Invoke-PipelineStep -Name "V18.40A candidate top/full canonical sync apply" -Script (Join-Path $Root "scripts\v18\run_v18_40A_candidate_top_full_canonical_sync.ps1") -Arguments @("-Root", $Root, "-ApplyCandidateTopFullCanonicalSync") -Required $true
Invoke-PipelineStep -Name "V18.39A alpha signal object layer" -Script (Join-Path $Root "scripts\v18\run_v18_39A_alpha_signal_object_layer.ps1") -Arguments @("-Root", $Root) -Required $true
if ($RunSingleTickerExplainer) {
    if ([string]::IsNullOrWhiteSpace($ExplainTicker)) {
        Write-Host "SKIPPED_V18_42A_SINGLE_TICKER_EXPLAINER_NO_TICKER"
    }
    else {
        Invoke-PipelineStep -Name "Optional V18.42A single ticker ranking explainer" -Script (Join-Path $Root "scripts\v18\run_v18_42A_single_ticker_ranking_explainer.ps1") -Arguments @("-Root", $Root, "-Ticker", $ExplainTicker, "-NeighborWindow", [string]$ExplainNeighborWindow, "-WriteCurrent") -Required $false
    }
}
if ($RunTopNRankingExplainer) {
    Invoke-PipelineStep -Name "Optional V18.43A Top-N ranking explainer packet" -Script (Join-Path $Root "scripts\v18\run_v18_43A_topn_ranking_explainer_packet.ps1") -Arguments @("-Root", $Root, "-TopN", [string]$TopNRankingExplainerCount, "-NeighborWindow", [string]$TopNRankingExplainerNeighborWindow, "-WriteCurrent", "-IncludeSingleTickerHints") -Required $false
}
Invoke-PipelineStep -Name "V18.45A ranked candidate freshness audit" -Script (Join-Path $Root "scripts\v18\run_v18_45A_current_ranked_candidate_freshness_audit.ps1") -Arguments @("-Root", $Root, "-RefreshMode", $RefreshMode) -Required $false
Invoke-PipelineStep -Name "V18.39B portfolio target preview" -Script (Join-Path $Root "scripts\v18\run_v18_39B_portfolio_target_preview.ps1") -Arguments @("-Root", $Root) -Required $false
Invoke-PipelineStep -Name "V18.39C shadow risk model preview" -Script (Join-Path $Root "scripts\v18\run_v18_39C_shadow_risk_model_preview.ps1") -Arguments @("-Root", $Root) -Required $false
Invoke-PipelineStep -Name "V18.38C-R1 command status normalization" -Script (Join-Path $Root "scripts\v18\run_v18_38C_command_center_status_normalization.ps1") -Arguments @("-Root", $Root) -Required $false
Invoke-PipelineStep -Name "V18.40B current warning cleanup status contract" -Script (Join-Path $Root "scripts\v18\run_v18_40B_current_warning_cleanup_status_contract.ps1") -Arguments @("-Root", $Root) -Required $true
Invoke-PipelineStep -Name "V18.40C fixable current warning reducer apply" -Script (Join-Path $Root "scripts\v18\run_v18_40C_fixable_current_warning_reducer.ps1") -Arguments @("-Root", $Root, "-ApplyFixableCurrentWarningReducer") -Required $true
Invoke-PipelineStep -Name "V18.40D residual action warning resolver apply" -Script (Join-Path $Root "scripts\v18\run_v18_40D_residual_action_warning_resolver.ps1") -Arguments @("-Root", $Root, "-ApplyResidualActionWarningResolver") -Required $true
Invoke-PipelineStep -Name "Optional Chinese homepage refresh" -Script (Join-Path $Root "scripts\v18\run_v18_33A_chinese_daily_operator_homepage.ps1") -Arguments @("-Root", $Root) -Required $false
Invoke-PipelineStep -Name "Optional daily readability refresh" -Script (Join-Path $Root "scripts\v18\run_v18_19A_daily_readability_refactor.ps1") -Arguments @("-Root", $Root) -Required $false

Write-Host ""
Write-Host "=== V18.41A STEP SUMMARY ==="
$StepResults | Format-Table -AutoSize

Write-Host ""
Write-Host "=== V18.41A FINAL SUMMARY GENERATION ==="
$SummaryScript = Join-Path $Root "scripts\v18\v18_41A_daily_clean_operator_pipeline_summary.py"
& $Python $SummaryScript --root $Root
$SummaryExit = $LASTEXITCODE

$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_41A_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.41A READ_FIRST ---"
    Get-Content $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($RunDailyOperatorHomepageV2) {
    if ($SummaryExit -ne 0) {
        Write-Host "SKIPPED_V18_44A_DAILY_OPERATOR_HOMEPAGE_SUMMARY_FAILED"
    }
    else {
        $HomepageArgs = @("-Root", $Root, "-WriteCurrent", "-IncludeFileChecklist", "-IncludeWarningDetails")
        if ($RunTopNRankingExplainer) {
            $HomepageArgs += "-RequireTopNCurrent"
        }
        Invoke-PipelineStep -Name "Optional V18.44A daily operator homepage V2" -Script (Join-Path $Root "scripts\v18\run_v18_44A_daily_operator_homepage_consolidation.ps1") -Arguments $HomepageArgs -Required $false
    }
}

Write-Host "V18_41A_READ_FIRST: $ReadFirst"
Write-Host "V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS: $Report"
Write-Host "=== DONE V18.41A DAILY CLEAN OPERATOR PIPELINE ==="

exit $SummaryExit
