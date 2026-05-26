$ErrorActionPreference = "Continue"

$Root = "D:\us-tech-quant"
Set-Location $Root

$OutDir = Join-Path $Root "outputs\v17\raw_universe_audit"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Summary = Join-Path $OutDir "V17_7C_MANUAL_DAILY_WITH_RAW_UNIVERSE_AUDIT_SUMMARY.md"
$StepsCsv = Join-Path $OutDir "v17_7C_manual_daily_with_raw_universe_audit_steps.csv"
$ReadFirst = Join-Path $OutDir "V17_7C_READ_FIRST.txt"

$BaseDaily = Join-Path $Root "scripts\run_v17_6F_manual_daily_full_universe_latest_price.ps1"
$RawAudit = Join-Path $Root "scripts\run_v17_7_raw_universe_full_screen_audit.ps1"
$SemanticAudit = Join-Path $Root "scripts\run_v17_7B_universe_semantic_audit.ps1"

$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Steps = New-Object System.Collections.Generic.List[object]

function Add-Step {
    param(
        [string]$Name,
        [string]$Status,
        [int]$ExitCode,
        [string]$Path,
        [string]$Note
    )

    $script:Steps.Add([pscustomobject]@{
        run_time = $RunTime
        step_name = $Name
        status = $Status
        exit_code = $ExitCode
        script_path = $Path
        note = $Note
    })
}

function Run-Step {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [bool]$Required = $true
    )

    Write-Host ""
    Write-Host "=== RUN STEP: $Name ==="

    if (-not (Test-Path $ScriptPath)) {
        $msg = "MISSING_SCRIPT: $ScriptPath"
        Write-Host $msg
        Add-Step -Name $Name -Status "MISSING" -ExitCode 9004 -Path $ScriptPath -Note $msg
        if ($Required) {
            return 9004
        } else {
            return 0
        }
    }

    powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath
    $code = $LASTEXITCODE

    if ($code -eq 0 -or $null -eq $code) {
        Add-Step -Name $Name -Status "OK" -ExitCode 0 -Path $ScriptPath -Note "completed"
        return 0
    } else {
        Add-Step -Name $Name -Status "FAIL" -ExitCode $code -Path $ScriptPath -Note "nonzero exit"
        if ($Required) {
            return $code
        } else {
            return 0
        }
    }
}

Write-Host ""
Write-Host "=== V17.7C MANUAL DAILY WITH RAW UNIVERSE AUDIT START ==="

$BaseExit = Run-Step -Name "V17_6F_MANUAL_DAILY" -ScriptPath $BaseDaily -Required $true
if ($BaseExit -ne 0) {
    Write-Host "BASE DAILY FAILED OR MISSING. Continue to write summary, but final status will be FAIL."
}

$RawExit = Run-Step -Name "V17_7_RAW_UNIVERSE_FULL_AUDIT" -ScriptPath $RawAudit -Required $true
$SemanticExit = Run-Step -Name "V17_7B_UNIVERSE_SEMANTIC_AUDIT" -ScriptPath $SemanticAudit -Required $true

$Steps | Export-Csv -Path $StepsCsv -NoTypeInformation -Encoding UTF8

$RawReadFirst = Join-Path $OutDir "V17_7_READ_FIRST.txt"
$SemanticReadFirst = Join-Path $OutDir "V17_7B_READ_FIRST.txt"
$RawSummary = Join-Path $OutDir "V17_7_RAW_UNIVERSE_FULL_SCREEN_AUDIT.md"
$SemanticSummary = Join-Path $OutDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md"
$SemanticCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv"

$UniverseSemanticStatus = ""
$RawUniverseCount = ""
$ClassifiedUniverseCount = ""
$MainComputeUniverseCount = ""
$SecondStageCandidateCount = ""
$RawPriceOkCount = ""
$RawPriceFailCount = ""

if (Test-Path $SemanticReadFirst) {
    $rf = Get-Content $SemanticReadFirst -Raw

    foreach ($line in ($rf -split "`r?`n")) {
        if ($line -match "^UNIVERSE_SEMANTIC_STATUS:\s*(.+)$") { $UniverseSemanticStatus = $Matches[1].Trim() }
        if ($line -match "^RAW_UNIVERSE_COUNT:\s*(.+)$") { $RawUniverseCount = $Matches[1].Trim() }
        if ($line -match "^CLASSIFIED_UNIVERSE_COUNT:\s*(.+)$") { $ClassifiedUniverseCount = $Matches[1].Trim() }
        if ($line -match "^MAIN_COMPUTE_UNIVERSE_COUNT:\s*(.+)$") { $MainComputeUniverseCount = $Matches[1].Trim() }
        if ($line -match "^SECOND_STAGE_CANDIDATE_COUNT:\s*(.+)$") { $SecondStageCandidateCount = $Matches[1].Trim() }
        if ($line -match "^RAW_PRICE_OK_COUNT:\s*(.+)$") { $RawPriceOkCount = $Matches[1].Trim() }
        if ($line -match "^RAW_PRICE_FAIL_COUNT:\s*(.+)$") { $RawPriceFailCount = $Matches[1].Trim() }
    }
}

$FailSteps = @($Steps | Where-Object { $_.status -ne "OK" })
$FailCount = $FailSteps.Count

$FinalStatus = if (
    $FailCount -eq 0 -and
    $UniverseSemanticStatus -eq "OK_EXPECTED_105_66_10" -and
    $RawUniverseCount -eq "105" -and
    $ClassifiedUniverseCount -eq "105" -and
    $MainComputeUniverseCount -eq "66" -and
    $SecondStageCandidateCount -eq "10" -and
    $RawPriceOkCount -eq "105" -and
    $RawPriceFailCount -eq "0"
) {
    "OK"
} elseif ($FailCount -eq 0) {
    "OK_DYNAMIC_COUNTS"
} else {
    "FAIL_CHECK_STEPS"
}

$Md = New-Object System.Collections.Generic.List[string]

$Md.Add("# V17.7C Manual Daily With RAW Universe Audit")
$Md.Add("")
$Md.Add("Generated: $RunTime")
$Md.Add("")
$Md.Add("## 1. Main Conclusion")
$Md.Add("")
$Md.Add("V17_7C_STATUS: $FinalStatus")
$Md.Add("")
$Md.Add("This wrapper runs the current manual daily flow, then forces RAW universe audit and universe semantic audit.")
$Md.Add("")
$Md.Add("## 2. Universe Count Summary")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---:|")
$Md.Add("| RAW_UNIVERSE_COUNT | $RawUniverseCount |")
$Md.Add("| CLASSIFIED_UNIVERSE_COUNT | $ClassifiedUniverseCount |")
$Md.Add("| MAIN_COMPUTE_UNIVERSE_COUNT | $MainComputeUniverseCount |")
$Md.Add("| SECOND_STAGE_CANDIDATE_COUNT | $SecondStageCandidateCount |")
$Md.Add("| RAW_PRICE_OK_COUNT | $RawPriceOkCount |")
$Md.Add("| RAW_PRICE_FAIL_COUNT | $RawPriceFailCount |")
$Md.Add("")
$Md.Add("## 3. Correct Interpretation")
$Md.Add("")
$Md.Add("原始池 105 个全部参与价格审计和分类；其中 66 个进入主计算/执行前置层；10 个进入 second stage 重点候选层。")
$Md.Add("")
$Md.Add("## 4. Step Results")
$Md.Add("")
$Md.Add("| step | status | exit_code |")
$Md.Add("|---|---|---:|")

foreach ($s in $Steps) {
    $Md.Add("| $($s.step_name) | $($s.status) | $($s.exit_code) |")
}

$Md.Add("")
$Md.Add("## 5. Read Files")
$Md.Add("")
$Md.Add("- V17.7C summary: $Summary")
$Md.Add("- V17.7C steps CSV: $StepsCsv")
$Md.Add("- V17.7 raw audit: $RawSummary")
$Md.Add("- V17.7B semantic audit: $SemanticSummary")
$Md.Add("- V17.7B semantic CSV: $SemanticCsv")
$Md.Add("")

$Md | Set-Content -Path $Summary -Encoding UTF8

$Rf = @()
$Rf += "=== V17.7C MANUAL DAILY WITH RAW UNIVERSE AUDIT READY ==="
$Rf += "V17_7C_STATUS: $FinalStatus"
$Rf += "UNIVERSE_SEMANTIC_STATUS: $UniverseSemanticStatus"
$Rf += "RAW_UNIVERSE_COUNT: $RawUniverseCount"
$Rf += "CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount"
$Rf += "MAIN_COMPUTE_UNIVERSE_COUNT: $MainComputeUniverseCount"
$Rf += "SECOND_STAGE_CANDIDATE_COUNT: $SecondStageCandidateCount"
$Rf += "RAW_PRICE_OK_COUNT: $RawPriceOkCount"
$Rf += "RAW_PRICE_FAIL_COUNT: $RawPriceFailCount"
$Rf += ""
$Rf += "START HERE:"
$Rf += $Summary
$Rf += ""
$Rf += "RAW AUDIT:"
$Rf += $RawSummary
$Rf += ""
$Rf += "SEMANTIC AUDIT:"
$Rf += $SemanticSummary
$Rf += ""
$Rf += "STEPS CSV:"
$Rf += $StepsCsv

$Rf | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== V17.7C MANUAL DAILY WITH RAW UNIVERSE AUDIT READY ==="
Write-Host "V17_7C_STATUS: $FinalStatus"
Write-Host "UNIVERSE_SEMANTIC_STATUS: $UniverseSemanticStatus"
Write-Host "RAW_UNIVERSE_COUNT: $RawUniverseCount"
Write-Host "CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount"
Write-Host "MAIN_COMPUTE_UNIVERSE_COUNT: $MainComputeUniverseCount"
Write-Host "SECOND_STAGE_CANDIDATE_COUNT: $SecondStageCandidateCount"
Write-Host "RAW_PRICE_OK_COUNT: $RawPriceOkCount"
Write-Host "RAW_PRICE_FAIL_COUNT: $RawPriceFailCount"
Write-Host ""
Write-Host "START HERE:"
Write-Host $Summary
Write-Host ""
Write-Host "READ FIRST:"
Write-Host $ReadFirst

Write-Host ""
Write-Host "=== V17.7C MANUAL DAILY WITH RAW UNIVERSE AUDIT DONE ==="

if ($FinalStatus -like "FAIL*") {
    exit 1
}

exit 0
