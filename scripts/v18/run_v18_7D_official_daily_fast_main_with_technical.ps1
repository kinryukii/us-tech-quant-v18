param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Join-Path $Root "scripts\v18"
$OpsDir = Join-Path $Root "outputs\v18\ops"
$ReadCenterDir = Join-Path $Root "outputs\v18\read_center"

New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$ProfileCsv = Join-Path $OpsDir "V18_7D_CURRENT_OFFICIAL_DAILY_FAST_MAIN_WITH_TECHNICAL_PROFILE.csv"
$ReportMd = Join-Path $OpsDir "V18_7D_CURRENT_OFFICIAL_DAILY_FAST_MAIN_WITH_TECHNICAL_REPORT.md"
$ReadFirst = Join-Path $OpsDir "V18_7D_READ_FIRST.txt"

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
    $Log = Join-Path $OpsDir ("V18_7D_STEP_" + $StepOrder + "_" + $SafeName + "_" + $Stamp + ".log")

    $CommandText = $ScriptPath
    if ($ArgList.Count -gt 0) {
        $CommandText = $CommandText + " " + ($ArgList -join " ")
    }

    Write-Host ""
    Write-Host "=== V18.7D STEP $StepOrder START: $StepName ==="
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

    Write-Host "=== V18.7D STEP $StepOrder DONE: $StepName | SECONDS: $([Math]::Round(($End-$Start).TotalSeconds, 3)) ==="
}

Write-Host ""
Write-Host "=== V18.7D OFFICIAL DAILY FAST MAIN WITH TECHNICAL START ==="
Write-Host "ROOT: $Root"
Write-Host "STAMP: $Stamp"

$TotalStart = Get-Date

$FastMain = Join-Path $ScriptDir "run_v18_7B_main_chain_linear_optimizer.ps1"
$TechA = Join-Path $ScriptDir "run_v18_6A_technical_timing_shadow.ps1"
$TechC = Join-Path $ScriptDir "run_v18_6C_R1_technical_timing_forward_tracker_freshness_guard.ps1"
$TechD = Join-Path $ScriptDir "run_v18_6D_technical_timing_read_center.ps1"
$FinalE = Join-Path $ScriptDir "run_v18_6E_final_read_center_with_technical.ps1"

Invoke-Step -StepOrder 1 -StepName "V18.7B_FAST_MAIN_CHAIN" -ScriptPath $FastMain
Invoke-Step -StepOrder 2 -StepName "V18.6A_TECHNICAL_TIMING_REFRESH" -ScriptPath $TechA
Invoke-Step -StepOrder 3 -StepName "V18.6C_R1_TECHNICAL_FRESHNESS_GUARD" -ScriptPath $TechC
Invoke-Step -StepOrder 4 -StepName "V18.6D_TECHNICAL_TIMING_READ_CENTER" -ScriptPath $TechD
Invoke-Step -StepOrder 5 -StepName "V18.6E_FINAL_READ_CENTER_WITH_TECHNICAL" -ScriptPath $FinalE

$TotalEnd = Get-Date

Add-Row -StepOrder 999 -StepName "TOTAL_V18_7D_OFFICIAL_DAILY_FAST_MAIN_WITH_TECHNICAL" -StartTime $TotalStart -EndTime $TotalEnd -Status "OK" -Command "V18.7D optimized official daily with technical" -LogPath ""

$Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ProfileCsv

$TotalRow = $Rows | Where-Object { $_.step_order -eq 999 } | Select-Object -First 1
$Sorted = $Rows | Sort-Object step_order
$Slowest = $Rows | Where-Object { $_.step_order -ne 999 } | Sort-Object elapsed_seconds -Descending

$FinalReadFirst = Join-Path $ReadCenterDir "V18_6E_READ_FIRST.txt"
$FinalReadCenter = Join-Path $ReadCenterDir "V18_6E_CURRENT_FINAL_READ_CENTER_WITH_TECHNICAL.md"

$OfficialImpact = "UNKNOWN"
$TechFreshRows = "UNKNOWN"
$TechStaleRows = "UNKNOWN"
$VixRegime = "UNKNOWN"

if (Test-Path $FinalReadFirst) {
    $Txt = Get-Content $FinalReadFirst -Raw -Encoding UTF8

    if ($Txt -match "OFFICIAL_DECISION_IMPACT:\s*`?\s*([A-Z_]+)") {
        $OfficialImpact = $Matches[1]
    }

    if ($Txt -match "TECH_FRESH_ROWS:\s*`?\s*([0-9]+)") {
        $TechFreshRows = $Matches[1]
    }

    if ($Txt -match "TECH_STALE_ROWS:\s*`?\s*([0-9]+)") {
        $TechStaleRows = $Matches[1]
    }

    if ($Txt -match "VIX:\s*.*?/\s*([A-Z_]+)") {
        $VixRegime = $Matches[1]
    }
}

$Md = @()
$Md += "# V18.7D Official Daily Fast Main With Technical"
$Md += ""
$Md += "Generated: ``$Stamp``"
$Md += ""
$Md += "## 1. Status"
$Md += ""
$Md += "- V18_7D_STATUS: ``OK_OFFICIAL_DAILY_FAST_MAIN_WITH_TECHNICAL_READY``"
$Md += "- TOTAL_SECONDS: ``$($TotalRow.elapsed_seconds)``"
$Md += "- TECH_FRESH_ROWS: ``$TechFreshRows``"
$Md += "- TECH_STALE_ROWS: ``$TechStaleRows``"
$Md += "- VIX_REGIME: ``$VixRegime``"
$Md += "- OFFICIAL_DECISION_IMPACT: ``$OfficialImpact``"
$Md += "- FINAL_READ_FIRST: ``$FinalReadFirst``"
$Md += "- FINAL_READ_CENTER: ``$FinalReadCenter``"
$Md += "- PROFILE_CSV: ``$ProfileCsv``"
$Md += ""
$Md += "## 2. Step Timing"
$Md += ""
$Md += "| step_order | step_name | elapsed_seconds | status |"
$Md += "|---:|---|---:|---|"

foreach ($R in $Sorted) {
    $Md += "| $($R.step_order) | $($R.step_name) | $($R.elapsed_seconds) | $($R.status) |"
}

$Md += ""
$Md += "## 3. Slowest Steps"
$Md += ""
$Md += "| rank | step_name | elapsed_seconds |"
$Md += "|---:|---|---:|"

$Rank = 1
foreach ($R in $Slowest) {
    $Md += "| $Rank | $($R.step_name) | $($R.elapsed_seconds) |"
    $Rank += 1
}

$Md += ""
$Md += "## 4. Interpretation"
$Md += ""
$Md += "- V18.7D uses V18.7B optimized main chain."
$Md += "- Technical timing layer still runs through V18.6A / V18.6C / V18.6D."
$Md += "- Final read center is still generated by V18.6E."
$Md += "- OFFICIAL_DECISION_IMPACT should remain NONE."

$Md | Set-Content -Encoding UTF8 -Path $ReportMd

$Read = @"
V18.7D OFFICIAL DAILY FAST MAIN WITH TECHNICAL READ FIRST

STATUS:
OK_OFFICIAL_DAILY_FAST_MAIN_WITH_TECHNICAL_READY

TOTAL_SECONDS:
$($TotalRow.elapsed_seconds)

TECH_FRESH_ROWS:
$TechFreshRows

TECH_STALE_ROWS:
$TechStaleRows

VIX_REGIME:
$VixRegime

OFFICIAL_DECISION_IMPACT:
$OfficialImpact

FINAL_READ_FIRST:
$FinalReadFirst

FINAL_READ_CENTER:
$FinalReadCenter

PROFILE:
$ProfileCsv

REPORT:
$ReportMd
"@

$Read | Set-Content -Encoding UTF8 -Path $ReadFirst

Write-Host ""
Write-Host "=== V18.7D OFFICIAL DAILY FAST MAIN WITH TECHNICAL READY ==="
Write-Host "TOTAL_SECONDS: $($TotalRow.elapsed_seconds)"
Write-Host "TECH_FRESH_ROWS: $TechFreshRows"
Write-Host "TECH_STALE_ROWS: $TechStaleRows"
Write-Host "VIX_REGIME: $VixRegime"
Write-Host "OFFICIAL_DECISION_IMPACT: $OfficialImpact"
Write-Host "FINAL_READ_FIRST: $FinalReadFirst"
Write-Host "FINAL_READ_CENTER: $FinalReadCenter"
Write-Host "PROFILE: $ProfileCsv"
Write-Host "REPORT: $ReportMd"
Write-Host "READ_FIRST: $ReadFirst"
Write-Host ""
Write-Host "=== SLOWEST STEPS ==="
$Slowest | Format-Table step_name, elapsed_seconds, status -AutoSize
Write-Host ""
Write-Host "=== V18.7D OFFICIAL DAILY FAST MAIN WITH TECHNICAL DONE ==="
