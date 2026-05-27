param(
    [switch]$UseYFinance,
    [switch]$FullDaily,
    [switch]$ReadCenterRefreshOnly,
    [switch]$ValidateOnly,
    [switch]$RunForwardTracker,
    [switch]$RunManualFeedback,
    [switch]$RunTradeReadinessRefresh,
    [switch]$RunChineseHomepage,
    [switch]$RunFreshnessGuard,
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
    [switch]$RunAlphaSignalObjectLayer,
    [switch]$RunPortfolioTargetPreview,
    [switch]$RunShadowRiskModelPreview,
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
    if ($RunChineseHomepage) {
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
    if ($RunFreshnessGuard) {
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
    Write-Host ""
    Write-Host "STEP FINAL: refresh V18.19A daily readability packet"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run19A -Root $Root
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V18_19A_READABILITY_REFRESH_STATUS: NONZERO_EXIT_$LASTEXITCODE"
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
    exit $DelegateExit
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
    exit $DelegateExit
}

Write-Host "=== V18 CURRENT DAILY COMMAND CENTER START ==="
Write-Host "MODE: $Mode"
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
Write-Host "RUN_ALPHA_SIGNAL_OBJECT_LAYER: $RunAlphaSignalObjectLayer"
Write-Host "RUN_PORTFOLIO_TARGET_PREVIEW: $RunPortfolioTargetPreview"
Write-Host "RUN_SHADOW_RISK_MODEL_PREVIEW: $RunShadowRiskModelPreview"

if (-not $ValidateOnly) {
    $CommandInfo = Get-Command $Run13D
    $Args13D = @("-Root", $Root)
    if ($Mode -eq "READ_CENTER_REFRESH_ONLY") {
        $Args13D += "-SkipOfficialDaily"
    }
    if ($UseYFinance -and $FullDaily -and $CommandInfo.Parameters.ContainsKey("UseYFinance")) {
        $Args13D += "-UseYFinance"
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run13D @Args13D
    if ($LASTEXITCODE -ne 0) {
        throw "V18_13D_DAILY_COMMAND_CENTER_FAILED"
    }
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $Run14A
$V14AExitCode = $LASTEXITCODE
if ($V14AExitCode -ne 0) {
    Write-Host "V18_14A_VALIDATION_STATUS: NONZERO_EXIT_$V14AExitCode"
}

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
    exit $ExitCode
}

Invoke-V18_19AReadabilityRefresh
exit 0
