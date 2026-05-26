# V18.6B Technical Timing Backtest Report

Generated: `20260516_004512`

## 1. Status

- V18_6B_STATUS: `OK_TECHNICAL_TIMING_BACKTEST_READY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- DETAIL_CSV: `D:\us-tech-quant\outputs\v18\technical_timing_backtest\V18_6B_CURRENT_TECHNICAL_TIMING_BACKTEST_DETAIL.csv`
- MATRIX_CSV: `D:\us-tech-quant\outputs\v18\technical_timing_backtest\V18_6B_CURRENT_TECHNICAL_TOPN_BACKTEST_MATRIX.csv`

## 2. Signal Forward Return Summary

### WATCH_POSITIVE

| signal         |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_win |   avg_loss |
|:---------------|---------------:|------:|----------:|-------------:|-----------:|----------:|-----------:|
| WATCH_POSITIVE |              1 | 16770 |  0.003232 |     0.00245  |   0.538939 |  0.026956 |  -0.024499 |
| WATCH_POSITIVE |              3 | 16751 |  0.00895  |     0.006772 |   0.56325  |  0.046698 |  -0.039733 |
| WATCH_POSITIVE |              5 | 16734 |  0.012188 |     0.009061 |   0.572368 |  0.058733 |  -0.050111 |
| WATCH_POSITIVE |             10 | 16721 |  0.023047 |     0.01579  |   0.582142 |  0.086127 |  -0.064832 |
| WATCH_POSITIVE |             20 | 16712 |  0.039959 |     0.02256  |   0.580122 |  0.13237  |  -0.087721 |

### PULLBACK_WATCH

| signal         |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_win |   avg_loss |
|:---------------|---------------:|------:|----------:|-------------:|-----------:|----------:|-----------:|
| PULLBACK_WATCH |              1 | 20561 |  0.001277 |     0.001274 |   0.520549 |  0.023485 |  -0.022834 |
| PULLBACK_WATCH |              3 | 20556 |  0.005039 |     0.003429 |   0.531134 |  0.044481 |  -0.039641 |
| PULLBACK_WATCH |              5 | 20551 |  0.008817 |     0.006536 |   0.548878 |  0.05787  |  -0.050866 |
| PULLBACK_WATCH |             10 | 20531 |  0.01875  |     0.012007 |   0.558375 |  0.086702 |  -0.067167 |
| PULLBACK_WATCH |             20 | 20509 |  0.03684  |     0.020375 |   0.570871 |  0.13281  |  -0.090829 |

### OVERHEAT_AVOID

| signal         |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_win |   avg_loss |
|:---------------|---------------:|------:|----------:|-------------:|-----------:|----------:|-----------:|
| OVERHEAT_AVOID |              1 |  8486 |  0.00102  |     0.000236 |   0.503771 |  0.021618 |  -0.019891 |
| OVERHEAT_AVOID |              3 |  8442 |  0.004763 |     0.002158 |   0.526534 |  0.039037 |  -0.033353 |
| OVERHEAT_AVOID |              5 |  8393 |  0.009536 |     0.004698 |   0.547361 |  0.052054 |  -0.041879 |
| OVERHEAT_AVOID |             10 |  8259 |  0.023077 |     0.013537 |   0.592808 |  0.07858  |  -0.057728 |
| OVERHEAT_AVOID |             20 |  8003 |  0.045017 |     0.02926  |   0.62789  |  0.121037 |  -0.083257 |

### BB_SQUEEZE

| signal     |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_win |   avg_loss |
|:-----------|---------------:|------:|----------:|-------------:|-----------:|----------:|-----------:|
| BB_SQUEEZE |              1 | 28864 |  0.001229 |     0.000693 |   0.514794 |  0.021028 |  -0.019777 |
| BB_SQUEEZE |              3 | 28842 |  0.003659 |     0.002338 |   0.526177 |  0.038906 |  -0.035482 |
| BB_SQUEEZE |              5 | 28820 |  0.006052 |     0.003523 |   0.531749 |  0.051663 |  -0.045744 |
| BB_SQUEEZE |             10 | 28755 |  0.013331 |     0.006555 |   0.539767 |  0.077771 |  -0.062245 |
| BB_SQUEEZE |             20 | 28713 |  0.034932 |     0.018992 |   0.577508 |  0.121334 |  -0.083171 |

## 3. TopN Daily Strategy Summary

| strategy             |   obs |   avg_net_ret_per_trade |   median_net_ret_per_trade |   win_rate |   ret_std |   sharpe_like |
|:---------------------|------:|------------------------:|---------------------------:|-----------:|----------:|--------------:|
| TECH_SCORE_TOP10_H20 |  1400 |                0.035136 |                   0.027003 |   0.604286 |  0.102224 |      0.343717 |
| TECH_SCORE_TOP5_H20  |  1400 |                0.035011 |                   0.021557 |   0.584286 |  0.118089 |      0.296483 |
| TECH_SCORE_TOP15_H20 |  1400 |                0.033553 |                   0.026356 |   0.627857 |  0.096699 |      0.346986 |
| TECH_SCORE_TOP5_H10  |  1410 |                0.016541 |                   0.009562 |   0.575177 |  0.080402 |      0.20573  |
| TECH_SCORE_TOP10_H10 |  1410 |                0.016215 |                   0.014949 |   0.596454 |  0.07087  |      0.228798 |
| TECH_SCORE_TOP15_H10 |  1410 |                0.015744 |                   0.014231 |   0.599291 |  0.067601 |      0.232894 |
| TECH_SCORE_TOP5_H5   |  1415 |                0.007729 |                   0.006329 |   0.559717 |  0.055861 |      0.138363 |
| TECH_SCORE_TOP10_H5  |  1415 |                0.007105 |                   0.007941 |   0.570318 |  0.049906 |      0.142366 |
| TECH_SCORE_TOP15_H5  |  1415 |                0.007034 |                   0.007577 |   0.574558 |  0.04776  |      0.147279 |
| TECH_SCORE_TOP5_H3   |  1417 |                0.004366 |                   0.004005 |   0.53705  |  0.043134 |      0.101225 |
| TECH_SCORE_TOP10_H3  |  1417 |                0.003834 |                   0.003834 |   0.538462 |  0.03896  |      0.098404 |
| TECH_SCORE_TOP15_H3  |  1417 |                0.003667 |                   0.004451 |   0.546224 |  0.037579 |      0.09759  |

## 4. Interpretation Rule

- If `WATCH_POSITIVE` and `PULLBACK_WATCH` have better 5/10/20 day forward return than neutral/overheat groups, V18.6A has useful timing value.
- If `OVERHEAT_AVOID` has weaker 3/5/10/20 day forward return, it can become a chase-risk filter.
- This module is still shadow only and does not change official daily decisions.
