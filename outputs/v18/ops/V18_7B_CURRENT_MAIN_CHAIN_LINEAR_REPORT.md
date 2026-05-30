# V18.7B Main Chain Linear Optimizer

Generated: `20260530_223454`

## 1. Status

- V18_7B_STATUS: `OK_MAIN_CHAIN_LINEAR_READY`
- TOTAL_SECONDS: `151.424`
- FINAL_ACTION: `BUY_CANDIDATES_REQUIRE_MANUAL_CONFIRMATION`
- BUY_PERMISSION: `UNKNOWN`
- OFFICIAL_DECISION_IMPACT: `NONE`
- PROFILE_CSV: `D:\us-tech-quant\outputs\v18\ops\V18_7B_CURRENT_MAIN_CHAIN_LINEAR_PROFILE.csv`

## 2. Step Timing

| step_order | step_name | elapsed_seconds | status |
|---:|---|---:|---|
| 1 | V18.4C_RUNTIME_AUDIT_ONCE | 1.229 | OK |
| 2 | V18.4C_FINAL_DAILY_SKIP_AUDIT | 82.676 | OK |
| 3 | V18.4D_FACTOR_PACK_AUDIT_REUSE_RUNTIME | 33.561 | OK |
| 4 | V18.4E_FACTOR_OUTPUT_FORWARD_AUDIT_REUSE_AUDITS | 23.726 | OK |
| 5 | V18.4F_FORWARD_TRACKER_FACTOR_COVERAGE | 8.581 | OK |
| 6 | V18.4G_SUMMARY_ONLY | 0.279 | OK |
| 7 | V18.4I_PROMOTION_MERGE_SKIP_UPSTREAM | 0.991 | OK |
| 8 | V18.4J_READ_CENTER_CLEANUP_ONLY | 0.305 | OK |
| 999 | TOTAL_V18_7B_MAIN_CHAIN_LINEAR | 151.424 | OK |

## 3. Slowest Steps

| rank | step_name | elapsed_seconds |
|---:|---|---:|
| 1 | V18.4C_FINAL_DAILY_SKIP_AUDIT | 82.676 |
| 2 | V18.4D_FACTOR_PACK_AUDIT_REUSE_RUNTIME | 33.561 |
| 3 | V18.4E_FACTOR_OUTPUT_FORWARD_AUDIT_REUSE_AUDITS | 23.726 |
| 4 | V18.4F_FORWARD_TRACKER_FACTOR_COVERAGE | 8.581 |
| 5 | V18.4C_RUNTIME_AUDIT_ONCE | 1.229 |
| 6 | V18.4I_PROMOTION_MERGE_SKIP_UPSTREAM | 0.991 |
| 7 | V18.4J_READ_CENTER_CLEANUP_ONLY | 0.305 |
| 8 | V18.4G_SUMMARY_ONLY | 0.279 |

## 4. Interpretation

- This wrapper linearizes the V18.4J main chain.
- It prevents V18.4J -> V18.4I -> V18.4G from recursively rerunning the full upstream stack.
- It does not change factor definitions or official decision logic.
- V18.4D and V18.4E still run normally in this simplified version.
