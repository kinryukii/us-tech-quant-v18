param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Join-Path $Root "scripts\v18"
$OpsDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ProfileCsv = Join-Path $OpsDir "V18_7A_CURRENT_FULL_SPEED_PROFILE.csv"
$ProfileMd = Join-Path $OpsDir "V18_7A_CURRENT_FULL_SPEED_PROFILE.md"
$ReadFirst = Join-Path $OpsDir "V18_7A_READ_FIRST.txt"

$Rows = New-Object System.Collections.Generic.List[object]

function Add-SpeedRow {
    param(
        [int]$StepOrder,
        [string]$StepName,
        [datetime]$StartTime,
        [datetime]$EndTime,
        [string]$Status,
        [string]$Command,
        [string]$StepLog,
        [string]$ErrorMessage = ""
    )

    $Rows.Add([pscustomobject]@{
        run_id = $RunId
        step_order = $StepOrder
        step_name = $StepName
        start_time = $StartTime.ToString("yyyy-MM-dd HH:mm:ss")
        end_time = $EndTime.ToString("yyyy-MM-dd HH:mm:ss")
        elapsed_seconds = [Math]::Round(($EndTime - $StartTime).TotalSeconds, 3)
        status = $Status
        command = $Command
        step_log = $StepLog
        error_message = $ErrorMessage
    }) | Out-Null
}

function Invoke-SpeedStep {
    param(
        [int]$StepOrder,
        [string]$StepName,
        [string]$ScriptPath,
        [string[]]$ArgList = @()
    )

    if (-not (Test-Path $ScriptPath)) {
        $start = Get-Date
        $end = Get-Date
        Add-SpeedRow `
            -StepOrder $StepOrder `
            -StepName $StepName `
            -StartTime $start `
            -EndTime $end `
            -Status "MISSING_SCRIPT" `
            -Command $ScriptPath `
            -StepLog "" `
            -ErrorMessage "Script not found"
        throw "Missing script: $ScriptPath"
    }

    $StepSafe = ($StepName -replace '[^A-Za-z0-9_\-]', '_')
    $StepLog = Join-Path $OpsDir ("V18_7A_STEP_" + $StepOrder + "_" + $StepSafe + "_" + $RunId + ".log")

    $CommandText = $ScriptPath
    if ($ArgList.Count -gt 0) {
        $CommandText = $CommandText + " " + ($ArgList -join " ")
    }

    Write-Host ""
    Write-Host "=== V18.7A STEP $StepOrder START: $StepName ==="
    Write-Host "COMMAND: $CommandText"
    Write-Host "LOG: $StepLog"

    $start = Get-Date
    $status = "OK"
    $err = ""

    try {
        & $ScriptPath @ArgList 2>&1 | Tee-Object -FilePath $StepLog

        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            $status = "FAIL_EXIT_CODE_$LASTEXITCODE"
            $err = "LASTEXITCODE=$LASTEXITCODE"
            throw $err
        }
    } catch {
        $status = "FAIL"
        $err = $_.Exception.Message
        $end = Get-Date

        Add-SpeedRow `
            -StepOrder $StepOrder `
            -StepName $StepName `
            -StartTime $start `
            -EndTime $end `
            -Status $status `
            -Command $CommandText `
            -StepLog $StepLog `
            -ErrorMessage $err

        $Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ProfileCsv
        throw
    }

    $end = Get-Date

    Add-SpeedRow `
        -StepOrder $StepOrder `
        -StepName $StepName `
        -StartTime $start `
        -EndTime $end `
        -Status $status `
        -Command $CommandText `
        -StepLog $StepLog `
        -ErrorMessage $err

    Write-Host "=== V18.7A STEP $StepOrder DONE: $StepName | SECONDS: $([Math]::Round(($end-$start).TotalSeconds, 3)) ==="
}

Write-Host ""
Write-Host "=== V18.7A FULL SPEED PROFILE START ==="
Write-Host "ROOT: $Root"
Write-Host "RUN_ID: $RunId"

$VenvActivate = Join-Path $Root ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
    Write-Host "VENV_ACTIVATED: $VenvActivate"
}

$TotalStart = Get-Date

try {
    Invoke-SpeedStep `
        -StepOrder 1 `
        -StepName "V18.4J_MAIN_FINAL_DAILY_READ_CENTER" `
        -ScriptPath (Join-Path $ScriptDir "run_v18_4J_R1_final_daily_read_center_wrapper.ps1")

    Invoke-SpeedStep `
        -StepOrder 2 `
        -StepName "V18.6A_TECHNICAL_TIMING_SHADOW_REFRESH" `
        -ScriptPath (Join-Path $ScriptDir "run_v18_6A_technical_timing_shadow.ps1")

    Invoke-SpeedStep `
        -StepOrder 3 `
        -StepName "V18.6C_R1_TECHNICAL_FRESHNESS_GUARD_FROM_CURRENT" `
        -ScriptPath (Join-Path $ScriptDir "run_v18_6C_R1_technical_timing_forward_tracker_freshness_guard.ps1")

    Invoke-SpeedStep `
        -StepOrder 4 `
        -StepName "V18.6D_TECHNICAL_TIMING_READ_CENTER_FROM_CURRENT" `
        -ScriptPath (Join-Path $ScriptDir "run_v18_6D_technical_timing_read_center.ps1")

    Invoke-SpeedStep `
        -StepOrder 5 `
        -StepName "V18.6E_FINAL_READ_CENTER_WITH_TECHNICAL" `
        -ScriptPath (Join-Path $ScriptDir "run_v18_6E_final_read_center_with_technical.ps1")

    $TotalEnd = Get-Date

    Add-SpeedRow `
        -StepOrder 999 `
        -StepName "TOTAL_FULL_PROFILED_RUN" `
        -StartTime $TotalStart `
        -EndTime $TotalEnd `
        -Status "OK" `
        -Command "V18.7A profiled full run" `
        -StepLog "" `
        -ErrorMessage ""

} catch {
    $TotalEnd = Get-Date

    Add-SpeedRow `
        -StepOrder 999 `
        -StepName "TOTAL_FULL_PROFILED_RUN" `
        -StartTime $TotalStart `
        -EndTime $TotalEnd `
        -Status "FAIL" `
        -Command "V18.7A profiled full run" `
        -StepLog "" `
        -ErrorMessage $_.Exception.Message

    $Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ProfileCsv
    throw
}

$Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ProfileCsv

$Sorted = $Rows | Sort-Object step_order
$Slowest = $Rows | Where-Object { $_.step_order -ne 999 } | Sort-Object elapsed_seconds -Descending
$TotalRow = $Rows | Where-Object { $_.step_order -eq 999 } | Select-Object -First 1

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# V18.7A Full Speed Profile")
$md.Add("")
$md.Add("Generated: ``$RunId``")
$md.Add("")
$md.Add("## 1. Status")
$md.Add("")
$md.Add("- V18_7A_STATUS: ``OK_FULL_SPEED_PROFILE_READY``")
$md.Add("- ROOT: ``$Root``")
$md.Add("- TOTAL_SECONDS: ``$($TotalRow.elapsed_seconds)``")
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

$rank = 1
foreach ($r in $Slowest) {
    $md.Add("| $rank | $($r.step_name) | $($r.elapsed_seconds) |")
    $rank += 1
}

$md.Add("")
$md.Add("## 4. Interpretation")
$md.Add("")
$md.Add("- If V18.4J dominates runtime, optimize repeated audit scans and main-chain IO first.")
$md.Add("- If V18.6C-R1 dominates runtime, optimize V18.6A technical engine: batch download + vectorized indicators.")
$md.Add("- If V18.6D or V18.6E dominates runtime, optimize read-center file IO and markdown generation.")
$md.Add("- This profiler does not change official decision logic.")

$md | Set-Content -Encoding UTF8 -Path $ProfileMd

$read = @"
V18.7A FULL SPEED PROFILE READ FIRST

STATUS:
OK_FULL_SPEED_PROFILE_READY

TOTAL_SECONDS:
$($TotalRow.elapsed_seconds)

PROFILE:
$ProfileCsv

REPORT:
$ProfileMd

RUN_ID:
$RunId
"@

$read | Set-Content -Encoding UTF8 -Path $ReadFirst

Write-Host ""
Write-Host "=== V18.7A FULL SPEED PROFILE READY ==="
Write-Host "TOTAL_SECONDS: $($TotalRow.elapsed_seconds)"
Write-Host "PROFILE: $ProfileCsv"
Write-Host "REPORT: $ProfileMd"
Write-Host "READ_FIRST: $ReadFirst"
Write-Host ""
Write-Host "=== SLOWEST STEPS ==="
$Slowest | Format-Table step_name, elapsed_seconds, status -AutoSize

Write-Host ""
Write-Host "=== V18.7A FULL SPEED PROFILE DONE ==="

