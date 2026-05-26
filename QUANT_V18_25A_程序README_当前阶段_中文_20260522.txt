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



  Get-Content "D:\us-tech-quant\outputs\v18\ops\V18_37C_READ_FIRST.txt"
Get-Content "D:\us-tech-quant\outputs\v18\ops\V18_34B_READ_FIRST.txt"
Get-Content "D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md"
Get-Content "D:\us-tech-quant\outputs\v18\read_center\V18_CURRENT_SHADOW_PORTFOLIO_FORWARD_BRIDGE.md"
