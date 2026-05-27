param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SnapshotRoot = Join-Path $Root ("archive\stable\V18_4G_R2_stable_final_daily_factor_audit_" + $Stamp)

$Manifest = Join-Path $SnapshotRoot ("V18_4G_R2_STABLE_MANIFEST_" + $Stamp + ".csv")
$Readme = Join-Path $SnapshotRoot "V18_4G_R2_STABLE_README.txt"
$Restore = Join-Path $SnapshotRoot "restore_v18_4G_R2_stable_snapshot.ps1"

New-Item -ItemType Directory -Force -Path $SnapshotRoot | Out-Null

$script:Rows = @()

function Copy-One {
    param(
        [string]$Source,
        [string]$Layer
    )

    if ([string]::IsNullOrWhiteSpace($Source)) {
        return
    }

    $exists = Test-Path -LiteralPath $Source

    $rel = ""
    if ($Source.StartsWith($Root)) {
        $rel = $Source.Substring($Root.Length).TrimStart("\")
    } else {
        $rel = Split-Path $Source -Leaf
    }

    $dest = Join-Path $SnapshotRoot $rel

    if ($exists) {
        New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
        Copy-Item -Force -LiteralPath $Source -Destination $dest
    }

    $script:Rows += [pscustomobject]@{
        layer = $Layer
        source = $Source
        relative_path = $rel
        destination = $dest
        exists = $exists
        copied = $exists
        size_bytes = if ($exists) { (Get-Item -LiteralPath $Source).Length } else { 0 }
    }
}

function Read-StatePath {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }

    $raw = Get-Content -Raw -LiteralPath $Path
    $p = $raw -replace [char]0xFEFF, ""
    $p = $p -replace "`r", ""
    $p = $p -replace "`n", ""
    $p = $p -replace "`t", ""
    $p = $p.Trim().Trim('"').Trim("'")
    return $p
}

Write-Host ""
Write-Host "=== V18.4G-R2 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT: $SnapshotRoot"

# Refresh the latest runtime graph without rerunning full daily chain.
$RuntimeAudit = Join-Path $Root "scripts\v18\run_v18_4C_runtime_dependency_audit.ps1"
if (Test-Path -LiteralPath $RuntimeAudit) {
    Write-Host ""
    Write-Host "=== REFRESH RUNTIME AUDIT ==="
    powershell -NoProfile -ExecutionPolicy Bypass -File $RuntimeAudit | Out-Host
}

$Graph = Join-Path $Root "outputs\v18\ops\V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv"

$RuntimeCode = @()

if (Test-Path -LiteralPath $Graph) {
    $RuntimeCode = @(
        Import-Csv -LiteralPath $Graph |
            Where-Object { $_.exists -eq "True" -and $_.callee -match '\.(ps1|py|bat|cmd)$' } |
            Select-Object -ExpandProperty callee -Unique
    )
}

# Add V18.4G outer scripts and audit scripts explicitly.
$ExtraCode = @()
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1")
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4C_R1_final_daily_wrapper.ps1")
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4C_runtime_dependency_audit.ps1")
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4C_cloud_earnings_event_update.ps1")
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4C_archive_old_event_price_scripts.ps1")
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4D_factor_pack_audit.ps1")
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4E_factor_output_forward_tracking_audit.ps1")
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4F_forward_tracker_factor_coverage_repair.ps1")
$ExtraCode += (Join-Path $Root "scripts\v18\run_v18_4G_R2_stable_snapshot.ps1")

# Add dynamic state-referenced base scripts.
$StateReferencedScripts = @()
$StateRoot = Join-Path $Root "state"

if (Test-Path -LiteralPath $StateRoot) {
    Get-ChildItem -LiteralPath $StateRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension.ToLowerInvariant() -in @(".txt", ".csv", ".md", ".json") } |
        ForEach-Object {
            try {
                $txt = Get-Content -Raw -LiteralPath $_.FullName
                $pattern = 'D:\\us-tech-quant\\[^\r\n,;"]+?\.ps1'
                foreach ($m in [regex]::Matches($txt, $pattern, "IgnoreCase")) {
                    $StateReferencedScripts += $m.Value.Trim().Trim('"').Trim("'")
                }
            } catch {}
        }
}

$AllCode = @($RuntimeCode + $ExtraCode + $StateReferencedScripts | Select-Object -Unique)

Write-Host ""
Write-Host "=== COPY CODE LAYER ==="
foreach ($f in $AllCode) {
    Copy-One -Source $f -Layer "code"
}

Write-Host ""
Write-Host "=== COPY OUTPUT LAYER ==="

$OutputDirs = @()
$OutputDirs += (Join-Path $Root "outputs\v18\daily_integrated")
$OutputDirs += (Join-Path $Root "outputs\v18\ops")
$OutputDirs += (Join-Path $Root "outputs\v18\factor_audit")
$OutputDirs += (Join-Path $Root "outputs\v18\outcome_summary")
$OutputDirs += (Join-Path $Root "outputs\v18\forward_outcome")
$OutputDirs += (Join-Path $Root "outputs\v18\factor_pack")
$OutputDirs += (Join-Path $Root "outputs\v18\factor_shadow")
$OutputDirs += (Join-Path $Root "outputs\v18\cockpit")
$OutputDirs += (Join-Path $Root "outputs\v17\ops")
$OutputDirs += (Join-Path $Root "outputs\v17\manual_daily")
$OutputDirs += (Join-Path $Root "outputs\v17\factor_effectiveness")
$OutputDirs += (Join-Path $Root "outputs\v16\read_center")

foreach ($dir in $OutputDirs) {
    if (Test-Path -LiteralPath $dir) {
        Get-ChildItem -LiteralPath $dir -Recurse -File -ErrorAction SilentlyContinue |
            ForEach-Object {
                Copy-One -Source $_.FullName -Layer "output"
            }
    }
}

Write-Host ""
Write-Host "=== COPY STATE LAYER ==="

$StateDir = Join-Path $Root "state"

if (Test-Path -LiteralPath $StateDir) {
    Get-ChildItem -LiteralPath $StateDir -Recurse -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            Copy-One -Source $_.FullName -Layer "state"
        }
}

Write-Host ""
Write-Host "=== PARSE CHECK CRITICAL POWERSHELL SCRIPTS ==="

$Critical = @()
$Critical += (Join-Path $Root "scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_4C_R1_final_daily_wrapper.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_4C_runtime_dependency_audit.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_4C_cloud_earnings_event_update.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_4C_archive_old_event_price_scripts.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_4D_factor_pack_audit.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_4E_factor_output_forward_tracking_audit.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_4F_forward_tracker_factor_coverage_repair.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1")
$Critical += (Join-Path $Root "scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1")

$BasePath17_2 = Read-StatePath -Path (Join-Path $Root "state\v17_2_base_official_daily_path.txt")
$BasePath17_4 = Read-StatePath -Path (Join-Path $Root "state\v17_4_base_official_daily_path.txt")

if (-not [string]::IsNullOrWhiteSpace($BasePath17_2)) {
    $Critical += $BasePath17_2
}

if (-not [string]::IsNullOrWhiteSpace($BasePath17_4)) {
    $Critical += $BasePath17_4
}

$ParseFail = @()

foreach ($f in ($Critical | Select-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $f)) {
        Write-Host "MISSING_CRITICAL: $f"
        $ParseFail += $f
        continue
    }

    try {
        [scriptblock]::Create((Get-Content -Raw -LiteralPath $f)) | Out-Null
        Write-Host "OK_PARSE: $f"
    } catch {
        Write-Host "FAIL_PARSE: $f"
        $ParseFail += $f
    }
}

Write-Host ""
Write-Host "=== VERIFY FINAL READ FILES ==="

$ReadFiles = @()
$ReadFiles += (Join-Path $Root "outputs\v18\daily_integrated\V18_4G_R1_READ_FIRST.txt")
$ReadFiles += (Join-Path $Root "outputs\v18\daily_integrated\V18_CURRENT_FINAL_DAILY.md")
$ReadFiles += (Join-Path $Root "outputs\v18\factor_audit\V18_4D_CURRENT_FACTOR_PACK_AUDIT.md")
$ReadFiles += (Join-Path $Root "outputs\v18\factor_audit\V18_4E_CURRENT_FACTOR_OUTPUT_FORWARD_AUDIT.md")
$ReadFiles += (Join-Path $Root "outputs\v18\factor_audit\V18_4F_CURRENT_FORWARD_FACTOR_COVERAGE.md")
$ReadFiles += (Join-Path $Root "state\v18\V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv")

$ReadMissing = @()

foreach ($f in $ReadFiles) {
    if (Test-Path -LiteralPath $f) {
        Write-Host "OK_FILE: $f"
    } else {
        Write-Host "MISSING_FILE: $f"
        $ReadMissing += $f
    }
}

$MissingCount = @($script:Rows | Where-Object { $_.exists -eq $false }).Count
$CopyCount = @($script:Rows | Where-Object { $_.copied -eq $true }).Count
$TotalBytes = ($script:Rows | Measure-Object -Property size_bytes -Sum).Sum

$script:Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $Manifest

$RestoreText = @"
param(
    [string]`$Root = "D:\us-tech-quant"
)

`$ErrorActionPreference = "Stop"

`$SnapshotRoot = "$SnapshotRoot"
`$Manifest = "$Manifest"

Write-Host ""
Write-Host "=== RESTORE V18.4G-R2 STABLE SNAPSHOT START ==="
Write-Host "SNAPSHOT: `$SnapshotRoot"
Write-Host "TARGET_ROOT: `$Root"

`$rows = Import-Csv -LiteralPath `$Manifest

foreach (`$r in `$rows) {
    if (`$r.copied -ne "True") {
        continue
    }

    `$src = Join-Path `$SnapshotRoot `$r.relative_path
    `$dst = Join-Path `$Root `$r.relative_path

    if (Test-Path -LiteralPath `$src) {
        New-Item -ItemType Directory -Force -Path (Split-Path `$dst -Parent) | Out-Null
        Copy-Item -Force -LiteralPath `$src -Destination `$dst
        Write-Host "RESTORED: `$dst"
    }
}

Write-Host ""
Write-Host "=== RESTORE V18.4G-R2 STABLE SNAPSHOT DONE ==="
Write-Host "NEXT DAILY COMMAND:"
Write-Host 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1"'
"@

$RestoreText | Set-Content -Encoding UTF8 -Path $Restore

$ReadmeText = @"
V18.4G-R2 STABLE SNAPSHOT

生成时间:
$Stamp

STATUS:
STABLE_SNAPSHOT_CREATED

SNAPSHOT:
$SnapshotRoot

CURRENT DAILY COMMAND:
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1"

SCOPE:
- V18.4G-R1 final daily factor audit wrapper
- V18.4C final daily wrapper
- V18.4C runtime dependency audit
- V18.4C cloud earnings event updater
- V18.4C state-path-protected archive cleaner
- V18.4D factor pack audit
- V18.4E factor output + forward tracking audit
- V18.4F forward factor coverage and expanded snapshot
- V18.4B promotion rules
- V18.4A forward outcome tracker
- V18.3E cockpit
- V18.3C factor shadow wrapper
- V17/V16 upstream runtime scripts
- Dynamic state-referenced base scripts
- Current outputs and state files

CURRENT EXPECTED STATUS:
V18_4G_R1_STATUS: OK_FINAL_DAILY_FACTOR_AUDIT_READY
RUNTIME_CODE_COUNT: 50
MISSING_REFERENCE_COUNT: 0
WORLDQUANT_STYLE_FACTOR_FOUND_COUNT: 6
WORLDQUANT_STYLE_FACTOR_RUNTIME_HIT_COUNT: 6
OUTPUT_COLUMN_FOUND_COUNT: 6
NON_NULL_VALUE_FACTOR_COUNT: 6
TOP_OR_RANK_OUTPUT_FOUND_COUNT: 6
FORWARD_COVERED_COUNT: 6
FORWARD_MISSING_COUNT: 0
EXPANDED_FORWARD_SNAPSHOT_ROWS: 105
CURRENT_SELECTED_FACTOR: F002

DYNAMIC STATE PATH PROTECTION:
state\v17_2_base_official_daily_path.txt
state\v17_4_base_official_daily_path.txt

MANIFEST:
$Manifest

RESTORE SCRIPT:
$Restore

COPY_COUNT:
$CopyCount

MISSING_COUNT:
$MissingCount

READ_MISSING_COUNT:
$($ReadMissing.Count)

PARSE_FAIL_COUNT:
$($ParseFail.Count)

TOTAL_BYTES:
$TotalBytes
"@

$ReadmeText | Set-Content -Encoding UTF8 -Path $Readme

Write-Host ""
Write-Host "=== V18.4G-R2 STABLE SNAPSHOT READY ==="
Write-Host "SNAPSHOT:"
Write-Host $SnapshotRoot
Write-Host ""
Write-Host "README:"
Write-Host $Readme
Write-Host ""
Write-Host "MANIFEST:"
Write-Host $Manifest
Write-Host ""
Write-Host "RESTORE SCRIPT:"
Write-Host $Restore
Write-Host ""
Write-Host "COPIED_COUNT: $CopyCount"
Write-Host "MISSING_COUNT: $MissingCount"
Write-Host "READ_MISSING_COUNT: $($ReadMissing.Count)"
Write-Host "PARSE_FAIL_COUNT: $($ParseFail.Count)"
