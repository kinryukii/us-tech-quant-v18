param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ScriptDir = Join-Path $Root "scripts\v18"
$OpsDir = Join-Path $Root "outputs\v18\ops"
$DailyOutDir = Join-Path $Root "outputs\v18\daily_integrated"
$ReadCenterDir = Join-Path $Root "outputs\v18\read_center"

New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null
New-Item -ItemType Directory -Force -Path $DailyOutDir | Out-Null
New-Item -ItemType Directory -Force -Path $ReadCenterDir | Out-Null

$ProfileCsv = Join-Path $OpsDir "V18_7B_CURRENT_MAIN_CHAIN_DEDUP_PROFILE.csv"
$ReportMd = Join-Path $OpsDir "V18_7B_CURRENT_MAIN_CHAIN_DEDUP_REPORT.md"
$ReadFirst = Join-Path $OpsDir "V18_7B_READ_FIRST.txt"

$Rows = New-Object System.Collections.Generic.List[object]

function Add-Row {
    param(
        [int]$StepOrder,
        [string]$StepName,
        [datetime]$StartTime,
        [datetime]$EndTime,
        [string]$Status,
        [string]$Command,
        [string]$LogPath,
        [string]$ErrorMessage = ""
    )

    $Rows.Add([pscustomobject]@{
        stamp = $Stamp
        step_order = $StepOrder
        step_name = $StepName
        start_time = $StartTime.ToString("yyyy-MM-dd HH:mm:ss")
        end_time = $EndTime.ToString("yyyy-MM-dd HH:mm:ss")
        elapsed_seconds = [Math]::Round(($EndTime - $StartTime).TotalSeconds, 3)
        status = $Status
        command = $Command
        log_path = $LogPath
        error_message = $ErrorMessage
    }) | Out-Null
}

function Test-ScriptParam {
    param(
        [string]$ScriptPath,
        [string]$ParamName
    )

    try {
        $cmd = Get-Command $ScriptPath -ErrorAction Stop
        return $cmd.Parameters.ContainsKey($ParamName)
    }
    catch {
        return $false
    }
}

function Invoke-Step {
    param(
        [int]$StepOrder,
        [string]$StepName,
        [string]$ScriptPath,
        [string[]]$ArgList = @()
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        throw "MISSING_SCRIPT: $ScriptPath"
    }

    $safe = $StepName -replace '[^A-Za-z0-9_\-]', '_'
    $log = Join-Path $OpsDir ("V18_7B_STEP_" + $StepOrder + "_" + $safe + "_" + $Stamp + ".log")

    $cmdText = $ScriptPath
    if ($ArgList.Count -gt 0) {
        $cmdText = $cmdText + " " + ($ArgList -join " ")
    }

    Write-Host ""
    Write-Host "=== V18.7B STEP $StepOrder START: $StepName ==="
    Write-Host "COMMAND: $cmdText"
    Write-Host "LOG: $log"

    $s = Get-Date
    $status = "OK"
    $err = ""

    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @ArgList *>&1 | Tee-Object -FilePath $log

        if ($LASTEXITCODE -ne 0) {
            $status = "FAIL_EXIT_CODE_$LASTEXITCODE"
            $err = "LASTEXITCODE=$LASTEXITCODE"
            throw $err
        }
    }
    catch {
        $status = "FAIL"
        $err = $_.Exception.Message
        $e = Get-Date
        Add-Row -StepOrder $StepOrder -StepName $StepName -StartTime $s -EndTime $e -Status $status -Command $cmdText -LogPath $log -ErrorMessage $err
        $Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ProfileCsv
        throw
    }

    $e = Get-Date
    Add-Row -StepOrder $StepOrder -StepName $StepName -StartTime $s -EndTime $e -Status $status -Command $cmdText -LogPath $log -ErrorMessage $err

    Write-Host "=== V18.7B STEP $StepOrder DONE: $StepName | SECONDS: $([Math]::Round(($e-$s).TotalSeconds, 3)) ==="
}

Write-Host ""
Write-Host "=== V18.7B MAIN CHAIN AUDIT DEDUP OPTIMIZER START ==="
Write-Host "ROOT: $Root"
Write-Host "STAMP: $Stamp"

$TotalStart = Get-Date

$RuntimeAudit = Join-Path $ScriptDir "run_v18_4C_runtime_dependency_audit.ps1"
$OldFinal = Join-Path $ScriptDir "run_v18_4B_R1_final_daily_wrapper.ps1"
$V18_4C = Join-Path $ScriptDir "run_v18_4C_R1_final_daily_wrapper.ps1"
$V18_4D = Join-Path $ScriptDir "run_v18_4D_factor_pack_audit.ps1"
$V18_4E = Join-Path $ScriptDir "run_v18_4E_factor_output_forward_tracking_audit.ps1"
$V18_4F = Join-Path $ScriptDir "run_v18_4F_forward_tracker_factor_coverage_repair.ps1"
$V18_4G = Join-Path $ScriptDir "run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1"
$V18_4I = Join-Path $ScriptDir "run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"
$V18_4J_Cleanup = Join-Path $ScriptDir "run_v18_4J_read_center_cleanup.ps1"

# 1. Runtime audit once
Invoke-Step `
    -StepOrder 1 `
    -StepName "V18.4C_RUNTIME_AUDIT_ONCE" `
    -ScriptPath $RuntimeAudit `
    -ArgList @("-Root", $Root, "-Entry", $OldFinal)

# 2. Final daily chain without repeated runtime audit
Invoke-Step `
    -StepOrder 2 `
    -StepName "V18.4C_FINAL_DAILY_SKIP_RUNTIME_AUDIT" `
    -ScriptPath $V18_4C `
    -ArgList @("-SkipAudit")

# 3. Factor pack audit, reuse runtime graph if patched
$Args4D = @()
if (Test-ScriptParam -ScriptPath $V18_4D -ParamName "SkipRuntimeRefresh") {
    $Args4D += "-SkipRuntimeRefresh"
}

Invoke-Step `
    -StepOrder 3 `
    -StepName "V18.4D_FACTOR_PACK_AUDIT_REUSE_RUNTIME" `
    -ScriptPath $V18_4D `
    -ArgList $Args4D

# 4. Factor output + forward audit, reuse runtime/factor audit if patched
$Args4E = @()
if (Test-ScriptParam -ScriptPath $V18_4E -ParamName "SkipRuntimeRefresh") {
    $Args4E += "-SkipRuntimeRefresh"
}
if (Test-ScriptParam -ScriptPath $V18_4E -ParamName "SkipFactorPackRefresh") {
    $Args4E += "-SkipFactorPackRefresh"
}

Invoke-Step `
    -StepOrder 4 `
    -StepName "V18.4E_FACTOR_OUTPUT_FORWARD_AUDIT_REUSE_AUDITS" `
    -ScriptPath $V18_4E `
    -ArgList $Args4E

# 5. Forward tracker factor coverage
Invoke-Step `
    -StepOrder 5 `
    -StepName "V18.4F_FORWARD_TRACKER_FACTOR_COVERAGE" `
    -ScriptPath $V18_4F

# 6. Build V18.4G summary from current outputs
Invoke-Step `
    -StepOrder 6 `
    -StepName "V18.4G_SUMMARY_FROM_CURRENT_AUDITS" `
    -ScriptPath $V18_4G `
    -ArgList @("-SkipFinalDaily", "-SkipFactorAudit")

# 7. Promotion merge only, skip upstream because current V18.4G already exists
Invoke-Step `
    -StepOrder 7 `
    -StepName "V18.4I_PROMOTION_MERGE_SKIP_UPSTREAM" `
    -ScriptPath $V18_4I `
    -ArgList @("-SkipUpstream")

# 8. Read center cleanup only
Invoke-Step `
    -StepOrder 8 `
    -StepName "V18.4J_READ_CENTER_CLEANUP_ONLY" `
    -ScriptPath $V18_4J_Cleanup

$TotalEnd = Get-Date
Add-Row `
    -StepOrder 999 `
    -StepName "TOTAL_V18_7B_MAIN_CHAIN_DEDUP" `
    -StartTime $TotalStart `
    -EndTime $TotalEnd `
    -Status "OK" `
    -Command "V18.7B optimized main-chain run" `
    -LogPath "" `
    -ErrorMessage ""

$Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ProfileCsv

$Sorted = $Rows | Sort-Object step_order
$Slowest = $Rows | Where-Object { $_.step_order -ne 999 } | Sort-Object elapsed_seconds -Descending
$TotalRow = $Rows | Where-Object { $_.step_order -eq 999 } | Select-Object -First 1

$MainReadFirst = Join-Path $ReadCenterDir "V18_CURRENT_READ_FIRST.md"
$MainReadCenter = Join-Path $ReadCenterDir "V18_4J_CURRENT_READ_CENTER.md"

$OfficialImpact = "UNKNOWN"
$FinalAction = "UNKNOWN"
$BuyPermission = "UNKNOWN"

if (Test-Path -LiteralPath $MainReadFirst) {
    $txt = Get-Content -LiteralPath $MainReadFirst -Raw -Encoding UTF8

    if ($txt -match "OFFICIAL_DECISION_IMPACT:\s*([A-Z_]+)") {
        $OfficialImpact = $Matches[1]
    }
    if ($txt -match "FINAL_ACTION:\s*([A-Z_]+)") {
        $FinalAction = $Matches[1]
    }
    if ($txt -match "BUY_PERMISSION:\s*([A-Z_]+)") {
        $BuyPermission = $Matches[1]
    }
}

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# V18.7B Main Chain Audit Dedup Optimizer")
$md.Add("")
$md.Add("Generated: ``$Stamp``")
$md.Add("")
$md.Add("## 1. Status")
$md.Add("")
$md.Add("- V18_7B_STATUS: ``OK_MAIN_CHAIN_DEDUP_READY``")
$md.Add("- TOTAL_SECONDS: ``$($TotalRow.elapsed_seconds)``")
$md.Add("- FINAL_ACTION: ``$FinalAction``")
$md.Add("- BUY_PERMISSION: ``$BuyPermission``")
$md.Add("- OFFICIAL_DECISION_IMPACT: ``$OfficialImpact``")
$md.Add("- PROFILE_CSV: ``$ProfileCsv``")
$md.Add("")
$md.Add("## 2. Step Timing")
$md.Add("")
$md.Add("| step_order | step_name | elapsed_seconds | status |")
$md.Add("|---:|---|---:|---|")

foreach ($r in $Sorted) {
    $md.Add("| $($r.step_order) | $($r.step_name) | $($r.elapsed_seconds) | $($r.status) |")
}

$md.Add("")
$md.Add("## 3. Slowest Steps")
$md.Add("")
$md.Add("| rank | step_name | elapsed_seconds |")
$md.Add("|---:|---|---:|")

$i = 1
foreach ($r in $Slowest) {
    $md.Add("| $i | $($r.step_name) | $($r.elapsed_seconds) |")
    $i += 1
}

$md.Add("")
$md.Add("## 4. Interpretation")
$md.Add("")
$md.Add("- V18.7B keeps the main chain complete while avoiding repeated audit recomputation inside one run.")
$md.Add("- Runtime audit is computed once, then reused by factor-pack and output-forward audit layers where supported.")
$md.Add("- V18.4G / V18.4I / V18.4J still execute and rebuild current outputs.")
$md.Add("- This optimizer should not change official decision impact.")

$md | Set-Content -Encoding UTF8 -Path $ReportMd

$read = @"
V18.7B MAIN CHAIN AUDIT DEDUP READ FIRST

STATUS:
OK_MAIN_CHAIN_DEDUP_READY

TOTAL_SECONDS:
$($TotalRow.elapsed_seconds)

FINAL_ACTION:
$FinalAction

BUY_PERMISSION:
$BuyPermission

OFFICIAL_DECISION_IMPACT:
$OfficialImpact

PROFILE:
$ProfileCsv

REPORT:
$ReportMd

MAIN_READ_FIRST:
$MainReadFirst

MAIN_READ_CENTER:
$MainReadCenter
"@

$read | Set-Content -Encoding UTF8 -Path $ReadFirst

Write-Host ""
Write-Host "=== V18.7B MAIN CHAIN AUDIT DEDUP READY ==="
Write-Host "TOTAL_SECONDS: $($TotalRow.elapsed_seconds)"
Write-Host "FINAL_ACTION: $FinalAction"
Write-Host "BUY_PERMISSION: $BuyPermission"
Write-Host "OFFICIAL_DECISION_IMPACT: $OfficialImpact"
Write-Host "PROFILE: $ProfileCsv"
Write-Host "REPORT: $ReportMd"
Write-Host "READ_FIRST: $ReadFirst"
Write-Host ""
Write-Host "=== SLOWEST STEPS ==="
$Slowest | Format-Table step_name, elapsed_seconds, status -AutoSize

Write-Host ""
Write-Host "=== V18.7B MAIN CHAIN AUDIT DEDUP DONE ==="
