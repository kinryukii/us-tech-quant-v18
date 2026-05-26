param(
    [string]$Root = "D:\us-tech-quant",
    [string]$Entry = "D:\us-tech-quant\scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1"
)

$ErrorActionPreference = "Stop"

$OutDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$CsvOut = Join-Path $OutDir "V18_4C_runtime_dependency_graph_$ts.csv"
$MdOut  = Join-Path $OutDir "V18_4C_RUNTIME_DEPENDENCY_AUDIT_$ts.md"
$CurrentCsv = Join-Path $OutDir "V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv"
$CurrentMd  = Join-Path $OutDir "V18_4C_CURRENT_RUNTIME_DEPENDENCY_AUDIT.md"

$visited = New-Object "System.Collections.Generic.HashSet[string]"
$rows = New-Object System.Collections.Generic.List[object]

function Convert-ToScriptPath {
    param(
        [string]$BaseFile,
        [string]$Raw,
        [hashtable]$VarMap
    )

    if ([string]::IsNullOrWhiteSpace($Raw)) { return $null }

    $p = $Raw.Trim().Trim('"').Trim("'")

    foreach ($k in ($VarMap.Keys | Sort-Object Length -Descending)) {
        $v = [string]$VarMap[$k]
        $p = $p.Replace("`${$k}", $v)
        $p = $p.Replace("`$$k", $v)
    }

    $p = $p.Trim().Trim('"').Trim("'")

    if ($p -notmatch '\.(ps1|py|bat|cmd)$') {
        return $null
    }

    try {
        if ($p -match '^[A-Za-z]:\\') {
            return [System.IO.Path]::GetFullPath($p)
        }

        # Repository-root script references.
        # Many project wrappers are launched from repo root and use .\scripts\...
        # Do not resolve these relative to the caller file's own folder.
        if ($p.StartsWith(".\scripts\")) {
            return [System.IO.Path]::GetFullPath((Join-Path $Root $p.TrimStart(".\")))
        }

        if ($p.StartsWith("scripts\")) {
            return [System.IO.Path]::GetFullPath((Join-Path $Root $p))
        }

        if ($p.StartsWith("\scripts\")) {
            return [System.IO.Path]::GetFullPath((Join-Path $Root $p.TrimStart("\")))
        }

        if ($p.StartsWith(".\")) {
            return [System.IO.Path]::GetFullPath((Join-Path (Split-Path $BaseFile -Parent) $p))
        }

        if ($p -match '^[^\\/]+?\.(ps1|py|bat|cmd)$') {
            return [System.IO.Path]::GetFullPath((Join-Path (Split-Path $BaseFile -Parent) $p))
        }

        if ($p -match '[\\/]') {
            return [System.IO.Path]::GetFullPath((Join-Path (Split-Path $BaseFile -Parent) $p))
        }
    } catch {
        return $null
    }

    return $null
}

function Resolve-BaseToken {
    param(
        [string]$BaseFile,
        [string]$Token,
        [hashtable]$VarMap
    )

    if ([string]::IsNullOrWhiteSpace($Token)) { return $null }

    $t = $Token.Trim().Trim('"').Trim("'")

    if ($t.StartsWith("$")) {
        $name = $t.TrimStart("$").Trim("{").Trim("}")
        if ($VarMap.ContainsKey($name)) {
            return [string]$VarMap[$name]
        }
    }

    foreach ($k in ($VarMap.Keys | Sort-Object Length -Descending)) {
        $v = [string]$VarMap[$k]
        $t = $t.Replace("`${$k}", $v)
        $t = $t.Replace("`$$k", $v)
    }

    if ($t -match '^[A-Za-z]:\\') {
        return $t
    }

    if ($t.StartsWith(".\")) {
        return [System.IO.Path]::GetFullPath((Join-Path (Split-Path $BaseFile -Parent) $t))
    }

    return $null
}

function Expand-JoinPathExpression {
    param(
        [string]$BaseFile,
        [string]$Expr,
        [hashtable]$VarMap
    )

    if ([string]::IsNullOrWhiteSpace($Expr)) { return $null }

    $e = $Expr.Trim()

    # Join-Path $Root "scripts\v18"
    if ($e -match 'Join-Path\s+(?:-Path\s+)?([^\s\)]+)\s+(?:-ChildPath\s+)?["'']([^"'']+)["'']') {
        $base = Resolve-BaseToken -BaseFile $BaseFile -Token $matches[1] -VarMap $VarMap
        $child = $matches[2]

        if ($base) {
            try {
                return [System.IO.Path]::GetFullPath((Join-Path $base $child))
            } catch {
                return $null
            }
        }
    }

    return $null
}

function Build-VarMap {
    param(
        [string]$File
    )

    $VarMap = @{}
    $VarMap["Root"] = $Root
    $VarMap["PSScriptRoot"] = Split-Path $File -Parent
    $VarMap["ScriptRoot"] = Split-Path $File -Parent

    $lines = Get-Content -LiteralPath $File

    for ($pass = 0; $pass -lt 8; $pass++) {
        foreach ($line in $lines) {
            $l = $line.Trim()
            if ($l.StartsWith("#")) { continue }

            # $Var = "literal"
            if ($l -match '^\$([A-Za-z_][A-Za-z0-9_]*)\s*=\s*["'']([^"'']+)["'']\s*$') {
                $name = $matches[1]
                $value = $matches[2]

                foreach ($k in ($VarMap.Keys | Sort-Object Length -Descending)) {
                    $v = [string]$VarMap[$k]
                    $value = $value.Replace("`${$k}", $v)
                    $value = $value.Replace("`$$k", $v)
                }

                if ($value -match '^[A-Za-z]:\\') {
                    $VarMap[$name] = $value
                } elseif ($value.StartsWith(".\")) {
                    $VarMap[$name] = [System.IO.Path]::GetFullPath((Join-Path (Split-Path $File -Parent) $value))
                } else {
                    $VarMap[$name] = $value
                }

                continue
            }

            # $Var = Join-Path ...
            if ($l -match '^\$([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(Join-Path\b.+)$') {
                $name = $matches[1]
                $expr = $matches[2]
                $resolved = Expand-JoinPathExpression -BaseFile $File -Expr $expr -VarMap $VarMap
                if ($resolved) {
                    $VarMap[$name] = $resolved
                }
                continue
            }
        }
    }

    return $VarMap
}

function Add-Edge {
    param(
        [string]$Caller,
        [string]$Callee,
        [int]$Depth,
        [string]$Kind
    )

    if ([string]::IsNullOrWhiteSpace($Callee)) { return }

    $exists = $false
    if (Test-Path $Callee) { $exists = $true }

    $rows.Add([pscustomobject]@{
        depth = $Depth
        kind = $Kind
        caller = $Caller
        callee = $Callee
        exists = $exists
        extension = [System.IO.Path]::GetExtension($Callee).ToLowerInvariant()
    }) | Out-Null
}

function Find-ReferencedScripts {
    param(
        [string]$File,
        [hashtable]$VarMap
    )

    $text = Get-Content -Raw -LiteralPath $File
    $found = New-Object System.Collections.Generic.List[object]

    # 1) Any resolved variable whose value is a script path.
    foreach ($k in $VarMap.Keys) {
        $v = [string]$VarMap[$k]
        $resolved = Convert-ToScriptPath -BaseFile $File -Raw $v -VarMap $VarMap
        if ($resolved) {
            $found.Add([pscustomobject]@{
                path = $resolved
                kind = "variable_script_value:$k"
            }) | Out-Null
        }
    }

    # 2) Absolute / relative script paths in text.
    $patterns = @(
        '([A-Za-z]:\\[^''"`r`n]+?\.(ps1|py|bat|cmd))',
        '((?:\.\\|scripts\\|\\scripts\\)[^''"`r`n]+?\.(ps1|py|bat|cmd))'
    )

    foreach ($pat in $patterns) {
        foreach ($m in [regex]::Matches($text, $pat, "IgnoreCase")) {
            $raw = $m.Groups[1].Value
            $resolved = Convert-ToScriptPath -BaseFile $File -Raw $raw -VarMap $VarMap
            if ($resolved) {
                $found.Add([pscustomobject]@{
                    path = $resolved
                    kind = "static_path_reference"
                }) | Out-Null
            }
        }
    }

    # 3) Quoted script file names, useful for Python subprocess and bare local scripts.
    foreach ($m in [regex]::Matches($text, '["'']([^"'']+?\.(ps1|py|bat|cmd))["'']', "IgnoreCase")) {
        $raw = $m.Groups[1].Value
        $resolved = Convert-ToScriptPath -BaseFile $File -Raw $raw -VarMap $VarMap
        if ($resolved) {
            $found.Add([pscustomobject]@{
                path = $resolved
                kind = "quoted_script_reference"
            }) | Out-Null
        }
    }

    # 4) -File $Variable
    foreach ($m in [regex]::Matches($text, '-File\s+(\$[A-Za-z_][A-Za-z0-9_]*)', "IgnoreCase")) {
        $varName = $m.Groups[1].Value.TrimStart("$")
        if ($VarMap.ContainsKey($varName)) {
            $resolved = Convert-ToScriptPath -BaseFile $File -Raw ([string]$VarMap[$varName]) -VarMap $VarMap
            if ($resolved) {
                $found.Add([pscustomobject]@{
                    path = $resolved
                    kind = "powershell_file_variable:$varName"
                }) | Out-Null
            }
        }
    }

    # 5) & $Variable / python $Variable / py $Variable
    foreach ($m in [regex]::Matches($text, '(?:^|\s)(&|python|python\.exe|py)\s+(\$[A-Za-z_][A-Za-z0-9_]*)', "IgnoreCase")) {
        $varName = $m.Groups[2].Value.TrimStart("$")
        if ($VarMap.ContainsKey($varName)) {
            $resolved = Convert-ToScriptPath -BaseFile $File -Raw ([string]$VarMap[$varName]) -VarMap $VarMap
            if ($resolved) {
                $found.Add([pscustomobject]@{
                    path = $resolved
                    kind = "command_variable:$varName"
                }) | Out-Null
            }
        }
    }

    # 6) -File (Join-Path ...)
    foreach ($m in [regex]::Matches($text, '-File\s+\((Join-Path[^\r\n\)]+)\)', "IgnoreCase")) {
        $resolved = Expand-JoinPathExpression -BaseFile $File -Expr $m.Groups[1].Value -VarMap $VarMap
        if ($resolved) {
            $resolved2 = Convert-ToScriptPath -BaseFile $File -Raw $resolved -VarMap $VarMap
            if ($resolved2) {
                $found.Add([pscustomobject]@{
                    path = $resolved2
                    kind = "powershell_file_joinpath"
                }) | Out-Null
            }
        }
    }

    return $found | Sort-Object path -Unique
}

function Walk {
    param(
        [string]$File,
        [int]$Depth,
        [string]$Caller,
        [string]$Kind
    )

    if ([string]::IsNullOrWhiteSpace($File)) { return }

    try {
        $full = [System.IO.Path]::GetFullPath($File)
    } catch {
        return
    }

    Add-Edge -Caller $Caller -Callee $full -Depth $Depth -Kind $Kind

    if (-not (Test-Path $full)) { return }

    if ($visited.Contains($full)) { return }
    $visited.Add($full) | Out-Null

    $ext = [System.IO.Path]::GetExtension($full).ToLowerInvariant()
    if ($ext -notin @(".ps1", ".py", ".bat", ".cmd")) { return }

    $VarMap = Build-VarMap -File $full
    $refs = Find-ReferencedScripts -File $full -VarMap $VarMap

    foreach ($r in $refs) {
        Walk -File $r.path -Depth ($Depth + 1) -Caller $full -Kind $r.kind
    }
}

Walk -File $Entry -Depth 0 -Caller "" -Kind "entry"

$rows | Export-Csv -NoTypeInformation -Encoding UTF8 $CsvOut
Copy-Item -Force $CsvOut $CurrentCsv

$existing = $rows | Where-Object { $_.exists -eq $true -and $_.extension -in @(".ps1",".py",".bat",".cmd") } | Select-Object -ExpandProperty callee -Unique
$missing = $rows | Where-Object { $_.exists -eq $false } | Select-Object -ExpandProperty callee -Unique
$byExt = $existing | Group-Object { [System.IO.Path]::GetExtension($_).ToLowerInvariant() }

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# V18.4C Runtime Dependency Audit") | Out-Null
$md.Add("") | Out-Null
$md.Add("生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')") | Out-Null
$md.Add("") | Out-Null
$md.Add("## 1. 结论") | Out-Null
$md.Add("") | Out-Null
$md.Add("- ENTRY: ``$Entry``") | Out-Null
$md.Add("- UNIQUE_EXISTING_CODE_COUNT: ``$($existing.Count)``") | Out-Null
$md.Add("- MISSING_REFERENCE_COUNT: ``$($missing.Count)``") | Out-Null
$md.Add("- GRAPH_CSV: ``$CsvOut``") | Out-Null
$md.Add("") | Out-Null

$md.Add("## 2. 按扩展名统计") | Out-Null
$md.Add("") | Out-Null
$md.Add("| ext | count |") | Out-Null
$md.Add("|---|---:|") | Out-Null
foreach ($g in $byExt) {
    $md.Add("| $($g.Name) | $($g.Count) |") | Out-Null
}
$md.Add("") | Out-Null

$md.Add("## 3. 参与运行的代码文件") | Out-Null
$md.Add("") | Out-Null
foreach ($f in ($existing | Sort-Object)) {
    $md.Add("- ``$f``") | Out-Null
}
$md.Add("") | Out-Null

if ($missing.Count -gt 0) {
    $md.Add("## 4. 缺失引用") | Out-Null
    $md.Add("") | Out-Null
    foreach ($m in ($missing | Sort-Object)) {
        $md.Add("- ``$m``") | Out-Null
    }
    $md.Add("") | Out-Null
}

$md.Add("## 5. 解释") | Out-Null
$md.Add("") | Out-Null
$md.Add("这个统计是增强静态依赖扫描：会识别显式脚本路径、Join-Path 变量、-File `$Variable、python `$Variable、以及脚本变量值。动态拼接特别复杂时仍可能低估，但比第一版更接近真实运行链路。") | Out-Null

$md -join "`r`n" | Set-Content -Encoding UTF8 $MdOut
Copy-Item -Force $MdOut $CurrentMd

Write-Host ""
Write-Host "=== V18.4C RUNTIME DEPENDENCY AUDIT READY ==="
Write-Host "UNIQUE_EXISTING_CODE_COUNT: $($existing.Count)"
Write-Host "MISSING_REFERENCE_COUNT: $($missing.Count)"
Write-Host "READ:"
Write-Host $CurrentMd
Write-Host "CSV:"
Write-Host $CurrentCsv

