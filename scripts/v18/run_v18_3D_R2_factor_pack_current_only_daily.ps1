$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$ScriptDir = Join-Path $Root "scripts\v18"
$OutDir = Join-Path $Root "outputs\v18\factor_pack"
$OpsDir = Join-Path $Root "outputs\v18\ops"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$Upstream = Join-Path $ScriptDir "run_v18_3D_R1_official_overlap_fix.ps1"
$UpstreamLog = Join-Path $OpsDir "V18_3D_R2_upstream_R1_run.log"

$R1Read = Join-Path $OutDir "V18_3D_R1_READ_FIRST.txt"
$R1Top30 = Join-Path $OutDir "V18_3D_R1_FACTOR_PACK_TOP30.md"
$R1OverlapMd = Join-Path $OutDir "V18_3D_R1_FACTOR_PACK_OFFICIAL_OVERLAP.md"
$R1OverlapCsv = Join-Path $OutDir "V18_3D_R1_SHADOW_TOP30_OFFICIAL_OVERLAP.csv"
$R1RankingCsv = Join-Path $OutDir "V18_3D_RAW105_FACTOR_PACK_RANKING.csv"
$R1ValuesCsv = Join-Path $OutDir "V18_3D_RAW105_FACTOR_PACK_VALUES.csv"

$R2Read = Join-Path $OutDir "V18_3D_R2_READ_FIRST.txt"
$R2Top30 = Join-Path $OutDir "V18_3D_R2_CURRENT_FACTOR_PACK_TOP30.md"
$R2OverlapMd = Join-Path $OutDir "V18_3D_R2_CURRENT_FACTOR_PACK_OFFICIAL_OVERLAP.md"
$R2OverlapCsv = Join-Path $OutDir "V18_3D_R2_CURRENT_SHADOW_TOP30_OFFICIAL_OVERLAP.csv"
$R2RankingCsv = Join-Path $OutDir "V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
$R2ValuesCsv = Join-Path $OutDir "V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_VALUES.csv"

$GlobalTop30 = Join-Path $OutDir "V18_CURRENT_FACTOR_PACK_TOP30.md"
$GlobalOverlapMd = Join-Path $OutDir "V18_CURRENT_FACTOR_PACK_OFFICIAL_OVERLAP.md"
$GlobalOverlapCsv = Join-Path $OutDir "V18_CURRENT_SHADOW_TOP30_OFFICIAL_OVERLAP.csv"
$GlobalRankingCsv = Join-Path $OutDir "V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
$GlobalValuesCsv = Join-Path $OutDir "V18_CURRENT_RAW105_FACTOR_PACK_VALUES.csv"

function Get-LineValue {
    param(
        [string]$Text,
        [string]$Key
    )
    $Pattern = "^\s*" + [regex]::Escape($Key) + "\s*:\s*(.*)$"
    foreach ($Line in ($Text -split "\r?\n")) {
        if ($Line -match $Pattern) {
            return $Matches[1].Trim()
        }
    }
    return "UNKNOWN"
}

function Copy-Required {
    param(
        [string]$Source,
        [string]$Dest
    )
    if (-not (Test-Path $Source)) {
        throw "Required output missing: $Source"
    }
    Copy-Item $Source $Dest -Force
}

Write-Host ""
Write-Host "=== V18.3D-R2 FACTOR PACK CURRENT-ONLY DAILY START ==="
Write-Host "ROOT: $Root"
Write-Host "UPSTREAM: $Upstream"
Write-Host ""

if (-not (Test-Path $Upstream)) {
    throw "Missing upstream script: $Upstream"
}

Write-Host "STEP 1: run upstream V18.3D-R1 quietly"
$UpstreamOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $Upstream *>&1
$UpstreamExit = $LASTEXITCODE
$UpstreamOutput | Set-Content -Path $UpstreamLog -Encoding UTF8

if ($UpstreamExit -ne 0) {
    Write-Host "V18_3D_R2_STATUS: FAIL_UPSTREAM_R1"
    Write-Host "UPSTREAM_EXIT_CODE: $UpstreamExit"
    Write-Host "UPSTREAM_LOG: $UpstreamLog"
    exit $UpstreamExit
}

if (-not (Test-Path $R1Read)) {
    Write-Host "V18_3D_R2_STATUS: FAIL_MISSING_R1_READ_FIRST"
    Write-Host "EXPECTED: $R1Read"
    Write-Host "UPSTREAM_LOG: $UpstreamLog"
    exit 1
}

$R1Text = Get-Content $R1Read -Raw -Encoding UTF8
$R1Status = Get-LineValue $R1Text "V18_3D_R1_STATUS"

if ($R1Status -ne "OK_OFFICIAL_OVERLAP_FIXED") {
    Write-Host "V18_3D_R2_STATUS: FAIL_R1_NOT_OK"
    Write-Host "UPSTREAM_R1_STATUS: $R1Status"
    Write-Host "UPSTREAM_LOG: $UpstreamLog"
    exit 1
}

Write-Host "STEP 2: publish fixed current outputs"

Copy-Required $R1Top30 $R2Top30
Copy-Required $R1OverlapMd $R2OverlapMd
Copy-Required $R1OverlapCsv $R2OverlapCsv
Copy-Required $R1RankingCsv $R2RankingCsv
Copy-Required $R1ValuesCsv $R2ValuesCsv

Copy-Required $R1Top30 $GlobalTop30
Copy-Required $R1OverlapMd $GlobalOverlapMd
Copy-Required $R1OverlapCsv $GlobalOverlapCsv
Copy-Required $R1RankingCsv $GlobalRankingCsv
Copy-Required $R1ValuesCsv $GlobalValuesCsv

$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$OfficialSource = Get-LineValue $R1Text "OFFICIAL_REVIEW_SOURCE"
$OfficialCount = Get-LineValue $R1Text "OFFICIAL_REVIEW_COUNT"
$OfficialNames = Get-LineValue $R1Text "OFFICIAL_REVIEW_NAMES"
$OverlapCount = Get-LineValue $R1Text "SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT"
$OverlapNames = Get-LineValue $R1Text "SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES"
$ShadowOnlyCount = Get-LineValue $R1Text "SHADOW_TOP30_ONLY_COUNT"
$OfficialNotTop30Count = Get-LineValue $R1Text "OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT"
$OfficialNotTop30Names = Get-LineValue $R1Text "OFFICIAL_REVIEW_NOT_SHADOW_TOP30_NAMES"
$DecisionImpact = Get-LineValue $R1Text "OFFICIAL_DECISION_IMPACT"
$PromotionAction = Get-LineValue $R1Text "PROMOTION_ACTION"

$ReadLines = @(
    "=== V18.3D-R2 FACTOR PACK CURRENT-ONLY DAILY ===",
    "",
    "V18_3D_R2_STATUS: OK_FACTOR_PACK_CURRENT_ONLY_READY",
    "RUN_TIME: $RunTime",
    "",
    "UPSTREAM_R1_STATUS: $R1Status",
    "UPSTREAM_LOG: $UpstreamLog",
    "",
    "OFFICIAL_REVIEW_SOURCE: $OfficialSource",
    "OFFICIAL_REVIEW_COUNT: $OfficialCount",
    "OFFICIAL_REVIEW_NAMES: $OfficialNames",
    "",
    "SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: $OverlapCount",
    "SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: $OverlapNames",
    "SHADOW_TOP30_ONLY_COUNT: $ShadowOnlyCount",
    "OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: $OfficialNotTop30Count",
    "OFFICIAL_REVIEW_NOT_SHADOW_TOP30_NAMES: $OfficialNotTop30Names",
    "",
    "OFFICIAL_DECISION_IMPACT: $DecisionImpact",
    "PROMOTION_ACTION: $PromotionAction",
    "",
    "CURRENT_TOP30: $R2Top30",
    "CURRENT_COMPARE_REPORT: $R2OverlapMd",
    "CURRENT_OVERLAP_CSV: $R2OverlapCsv",
    "CURRENT_RANKING_CSV: $R2RankingCsv",
    "CURRENT_VALUES_CSV: $R2ValuesCsv",
    "",
    "GLOBAL_CURRENT_TOP30: $GlobalTop30",
    "GLOBAL_CURRENT_COMPARE_REPORT: $GlobalOverlapMd",
    "GLOBAL_CURRENT_OVERLAP_CSV: $GlobalOverlapCsv",
    "GLOBAL_CURRENT_RANKING_CSV: $GlobalRankingCsv",
    "GLOBAL_CURRENT_VALUES_CSV: $GlobalValuesCsv",
    "",
    "READ_FIRST: $R2Read"
)

$ReadLines | Set-Content -Path $R2Read -Encoding UTF8

Write-Host ""
Write-Host "=== V18.3D-R2 READ FIRST ==="
Get-Content $R2Read -Encoding UTF8
Write-Host ""
Write-Host "=== V18.3D-R2 FACTOR PACK CURRENT-ONLY DAILY DONE ==="
