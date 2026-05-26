param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$SkipOfficialDaily,
    [switch]$SkipShadowResearch,
    [switch]$UseExistingShadowResearchOutputs,
    [switch]$UseYFinance,
    [int]$MinCount = 20,
    [double]$TopFraction = 0.30
)

$ErrorActionPreference = "Stop"

function Get-ReadFirstValue {
    param(
        [string]$Path,
        [string]$Key
    )

    if (-not (Test-Path $Path)) {
        return ""
    }

    $Target = $Key.Trim()
    if (-not $Target.EndsWith(":")) {
        $Target = $Target + ":"
    }

    $Lines = Get-Content $Path -Encoding UTF8
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        $Line = $Lines[$i].Trim()

        if ($Line -eq $Target) {
            for ($j = $i + 1; $j -lt $Lines.Count; $j++) {
                $Next = $Lines[$j].Trim()
                if ($Next -ne "") {
                    return $Next
                }
            }
        }

        if ($Line.StartsWith($Target)) {
            $Value = $Line.Substring($Target.Length).Trim()
            if ($Value -ne "") {
                return $Value
            }
        }
    }

    return ""
}

Write-Host ""
Write-Host "=== V18.12F SHADOW RESEARCH DAILY WITH SELL TIMING START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SHADOW_ONLY"
Write-Host "SKIP_SHADOW_RESEARCH: $SkipShadowResearch"
Write-Host "USE_EXISTING_SHADOW_RESEARCH_OUTPUTS: $UseExistingShadowResearchOutputs"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

Set-Location $Root

$ShadowWrapper = Join-Path $Root "scripts\v18\run_v18_current_shadow_research_daily.ps1"
$SellTimingWrapper = Join-Path $Root "scripts\v18\run_v18_12E_sell_timing_daily_wrapper.ps1"
$ReadCenterScript = Join-Path $Root "scripts\v18\v18_12F_shadow_research_sell_timing_read_center.py"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$ReadFirst = Join-Path $Root "outputs\v18\sell_timing\V18_12F_READ_FIRST.txt"
$SellTimingReadFirst = Join-Path $Root "outputs\v18\sell_timing\V18_12E_READ_FIRST.txt"

$ShadowStatus = "NOT_RUN"
$SellTimingStatus = "NOT_RUN"
$ShadowExitCode = 0
$SellTimingExitCode = 0
$ReuseExistingShadowOutputs = $SkipShadowResearch -or $UseExistingShadowResearchOutputs

if ($ReuseExistingShadowOutputs) {
    $ShadowStatus = "SKIPPED_USE_EXISTING_OUTPUTS"
    Write-Host ""
    Write-Host "SKIP_STEP: scripts\v18\run_v18_current_shadow_research_daily.ps1"
    Write-Host "SHADOW_RESEARCH_STATUS: $ShadowStatus"
    Write-Host "SAFE_MODE: existing shadow research outputs will be audited and reused if present."
}
elseif (Test-Path $ShadowWrapper) {
    Write-Host ""
    Write-Host "RUN_STEP: scripts\v18\run_v18_current_shadow_research_daily.ps1"

    $ShadowArgs = @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $ShadowWrapper,
        "-Root",
        $Root,
        "-MinCount",
        "$MinCount",
        "-TopFraction",
        "$TopFraction"
    )

    if ($SkipOfficialDaily) {
        $ShadowArgs += "-SkipOfficialDaily"
    }

    if ($UseYFinance) {
        $ShadowArgs += "-UseYFinance"
    }

    & powershell @ShadowArgs
    $ShadowExitCode = $LASTEXITCODE
    if ($ShadowExitCode -eq 0) {
        $ShadowStatus = "OK_SHADOW_RESEARCH_DAILY_RAN"
    }
    else {
        $ShadowStatus = "FAILED_SHADOW_RESEARCH_DAILY"
        Write-Host "STEP_FAILED: scripts\v18\run_v18_current_shadow_research_daily.ps1 EXIT=$ShadowExitCode"
    }
}
else {
    $ShadowStatus = "MISSING_SHADOW_RESEARCH_DAILY_WRAPPER"
    Write-Host ""
    Write-Host "STEP_MISSING: scripts\v18\run_v18_current_shadow_research_daily.ps1"
    Write-Host "SAFE_CONTINUE: sell timing and read-center are shadow-only and independent."
}

if (-not (Test-Path $SellTimingWrapper)) {
    $SellTimingStatus = "MISSING_CRITICAL_V18_12E_SELL_TIMING_DAILY_WRAPPER"
    $SellTimingExitCode = 12
    Write-Host ""
    Write-Host "STEP_MISSING: scripts\v18\run_v18_12E_sell_timing_daily_wrapper.ps1"
    Write-Host "SELL_TIMING_STATUS: $SellTimingStatus"
    Write-Host "FAIL_STATUS: FAIL_V18_12F_SELL_TIMING_DEPENDENCY_MISSING"
}
else {
    Write-Host ""
    Write-Host "RUN_STEP: scripts\v18\run_v18_12E_sell_timing_daily_wrapper.ps1"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $SellTimingWrapper -Root $Root
    $SellTimingExitCode = $LASTEXITCODE
    if ($SellTimingExitCode -eq 0) {
        $SellTimingReadFirstStatus = Get-ReadFirstValue $SellTimingReadFirst "STATUS:"
        if ($SellTimingReadFirstStatus -ne "") {
            $SellTimingStatus = $SellTimingReadFirstStatus
        }
        else {
            $SellTimingStatus = "OK_V18_12E_SELL_TIMING_DAILY_RAN"
        }
    }
    else {
        $SellTimingStatus = "FAILED_V18_12E_SELL_TIMING_DAILY"
        Write-Host "STEP_FAILED: scripts\v18\run_v18_12E_sell_timing_daily_wrapper.ps1 EXIT=$SellTimingExitCode"
    }
}

if (-not (Test-Path $ReadCenterScript)) {
    throw "Missing Python script: $ReadCenterScript"
}

if (Test-Path $VenvPython) {
    $Python = $VenvPython
}
else {
    $Python = "python"
}

Write-Host ""
Write-Host "RUN_STEP: scripts\v18\v18_12F_shadow_research_sell_timing_read_center.py"
Write-Host "PYTHON: $Python"
& $Python $ReadCenterScript --root $Root --shadow-status $ShadowStatus --shadow-exit-code $ShadowExitCode --sell-timing-status $SellTimingStatus --sell-timing-exit-code $SellTimingExitCode
if ($LASTEXITCODE -ne 0) {
    Write-Host "V18.12F READ CENTER FAILED: $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== V18.12F SHADOW RESEARCH DAILY WITH SELL TIMING DONE ==="

if (Test-Path $ReadFirst) {
    Write-Host ""
    Write-Host "=== V18.12F READ FIRST ==="
    Get-Content -Path $ReadFirst -Encoding UTF8
}

if ($SellTimingExitCode -ne 0) {
    exit $SellTimingExitCode
}

if (($ShadowExitCode -ne 0) -and ($ShadowStatus -ne "MISSING_SHADOW_RESEARCH_DAILY_WRAPPER")) {
    exit $ShadowExitCode
}
