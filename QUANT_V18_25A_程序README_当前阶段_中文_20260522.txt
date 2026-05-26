Set-Location "D:\us-tech-quant"
& "D:\us-tech-quant\.venv\Scripts\Activate.ps1"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1" `
  -RunUniverseRollingScan `
  -RunForwardTracker `
  -RunManualFeedback `
  -RunCandidateSourceNormalization `
  -RunUniverseCandidateAudit `
  -RunLeanInspiredStrategyMotifLab `
  -RunShadowPortfolioConstruction `
  -RunShadowPortfolioForwardBridge `
  -ApplyShadowPortfolioSnapshot `
  -RunTradeReadinessRefresh `
  -RunChineseHomepage `
  -RunFreshnessGuard



Get-Content "D:\us-tech-quant\outputs\v18\ops\V18_38C_READ_FIRST.txt"
Get-Content "D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md"
Get-Content "D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md"
Get-Content "D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md"