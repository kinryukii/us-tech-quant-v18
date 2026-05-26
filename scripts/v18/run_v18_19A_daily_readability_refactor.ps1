param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

if (-not $PSBoundParameters.ContainsKey("Root") -or [string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

if (-not (Test-Path $Root)) {
    throw "Missing root directory: $Root"
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_19A_daily_readability_refactor.py"

if (-not (Test-Path $Python)) {
    throw "Missing Python executable: $Python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.19A Python script: $Script"
}

Write-Host "=== V18.19A DAILY READABILITY REFACTOR START ==="
Write-Host "ROOT: $Root"
Write-Host "SCRIPT: $Script"

& $Python $Script --root $Root
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$AuditPath = Join-Path $Root "outputs\v18\ops\V18_19A_DAILY_READABILITY_AUDIT.csv"
$ReadFirstPath = Join-Path $Root "outputs\v18\ops\V18_19A_READ_FIRST.txt"
$BriefPath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_DAILY_BRIEF.md"
$PacketDir = Join-Path $Root "outputs\v18\read_center\daily_packet"

$ReadFirstMap = @{}
if (Test-Path $ReadFirstPath) {
    Get-Content -Path $ReadFirstPath | ForEach-Object {
        if ($_ -match '^\s*([^:]+):\s*(.*)$') {
            $key = $Matches[1].Trim().TrimStart('-').Trim().ToUpperInvariant()
            $value = $Matches[2].Trim()
            if ($key) {
                $ReadFirstMap[$key] = $value
            }
        }
    }
}

$Summary = @{}
if (Test-Path $AuditPath) {
    Import-Csv $AuditPath | Where-Object { $_.category -eq "summary" } | ForEach-Object {
        $Summary[$_.metric] = $_.value
    }
}

$Status = if ($ReadFirstMap.ContainsKey("STATUS")) { $ReadFirstMap["STATUS"] } elseif ($Summary.ContainsKey("STATUS")) { $Summary["STATUS"] } else { "FAIL_V18_19A_DAILY_READABILITY_FAILED" }
$Trust = if ($ReadFirstMap.ContainsKey("DAILY_TRUST_LEVEL")) { $ReadFirstMap["DAILY_TRUST_LEVEL"] } elseif ($Summary.ContainsKey("DAILY_TRUST_LEVEL")) { $Summary["DAILY_TRUST_LEVEL"] } else { "UNKNOWN" }
$AutoTrade = if ($ReadFirstMap.ContainsKey("AUTO_TRADE")) { $ReadFirstMap["AUTO_TRADE"] } elseif ($Summary.ContainsKey("AUTO_TRADE")) { $Summary["AUTO_TRADE"] } else { "UNKNOWN" }
$AutoSell = if ($ReadFirstMap.ContainsKey("AUTO_SELL")) { $ReadFirstMap["AUTO_SELL"] } elseif ($Summary.ContainsKey("AUTO_SELL")) { $Summary["AUTO_SELL"] } else { "UNKNOWN" }
$Official = if ($ReadFirstMap.ContainsKey("OFFICIAL_DECISION_IMPACT")) { $ReadFirstMap["OFFICIAL_DECISION_IMPACT"] } elseif ($Summary.ContainsKey("OFFICIAL_DECISION_IMPACT")) { $Summary["OFFICIAL_DECISION_IMPACT"] } else { "UNKNOWN" }
$ValidationFailCount = if ($ReadFirstMap.ContainsKey("VALIDATION_FAIL_COUNT")) { $ReadFirstMap["VALIDATION_FAIL_COUNT"] } elseif ($Summary.ContainsKey("VALIDATION_FAIL_COUNT")) { $Summary["VALIDATION_FAIL_COUNT"] } else { "UNKNOWN" }

Write-Host ""
Write-Host "=== V18.19A DAILY READABILITY REFACTOR READY ==="
Write-Host "STATUS: $Status"
Write-Host "DAILY_TRUST_LEVEL: $Trust"
Write-Host "READ_FIRST: $BriefPath"
Write-Host "PACKET_DIR: $PacketDir"
Write-Host "AUTO_TRADE: $AutoTrade"
Write-Host "AUTO_SELL: $AutoSell"
Write-Host "OFFICIAL_DECISION_IMPACT: $Official"
Write-Host "VALIDATION_FAIL_COUNT: $ValidationFailCount"

Write-Host ""
Write-Host "READ FIRST:"
Write-Host $BriefPath
Write-Host ""
Write-Host "DETAIL PACKET:"
Write-Host $PacketDir

exit 0
