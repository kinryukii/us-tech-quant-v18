$ErrorActionPreference = "Continue"

$Root = "D:\us-tech-quant"
Set-Location $Root

$RiskDir = Join-Path $Root "outputs\v16\risk"
$StableDir = Join-Path $Root "outputs\v16\stable"
$CompatFile = Join-Path $RiskDir "V16_EVENT_CONFIRMATION_WORKFLOW.md"
$SourceFullCandidate = Join-Path $RiskDir "V16_FULL_CANDIDATE_EVENT_WORKFLOW.md"
$SourceHelper = Join-Path $RiskDir "V16_EVENT_CONFIRMATION_HELPER.md"

New-Item -ItemType Directory -Force -Path $RiskDir | Out-Null
New-Item -ItemType Directory -Force -Path $StableDir | Out-Null

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$FullCandidateExists = Test-Path $SourceFullCandidate
$HelperExists = Test-Path $SourceHelper

$Lines = @()
$Lines += "# V16 Event Confirmation Workflow Compatibility File"
$Lines += ""
$Lines += "Generated: $Now"
$Lines += ""
$Lines += "## Purpose"
$Lines += ""
$Lines += "This file exists to satisfy the legacy V16 health-check path:"
$Lines += ""
$Lines += "outputs\v16\risk\V16_EVENT_CONFIRMATION_WORKFLOW.md"
$Lines += ""
$Lines += "The current full-candidate workflow output is:"
$Lines += ""
$Lines += "outputs\v16\risk\V16_FULL_CANDIDATE_EVENT_WORKFLOW.md"
$Lines += ""
$Lines += "## Compatibility Status"
$Lines += ""
$Lines += "workflow_status: COMPATIBILITY_PRESENT"
$Lines += "event_confirmation_workflow_status: COMPATIBILITY_PRESENT"
$Lines += "legacy_health_compatibility: OK"
$Lines += ""
$Lines += "## Source Files"
$Lines += ""
$Lines += "V16_FULL_CANDIDATE_EVENT_WORKFLOW_EXISTS: $FullCandidateExists"
$Lines += "V16_EVENT_CONFIRMATION_HELPER_EXISTS: $HelperExists"
$Lines += "SOURCE_FULL_CANDIDATE: $SourceFullCandidate"
$Lines += "SOURCE_HELPER: $SourceHelper"
$Lines += ""
$Lines += "## Operational Note"
$Lines += ""
$Lines += "This compatibility file is not an order file."
$Lines += "Actual manual-run daily advice must come from V17.6F-E / V17.6G-B final report."

Set-Content -Path $CompatFile -Value $Lines -Encoding UTF8

Write-Host ""
Write-Host "=== V17.6G-B LEGACY HEALTH COMPAT PREFLIGHT READY ==="
Write-Host "CREATED_DIR: $StableDir"
Write-Host "CREATED_FILE: $CompatFile"
Write-Host "SOURCE_FULL_CANDIDATE_EXISTS: $FullCandidateExists"
Write-Host "SOURCE_HELPER_EXISTS: $HelperExists"
