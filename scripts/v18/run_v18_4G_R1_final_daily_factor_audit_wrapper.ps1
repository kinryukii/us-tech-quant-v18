param(
    [switch]$SkipFinalDaily,
    [switch]$SkipFactorAudit
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$V18 = Join-Path $Root "scripts\v18"
$OutDir = Join-Path $Root "outputs\v18\daily_integrated"
$OpsDir = Join-Path $Root "outputs\v18\ops"
$FactorAuditDir = Join-Path $Root "outputs\v18\factor_audit"

New-Item -ItemType Directory -Force -Path $OutDir, $OpsDir, $FactorAuditDir | Out-Null

$V18_4C = Join-Path $V18 "run_v18_4C_R1_final_daily_wrapper.ps1"
$V18_4D = Join-Path $V18 "run_v18_4D_factor_pack_audit.ps1"
$V18_4E = Join-Path $V18 "run_v18_4E_factor_output_forward_tracking_audit.ps1"
$V18_4F = Join-Path $V18 "run_v18_4F_forward_tracker_factor_coverage_repair.ps1"

$ReadFirst = Join-Path $OutDir "V18_4G_R1_READ_FIRST.txt"
$CurrentFinal = Join-Path $OutDir "V18_CURRENT_FINAL_DAILY.md"

$LogDir = Join-Path $OpsDir ("V18_4G_R1_" + $Stamp)
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host ""
Write-Host "=== V18.4G-R1 FINAL DAILY FACTOR AUDIT WRAPPER START ==="
Write-Host "ROOT: $Root"
Write-Host "STAMP: $Stamp"

function Require-File {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "REQUIRED_FILE_MISSING: $Path"
    }
}

Require-File $V18_4C
Require-File $V18_4D
Require-File $V18_4E
Require-File $V18_4F

if (-not $SkipFinalDaily) {
    Write-Host ""
    Write-Host "STEP 1: V18.4C final daily wrapper"
    $log = Join-Path $LogDir "step1_v18_4C_final_daily.log"
    powershell -NoProfile -ExecutionPolicy Bypass -File $V18_4C *>&1 | Tee-Object -FilePath $log
} else {
    Write-Host ""
    Write-Host "STEP 1 SKIPPED: V18.4C final daily wrapper"
}

if (-not $SkipFactorAudit) {
    Write-Host ""
    Write-Host "STEP 2: V18.4D factor pack audit"
    $log = Join-Path $LogDir "step2_v18_4D_factor_pack_audit.log"
    powershell -NoProfile -ExecutionPolicy Bypass -File $V18_4D *>&1 | Tee-Object -FilePath $log

    Write-Host ""
    Write-Host "STEP 3: V18.4E factor output + forward audit"
    $log = Join-Path $LogDir "step3_v18_4E_factor_output_forward_audit.log"
    powershell -NoProfile -ExecutionPolicy Bypass -File $V18_4E *>&1 | Tee-Object -FilePath $log

    Write-Host ""
    Write-Host "STEP 4: V18.4F forward tracker factor coverage"
    $log = Join-Path $LogDir "step4_v18_4F_forward_factor_coverage.log"
    powershell -NoProfile -ExecutionPolicy Bypass -File $V18_4F *>&1 | Tee-Object -FilePath $log
} else {
    Write-Host ""
    Write-Host "STEP 2-4 SKIPPED: factor audits"
}

# Collect current status files
$RuntimeAuditMd = Join-Path $OpsDir "V18_4C_CURRENT_RUNTIME_DEPENDENCY_AUDIT.md"
$FactorAuditMd = Join-Path $FactorAuditDir "V18_4D_CURRENT_FACTOR_PACK_AUDIT.md"
$OutputAuditMd = Join-Path $FactorAuditDir "V18_4E_CURRENT_FACTOR_OUTPUT_FORWARD_AUDIT.md"
$CoverageMd = Join-Path $FactorAuditDir "V18_4F_CURRENT_FORWARD_FACTOR_COVERAGE.md"

$RuntimeGraph = Join-Path $OpsDir "V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv"
$CoverageCsv = Join-Path $FactorAuditDir "V18_4F_CURRENT_FORWARD_FACTOR_COVERAGE.csv"
$ExpandedSnapshot = Join-Path $Root "state\v18\V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv"

function Get-MdValue {
    param(
        [string]$Path,
        [string]$Key
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }

    $line = Select-String -LiteralPath $Path -Pattern $Key -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 1

    if (-not $line) {
        return ""
    }

    if ($line.Line -match "$([regex]::Escape($Key)):\s*``?([^``\r\n]+)``?") {
        return $matches[1].Trim()
    }

    if ($line.Line -match "$([regex]::Escape($Key))\s*:\s*([^`\r\n]+)") {
        return $matches[1].Trim()
    }

    return $line.Line.Trim()
}

$RuntimeCodeCount = Get-MdValue -Path $RuntimeAuditMd -Key "UNIQUE_EXISTING_CODE_COUNT"
$MissingRefCount = Get-MdValue -Path $RuntimeAuditMd -Key "MISSING_REFERENCE_COUNT"

$WqExpected = Get-MdValue -Path $FactorAuditMd -Key "WORLDQUANT_STYLE_FACTOR_COUNT_EXPECTED"
$WqFound = Get-MdValue -Path $FactorAuditMd -Key "WORLDQUANT_STYLE_FACTOR_FOUND_COUNT"
$WqRuntime = Get-MdValue -Path $FactorAuditMd -Key "WORLDQUANT_STYLE_FACTOR_RUNTIME_HIT_COUNT"

$OutputFound = Get-MdValue -Path $OutputAuditMd -Key "OUTPUT_COLUMN_FOUND_COUNT"
$NonNullFound = Get-MdValue -Path $OutputAuditMd -Key "NON_NULL_VALUE_FACTOR_COUNT"
$RankFound = Get-MdValue -Path $OutputAuditMd -Key "TOP_OR_RANK_OUTPUT_FOUND_COUNT"
$ForwardFoundE = Get-MdValue -Path $OutputAuditMd -Key "FORWARD_TRACKING_FOUND_COUNT"
$SelectedFactor = Get-MdValue -Path $OutputAuditMd -Key "CURRENT_SELECTED_FACTOR"

$ForwardCovered = Get-MdValue -Path $CoverageMd -Key "FORWARD_COVERED_COUNT"
$ForwardMissing = Get-MdValue -Path $CoverageMd -Key "FORWARD_MISSING_COUNT"
$ExpandedRows = Get-MdValue -Path $CoverageMd -Key "EXPANDED_FORWARD_SNAPSHOT_ROWS"
$BestFactorFile = Get-MdValue -Path $CoverageMd -Key "BEST_FACTOR_OUTPUT_FILE"

$FinalAction = ""
$BuyPermission = ""
$TodaySafe = ""
$ActionableBuyCount = ""

if (Test-Path -LiteralPath $CurrentFinal) {
    $FinalAction = Get-MdValue -Path $CurrentFinal -Key "FINAL_ACTION"
    $BuyPermission = Get-MdValue -Path $CurrentFinal -Key "BUY_PERMISSION"
    $TodaySafe = Get-MdValue -Path $CurrentFinal -Key "TODAY_SAFE"
    $ActionableBuyCount = Get-MdValue -Path $CurrentFinal -Key "ACTIONABLE_BUY_COUNT_TODAY"
}

$Status = "OK_FINAL_DAILY_FACTOR_AUDIT_READY"

if ($MissingRefCount -ne "" -and $MissingRefCount -ne "0") {
    $Status = "WARN_MISSING_REFERENCES"
}

if ($WqExpected -ne "" -and $WqFound -ne "" -and $WqExpected -ne $WqFound) {
    $Status = "WARN_WORLDQUANT_FACTOR_NOT_FULLY_FOUND"
}

if ($ForwardMissing -ne "" -and $ForwardMissing -ne "0") {
    $Status = "WARN_FORWARD_FACTOR_COVERAGE_INCOMPLETE"
}

$Read = @()
$Read += "V18.4G-R1 FINAL DAILY FACTOR AUDIT"
$Read += ""
$Read += "生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$Read += ""
$Read += "STATUS: $Status"
$Read += ""
$Read += "=== DAILY DECISION ==="
$Read += "FINAL_ACTION: $FinalAction"
$Read += "TODAY_SAFE: $TodaySafe"
$Read += "BUY_PERMISSION: $BuyPermission"
$Read += "ACTIONABLE_BUY_COUNT_TODAY: $ActionableBuyCount"
$Read += ""
$Read += "=== RUNTIME AUDIT ==="
$Read += "RUNTIME_CODE_COUNT: $RuntimeCodeCount"
$Read += "MISSING_REFERENCE_COUNT: $MissingRefCount"
$Read += ""
$Read += "=== WORLDQUANT-STYLE FACTORS ==="
$Read += "WORLDQUANT_STYLE_FACTOR_COUNT_EXPECTED: $WqExpected"
$Read += "WORLDQUANT_STYLE_FACTOR_FOUND_COUNT: $WqFound"
$Read += "WORLDQUANT_STYLE_FACTOR_RUNTIME_HIT_COUNT: $WqRuntime"
$Read += ""
$Read += "=== FACTOR OUTPUT AUDIT ==="
$Read += "OUTPUT_COLUMN_FOUND_COUNT: $OutputFound"
$Read += "NON_NULL_VALUE_FACTOR_COUNT: $NonNullFound"
$Read += "TOP_OR_RANK_OUTPUT_FOUND_COUNT: $RankFound"
$Read += "FORWARD_TRACKING_FOUND_COUNT_V18_4E: $ForwardFoundE"
$Read += "CURRENT_SELECTED_FACTOR: $SelectedFactor"
$Read += ""
$Read += "=== FORWARD FACTOR COVERAGE ==="
$Read += "FORWARD_COVERED_COUNT: $ForwardCovered"
$Read += "FORWARD_MISSING_COUNT: $ForwardMissing"
$Read += "EXPANDED_FORWARD_SNAPSHOT_ROWS: $ExpandedRows"
$Read += "BEST_FACTOR_OUTPUT_FILE: $BestFactorFile"
$Read += ""
$Read += "=== IMPORTANT FILES ==="
$Read += "CURRENT_FINAL_DAILY: $CurrentFinal"
$Read += "RUNTIME_AUDIT: $RuntimeAuditMd"
$Read += "FACTOR_PACK_AUDIT: $FactorAuditMd"
$Read += "FACTOR_OUTPUT_AUDIT: $OutputAuditMd"
$Read += "FORWARD_COVERAGE_AUDIT: $CoverageMd"
$Read += "EXPANDED_FACTOR_SNAPSHOT: $ExpandedSnapshot"
$Read += "LOG_DIR: $LogDir"
$Read += ""
$Read += "=== OFFICIAL IMPACT ==="
$Read += "F006-F011 official decision impact remains NONE unless promotion rules activate after enough forward outcomes."
$Read += ""
$Read += "NEXT_DAILY_COMMAND:"
$Read += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1"'

$Read -join "`r`n" | Set-Content -Encoding UTF8 -LiteralPath $ReadFirst

Write-Host ""
Write-Host "=== V18.4G-R1 FINAL DAILY FACTOR AUDIT READY ==="
Write-Host "STATUS: $Status"
Write-Host "RUNTIME_CODE_COUNT: $RuntimeCodeCount"
Write-Host "MISSING_REFERENCE_COUNT: $MissingRefCount"
Write-Host "WORLDQUANT_STYLE_FACTOR_FOUND_COUNT: $WqFound"
Write-Host "WORLDQUANT_STYLE_FACTOR_RUNTIME_HIT_COUNT: $WqRuntime"
Write-Host "OUTPUT_COLUMN_FOUND_COUNT: $OutputFound"
Write-Host "NON_NULL_VALUE_FACTOR_COUNT: $NonNullFound"
Write-Host "TOP_OR_RANK_OUTPUT_FOUND_COUNT: $RankFound"
Write-Host "FORWARD_COVERED_COUNT: $ForwardCovered"
Write-Host "FORWARD_MISSING_COUNT: $ForwardMissing"
Write-Host "EXPANDED_FORWARD_SNAPSHOT_ROWS: $ExpandedRows"
Write-Host "CURRENT_SELECTED_FACTOR: $SelectedFactor"
Write-Host ""
Write-Host "READ FIRST:"
Write-Host $ReadFirst
Write-Host ""
Write-Host "NEXT DAILY COMMAND:"
Write-Host 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1"'
