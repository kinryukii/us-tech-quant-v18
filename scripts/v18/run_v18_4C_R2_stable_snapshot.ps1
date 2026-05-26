param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SnapshotRoot = Join-Path $Root "archive\stable\V18_4C_R2_stable_runtime_audit_event_price_cleanup_$Stamp"

$Manifest = Join-Path $SnapshotRoot "V18_4C_R2_STABLE_MANIFEST_$Stamp.csv"
$Readme = Join-Path $SnapshotRoot "V18_4C_R2_STABLE_README.txt"
$Restore = Join-Path $SnapshotRoot "restore_v18_4C_R2_stable_snapshot.ps1"

New-Item -ItemType Directory -Force -Path $SnapshotRoot | Out-Null

$rows = New-Object System.Collections.Generic.List[object]

function Copy-One {
    param(
        [string]$Source,
        [string]$Root,
        [string]$SnapshotRoot,
        [string]$Layer
    )

    if ([string]::IsNullOrWhiteSpace($Source)) { return }

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

    $script:rows.Add([pscustomobject]@{
        layer = $Layer
        source = $Source
        relative_path = $rel
        destination = $dest
        exists = $exists
        copied = $exists
        size_bytes = if ($exists) { (Get-Item -LiteralPath $Source).Length } else { 0 }
    }) | Out-Null
}

Write-Host ""
Write-Host "=== V18.4C-R2 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT: $SnapshotRoot"

# Refresh audit before snapshot
$AuditScript = Join-Path $Root "scripts\v18\run_v18_4C_runtime_dependency_audit.ps1"
if (Test-Path $AuditScript) {
    powershell -NoProfile -ExecutionPolicy Bypass -File $AuditScript | Out-Host
}

$Graph = Join-Path $Root "outputs\v18\ops\V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv"

$codeFiles = @()

if (Test-Path $Graph) {
    $graphRows = Import-Csv -LiteralPath $Graph
    $codeFiles = @(
        $graphRows |
            Where-Object { $_.exists -eq "True" -and $_.callee -match '\.(ps1|py|bat|cmd)$' } |
            Select-Object -ExpandProperty callee -Unique
    )
}

# Always include V18.4C outer scripts even if the graph entry is V18.4B inner chain.
$extraCode = @(
    (Join-Path $Root "scripts\v18\run_v18_4C_R1_final_daily_wrapper.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_4C_runtime_dependency_audit.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_4C_cloud_earnings_event_update.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_4C_archive_old_event_price_scripts.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_4C_R2_stable_snapshot.ps1")
)

$allCode = @($codeFiles + $extraCode | Select-Object -Unique)

Write-Host ""
Write-Host "=== COPY CODE LAYER ==="
foreach ($f in $allCode) {
    Copy-One -Source $f -Root $Root -SnapshotRoot $SnapshotRoot -Layer "code"
}

Write-Host ""
Write-Host "=== COPY OUTPUT LAYER ==="
$outputDirs = @(
    (Join-Path $Root "outputs\v18\daily_integrated"),
    (Join-Path $Root "outputs\v18\ops"),
    (Join-Path $Root "outputs\v18\outcome_summary"),
    (Join-Path $Root "outputs\v18\factor_shadow"),
    (Join-Path $Root "outputs\v18\factor_pack"),
    (Join-Path $Root "outputs\v17"),
    (Join-Path $Root "outputs\v16\read_center")
)

foreach ($dir in $outputDirs) {
    if (Test-Path $dir) {
        Get-ChildItem -LiteralPath $dir -Recurse -File | ForEach-Object {
            Copy-One -Source $_.FullName -Root $Root -SnapshotRoot $SnapshotRoot -Layer "output"
        }
    }
}

Write-Host ""
Write-Host "=== COPY STATE LAYER ==="
$stateDirs = @(
    (Join-Path $Root "state\v18"),
    (Join-Path $Root "state\v17"),
    (Join-Path $Root "state\v16")
)

foreach ($dir in $stateDirs) {
    if (Test-Path $dir) {
        Get-ChildItem -LiteralPath $dir -Recurse -File | ForEach-Object {
            Copy-One -Source $_.FullName -Root $Root -SnapshotRoot $SnapshotRoot -Layer "state"
        }
    }
}

Write-Host ""
Write-Host "=== PARSE CHECK SNAPSHOT CRITICAL SCRIPTS ==="

$critical = @(
    (Join-Path $Root "scripts\v18\run_v18_4C_R1_final_daily_wrapper.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_4C_runtime_dependency_audit.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_4C_cloud_earnings_event_update.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_4C_archive_old_event_price_scripts.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1"),
    (Join-Path $Root "scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1")
)

$parseFail = New-Object System.Collections.Generic.List[string]

foreach ($f in $critical) {
    if (Test-Path $f) {
        try {
            [scriptblock]::Create((Get-Content -Raw -LiteralPath $f)) | Out-Null
            Write-Host "OK_PARSE: $f"
        } catch {
            Write-Host "FAIL_PARSE: $f"
            $parseFail.Add($f) | Out-Null
        }
    } else {
        Write-Host "MISSING_CRITICAL: $f"
        $parseFail.Add($f) | Out-Null
    }
}

$missingCount = @($rows | Where-Object { $_.exists -eq $false }).Count
$copyCount = @($rows | Where-Object { $_.copied -eq $true }).Count
$totalBytes = ($rows | Measure-Object -Property size_bytes -Sum).Sum

$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $Manifest

$restoreText = @"
param(
    [string]`$Root = "D:\us-tech-quant"
)

`$ErrorActionPreference = "Stop"

`$SnapshotRoot = "$SnapshotRoot"

Write-Host ""
Write-Host "=== RESTORE V18.4C-R2 STABLE SNAPSHOT START ==="
Write-Host "SNAPSHOT: `$SnapshotRoot"
Write-Host "TARGET_ROOT: `$Root"

`$manifest = Import-Csv -LiteralPath "$Manifest"

foreach (`$r in `$manifest) {
    if (`$r.copied -ne "True") { continue }

    `$src = Join-Path `$SnapshotRoot `$r.relative_path
    `$dst = Join-Path `$Root `$r.relative_path

    if (Test-Path -LiteralPath `$src) {
        New-Item -ItemType Directory -Force -Path (Split-Path `$dst -Parent) | Out-Null
        Copy-Item -Force -LiteralPath `$src -Destination `$dst
        Write-Host "RESTORED: `$dst"
    }
}

Write-Host ""
Write-Host "=== RESTORE V18.4C-R2 STABLE SNAPSHOT DONE ==="
Write-Host "NEXT DAILY COMMAND:"
Write-Host 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4C_R1_final_daily_wrapper.ps1"'
"@

$restoreText | Set-Content -Encoding UTF8 -Path $Restore

$readmeText = @"
V18.4C-R2 STABLE SNAPSHOT

生成时间:
$Stamp

SNAPSHOT:
$SnapshotRoot

STATUS:
STABLE_SNAPSHOT_CREATED

SCOPE:
- V18.4C-R1 final daily wrapper
- V18.4C runtime dependency audit
- V18.4C cloud earnings event updater
- V18.4C old event/price/update archive cleaner
- V18.4B-R1 final daily wrapper
- V18.4B promotion rules
- V18.4A forward tracker
- V18.3E cockpit
- V18.3C factor shadow wrapper
- V17/V16 upstream scripts required by current runtime graph
- Current outputs and state files

CURRENT DAILY COMMAND:
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4C_R1_final_daily_wrapper.ps1"

CURRENT AUDIT:
UNIQUE_EXISTING_CODE_COUNT should be 50
MISSING_REFERENCE_COUNT should be 0

CLEANUP RESULT:
Old event/price/update archive candidates were already moved to:
D:\us-tech-quant\archive\deprecated\v18_4C_event_price_merge_20260514_223322

CLOUD EVENTS:
Cloud earnings event calendar has been written to:
D:\us-tech-quant\state\v16\event_calendar.csv
D:\us-tech-quant\state\v18\cloud_earnings_event_calendar.csv

MANIFEST:
$Manifest

RESTORE SCRIPT:
$Restore

COPY_COUNT:
$copyCount

MISSING_COUNT:
$missingCount

PARSE_FAIL_COUNT:
$($parseFail.Count)

TOTAL_BYTES:
$totalBytes
"@

$readmeText | Set-Content -Encoding UTF8 -Path $Readme

Write-Host ""
Write-Host "=== V18.4C-R2 STABLE SNAPSHOT READY ==="
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
Write-Host "COPIED_COUNT: $copyCount"
Write-Host "MISSING_COUNT: $missingCount"
Write-Host "PARSE_FAIL_COUNT: $($parseFail.Count)"
