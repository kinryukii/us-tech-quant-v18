$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$UpstreamPs = Join-Path $Root "scripts\v18\run_v18_3D_factor_pack_shadow_extension.ps1"
$FixPy = Join-Path $Root "scripts\v18\v18_3D_R1_official_overlap_fix.py"

Write-Host ""
Write-Host "=== V18.3D-R1 OFFICIAL OVERLAP FIX START ==="
Write-Host "ROOT: $Root"
Write-Host "PYTHON: $Py"
Write-Host "UPSTREAM: $UpstreamPs"
Write-Host "FIX_SCRIPT: $FixPy"
Write-Host ""

if (!(Test-Path $Py)) {
    throw "Python not found: $Py"
}
if (!(Test-Path $UpstreamPs)) {
    throw "Upstream V18.3D wrapper not found: $UpstreamPs"
}
if (!(Test-Path $FixPy)) {
    throw "Fix script not found: $FixPy"
}

Write-Host "STEP 1: run upstream V18.3D factor pack"
powershell -NoProfile -ExecutionPolicy Bypass -File $UpstreamPs

Write-Host ""
Write-Host "STEP 2: repair official review overlap detection"
& $Py $FixPy

if ($LASTEXITCODE -ne 0) {
    throw "V18.3D-R1 official overlap fix failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== V18.3D-R1 OFFICIAL OVERLAP FIX DONE ==="
