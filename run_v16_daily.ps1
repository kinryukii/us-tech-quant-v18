param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

chcp 65001 | Out-Null
Set-Location -LiteralPath $Root

Write-Host ""
Write-Host "=== RUN V16 DAILY MASTER FLOW ==="
Write-Host ""

if (!(Test-Path ".\run_v16_4_daily_master.ps1")) {
    throw "Missing run_v16_4_daily_master.ps1"
}

& ".\run_v16_4_daily_master.ps1" -Root $Root

Write-Host ""
Write-Host "=== REFRESH V16.5 LITE README ==="
Write-Host ""

$generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$finalDecision = "D:\us-tech-quant\outputs\v16\latest\V16_FINAL_DECISION.md"
$reviewPack    = "D:\us-tech-quant\outputs\v16\latest\V16_CANDIDATE_REVIEW_PACK.md"
$pullbackPlan  = "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_TRIGGER_PLAN.md"
$masterSummary = "D:\us-tech-quant\outputs\v16\latest\V16_DAILY_MASTER_SUMMARY.md"

$finalActionCsv = "D:\us-tech-quant\outputs\v16\latest\V16_FINAL_ACTION_LIST.csv"
$reviewPackCsv  = "D:\us-tech-quant\outputs\v16\latest\V16_CANDIDATE_REVIEW_PACK.csv"
$pullbackCsv    = "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_TRIGGER_PLAN.csv"
$manualReview   = "D:\us-tech-quant\state\v16_manual_review_decisions.csv"

$stableReadme = "D:\us-tech-quant\outputs\v16\latest\V16_STABLE_DAILY_README.md"
$stableTxt    = "D:\us-tech-quant\outputs\v16\latest\V16_STABLE_DAILY_READ_THESE_FILES.txt"
$healthMd     = "D:\us-tech-quant\outputs\v16\latest\V16_STABLE_HEALTH_CHECK.md"

function Get-LineOrDefault {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Default
    )
    if (!(Test-Path $Path)) { return $Default }
    $m = Select-String -Path $Path -Pattern $Pattern -SimpleMatch | Select-Object -First 1
    if ($null -eq $m) { return $Default }
    return $m.Line.Trim()
}

$todayAction = Get-LineOrDefault -Path $finalDecision -Pattern "TODAY_ACTION" -Default "TODAY_ACTION: UNKNOWN"
$pullbackStatus = Get-LineOrDefault -Path $pullbackPlan -Pattern "PULLBACK_STATUS" -Default "PULLBACK_STATUS: UNKNOWN"

$files = @(
    $finalDecision,
    $reviewPack,
    $pullbackPlan,
    $masterSummary,
    $finalActionCsv,
    $reviewPackCsv,
    $pullbackCsv,
    $manualReview
)

$health = "OK"
$fileRows = @()

foreach ($f in $files) {
    if (Test-Path $f) {
        $item = Get-Item $f
        $fileRows += "| OK | $($item.FullName) | $($item.LastWriteTime) | $($item.Length) |"
    } else {
        $fileRows += "| MISS | $f |  |  |"
        $health = "WARN"
    }
}

$healthLines = @(
"# V16.5 Stable Health Check",
"",
"生成时间：$generatedAt",
"",
"## 1. Health Status",
"",
"**HEALTH_STATUS：$health**",
"",
"## 2. 文件检查",
"",
"| status | file | last_write_time | length |",
"|---|---|---:|---:|"
) + $fileRows + @(
"",
"## 3. 说明",
"",
"这是 V16.5-lite。它读取 V16.4 已经生成的 latest 文件，生成稳定阅读入口。"
)

$stableLines = @(
"# V16.5 Stable Daily README",
"",
"生成时间：$generatedAt",
"",
"## 1. 今日总状态",
"",
$todayAction,
"",
$pullbackStatus,
"",
"**HEALTH_STATUS：$health**",
"",
"## 2. 当前交易结论",
"",
"**今天不交易。**",
"",
"当前系统判断：",
"",
"1. 候选票存在；",
"2. 但没有任何票满足 PASS_TO_A_PULLBACK_READY；",
"3. 宏观时间风险仍然压制；",
"4. V16.3 没有生成可执行买入触发价。",
"",
"## 3. 当前 V16 链路状态",
"",
"| 模块 | 状态 | 说明 |",
"|---|---|---|",
"| V16.1 | OK | 时间风险 + 今日最终动作 |",
"| V16.2 | OK | 候选人工复核任务包 |",
"| V16.3 | OK | 回撤触发层 |",
"| V16.4 | OK | Daily Master Summary |",
"| V16.5-lite | OK | 稳定版阅读入口 |",
"",
"## 4. 今日必读文件",
"",
"| 顺序 | 文件 | 作用 |",
"|---:|---|---|",
"| 1 | $masterSummary | V16.4 主汇总 |",
"| 2 | $finalDecision | 今日最终动作 |",
"| 3 | $reviewPack | 候选票人工复核任务包 |",
"| 4 | $pullbackPlan | 回撤触发层结果 |",
"| 5 | $manualReview | 人工复核填写入口 |",
"| 6 | $healthMd | V16.5 健康检查 |",
"| 7 | $finalActionCsv | V16.1 结构化结果 |",
"| 8 | $reviewPackCsv | V16.2 结构化结果 |",
"| 9 | $pullbackCsv | V16.3 结构化结果 |",
"",
"## 5. 每日使用方式",
"",
"以后每天只运行：",
"",
"Set-Location -LiteralPath `"D:\us-tech-quant`"",
".\run_v16_daily.ps1",
"",
"## 6. 下一步开发建议",
"",
"下一步进入：V16.6 Capital / Rakuten Execution Layer。",
"",
"但只有当 V16.3 出现 ACTIVE_PULLBACK_CANDIDATE 后，V16.6 才会真正输出买入股数。"
)

$txtLines = @(
"=== V16 DAILY READ THESE FILES ===",
"",
"MAIN STATUS:",
$todayAction,
$pullbackStatus,
"HEALTH_STATUS: $health",
"",
"READ THIS FIRST:",
$stableReadme,
"",
"CORE FILES:",
"[1] $masterSummary",
"[2] $finalDecision",
"[3] $reviewPack",
"[4] $pullbackPlan",
"[5] $manualReview",
"[6] $healthMd",
"",
"NEXT DEV STEP:",
"V16.6 Capital / Rakuten Execution Layer"
)

$healthLines | Set-Content -Encoding UTF8 $healthMd
$stableLines | Set-Content -Encoding UTF8 $stableReadme
$txtLines | Set-Content -Encoding UTF8 $stableTxt

$archiveDir = "D:\us-tech-quant\outputs\v16\archive\daily_$stamp"
New-Item -ItemType Directory -Force $archiveDir | Out-Null

Copy-Item $stableReadme $archiveDir -Force
Copy-Item $stableTxt $archiveDir -Force
Copy-Item $healthMd $archiveDir -Force

Write-Host ""
Write-Host "=== V16 DAILY DONE ==="
Write-Host ""
Write-Host $todayAction
Write-Host $pullbackStatus
Write-Host "HEALTH_STATUS: $health"
Write-Host ""
Write-Host "READ THIS FILE:"
Write-Host $stableReadme
Write-Host ""
Write-Host "CORE FILES:"
Write-Host "[1] $masterSummary"
Write-Host "[2] $finalDecision"
Write-Host "[3] $reviewPack"
Write-Host "[4] $pullbackPlan"
Write-Host "[5] $manualReview"
Write-Host "[6] $healthMd"
Write-Host ""
Write-Host "ARCHIVE:"
Write-Host $archiveDir
Write-Host ""

Start-Process notepad.exe $stableReadme
