param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Join-Path $Root "scripts\v18"
$OpsDir = Join-Path $Root "outputs\v18\ops"
$ReadCenterDir = Join-Path $Root "outputs\v18\read_center"

New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$ProfileCsv = Join-Path $OpsDir "V18_7B_CURRENT_MAIN_CHAIN_LINEAR_PROFILE.csv"
$ReportMd = Join-Path $OpsDir "V18_7B_CURRENT_MAIN_CHAIN_LINEAR_REPORT.md"
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

function Invoke-Step {
    param(
        [int]$StepOrder,
        [string]$StepName,
        [string]$ScriptPath,
        [string[]]$ArgList = @()
    )

    if (-not (Test-Path $ScriptPath)) {
        throw "MISSING_SCRIPT: $ScriptPath"
    }

    $SafeName = $StepName -replace '[^A-Za-z0-9_\-]', '_'
    $Log = Join-Path $OpsDir ("V18_7B_STEP_" + $StepOrder + "_" + $SafeName + "_" + $Stamp + ".log")

    $CommandText = $ScriptPath
    if ($ArgList.Count -gt 0) {
        $CommandText = $CommandText + " " + ($ArgList -join " ")
    }

    Write-Host ""
    Write-Host "=== V18.7B STEP $StepOrder START: $StepName ==="
    Write-Host "COMMAND: $CommandText"
    Write-Host "LOG: $Log"

    $Start = Get-Date
    $Status = "OK"
    $Err = ""

    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @ArgList *>&1 | Tee-Object -FilePath $Log

        if ($LASTEXITCODE -ne 0) {
            $Status = "FAIL_EXIT_CODE_$LASTEXITCODE"
            $Err = "LASTEXITCODE=$LASTEXITCODE"
            throw $Err
        }
    }
    catch {
        $Status = "FAIL"
        $Err = $_.Exception.Message
        $End = Get-Date
        Add-Row -StepOrder $StepOrder -StepName $StepName -StartTime $Start -EndTime $End -Status $Status -Command $CommandText -LogPath $Log -ErrorMessage $Err
        $Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ProfileCsv
        throw
    }

    $End = Get-Date
    Add-Row -StepOrder $StepOrder -StepName $StepName -StartTime $Start -EndTime $End -Status $Status -Command $CommandText -LogPath $Log -ErrorMessage $Err

    Write-Host "=== V18.7B STEP $StepOrder DONE: $StepName | SECONDS: $([Math]::Round(($End-$Start).TotalSeconds, 3)) ==="
}

Write-Host ""
Write-Host "=== V18.7B MAIN CHAIN LINEAR OPTIMIZER START ==="
Write-Host "ROOT: $Root"
Write-Host "STAMP: $Stamp"

$TotalStart = Get-Date

$RuntimeAudit = Join-Path $ScriptDir "run_v18_4C_runtime_dependency_audit.ps1"
$OldFinal = Join-Path $ScriptDir "run_v18_4B_R1_final_daily_wrapper.ps1"
$V18_4C = Join-Path $ScriptDir "run_v18_4C_R1_final_daily_wrapper.ps1"
$V18_4D = Join-Path $ScriptDir "run_v18_4D_factor_pack_audit.ps1"
$V18_4E = Join-Path $ScriptDir "run_v18_7C_factor_output_forward_tracking_audit_fast.ps1"
$V18_4F = Join-Path $ScriptDir "run_v18_4F_forward_tracker_factor_coverage_repair.ps1"
$V18_4G = Join-Path $ScriptDir "run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1"
$V18_4I = Join-Path $ScriptDir "run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"
$V18_4J_Cleanup = Join-Path $ScriptDir "run_v18_4J_read_center_cleanup.ps1"

Invoke-Step -StepOrder 1 -StepName "V18.4C_RUNTIME_AUDIT_ONCE" -ScriptPath $RuntimeAudit -ArgList @("-Root", $Root, "-Entry", $OldFinal)

Invoke-Step -StepOrder 2 -StepName "V18.4C_FINAL_DAILY_SKIP_AUDIT" -ScriptPath $V18_4C -ArgList @("-SkipAudit")

Invoke-Step -StepOrder 3 -StepName "V18.4D_FACTOR_PACK_AUDIT_REUSE_RUNTIME" -ScriptPath $V18_4D -ArgList @("-SkipRuntimeRefresh")

Invoke-Step -StepOrder 4 -StepName "V18.4E_FACTOR_OUTPUT_FORWARD_AUDIT_REUSE_AUDITS" -ScriptPath $V18_4E -ArgList @("-SkipRuntimeRefresh", "-SkipFactorPackRefresh")

Invoke-Step -StepOrder 5 -StepName "V18.4F_FORWARD_TRACKER_FACTOR_COVERAGE" -ScriptPath $V18_4F

Invoke-Step -StepOrder 6 -StepName "V18.4G_SUMMARY_ONLY" -ScriptPath $V18_4G -ArgList @("-SkipFinalDaily", "-SkipFactorAudit")

Invoke-Step -StepOrder 7 -StepName "V18.4I_PROMOTION_MERGE_SKIP_UPSTREAM" -ScriptPath $V18_4I -ArgList @("-SkipUpstream")

Invoke-Step -StepOrder 8 -StepName "V18.4J_READ_CENTER_CLEANUP_ONLY" -ScriptPath $V18_4J_Cleanup

$TotalEnd = Get-Date

Add-Row -StepOrder 999 -StepName "TOTAL_V18_7B_MAIN_CHAIN_LINEAR" -StartTime $TotalStart -EndTime $TotalEnd -Status "OK" -Command "V18.7B linear optimized main-chain run" -LogPath ""

$Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ProfileCsv

$TotalRow = $Rows | Where-Object { $_.step_order -eq 999 } | Select-Object -First 1
$Sorted = $Rows | Sort-Object step_order
$Slowest = $Rows | Where-Object { $_.step_order -ne 999 } | Sort-Object elapsed_seconds -Descending

$MainReadFirst = Join-Path $ReadCenterDir "V18_CURRENT_READ_FIRST.md"
$MainReadCenter = Join-Path $ReadCenterDir "V18_4J_CURRENT_READ_CENTER.md"

$OfficialImpact = "UNKNOWN"
$FinalAction = "UNKNOWN"
$BuyPermission = "UNKNOWN"

if (Test-Path $MainReadFirst) {
    $Txt = Get-Content $MainReadFirst -Raw -Encoding UTF8

    if ($Txt -match "OFFICIAL_DECISION_IMPACT:\s*([A-Z_]+)") {
        $OfficialImpact = $Matches[1]
    }

    if ($Txt -match "FINAL_ACTION:\s*([A-Z_]+)") {
        $FinalAction = $Matches[1]
    }

    if ($Txt -match "BUY_PERMISSION:\s*([A-Z_]+)") {
        $BuyPermission = $Matches[1]
    }
}

$Md = New-Object System.Collections.Generic.List[string]
$Md.Add("# V18.7B Main Chain Linear Optimizer")
$Md.Add("")
$Md.Add("Generated: ``$Stamp``")
$Md.Add("")
$Md.Add("## 1. Status")
$Md.Add("")
$Md.Add("- V18_7B_STATUS: ``OK_MAIN_CHAIN_LINEAR_READY``")
$Md.Add("- TOTAL_SECONDS: ``$($TotalRow.elapsed_seconds)``")
$Md.Add("- FINAL_ACTION: ``$FinalAction``")
$Md.Add("- BUY_PERMISSION: ``$BuyPermission``")
$Md.Add("- OFFICIAL_DECISION_IMPACT: ``$OfficialImpact``")
$Md.Add("- PROFILE_CSV: ``$ProfileCsv``")
$Md.Add("")
$Md.Add("## 2. Step Timing")
$Md.Add("")
$Md.Add("| step_order | step_name | elapsed_seconds | status |")
$Md.Add("|---:|---|---:|---|")

foreach ($R in $Sorted) {
    $Md.Add("| $($R.step_order) | $($R.step_name) | $($R.elapsed_seconds) | $($R.status) |")
}

$Md.Add("")
$Md.Add("## 3. Slowest Steps")
$Md.Add("")
$Md.Add("| rank | step_name | elapsed_seconds |")
$Md.Add("|---:|---|---:|")

$Rank = 1
foreach ($R in $Slowest) {
    $Md.Add("| $Rank | $($R.step_name) | $($R.elapsed_seconds) |")
    $Rank += 1
}

$Md.Add("")
$Md.Add("## 4. Interpretation")
$Md.Add("")
$Md.Add("- This wrapper linearizes the V18.4J main chain.")
$Md.Add("- It prevents V18.4J -> V18.4I -> V18.4G from recursively rerunning the full upstream stack.")
$Md.Add("- It does not change factor definitions or official decision logic.")
$Md.Add("- V18.4D and V18.4E still run normally in this simplified version.")

$Md | Set-Content -Encoding UTF8 -Path $ReportMd

$Read = @"
V18.7B MAIN CHAIN LINEAR OPTIMIZER READ FIRST

STATUS:
OK_MAIN_CHAIN_LINEAR_READY

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

$Read | Set-Content -Encoding UTF8 -Path $ReadFirst

Write-Host ""
Write-Host "=== V18.7B MAIN CHAIN LINEAR OPTIMIZER READY ==="
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
