# V18 中文每日运行说明 / Runbook

## 1. 每日最推荐运行方式
```powershell
Set-Location "D:\us-tech-quant"
& "D:\us-tech-quant\.venv\Scripts\Activate.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1" -RunUniverseRollingScan -RunForwardTracker -RunManualFeedback -RunChineseHomepage
```

## 2. 轻量只刷新中文首页
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_33A_chinese_daily_operator_homepage.ps1"
```

## 3. 每天运行后先读什么
- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`
- `outputs/v18/read_center/V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md`
- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`
- `outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md`
- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`
- `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`

## 4. 状态解释
- 结论: WARN 说明有缺失或未知字段，先读警告来源再动作。
- OK: 中文日报已生成，核心一致性可接受。
- WARN: 先读警告来源，再决定是否继续动作。
- FAIL: 不要用该报告做交易判断。
- `AUTO_TRADE` / `AUTO_SELL` 必须保持禁用。

## 5. 今日系统快照
- 候选数: `252`
- 冻结覆盖状态: `FULL_MATCH`
- 冻结 ticker 数: `252`
- 预期候选数: `252`
- 当前允许交易候选数: `0`
- 账户状态质量: `WARN_TEMPLATE_EMPTY_ACCOUNT`
- `AUTO_TRADE`: `DISABLED`
- `AUTO_SELL`: `DISABLED`
- `OFFICIAL_DECISION_IMPACT`: `NONE`
- `FORBIDDEN_MODIFIED`: `FALSE`

## 6. Codex 省 token 开发方式
以后先读这组短文件：
- `docs/v18/V18_CODEX_SAFETY_CONTRACT.md`
- `docs/v18/V18_CODEX_TASK_TEMPLATE.md`
- `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`
- `outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md`
- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`

## 7. 出错时怎么处理
- 如果冻结覆盖不是 `FULL_MATCH`，先读 `V18_CURRENT_CONTEXT_CONSISTENCY.md`。
- 如果账户状态是模板/空账户，先读 `V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`。
- 如果当前允许交易候选为 `0`，优先读 `V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`（若存在）。
- 如果中文首页缺失，先重跑 `V18.33A` wrapper。
- 如果命令中心失败，不要拿旧报告臆测交易可执行性。

## 8. 当前应读文件
- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`
- `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`
- `outputs/v18/read_center/V18_CURRENT_CONTEXT_CONSISTENCY.md`
- `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`
- `outputs/v18/read_center/V18_CURRENT_ACCOUNT_AWARE_MANUAL_TRADE_PLAN.md`
- `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`

## 9. 运行说明
- 中文首页是否存在: `TRUE`
- 一致性文件是否存在: `TRUE`
- 运行说明是否已刷新中文首页: `FALSE`
- 命令中心是否支持 `-RunChineseHomepage`: `TRUE`

## 10. 警告
- WARN: 当前允许交易候选为 0。
- WARN: 账户仍是模板/空账户状态。

## 11. 说明
- 这是给日常 operator 用的中文只读说明，不改交易逻辑。
- 中文只出现在 Markdown 报告层，不进入核心 CSV / ledger / 状态字段。
