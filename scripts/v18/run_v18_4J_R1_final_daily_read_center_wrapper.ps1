$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"

$FinalDailyPromotionWrapper = Join-Path $Root "scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"
$ReadCenterWrapper = Join-Path $Root "scripts\v18\run_v18_4J_read_center_cleanup.ps1"

$DailyOutDir = Join-Path $Root "outputs\v18\daily_integrated"
$ReadCenterDir = Join-Path $Root "outputs\v18\read_center"
$OpsDir = Join-Path $Root "outputs\v18\ops"

New-Item -ItemType Directory -Force -Path $DailyOutDir | Out-Null
New-Item -ItemType Directory -Force -Path $ReadCenterDir | Out-Null
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$FinalReadFirst = Join-Path $DailyOutDir "V18_4J_R1_READ_FIRST.txt"
$CurrentReadFirst = Join-Path $ReadCenterDir "V18_CURRENT_READ_FIRST.md"
$ReadCenter = Join-Path $ReadCenterDir "V18_4J_CURRENT_READ_CENTER.md"
$ReadCenterTxt = Join-Path $ReadCenterDir "V18_4J_READ_FIRST.txt"
$Checkpoint = Join-Path $OpsDir "V18_4J_R1_CHECKPOINT.txt"

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$CheckpointLines = @()
$CheckpointLines += "V18_4J_R1_CHECKPOINT_START: $Now"
Set-Content -Path $Checkpoint -Value $CheckpointLines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4J-R1 FINAL DAILY READ CENTER WRAPPER START ==="

if (!(Test-Path $FinalDailyPromotionWrapper)) {
    throw "Missing final daily promotion wrapper: $FinalDailyPromotionWrapper"
}

if (!(Test-Path $ReadCenterWrapper)) {
    throw "Missing read center wrapper: $ReadCenterWrapper"
}

Write-Host ""
Write-Host "STEP 1: run V18.4I-R1 final daily promotion merge wrapper"

$CheckpointLines += "STEP_1_START: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
Set-Content -Path $Checkpoint -Value $CheckpointLines -Encoding UTF8

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $FinalDailyPromotionWrapper

$Step1Exit = $LASTEXITCODE

$CheckpointLines += "STEP_1_EXIT_CODE: $Step1Exit"
$CheckpointLines += "STEP_1_END: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
Set-Content -Path $Checkpoint -Value $CheckpointLines -Encoding UTF8

if ($Step1Exit -ne 0) {
    throw "V18.4I-R1 final daily promotion merge wrapper failed with exit code $Step1Exit"
}

Write-Host ""
Write-Host "STEP 1 DONE"
Write-Host ""
Write-Host "STEP 2: refresh V18.4J read center from updated outputs"

$CheckpointLines += "STEP_2_START: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
Set-Content -Path $Checkpoint -Value $CheckpointLines -Encoding UTF8

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ReadCenterWrapper

$Step2Exit = $LASTEXITCODE

$CheckpointLines += "STEP_2_EXIT_CODE: $Step2Exit"
$CheckpointLines += "STEP_2_END: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
Set-Content -Path $Checkpoint -Value $CheckpointLines -Encoding UTF8

if ($Step2Exit -ne 0) {
    throw "V18.4J read center cleanup failed with exit code $Step2Exit"
}

Write-Host ""
Write-Host "STEP 2 DONE"

if (!(Test-Path $CurrentReadFirst)) {
    throw "Missing current read first: $CurrentReadFirst"
}

if (!(Test-Path $ReadCenter)) {
    throw "Missing read center: $ReadCenter"
}

if (!(Test-Path $ReadCenterTxt)) {
    throw "Missing read center txt: $ReadCenterTxt"
}

$ReadCenterTxtContent = Get-Content $ReadCenterTxt -Raw -Encoding UTF8
$Now2 = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Lines = @()
$Lines += "V18_4J_R1_STATUS: OK_FINAL_DAILY_READ_CENTER_READY"
$Lines += "GENERATED_AT: $Now2"
$Lines += ""
$Lines += "FINAL_DAILY_COMMAND:"
$Lines += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1"'
$Lines += ""
$Lines += "UPSTREAM_FINAL_DAILY_PROMOTION_WRAPPER: $FinalDailyPromotionWrapper"
$Lines += "READ_CENTER_WRAPPER: $ReadCenterWrapper"
$Lines += ""
$Lines += "CURRENT_READ_FIRST: $CurrentReadFirst"
$Lines += "READ_CENTER: $ReadCenter"
$Lines += "READ_CENTER_TXT: $ReadCenterTxt"
$Lines += "CHECKPOINT: $Checkpoint"
$Lines += ""
$Lines += "SAFETY:"
$Lines += "OFFICIAL_DECISION_IMPACT: NONE"
$Lines += "PROMOTION_ACTION: NONE"
$Lines += "DIRECT_PROMOTION: NO"
$Lines += ""
$Lines += "READ_CENTER_CONTEXT:"
$Lines += $ReadCenterTxtContent

Set-Content -Path $FinalReadFirst -Value $Lines -Encoding UTF8

$CheckpointLines += "FINAL_READ_FIRST_CREATED: $FinalReadFirst"
$CheckpointLines += "V18_4J_R1_STATUS: OK_FINAL_DAILY_READ_CENTER_READY"
$CheckpointLines += "DONE: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
Set-Content -Path $Checkpoint -Value $CheckpointLines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4J-R1 FINAL DAILY READ CENTER WRAPPER READY ==="
Write-Host "V18_4J_R1_STATUS: OK_FINAL_DAILY_READ_CENTER_READY"
Write-Host "FINAL_DAILY_COMMAND:"
Write-Host 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1"'
Write-Host "CURRENT_READ_FIRST: $CurrentReadFirst"
Write-Host "READ_CENTER: $ReadCenter"
Write-Host "FINAL_READ_FIRST: $FinalReadFirst"
Write-Host "CHECKPOINT: $Checkpoint"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "PROMOTION_ACTION: NONE"
Write-Host "DIRECT_PROMOTION: NO"

Write-Host ""
Write-Host "=== V18.4J-R1 FINAL DAILY READ CENTER WRAPPER DONE ==="