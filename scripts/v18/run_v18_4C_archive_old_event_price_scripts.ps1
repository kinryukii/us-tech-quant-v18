param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Join-Path $Root "scripts"
$OutDir = Join-Path $Root "outputs\v18\ops"
$CurrentGraph = Join-Path $OutDir "V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv"

if (-not (Test-Path $CurrentGraph)) {
    throw "Dependency graph not found. Run run_v18_4C_runtime_dependency_audit.ps1 first."
}

$deps = Import-Csv -LiteralPath $CurrentGraph

$protected = @{}

foreach ($d in $deps) {
    if ($d.exists -eq "True" -and $d.callee) {
        try {
            $protected[[System.IO.Path]::GetFullPath($d.callee).ToLowerInvariant()] = $true
        } catch {}
    }
}

# STATE_PATH_REFERENCED_PROTECT
# Protect any .ps1 path explicitly referenced by state/*.txt/csv/md/json files.
$stateReferencedScripts = @{}

$stateRoot = Join-Path $Root "state"

if (Test-Path -LiteralPath $stateRoot) {
    Get-ChildItem -LiteralPath $stateRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension.ToLowerInvariant() -in @(".txt", ".csv", ".md", ".json") } |
        ForEach-Object {
            try {
                $stateText = Get-Content -Raw -LiteralPath $_.FullName -ErrorAction SilentlyContinue
                $pattern = 'D:\\us-tech-quant\\[^\r\n,;"]+?\.ps1'

                foreach ($m in [regex]::Matches($stateText, $pattern, "IgnoreCase")) {
                    $refPath = $m.Value.Trim().Trim('"').Trim("'")

                    if (-not [string]::IsNullOrWhiteSpace($refPath)) {
                        try {
                            $stateReferencedScripts[[System.IO.Path]::GetFullPath($refPath).ToLowerInvariant()] = $true
                        } catch {}
                    }
                }
            } catch {}
        }
}

$extraProtectPatterns = @(
    "*run_v18_4B_R1_final_daily_wrapper.ps1",
    "*run_v18_4B_factor_outcome_summary_promotion_rules.ps1",
    "*v18_4B_factor_outcome_summary_promotion_rules.py",
    "*run_v18_4A_R1_daily_integrated_wrapper.ps1",
    "*run_v18_4A_factor_forward_outcome_tracker.ps1",
    "*v18_4A_factor_forward_outcome_tracker.py",
    "*run_v18_4C_*",
    "*run_v18_4D_*",
    "*run_v18_4E_*",
    "*run_v18_4F_*",
    "*run_v18_4G_*"
)

$candidatePatterns = @(
    "*event*.ps1",
    "*event*.py",
    "*calendar*.ps1",
    "*calendar*.py",
    "*price*.ps1",
    "*price*.py",
    "*freshness*.ps1",
    "*freshness*.py",
    "*update*.ps1",
    "*update*.py"
)

$allCandidates = @()

foreach ($pat in $candidatePatterns) {
    $files = Get-ChildItem -Path $ScriptRoot -Recurse -File -Include $pat -ErrorAction SilentlyContinue

    foreach ($file in $files) {
        $full = $file.FullName
        $lower = ""

        try {
            $lower = [System.IO.Path]::GetFullPath($full).ToLowerInvariant()
        } catch {
            continue
        }

        $isProtected = $false

        if ($protected.ContainsKey($lower)) {
            $isProtected = $true
        }

        if ($stateReferencedScripts.ContainsKey($lower)) {
            $isProtected = $true
        }

        foreach ($pp in $extraProtectPatterns) {
            if ($file.Name -like $pp) {
                $isProtected = $true
            }
        }

        if ($full -match "\\archive\\" -or $full -match "\\deprecated\\") {
            $isProtected = $true
        }

        if (-not $isProtected) {
            $allCandidates += [pscustomobject]@{
                full_name = $full
                name = $file.Name
                length = $file.Length
                last_write_time = $file.LastWriteTime
            }
        }
    }
}

$candidates = @($allCandidates | Sort-Object full_name -Unique)

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$Report = Join-Path $OutDir "V18_4C_DEPRECATED_EVENT_PRICE_SCRIPT_CANDIDATES_$ts.csv"

$candidates | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $Report

Write-Host ""
Write-Host "=== V18.4C OLD EVENT/PRICE SCRIPT CANDIDATES ==="
Write-Host "CANDIDATE_COUNT: $($candidates.Count)"
Write-Host "STATE_REFERENCED_PROTECTED_COUNT: $($stateReferencedScripts.Count)"
Write-Host "REPORT:"
Write-Host $Report

if ($DryRun) {
    Write-Host "DRY_RUN: no files moved."

    foreach ($c in $candidates) {
        Write-Host "WOULD_ARCHIVE: $($c.full_name)"
    }

    return
}

if ($candidates.Count -eq 0) {
    Write-Host "NO_CANDIDATES_TO_ARCHIVE"
    return
}

$ArchiveDir = Join-Path $Root "archive\deprecated\v18_4C_event_price_merge_$ts"
New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null

foreach ($c in $candidates) {
    $src = $c.full_name
    $rel = $src.Substring($Root.Length).TrimStart("\")
    $dst = Join-Path $ArchiveDir $rel
    $dstParent = Split-Path $dst -Parent

    New-Item -ItemType Directory -Force -Path $dstParent | Out-Null
    Move-Item -Force -LiteralPath $src -Destination $dst

    Write-Host "ARCHIVED: $src"
}

Write-Host ""
Write-Host "=== V18.4C ARCHIVE DONE ==="
Write-Host "ARCHIVE_DIR:"
Write-Host $ArchiveDir
