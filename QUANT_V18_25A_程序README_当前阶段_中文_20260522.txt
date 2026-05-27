Set-Location "D:\us-tech-quant"
.\.venv\Scripts\Activate.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\v18\run_v18_41A_daily_clean_operator_pipeline.ps1"

Get-Content ".\outputs\v18\ops\V18_41A_READ_FIRST.txt"
ii ".\outputs\v18\read_center\V18_CURRENT_DAILY_CLEAN_OPERATOR_STATUS.md"

Import-Csv ".\outputs\v18\signals\V18_39A_ALPHA_SIGNAL_OBJECTS.csv" |
Where-Object { $_.alpha_direction -eq "LONG_CANDIDATE" } |
Select-Object ticker, rank, rank_bucket, alpha_direction, alpha_confidence, confidence_score_numeric |
Format-Table -AutoSize