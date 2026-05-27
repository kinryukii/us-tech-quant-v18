
$ErrorActionPreference = "Stop"

$Root = if ($env:US_TECH_QUANT_ROOT) { $env:US_TECH_QUANT_ROOT } else { "D:\us-tech-quant" }
$PyScript = Join-Path $Root "scripts\v18\v18_3D_factor_pack_shadow_extension.py"
$ReadFirst = Join-Path $Root "outputs\v18\factor_pack\V18_3D_READ_FIRST.txt"

$PythonCandidates = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    "python"
)

$Python = $null
foreach ($p in $PythonCandidates) {
    try {
        if ($p -eq "python") {
            $cmd = Get-Command python -ErrorAction SilentlyContinue
            if ($cmd) { $Python = "python"; break }
        } elseif (Test-Path $p) {
            $Python = $p; break
        }
    } catch {}
}

if (-not $Python) {
    throw "Python not found. Please activate .venv or set US_TECH_QUANT_ROOT."
}

Write-Host ""
Write-Host "=== V18.3D FACTOR PACK SHADOW EXTENSION START ==="
Write-Host "ROOT: $Root"
Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $PyScript"
Write-Host ""

if (-not (Test-Path $PyScript)) {
    throw "Missing Python script: $PyScript"
}

& $Python $PyScript
$code = $LASTEXITCODE

Write-Host ""
Write-Host "=== V18.3D READ FIRST ==="
if (Test-Path $ReadFirst) {
    Get-Content $ReadFirst -Encoding UTF8
} else {
    Write-Host "READ_FIRST_NOT_FOUND: $ReadFirst"
}

if ($code -ne 0) {
    throw "V18.3D failed with exit code $code"
}

Write-Host ""
Write-Host "=== V18.3D FACTOR PACK SHADOW EXTENSION DONE ==="
