# V18.7B Main Chain Linear Optimizer

Generated: `20260527_222158`

## 1. Status

- V18_7B_STATUS: `OK_MAIN_CHAIN_LINEAR_READY`
- TOTAL_SECONDS: `136.554`
- FINAL_ACTION: `BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION`
- BUY_PERMISSION: `UNKNOWN`
- OFFICIAL_DECISION_IMPACT: `NONE`
- PROFILE_CSV: `D:\us-tech-quant\outputs\v18\ops\V18_7B_CURRENT_MAIN_CHAIN_LINEAR_PROFILE.csv`

## 2. Step Timing

| step_order | step_name | elapsed_seconds | status |
|---:|---|---:|---|
| 1 | V18.4C_RUNTIME_AUDIT_ONCE | 1.1 | OK |
| 2 | V18.4C_FINAL_DAILY_SKIP_AUDIT | 69.15 | OK |
| 3 | V18.4D_FACTOR_PACK_AUDIT_REUSE_RUNTIME | 28.001 | OK |
| 4 | V18.4E_FACTOR_OUTPUT_FORWARD_AUDIT_REUSE_AUDITS | 26.678 | OK |
| 5 | V18.4F_FORWARD_TRACKER_FACTOR_COVERAGE | 9.647 | OK |
| 6 | V18.4G_SUMMARY_ONLY | 0.33 | OK |
| 7 | V18.4I_PROMOTION_MERGE_SKIP_UPSTREAM | 1.221 | OK |
| 8 | V18.4J_READ_CENTER_CLEANUP_ONLY | 0.331 | OK |
| 999 | TOTAL_V18_7B_MAIN_CHAIN_LINEAR | 136.554 | OK |

## 3. Slowest Steps

| rank | step_name | elapsed_seconds |
|---:|---|---:|
| 1 | V18.4C_FINAL_DAILY_SKIP_AUDIT | 69.15 |
| 2 | V18.4D_FACTOR_PACK_AUDIT_REUSE_RUNTIME | 28.001 |
| 3 | V18.4E_FACTOR_OUTPUT_FORWARD_AUDIT_REUSE_AUDITS | 26.678 |
| 4 | V18.4F_FORWARD_TRACKER_FACTOR_COVERAGE | 9.647 |
| 5 | V18.4I_PROMOTION_MERGE_SKIP_UPSTREAM | 1.221 |
| 6 | V18.4C_RUNTIME_AUDIT_ONCE | 1.1 |
| 7 | V18.4J_READ_CENTER_CLEANUP_ONLY | 0.331 |
| 8 | V18.4G_SUMMARY_ONLY | 0.33 |

## 4. Interpretation

- This wrapper linearizes the V18.4J main chain.
- It prevents V18.4J -> V18.4I -> V18.4G from recursively rerunning the full upstream stack.
- It does not change factor definitions or official decision logic.
- V18.4D and V18.4E still run normally in this simplified version.
