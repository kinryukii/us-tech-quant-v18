param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

chcp 65001 | Out-Null
Set-Location -LiteralPath $Root

New-Item -ItemType Directory -Force ".\outputs\v16\latest" | Out-Null
New-Item -ItemType Directory -Force ".\outputs\v16\archive" | Out-Null

Write-Host ""
Write-Host "=== V16.4 DAILY MASTER RUNNER START ==="
Write-Host ""

$steps = @(
    @{
        Name = "V16.1 Time Risk + Final Decision"
        Script = ".\run_v16_1_time_risk_final_decision.ps1"
    },
    @{
        Name = "V16.2 Candidate Review Pack"
        Script = ".\run_v16_2_candidate_review_pack.ps1"
    },
    @{
        Name = "V16.3 Pullback Trigger Layer"
        Script = ".\run_v16_3_pullback_trigger_layer.ps1"
    }
)

$runLog = @()

foreach ($step in $steps) {
    Write-Host ""
    Write-Host "=== RUN $($step.Name) ==="
    Write-Host ""

    if (!(Test-Path $step.Script)) {
        $msg = "MISS $($step.Script)"
        Write-Host $msg
        $runLog += $msg
        throw "Missing script: $($step.Script)"
    }

    & $step.Script -Root $Root

    $msg = "OK $($step.Name)"
    $runLog += $msg
}

$finalDecision = "D:\us-tech-quant\outputs\v16\latest\V16_FINAL_DECISION.md"
$reviewPack    = "D:\us-tech-quant\outputs\v16\latest\V16_CANDIDATE_REVIEW_PACK.md"
$pullbackPlan  = "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_TRIGGER_PLAN.md"

$finalActionCsv = "D:\us-tech-quant\outputs\v16\latest\V16_FINAL_ACTION_LIST.csv"
$reviewPackCsv  = "D:\us-tech-quant\outputs\v16\latest\V16_CANDIDATE_REVIEW_PACK.csv"
$pullbackCsv    = "D:\us-tech-quant\outputs\v16\latest\V16_PULLBACK_TRIGGER_PLAN.csv"

$manualReview = "D:\us-tech-quant\state\v16_manual_review_decisions.csv"

$masterSummary = "D:\us-tech-quant\outputs\v16\latest\V16_DAILY_MASTER_SUMMARY.md"
$readThese     = "D:\us-tech-quant\outputs\v16\latest\V16_DAILY_READ_THESE_FILES.txt"

function Get-LineOrDefault {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Default
    )
    if (!(Test-Path $Path)) {
        return $Default
    }
    $m = Select-String -Path $Path -Pattern $Pattern -SimpleMatch | Select-Object -First 1
    if ($null -eq $m) {
        return $Default
    }
    return $m.Line.Trim()
}

$todayActionLine = Get-LineOrDefault -Path $finalDecision -Pattern "TODAY_ACTION" -Default "TODAY_ACTION: UNKNOWN"
$pullbackLine = Get-LineOrDefault -Path $pullbackPlan -Pattern "PULLBACK_STATUS" -Default "PULLBACK_STATUS: UNKNOWN"

$generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$files = @(
    $finalDecision,
    $reviewPack,
    $pullbackPlan,
    $finalActionCsv,
    $reviewPackCsv,
    $pullbackCsv,
    $manualReview
)

$fileStatusRows = foreach ($f in $files) {
    if (Test-Path $f) {
        $item = Get-Item $f
        "| OK | $($item.FullName) | $($item.LastWriteTime) | $($item.Length) |"
    } else {
        "| MISS | $f |  |  |"
    }
}

$runLogText = ($runLog | ForEach-Object { "- $_" }) -join "`n"
$fileStatusText = $fileStatusRows -join "`n"

@"
# V16.4 Daily Master Summary

生成时间：$generatedAt

## 1. 今日总状态

$todayActionLine

$pullbackLine

## 2. 本次执行链路

$runLogText

## 3. 当前解释

如果当前状态仍然是：

- `NO_TRADE_REVIEW_ONLY`
- `NO_ACTIVE_PULLBACK_CANDIDATES`

说明系统没有失败，而是完成了风控判断：

1. 候选票存在；
2. 但没有任何票满足 `PASS_TO_A_PULLBACK_READY`；
3. 宏观时间风险仍然压制；
4. 因此今天没有可执行买入价。

## 4. 今日必读文件

| 顺序 | 文件 | 作用 |
|---:|---|---|
| 1 | $finalDecision | 今日最终动作 |
| 2 | $reviewPack | 候选票人工复核任务包 |
| 3 | $pullbackPlan | 回撤触发层结果 |
| 4 | $manualReview | 人工复核填写入口 |
| 5 | $finalActionCsv | V16.1 结构化结果 |
| 6 | $reviewPackCsv | V16.2 结构化结果 |
| 7 | $pullbackCsv | V16.3 结构化结果 |

## 5. 文件检查

| status | file | last_write_time | length |
|---|---|---:|---:|
$fileStatusText

## 6. 当前交易结论

**今天不交易。**

原因：

- 当前没有 A 类触发候选；
- CPI 前宏观时间风险仍高；
- 人工复核结果没有任何 `PASS_TO_A_PULLBACK_READY`；
- V16.3 没有生成可执行买入价。

## 7. 下一步开发建议

下一步进入：

**V16.5 Stable Daily README / Terminal UX**

目标：

- 每天终端只显示最终结论和必读文件；
- 不再刷长 Markdown；
- 保留 archive；
- 增加健康检查；
- 固定 latest 文件路径；
- 输出适合日常点击阅读的清单。
"@ | Set-Content -Encoding UTF8 $masterSummary

@"
=== V16.4 DAILY READ THESE FILES ===

MAIN STATUS:
$todayActionLine
$pullbackLine

READ THESE FILES:

[1] Master Summary
$masterSummary

[2] Final Decision
$finalDecision

[3] Candidate Review Pack
$reviewPack

[4] Pullback Trigger Plan
$pullbackPlan

[5] Manual Review Worksheet
$manualReview

CSV FILES:

[6] Final Action CSV
$finalActionCsv

[7] Candidate Review CSV
$reviewPackCsv

[8] Pullback Trigger CSV
$pullbackCsv

NEXT DEV STEP:
V16.5 Stable Daily README / Terminal UX
"@ | Set-Content -Encoding UTF8 $readThese

$archiveDir = "D:\us-tech-quant\outputs\v16\archive\master_" + (Get-Date -Format "yyyyMMdd_HHmmss")
New-Item -ItemType Directory -Force $archiveDir | Out-Null

Copy-Item $masterSummary $archiveDir -Force
Copy-Item $readThese $archiveDir -Force

Write-Host ""
Write-Host "=== V16.4 DAILY MASTER RUNNER DONE ==="
Write-Host ""
Write-Host $todayActionLine
Write-Host $pullbackLine
Write-Host ""
Write-Host "READ THESE FILES:"
Write-Host "[1] $masterSummary"
Write-Host "[2] $finalDecision"
Write-Host "[3] $reviewPack"
Write-Host "[4] $pullbackPlan"
Write-Host "[5] $manualReview"
Write-Host ""
Write-Host "ARCHIVE:"
Write-Host $archiveDir
Write-Host ""

Start-Process explorer.exe "D:\us-tech-quant\outputs\v16\latest"
Start-Process notepad.exe $masterSummary
