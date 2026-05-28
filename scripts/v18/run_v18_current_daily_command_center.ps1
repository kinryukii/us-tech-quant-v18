param(
    [ValidateSet("Rolling", "Full")]
    [string]$RefreshMode = "Rolling",
    [switch]$UseYFinance,
    [switch]$FullDaily,
    [switch]$ReadCenterRefreshOnly,
    [switch]$ValidateOnly,
    [switch]$RunForwardTracker,
    [switch]$RunManualFeedback,
    [switch]$RunTradeReadinessRefresh,
    [switch]$RunChineseHomepage,
    [switch]$RunFreshnessGuard,
    [switch]$RunLegacyChineseHomepage,
    [switch]$RunLegacyDailyOutputFreshnessGuard,
    [switch]$RunCandidateSourceNormalization,
    [switch]$ApplyCandidateCanonicalAliasRepair,
    [switch]$RunCandidateSourceDependencyReview,
    [switch]$ApplyCandidateSourceDependencyPatches,
    [switch]$RunFullUniverseFactorTechnicalRecompute,
    [switch]$UseYFinanceForFullUniverseRecompute,
    [switch]$ApplyFullUniverseRecomputedCandidates,
    [switch]$RunOnlineBackfillCandidateBridge,
    [switch]$UseYFinanceForCandidateBridgeBackfill,
    [switch]$ApplyOnlineBackfilledRecomputedCandidates,
    [switch]$RunNextSignalFreezeExpansion,
    [switch]$ApplyNextSignalFreezeExpansion,
    [switch]$RunUniverseInvalidTickerPrune,
    [switch]$ApplyUniverseInvalidTickerPrune,
    [switch]$RunUniverseCandidateAudit,
    [switch]$RunPaperTradingForwardAttribution,
    [switch]$UpdatePaperTradingLedger,
    [switch]$UseYFinanceForPaperTradingPrices,
    [switch]$RunPaperTradingForwardReturnFiller,
    [switch]$UpdatePaperTradingForwardReturns,
    [switch]$UseYFinanceForPaperForwardPrices,
    [switch]$RunFactorImplementationAudit,
    [switch]$RunFactorImplementationStrictAudit,
    [switch]$RunLeanInspiredStrategyMotifLab,
    [switch]$RunShadowPortfolioConstruction,
    [switch]$RunShadowPortfolioForwardBridge,
    [switch]$ApplyShadowPortfolioSnapshot,
    [switch]$RunForwardEvidenceDashboard,
    [switch]$RunResearchExperimentRegistry,
    [switch]$RunCommandStatusNormalization,
    [switch]$RunCandidateTopFullCanonicalSync,
    [switch]$ApplyCandidateTopFullCanonicalSync,
    [switch]$RunAlphaSignalObjectLayer,
    [switch]$RunPortfolioTargetPreview,
    [switch]$RunShadowRiskModelPreview,
    [switch]$RunKdjMacdShadowLayer,
    [switch]$RunCurrentWarningCleanupStatusContract,
    [switch]$RunFixableCurrentWarningReducer,
    [switch]$ApplyFixableCurrentWarningReducer,
    [switch]$RunResidualActionWarningResolver,
    [switch]$ApplyResidualActionWarningResolver,
    [switch]$RunFactorGovernanceRegistry,
    [switch]$RunTop20PriorityTracker,
    [switch]$RunTop20EventEarningsRisk,
    [switch]$RunTop20EventCoverageRepair,
    [switch]$RunTop20RiskEventAutoFetch,
    [switch]$RunUniverseRollingScan,
    [switch]$UseYFinanceForRollingScan,
    [switch]$ForceSameDayPromotion,
    [switch]$DisableSameDayPromotionGuard
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Run13D = Join-Path $Root "scripts\v18\run_v18_13D_daily_command_center.ps1"
$Run14A = Join-Path $Root "scripts\v18\run_v18_14A_full_daily_mode_validation.ps1"
$Script14B = Join-Path $Root "scripts\v18\v18_14B_current_daily_command_center.py"
$Run14C = Join-Path $Root "scripts\v18\run_v18_14C_ranked_candidate_forward_tracker.ps1"
$Run14D = Join-Path $Root "scripts\v18\run_v18_14D_ranked_candidate_forward_price_filler.ps1"
$Script14E = Join-Path $Root "scripts\v18\v18_14E_current_daily_with_forward_tracker.py"
$Run15B = Join-Path $Root "scripts\v18\run_v18_15B_current_daily_with_manual_feedback.ps1"
$Run16F = Join-Path $Root "scripts\v18\run_v18_16F_current_daily_with_rolling_universe_scan.ps1"
$Run19A = Join-Path $Root "scripts\v18\run_v18_19A_daily_readability_refactor.ps1"
$Run47A = Join-Path $Root "scripts\v18\run_v18_47A_factor_governance_registry.ps1"
$Run47B = Join-Path $Root "scripts\v18\run_v18_47B_top20_priority_tracker.ps1"
$Run47C = Join-Path $Root "scripts\v18\run_v18_47C_top20_event_earnings_risk_layer.ps1"
$Run47CR1 = Join-Path $Root "scripts\v18\run_v18_47C_R1_event_source_coverage_repair.ps1"
$Run47CR2 = Join-Path $Root "scripts\v18\run_v18_47C_R2_top20_90d_risk_event_auto_fetcher.ps1"

if (-not (Test-Path $Python)) { throw "Missing Python executable: $Python" }
if (-not (Test-Path $Run13D)) { throw "Missing V18.13D wrapper: $Run13D" }
if (-not (Test-Path $Run14A)) { throw "Missing V18.14A wrapper: $Run14A" }
if (-not (Test-Path $Script14B)) { throw "Missing V18.14B script: $Script14B" }
if ($RunForwardTracker -and -not (Test-Path $Run14C)) { throw "Missing V18.14C wrapper: $Run14C" }
if ($RunForwardTracker -and -not (Test-Path $Run14D)) { throw "Missing V18.14D wrapper: $Run14D" }
if ($RunForwardTracker -and -not (Test-Path $Script14E)) { throw "Missing V18.14E script: $Script14E" }
if ($RunManualFeedback -and -not (Test-Path $Run15B)) { throw "Missing V18.15B wrapper: $Run15B" }
if ($RunUniverseRollingScan -and -not (Test-Path $Run16F)) { throw "Missing V18.16F wrapper: $Run16F" }
if (-not (Test-Path $Run19A)) { throw "Missing V18.19A wrapper: $Run19A" }
if ($RunFactorGovernanceRegistry -and -not (Test-Path $Run47A)) { throw "Missing V18.47A wrapper: $Run47A" }
if ($RunTop20PriorityTracker -and -not (Test-Path $Run47B)) { throw "Missing V18.47B wrapper: $Run47B" }
if ($RunTop20EventEarningsRisk -and -not (Test-Path $Run47C)) { throw "Missing V18.47C wrapper: $Run47C" }
if ($RunTop20EventCoverageRepair -and -not (Test-Path $Run47CR1)) { throw "Missing V18.47C-R1 wrapper: $Run47CR1" }
if ($RunTop20RiskEventAutoFetch -and -not (Test-Path $Run47CR2)) { throw "Missing V18.47C-R2 wrapper: $Run47CR2" }

$RefreshModeExplicit = $PSBoundParameters.ContainsKey("RefreshMode")
$ManualModeExplicit = (
    $FullDaily -or $ReadCenterRefreshOnly -or $ValidateOnly -or
    $RunUniverseRollingScan -or $RunForwardTracker -or $RunManualFeedback -or
    $RunFullUniverseFactorTechnicalRecompute -or $ApplyFullUniverseRecomputedCandidates -or
    $RunCandidateTopFullCanonicalSync -or $ApplyCandidateTopFullCanonicalSync
)
$ApplyRefreshModePreset = $RefreshModeExplicit -or -not $ManualModeExplicit
if ($ApplyRefreshModePreset) {
    $FullDaily = $true
    if ($RefreshMode -eq "Full") {
        $UseYFinance = $true
        $RunFullUniverseFactorTechnicalRecompute = $true
        $UseYFinanceForFullUniverseRecompute = $true
        $ApplyFullUniverseRecomputedCandidates = $true
        $RunCandidateTopFullCanonicalSync = $true
        $ApplyCandidateTopFullCanonicalSync = $true
    }
    else {
        $RunForwardTracker = $true
        $RunManualFeedback = $true
        $RunUniverseRollingScan = $true
        $RunChineseHomepage = $true
        $RunFreshnessGuard = $true
    }
}

function Read-V18KeyValueFile {
    param([string]$Path)
    $Map = @{}
    if (Test-Path $Path) {
        foreach ($Line in (Get-Content $Path)) {
            if ($Line -match "^\s*([^:]+):\s*(.*)\s*$") {
                $Map[$Matches[1].Trim()] = $Matches[2].Trim()
            }
        }
    }
    return $Map
}

function Get-V18CurrentAuthoritativeChainStatus {
    $Read35D = Read-V18KeyValueFile (Join-Path $Root "outputs\v18\ops\V18_35D_READ_FIRST.txt")
    $Read40A = Read-V18KeyValueFile (Join-Path $Root "outputs\v18\ops\V18_40A_READ_FIRST.txt")
    $Read41A = Read-V18KeyValueFile (Join-Path $Root "outputs\v18\ops\V18_41A_READ_FIRST.txt")
    $Read44A = Read-V18KeyValueFile (Join-Path $Root "outputs\v18\ops\V18_44A_READ_FIRST.txt")
    $Read45A = Read-V18KeyValueFile (Join-Path $Root "outputs\v18\ops\V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_READ_FIRST.txt")

    $Reasons = @()
    if ($RefreshMode -ne "Full") { $Reasons += "REFRESH_MODE_NOT_FULL" }
    if (-not $Read35D.ContainsKey("STATUS") -or $Read35D["STATUS"].StartsWith("FAIL_")) { $Reasons += "FULL_UNIVERSE_RECOMPUTE_NOT_READY" }
    if ($Read45A["FULL_RANKING_RECOMPUTE_COMPLETE"] -ne "TRUE") { $Reasons += "FULL_RANKING_RECOMPUTE_NOT_COMPLETE" }
    if ($Read40A["MISMATCH_COUNT"] -ne "0" -or $Read40A["ORDER_MATCHES_FULL_TOP20"] -ne "TRUE") { $Reasons += "TOP_FULL_SYNC_NOT_READY" }
    if ($Read45A["TOPN_CURRENT_READY"] -ne "TRUE" -or $Read45A["FRESH_TOPN_COUNT"] -ne "20" -or $Read45A["STALE_TOPN_COUNT"] -ne "0") { $Reasons += "CURRENT_TOPN_NOT_READY" }
    if ($Read45A["FULL_PRICE_REFRESH_COMPLETE"] -ne "TRUE") { $Reasons += "FULL_PRICE_REFRESH_NOT_COMPLETE" }
    if ($Read45A["CURRENT_PRICE_REFRESH_BLOCKING_FAILED_TICKER_COUNT"] -ne "0") { $Reasons += "CURRENT_PRICE_REFRESH_BLOCKING_FAILED_TICKERS_PRESENT" }
    if (-not $Read44A.ContainsKey("STATUS") -or $Read44A["STATUS"].StartsWith("FAIL_")) { $Reasons += "HOMEPAGE_CONSOLIDATION_NOT_READY" }
    if ($Read41A["TOP_FULL_MISMATCH_COUNT"] -ne "0") { $Reasons += "TOP_FULL_MISMATCH_EXISTS" }
    if ($Read41A["BLOCKING_CURRENT_FAILURE_COUNT"] -ne "0") { $Reasons += "BLOCKING_CURRENT_FAILURE_EXISTS" }
    if (
        $Read41A["TRADING_EXECUTION_ALLOWED"] -ne "FALSE" -or
        $Read41A["AUTO_TRADE"] -ne "DISABLED" -or
        $Read41A["AUTO_SELL"] -ne "DISABLED" -or
        $Read41A["BROKER_API_USED"] -ne "FALSE" -or
        $Read41A["ORDER_EXECUTION_USED"] -ne "FALSE"
    ) {
        $Reasons += "TRADING_SAFETY_FIELDS_MISSING"
    }

    $Ready = $Reasons.Count -eq 0
    return @{
        Ready = $Ready
        BlockedReason = if ($Ready) { "NONE" } else { ($Reasons -join ";") }
        Read35D = $Read35D
        Read40A = $Read40A
        Read41A = $Read41A
        Read44A = $Read44A
        Read45A = $Read45A
    }
}

function Invoke-V18_19AReadabilityRefresh {
    if ($RunTradeReadinessRefresh) {
        Write-Host ""
        Write-Host "STEP FINAL: refresh V18.34C current trade readiness report"
        $Run34C = Join-Path $Root "scripts\v18\run_v18_34C_trade_readiness_current_refresh.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run34C -ApplyRefresh
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_34C_TRADE_READINESS_REFRESH_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_34C_TRADE_READINESS_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_DAILY_TRADE_READINESS.md')"
    }
    if ($RunChineseHomepage -or $RunLegacyChineseHomepage) {
        Write-Host ""
        Write-Host "STEP FINAL: refresh V18.33A Chinese daily operator homepage"
        $Run33A = Join-Path $Root "scripts\v18\run_v18_33A_chinese_daily_operator_homepage.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run33A
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_33A_CHINESE_HOME_REFRESH_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_33A_CHINESE_HOME_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md')"
    }
    if ($RunFreshnessGuard -or $RunLegacyDailyOutputFreshnessGuard) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.34B daily output freshness guard"
        $Run34B = Join-Path $Root "scripts\v18\run_v18_34B_daily_output_freshness_guard.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run34B
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_34B_FRESHNESS_GUARD_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_34B_FRESHNESS_REPORT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md')"
    }
    if ($RunCandidateSourceNormalization) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.35B current candidate source normalization"
        $Run35B = Join-Path $Root "scripts\v18\run_v18_35B_current_candidate_source_normalization.ps1"
        $Args35B = @()
        if ($ApplyCandidateCanonicalAliasRepair) { $Args35B += "-ApplyCanonicalAliasRepair" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run35B @Args35B
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_35B_CANDIDATE_SOURCE_NORMALIZATION_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_35B_CANDIDATE_SOURCE_NORMALIZATION_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_CANDIDATE_SOURCE_NORMALIZATION.md')"
    }
    if ($RunCandidateSourceDependencyReview) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.35C candidate source dependency role review"
        $Run35C = Join-Path $Root "scripts\v18\run_v18_35C_candidate_source_dependency_role_review.ps1"
        $Args35C = @()
        if ($ApplyCandidateSourceDependencyPatches) { $Args35C += "-ApplySafeReferencePatches" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run35C @Args35C
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_35C_CANDIDATE_SOURCE_DEPENDENCY_REVIEW_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_CANDIDATE_SOURCE_DEPENDENCY_REVIEW.md')"
    }
    if ($RunFullUniverseFactorTechnicalRecompute) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.35D full universe factor/technical recompute"
        $Run35D = Join-Path $Root "scripts\v18\run_v18_35D_full_universe_factor_technical_recompute.ps1"
        $Args35D = @()
        if ($UseYFinanceForFullUniverseRecompute) { $Args35D += "-UseYFinanceForFullUniverseRecompute" }
        if ($ApplyFullUniverseRecomputedCandidates) { $Args35D += "-ApplyFullUniverseRecomputedCandidates" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run35D @Args35D
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_35D_FULL_UNIVERSE_RECOMPUTE_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_35D_FULL_UNIVERSE_RECOMPUTE_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_FULL_UNIVERSE_RECOMPUTE.md')"
    }
    if ($RunOnlineBackfillCandidateBridge) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.35E online backfill candidate adoption bridge"
        $Run35E = Join-Path $Root "scripts\v18\run_v18_35E_online_backfill_candidate_adoption_bridge.ps1"
        $Args35E = @()
        if ($UseYFinanceForCandidateBridgeBackfill) { $Args35E += "-UseYFinanceForCandidateBridgeBackfill" }
        if ($ApplyOnlineBackfilledRecomputedCandidates) { $Args35E += "-ApplyOnlineBackfilledRecomputedCandidates" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run35E @Args35E
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_ONLINE_BACKFILL_CANDIDATE_BRIDGE.md')"
    }
    if ($RunNextSignalFreezeExpansion) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.35F next signal freeze expansion"
        $Run35F = Join-Path $Root "scripts\v18\run_v18_35F_next_signal_freeze_expansion.ps1"
        $Args35F = @()
        if ($ApplyNextSignalFreezeExpansion) { $Args35F += "-ApplyNextSignalFreezeExpansion" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run35F @Args35F
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_NEXT_SIGNAL_FREEZE_EXPANSION.md')"
    }
    if ($RunUniverseInvalidTickerPrune) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.35G universe invalid ticker prune"
        $Run35G = Join-Path $Root "scripts\v18\run_v18_35G_universe_invalid_ticker_prune.ps1"
        $Args35G = @()
        if ($ApplyUniverseInvalidTickerPrune) { $Args35G += "-ApplyUniverseInvalidTickerPrune" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run35G @Args35G
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_UNIVERSE_INVALID_TICKER_PRUNE.md')"
    }
    if ($RunUniverseCandidateAudit) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.35A universe-to-candidate diff audit"
        $Run35A = Join-Path $Root "scripts\v18\run_v18_35A_universe_to_candidate_diff_audit.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run35A
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_35A_UNIVERSE_CANDIDATE_AUDIT_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_35A_UNIVERSE_CANDIDATE_AUDIT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_UNIVERSE_TO_CANDIDATE_AUDIT.md')"
    }
    if ($RunPaperTradingForwardAttribution) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.36A paper trading forward attribution"
        $Run36A = Join-Path $Root "scripts\v18\run_v18_36A_paper_trading_forward_attribution.ps1"
        $Args36A = @()
        if ($UpdatePaperTradingLedger) { $Args36A += "-UpdatePaperTradingLedger" }
        if ($UseYFinanceForPaperTradingPrices) { $Args36A += "-UseYFinanceForPaperTradingPrices" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run36A @Args36A
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_PAPER_TRADING_FORWARD_ATTRIBUTION.md')"
    }
    if ($RunPaperTradingForwardReturnFiller) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.36B paper forward return filler"
        $Run36B = Join-Path $Root "scripts\v18\run_v18_36B_paper_trading_forward_return_filler.ps1"
        $Args36B = @()
        if ($UpdatePaperTradingForwardReturns) { $Args36B += "-UpdatePaperTradingForwardReturns" }
        if ($UseYFinanceForPaperForwardPrices) { $Args36B += "-UseYFinanceForPaperForwardPrices" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run36B @Args36B
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_36B_PAPER_FORWARD_RETURN_FILLER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_36B_PAPER_FORWARD_RETURN_FILLER_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_PAPER_FORWARD_RETURN_FILLER.md')"
    }
    if ($RunFactorImplementationAudit) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.36C factor implementation audit"
        $Run36C = Join-Path $Root "scripts\v18\run_v18_36C_factor_implementation_audit.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run36C
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_36C_FACTOR_IMPLEMENTATION_AUDIT_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_36C_FACTOR_IMPLEMENTATION_AUDIT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_FACTOR_IMPLEMENTATION_AUDIT.md')"
    }
    if ($RunFactorImplementationStrictAudit) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.36C-R1 strict factor implementation audit"
        $Run36CR1 = Join-Path $Root "scripts\v18\run_v18_36C_R1_strict_evidence_classification_patch.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run36CR1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_STRICT_FACTOR_IMPLEMENTATION_AUDIT.md')"
    }
    if ($RunLeanInspiredStrategyMotifLab) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.37A LEAN-inspired strategy motif lab"
        $Run37A = Join-Path $Root "scripts\v18\run_v18_37A_lean_inspired_strategy_motif_lab.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run37A -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_LAB_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_LAB_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_LEAN_INSPIRED_STRATEGY_LAB.md')"
    }
    if ($RunShadowPortfolioConstruction) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.37B shadow portfolio construction comparison"
        $Run37B = Join-Path $Root "scripts\v18\run_v18_37B_shadow_portfolio_construction_comparison.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run37B -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_37B_SHADOW_PORTFOLIO_CONSTRUCTION_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_37B_SHADOW_PORTFOLIO_CONSTRUCTION_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_SHADOW_PORTFOLIO_CONSTRUCTION.md')"
    }
    if ($RunShadowPortfolioForwardBridge) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.37C shadow portfolio daily snapshot forward bridge"
        $Run37C = Join-Path $Root "scripts\v18\run_v18_37C_shadow_portfolio_daily_snapshot_forward_bridge.ps1"
        $Args37C = @("-Root", $Root)
        if ($ApplyShadowPortfolioSnapshot) { $Args37C += "-ApplySnapshot" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run37C @Args37C
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_37C_SHADOW_PORTFOLIO_FORWARD_BRIDGE_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_37C_SHADOW_PORTFOLIO_FORWARD_BRIDGE_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_SHADOW_PORTFOLIO_FORWARD_BRIDGE.md')"
    }
    if ($RunForwardEvidenceDashboard) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.38A forward evidence dashboard"
        $Run38A = Join-Path $Root "scripts\v18\run_v18_38A_forward_evidence_dashboard.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run38A -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_38A_FORWARD_EVIDENCE_DASHBOARD_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_38A_FORWARD_EVIDENCE_DASHBOARD_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md')"
    }
    if ($RunResearchExperimentRegistry) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.38B research experiment registry"
        $Run38B = Join-Path $Root "scripts\v18\run_v18_38B_research_experiment_registry.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run38B -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_38B_RESEARCH_EXPERIMENT_REGISTRY_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_38B_RESEARCH_EXPERIMENT_REGISTRY_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md')"
    }
    if ($RunCommandStatusNormalization) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.38C/R1 command center status normalization"
        $Run38C = Join-Path $Root "scripts\v18\run_v18_38C_command_center_status_normalization.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run38C -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_38C_COMMAND_STATUS_NORMALIZATION_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_38C_COMMAND_STATUS_NORMALIZATION_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md')"
    }
    if ($RunCandidateTopFullCanonicalSync) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.40A candidate top/full canonical sync"
        $Run40ACandidates = Join-Path $Root "scripts\v18\run_v18_40A_candidate_top_full_canonical_sync.ps1"
        $Args40ACandidates = @("-Root", $Root)
        if ($ApplyCandidateTopFullCanonicalSync) { $Args40ACandidates += "-ApplyCandidateTopFullCanonicalSync" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run40ACandidates @Args40ACandidates
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_40A_CANDIDATE_TOP_FULL_CANONICAL_SYNC_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_CANDIDATE_TOP_FULL_CANONICAL_SYNC.md')"
    }
    if ($RunAlphaSignalObjectLayer) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.39A alpha signal object layer"
        $Run39A = Join-Path $Root "scripts\v18\run_v18_39A_alpha_signal_object_layer.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run39A -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_39A_ALPHA_SIGNAL_OBJECT_LAYER_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_ALPHA_SIGNAL_OBJECTS.md')"
    }
    if ($RunPortfolioTargetPreview) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.39B portfolio target preview"
        $Run39B = Join-Path $Root "scripts\v18\run_v18_39B_portfolio_target_preview.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run39B -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_39B_PORTFOLIO_TARGET_PREVIEW_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_39B_PORTFOLIO_TARGET_PREVIEW_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_PORTFOLIO_TARGET_PREVIEW.md')"
    }
    if ($RunShadowRiskModelPreview) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.39C shadow risk model preview"
        $Run39C = Join-Path $Root "scripts\v18\run_v18_39C_shadow_risk_model_preview.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run39C -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_39C_SHADOW_RISK_MODEL_PREVIEW_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_39C_SHADOW_RISK_MODEL_PREVIEW_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md')"
    }
    if ($RunCurrentWarningCleanupStatusContract) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.40B current warning cleanup status contract"
        $Run40B = Join-Path $Root "scripts\v18\run_v18_40B_current_warning_cleanup_status_contract.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run40B -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_40B_CURRENT_WARNING_CLEANUP_STATUS_CONTRACT_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_40B_CURRENT_OPERATOR_CLEAN_STATUS_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_OPERATOR_CLEAN_STATUS.md')"
    }
    if ($RunFixableCurrentWarningReducer) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.40C fixable current warning reducer"
        $Run40C = Join-Path $Root "scripts\v18\run_v18_40C_fixable_current_warning_reducer.ps1"
        $Args40C = @("-Root", $Root)
        if ($ApplyFixableCurrentWarningReducer) { $Args40C += "-ApplyFixableCurrentWarningReducer" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run40C @Args40C
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_40C_FIXABLE_CURRENT_WARNING_REDUCER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_40C_READ_FIRST_PATH: $(Join-Path $Root 'outputs\v18\ops\V18_40C_READ_FIRST.txt')"
        Write-Host "V18_40C_FIXABLE_WARNING_REDUCER_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_FIXABLE_WARNING_REDUCER.md')"
    }
    if ($RunResidualActionWarningResolver) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.40D residual action warning resolver"
        $Run40D = Join-Path $Root "scripts\v18\run_v18_40D_residual_action_warning_resolver.ps1"
        $Args40D = @("-Root", $Root)
        if ($ApplyResidualActionWarningResolver) { $Args40D += "-ApplyResidualActionWarningResolver" }
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run40D @Args40D
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_40D_READ_FIRST_PATH: $(Join-Path $Root 'outputs\v18\ops\V18_40D_READ_FIRST.txt')"
        Write-Host "V18_40D_RESIDUAL_ACTION_WARNING_RESOLVER_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_RESIDUAL_ACTION_WARNING_RESOLVER.md')"
    }
    if ($RunKdjMacdShadowLayer) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.40A KDJ + MACD shadow layer"
        $Run40A = Join-Path $Root "scripts\v18\run_v18_40A_kdj_macd_shadow_layer.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run40A -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_40A_KDJ_MACD_SHADOW_LAYER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_40A_KDJ_MACD_SHADOW_LAYER_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_KDJ_MACD_SHADOW_REPORT.md')"
    }
    Write-Host ""
    Write-Host "STEP FINAL: run V18.45A current ranked candidate freshness audit"
    $Run45A = Join-Path $Root "scripts\v18\run_v18_45A_current_ranked_candidate_freshness_audit.ps1"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run45A -Root $Root -RefreshMode $RefreshMode
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V18_45A_RANKED_CANDIDATE_FRESHNESS_AUDIT_STATUS: NONZERO_EXIT_$LASTEXITCODE"
    }
    Write-Host "V18_45A_FRESHNESS_AUDIT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_AUDIT.md')"
    if ($RefreshMode -eq "Full") {
        $Read45A = Join-Path $Root "outputs\v18\ops\V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_READ_FIRST.txt"
        $Map45A = @{}
        if (Test-Path $Read45A) {
            foreach ($Line45A in (Get-Content $Read45A)) {
                if ($Line45A -match "^\s*([^:]+):\s*(.*)\s*$") {
                    $Map45A[$Matches[1].Trim()] = $Matches[2].Trim()
                }
            }
        }
        if (
            $Map45A["FULL_RANKING_RECOMPUTE_COMPLETE"] -eq "TRUE" -and
            $Map45A["TOPN_CURRENT_READY"] -eq "TRUE"
        ) {
            Write-Host "CURRENT_FULL_REFRESH_VALIDATION_STATUS: CURRENT_AUTHORITATIVE_CHAIN_READY"
        }
        else {
            Write-Host "CURRENT_FULL_REFRESH_VALIDATION_STATUS: CURRENT_AUTHORITATIVE_CHAIN_REVIEW_NEEDED"
        }
    }
    Write-Host ""
    Write-Host "STEP FINAL: refresh V18.19A daily readability packet"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run19A -Root $Root
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V18_19A_READABILITY_REFRESH_STATUS: NONZERO_EXIT_$LASTEXITCODE"
    }
    if ($ApplyRefreshModePreset) {
        Write-Host ""
        Write-Host "STEP FINAL: refresh V18.41A summary and V18.44A operator homepage current aliases"
        $Summary41A = Join-Path $Root "scripts\v18\v18_41A_daily_clean_operator_pipeline_summary.py"
        & $Python $Summary41A --root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_41A_SUMMARY_REFRESH_STATUS: NONZERO_EXIT_$LASTEXITCODE"
        }
        $Run44A = Join-Path $Root "scripts\v18\run_v18_44A_daily_operator_homepage_consolidation.ps1"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run44A -Root $Root -WriteCurrent -IncludeFileChecklist -IncludeWarningDetails -RequireTopNCurrent
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_44A_OPERATOR_HOMEPAGE_REFRESH_STATUS: NONZERO_EXIT_$LASTEXITCODE"
        }
        $ChainStatus = Get-V18CurrentAuthoritativeChainStatus
        $CurrentAuthoritativeChainReady = $ChainStatus["Ready"]
        if ($Legacy14AFailReasonsRecognized -and $CurrentAuthoritativeChainReady) {
            $Legacy14AStatus = "LEGACY_READ_CENTER_VALIDATION_NONBLOCKING"
            $Legacy14ASuppressionAllowed = "TRUE"
            $Legacy14ASuppressionBlockedReason = "NONE"
            $CurrentFullRefreshValidationStatus = "CURRENT_AUTHORITATIVE_CHAIN_READY"
        }
        elseif ($Legacy14AFailReasonsRecognized) {
            $Legacy14AStatus = "LEGACY_READ_CENTER_VALIDATION_PENDING_AUTHORITATIVE_CHAIN"
            $Legacy14ASuppressionAllowed = "FALSE"
            $Legacy14ASuppressionBlockedReason = $ChainStatus["BlockedReason"]
            $CurrentFullRefreshValidationStatus = "CURRENT_AUTHORITATIVE_CHAIN_REVIEW_NEEDED"
        }
        $Read19A = Read-V18KeyValueFile (Join-Path $Root "outputs\v18\ops\V18_19A_READ_FIRST.txt")
        $Out46B = Join-Path $Root "outputs\v18\ops\V18_46B_READ_FIRST.txt"
        $Lines46B = @(
            "PATCH_VERSION: V18.46B",
            "PATCH_NAME: STRICT_AUTHORITATIVE_CHAIN_GATE_FOR_LEGACY_NONBLOCKING_WARNINGS",
            "CURRENT_AUTHORITATIVE_CHAIN_READY: $($CurrentAuthoritativeChainReady.ToString().ToUpper())",
            "LEGACY_V18_14A_SUPPRESSION_ALLOWED: $Legacy14ASuppressionAllowed",
            "LEGACY_V18_14A_SUPPRESSION_BLOCKED_REASON: $Legacy14ASuppressionBlockedReason",
            "OLD_HOMEPAGE_CANDIDATE_COUNT_SUPPRESSION_ALLOWED: $($ChainStatus['Read44A']['OLD_HOMEPAGE_CANDIDATE_COUNT_SUPPRESSION_ALLOWED'])",
            "OLD_HOMEPAGE_CANDIDATE_COUNT_SUPPRESSION_BLOCKED_REASON: $($ChainStatus['Read44A']['OLD_HOMEPAGE_CANDIDATE_COUNT_SUPPRESSION_BLOCKED_REASON'])",
            "FULL_RANKING_RECOMPUTE_COMPLETE: $($ChainStatus['Read45A']['FULL_RANKING_RECOMPUTE_COMPLETE'])",
            "FULL_PRICE_REFRESH_COMPLETE: $($ChainStatus['Read45A']['FULL_PRICE_REFRESH_COMPLETE'])",
            "TOPN_CURRENT_READY: $($ChainStatus['Read45A']['TOPN_CURRENT_READY'])",
            "FRESH_TOPN_COUNT: $($ChainStatus['Read45A']['FRESH_TOPN_COUNT'])",
            "STALE_TOPN_COUNT: $($ChainStatus['Read45A']['STALE_TOPN_COUNT'])",
            "TOP_FULL_MISMATCH_COUNT: $($ChainStatus['Read41A']['TOP_FULL_MISMATCH_COUNT'])",
            "BLOCKING_CURRENT_FAILURE_COUNT: $($ChainStatus['Read41A']['BLOCKING_CURRENT_FAILURE_COUNT'])",
            "VALIDATION_FAIL_COUNT: $($Read19A['VALIDATION_FAIL_COUNT'])",
            "BUY_CANDIDATE_REPORT_TRUST: $($ChainStatus['Read45A']['BUY_CANDIDATE_REPORT_TRUST'])",
            "DAILY_TRUST_LEVEL: $($Read19A['DAILY_TRUST_LEVEL'])",
            "OFFICIAL_DECISION_IMPACT: NONE",
            "AUTO_TRADE: DISABLED",
            "AUTO_SELL: DISABLED",
            "BROKER_API_USED: $($ChainStatus['Read41A']['BROKER_API_USED'])",
            "ORDER_EXECUTION_USED: $($ChainStatus['Read41A']['ORDER_EXECUTION_USED'])",
            "RANKING_LOGIC_CHANGED: FALSE",
            "FACTOR_WEIGHTS_CHANGED: FALSE"
        )
        Set-Content -Path $Out46B -Value $Lines46B -Encoding UTF8
        Write-Host "CURRENT_AUTHORITATIVE_CHAIN_READY: $($CurrentAuthoritativeChainReady.ToString().ToUpper())"
        Write-Host "LEGACY_V18_14A_VALIDATION_STATUS: $Legacy14AStatus"
        Write-Host "LEGACY_V18_14A_SUPPRESSION_ALLOWED: $Legacy14ASuppressionAllowed"
        Write-Host "LEGACY_V18_14A_SUPPRESSION_BLOCKED_REASON: $Legacy14ASuppressionBlockedReason"
        Write-Host "CURRENT_FULL_REFRESH_VALIDATION_STATUS: $CurrentFullRefreshValidationStatus"
        Write-Host "V18_46B_READ_FIRST_PATH: $Out46B"
    }
}

function Invoke-V18_47AFactorGovernanceRegistry {
    if ($RunFactorGovernanceRegistry) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.47A factor governance registry"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run47A -Root $Root -WriteCurrent
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_47A_FACTOR_GOVERNANCE_REGISTRY_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_47A_FACTOR_GOVERNANCE_REGISTRY_PATH: $(Join-Path $Root 'outputs\v18\factor_governance\V18_47A_FACTOR_GOVERNANCE_REGISTRY.csv')"
        Write-Host "V18_47A_FACTOR_GOVERNANCE_CURRENT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_FACTOR_GOVERNANCE_REGISTRY.md')"
    }
}

function Invoke-V18_47BTop20PriorityTracker {
    if ($RunTop20PriorityTracker) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.47B Top20 priority tracker"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run47B -Root $Root -WriteCurrent
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_47B_TOP20_PRIORITY_TRACKER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_47B_TOP20_PRIORITY_TRACKER_PATH: $(Join-Path $Root 'outputs\v18\tracking\V18_47B_TOP20_PRIORITY_TRACKER.csv')"
        Write-Host "V18_47B_TOP20_PRIORITY_CURRENT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_TOP20_PRIORITY_TRACKER.md')"
    }
}

function Invoke-V18_47CTop20EventEarningsRisk {
    if ($RunTop20EventEarningsRisk) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.47C Top20 event / earnings risk layer"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run47C -Root $Root -WriteCurrent
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_47C_TOP20_EVENT_EARNINGS_RISK_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_47C_TOP20_EVENT_EARNINGS_RISK_PATH: $(Join-Path $Root 'outputs\v18\event_risk\V18_47C_TOP20_EVENT_EARNINGS_RISK.csv')"
        Write-Host "V18_47C_TOP20_EVENT_EARNINGS_CURRENT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_CURRENT_TOP20_EVENT_EARNINGS_RISK.md')"
    }
}

function Invoke-V18_47CR1Top20EventCoverageRepair {
    if ($RunTop20EventCoverageRepair) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.47C-R1 event source coverage repair"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run47CR1 -Root $Root -WriteCurrent
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_47C_R1_EVENT_SOURCE_COVERAGE_REPAIR_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_47C_R1_EVENT_SOURCE_COVERAGE_AUDIT_PATH: $(Join-Path $Root 'outputs\v18\event_risk\V18_47C_R1_EVENT_SOURCE_COVERAGE_AUDIT.csv')"
        Write-Host "V18_47C_R1_EVENT_SOURCE_COVERAGE_REPORT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_47C_R1_EVENT_SOURCE_COVERAGE_REPAIR_REPORT.md')"
    }
}

function Invoke-V18_47CR2Top20RiskEventAutoFetch {
    if ($RunTop20RiskEventAutoFetch) {
        Write-Host ""
        Write-Host "STEP FINAL: run V18.47C-R2 Top20 90-day risk event auto fetcher"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Run47CR2 -Root $Root -WriteCurrent
        if ($LASTEXITCODE -ne 0) {
            Write-Host "V18_47C_R2_TOP20_RISK_EVENT_AUTO_FETCH_STATUS: NONZERO_EXIT_$LASTEXITCODE"
            exit $LASTEXITCODE
        }
        Write-Host "V18_47C_R2_TOP20_RISK_EVENT_CACHE_PATH: $(Join-Path $Root 'outputs\v18\event_risk\V18_47C_R2_TOP20_90D_RISK_EVENT_CACHE.csv')"
        Write-Host "V18_47C_R2_TOP20_RISK_EVENT_REPORT_PATH: $(Join-Path $Root 'outputs\v18\read_center\V18_47C_R2_TOP20_90D_RISK_EVENT_AUTO_FETCH_REPORT.md')"
    }
}

$Mode = "READ_CENTER_REFRESH_ONLY"
if ($ValidateOnly) {
    $Mode = "VALIDATE_ONLY"
}
elseif ($FullDaily) {
    $Mode = "FULL_DAILY"
}
elseif ($ReadCenterRefreshOnly) {
    $Mode = "READ_CENTER_REFRESH_ONLY"
}
else {
    Write-Host "DEFAULT_MODE: READ_CENTER_REFRESH_ONLY"
    Write-Host "To run real full daily mode, use -FullDaily -UseYFinance"
}

Write-Host "REFRESH_MODE: $RefreshMode"
Write-Host "REFRESH_MODE_PRESET_APPLIED: $($ApplyRefreshModePreset.ToString().ToUpper())"

if ($RunUniverseRollingScan) {
    Write-Host "DELEGATING_TO: V18.16F_CURRENT_DAILY_WITH_ROLLING_UNIVERSE_SCAN"
    $Args16F = @()
    if ($RunForwardTracker) { $Args16F += "-RunForwardTracker" }
    if ($RunManualFeedback) { $Args16F += "-RunManualFeedback" }
    if ($UseYFinanceForRollingScan) { $Args16F += "-UseYFinanceForRollingScan" }
    if ($ForceSameDayPromotion) { $Args16F += "-ForceSameDayPromotion" }
    if ($DisableSameDayPromotionGuard) { $Args16F += "-DisableSameDayPromotionGuard" }
    if ($FullDaily) { $Args16F += "-FullDaily" }
    if ($ReadCenterRefreshOnly) { $Args16F += "-ReadCenterRefreshOnly" }
    if ($ValidateOnly) { $Args16F += "-ValidateOnly" }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run16F @Args16F
    $DelegateExit = $LASTEXITCODE
    Invoke-V18_19AReadabilityRefresh
    Invoke-V18_47AFactorGovernanceRegistry
    Invoke-V18_47BTop20PriorityTracker
    Invoke-V18_47CTop20EventEarningsRisk
    Invoke-V18_47CR1Top20EventCoverageRepair
    Invoke-V18_47CR2Top20RiskEventAutoFetch
    if ($DelegateExit -ne 0) {
        $Read16F = Join-Path $Root "outputs\v18\ops\V18_16F_READ_FIRST.txt"
        $Status16F = ""
        if (Test-Path $Read16F) {
            $Status16F = (Get-Content $Read16F | Where-Object { $_ -like "STATUS:*" } | Select-Object -First 1)
        }
        if ($Status16F -like "STATUS: FAIL_*") {
            exit $DelegateExit
        }
        Write-Host "V18_16F_DELEGATE_NONZERO_TREATED_AS_WARN: $DelegateExit"
    }
    exit 0
}

if ($RunManualFeedback) {
    Write-Host "DELEGATING_TO: V18.15B_CURRENT_DAILY_WITH_MANUAL_FEEDBACK"
    $Args15B = @("-RunManualFeedback")
    if ($FullDaily) { $Args15B += "-FullDaily" }
    if ($ReadCenterRefreshOnly) { $Args15B += "-ReadCenterRefreshOnly" }
    if ($ValidateOnly) { $Args15B += "-ValidateOnly" }
    if ($RunForwardTracker) { $Args15B += "-RunForwardTracker" }
    if ($UseYFinance -and $FullDaily) { $Args15B += "-UseYFinance" }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run15B @Args15B
    $DelegateExit = $LASTEXITCODE
    Invoke-V18_19AReadabilityRefresh
    Invoke-V18_47AFactorGovernanceRegistry
    Invoke-V18_47BTop20PriorityTracker
    Invoke-V18_47CTop20EventEarningsRisk
    Invoke-V18_47CR1Top20EventCoverageRepair
    Invoke-V18_47CR2Top20RiskEventAutoFetch
    if ($DelegateExit -ne 0 -and $ApplyRefreshModePreset) {
        $FreshnessRead = Join-Path $Root "outputs\v18\ops\V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_READ_FIRST.txt"
        $FreshnessStatus = ""
        if (Test-Path $FreshnessRead) {
            $FreshnessStatus = (Get-Content $FreshnessRead | Where-Object { $_ -like "STATUS:*" } | Select-Object -First 1)
        }
        if ($FreshnessStatus -like "STATUS: FAIL_*") {
            exit $DelegateExit
        }
        Write-Host "V18_15B_DELEGATE_NONZERO_TREATED_AS_WARN: $DelegateExit"
        exit 0
    }
    exit $DelegateExit
}

Write-Host "=== V18 CURRENT DAILY COMMAND CENTER START ==="
Write-Host "MODE: $Mode"
Write-Host "REFRESH_MODE: $RefreshMode"
Write-Host "REFRESH_MODE_PRESET_APPLIED: $($ApplyRefreshModePreset.ToString().ToUpper())"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "CURRENT_ENTRY_ONLY: TRUE"
Write-Host "RUN_FORWARD_TRACKER: $RunForwardTracker"
Write-Host "RUN_MANUAL_FEEDBACK: $RunManualFeedback"
Write-Host "RUN_LEAN_INSPIRED_STRATEGY_MOTIF_LAB: $RunLeanInspiredStrategyMotifLab"
Write-Host "RUN_SHADOW_PORTFOLIO_CONSTRUCTION: $RunShadowPortfolioConstruction"
Write-Host "RUN_SHADOW_PORTFOLIO_FORWARD_BRIDGE: $RunShadowPortfolioForwardBridge"
Write-Host "APPLY_SHADOW_PORTFOLIO_SNAPSHOT: $ApplyShadowPortfolioSnapshot"
Write-Host "RUN_FORWARD_EVIDENCE_DASHBOARD: $RunForwardEvidenceDashboard"
Write-Host "RUN_RESEARCH_EXPERIMENT_REGISTRY: $RunResearchExperimentRegistry"
Write-Host "RUN_COMMAND_STATUS_NORMALIZATION: $RunCommandStatusNormalization"
Write-Host "RUN_CANDIDATE_TOP_FULL_CANONICAL_SYNC: $RunCandidateTopFullCanonicalSync"
Write-Host "APPLY_CANDIDATE_TOP_FULL_CANONICAL_SYNC: $ApplyCandidateTopFullCanonicalSync"
Write-Host "RUN_ALPHA_SIGNAL_OBJECT_LAYER: $RunAlphaSignalObjectLayer"
Write-Host "RUN_PORTFOLIO_TARGET_PREVIEW: $RunPortfolioTargetPreview"
Write-Host "RUN_SHADOW_RISK_MODEL_PREVIEW: $RunShadowRiskModelPreview"
Write-Host "RUN_KDJ_MACD_SHADOW_LAYER: $RunKdjMacdShadowLayer"
Write-Host "RUN_CURRENT_WARNING_CLEANUP_STATUS_CONTRACT: $RunCurrentWarningCleanupStatusContract"
Write-Host "RUN_FIXABLE_CURRENT_WARNING_REDUCER: $RunFixableCurrentWarningReducer"
Write-Host "APPLY_FIXABLE_CURRENT_WARNING_REDUCER: $ApplyFixableCurrentWarningReducer"
Write-Host "RUN_RESIDUAL_ACTION_WARNING_RESOLVER: $RunResidualActionWarningResolver"
Write-Host "APPLY_RESIDUAL_ACTION_WARNING_RESOLVER: $ApplyResidualActionWarningResolver"
Write-Host "RUN_LEGACY_CHINESE_HOMEPAGE: $RunLegacyChineseHomepage"
Write-Host "RUN_LEGACY_DAILY_OUTPUT_FRESHNESS_GUARD: $RunLegacyDailyOutputFreshnessGuard"

if (-not $ValidateOnly) {
    $CommandInfo = Get-Command $Run13D
    $Args13D = @("-Root", $Root)
    if ($Mode -eq "READ_CENTER_REFRESH_ONLY") {
        $Args13D += "-SkipOfficialDaily"
    }
    if ($ApplyRefreshModePreset) {
        $Args13D += "-SkipOfficialDaily"
    }
    if ($UseYFinance -and $FullDaily -and $CommandInfo.Parameters.ContainsKey("UseYFinance")) {
        $Args13D += "-UseYFinance"
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run13D @Args13D
    if ($LASTEXITCODE -ne 0) {
        $CanTreatOfficialDailyAsWarn = $false
        if ($ApplyRefreshModePreset) {
            $Read40B = Join-Path $Root "outputs\v18\ops\V18_40B_READ_FIRST.txt"
            if (Test-Path $Read40B) {
                $Map40B = @{}
                Get-Content $Read40B | ForEach-Object {
                    if ($_ -match "^\s*([^:]+):\s*(.*)\s*$") {
                        $Map40B[$Matches[1].Trim()] = $Matches[2].Trim()
                    }
                }
                $CanTreatOfficialDailyAsWarn = (
                    $Map40B["DAILY_RUN_USABLE"] -eq "TRUE" -and
                    $Map40B["BUY_CANDIDATE_REPORT_USABLE"] -eq "TRUE" -and
                    $Map40B["BLOCKING_CURRENT_FAILURE_COUNT"] -eq "0" -and
                    $Map40B["TRADING_EXECUTION_ALLOWED"] -eq "FALSE"
                )
            }
        }
        if ($CanTreatOfficialDailyAsWarn) {
            Write-Host "V18_13D_OFFICIAL_DAILY_NONZERO_TREATED_AS_WARN: $LASTEXITCODE"
        }
        else {
        throw "V18_13D_DAILY_COMMAND_CENTER_FAILED"
        }
    }
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $Run14A
$V14AExitCode = $LASTEXITCODE
$Legacy14AStatus = "OK_OR_NOT_RUN"
$Legacy14ANonblockingReason = "NONE"
$Legacy14AFailReasonsRecognized = $false
$Legacy14ASuppressionAllowed = "FALSE"
$Legacy14ASuppressionBlockedReason = "LEGACY_FAIL_REASONS_NOT_RECOGNIZED"
$CurrentFullRefreshValidationStatus = "LEGACY_VALIDATION_NOT_APPLICABLE"
if ($V14AExitCode -ne 0) {
    $Read14A = Join-Path $Root "outputs\v18\ops\V18_14A_READ_FIRST.txt"
    $Reason14A = ""
    if (Test-Path $Read14A) {
        foreach ($Line14A in (Get-Content $Read14A)) {
            if ($Line14A -match "^\s*(FAIL_REASONS|FAILURE_REASONS|VALIDATION_FAIL_REASONS|VALIDATION_FAILURE_REASONS|REASON|FAIL_REASON):\s*(.*)\s*$") {
                $Reason14A = $Matches[2].Trim()
            }
        }
    }
    $LegacyReadCenterOnly = (
        $ApplyRefreshModePreset -and
        $RefreshMode -eq "Full" -and
        $Reason14A.ToUpper().Contains("READ_CENTER_REFRESH_ONLY") -and
        $Reason14A.ToUpper().Contains("OFFICIAL_DAILY_STATUS_SKIPPED")
    )
    $Legacy14AFailReasonsRecognized = $LegacyReadCenterOnly
    if ($LegacyReadCenterOnly) {
        $Legacy14AStatus = "LEGACY_READ_CENTER_VALIDATION_PENDING_AUTHORITATIVE_CHAIN"
        $Legacy14ANonblockingReason = "READ_CENTER_REFRESH_ONLY;OFFICIAL_DAILY_STATUS_SKIPPED"
        $CurrentFullRefreshValidationStatus = "PENDING_AUTHORITATIVE_CHAIN"
        $Legacy14ASuppressionBlockedReason = "CURRENT_AUTHORITATIVE_CHAIN_NOT_READY"
        Write-Host "V18_14A_VALIDATION_STATUS: LEGACY_READ_CENTER_VALIDATION_PENDING_AUTHORITATIVE_CHAIN"
    }
    else {
        $Legacy14AStatus = "NONZERO_EXIT_$V14AExitCode"
        $Legacy14ANonblockingReason = $Reason14A
        $CurrentFullRefreshValidationStatus = "LEGACY_VALIDATION_REVIEW_NEEDED"
        $Legacy14ASuppressionBlockedReason = "LEGACY_FAIL_REASONS_NOT_RECOGNIZED"
        Write-Host "V18_14A_VALIDATION_STATUS: NONZERO_EXIT_$V14AExitCode"
    }
}
Write-Host "LEGACY_V18_14A_VALIDATION_STATUS: $Legacy14AStatus"
Write-Host "LEGACY_V18_14A_NONBLOCKING_REASON: $Legacy14ANonblockingReason"
Write-Host "LEGACY_V18_14A_SUPPRESSION_ALLOWED: $Legacy14ASuppressionAllowed"
Write-Host "LEGACY_V18_14A_SUPPRESSION_BLOCKED_REASON: $Legacy14ASuppressionBlockedReason"
Write-Host "CURRENT_FULL_REFRESH_VALIDATION_STATUS: $CurrentFullRefreshValidationStatus"

& $Python $Script14B --root $Root --mode $Mode
$V14BExitCode = $LASTEXITCODE
if ($V14BExitCode -ne 0) {
    exit $V14BExitCode
}

if ($RunForwardTracker) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run14C
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V18_14C_FORWARD_TRACKER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
    }

    $DArgs = @()
    if ($UseYFinance -and $FullDaily) {
        $DArgs += "-UseYFinance"
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run14D @DArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V18_14D_FORWARD_PRICE_FILLER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
    }

    & $Python $Script14E --root $Root --mode $Mode --forward-tracker-run RAN
    $ExitCode = $LASTEXITCODE
    Invoke-V18_19AReadabilityRefresh
    Invoke-V18_47AFactorGovernanceRegistry
    Invoke-V18_47BTop20PriorityTracker
    Invoke-V18_47CTop20EventEarningsRisk
    Invoke-V18_47CR1Top20EventCoverageRepair
    Invoke-V18_47CR2Top20RiskEventAutoFetch
    exit $ExitCode
}

Invoke-V18_19AReadabilityRefresh
Invoke-V18_47AFactorGovernanceRegistry
Invoke-V18_47BTop20PriorityTracker
Invoke-V18_47CTop20EventEarningsRisk
Invoke-V18_47CR1Top20EventCoverageRepair
Invoke-V18_47CR2Top20RiskEventAutoFetch
exit 0
