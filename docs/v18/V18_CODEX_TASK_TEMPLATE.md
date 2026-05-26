# V18 Codex Task Template

## Use model
Use model: gpt-5.5

## Repository
`D:\us-tech-quant`

## First read
1. `docs/v18/V18_CODEX_SAFETY_CONTRACT.md`
2. `docs/v18/V18_CODEX_TASK_TEMPLATE.md`
3. `outputs/v18/ops/V18_PROJECT_CONTEXT_COMPACT.md`
4. `outputs/v18/read_center/V18_CURRENT_DAILY_TRADE_READINESS.md`
5. `outputs/v18/read_center/V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md`

## Task
Describe the exact V18 task, version step, and intended output.

## Modify only
List the exact scripts, docs, or generated outputs that may be modified.

## Create outputs
List every expected output file.

## Do not
- Do not add broker/API/trading/order execution code.
- Do not enable `AUTO_TRADE` or `AUTO_SELL`.
- Do not change `OFFICIAL_DECISION_IMPACT` from `NONE` unless explicitly scoped.
- Do not modify protected state, ledgers, or core ranking/factor/recommendation/buyability/sizing/cost/account-aware logic unless explicitly scoped.
- Do not run heavy daily pipeline steps unless explicitly scoped.
- Do not infer from archived stale files unless asked.

## Validation
List exact compile, parse, dry-run, live-run, and audit checks to execute.

## Success criteria
List exact status codes, output files, row counts, safety fields, and warning behavior expected.

## Run commands
```powershell
python -m py_compile <script>
powershell -NoProfile -ExecutionPolicy Bypass -File <wrapper> -DryRun
powershell -NoProfile -ExecutionPolicy Bypass -File <wrapper>
```

## Final response requirements
Report files changed, status, key fields, warnings or unknowns, validation results, and confirmation that protected trading/state logic was not modified.
