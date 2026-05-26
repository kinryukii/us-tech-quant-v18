# V18.6B-R1 Technical Timing Diagnostic Patch

## 1. Status

- V18_6B_R1_STATUS: `OK_TECHNICAL_TIMING_DIAGNOSTIC_READY`
- OFFICIAL_DECISION_IMPACT: `NONE`
- MAIN_PURPOSE: `OVERHEAT_DECOMPOSITION_AND_BENCHMARK_EXCESS`

## 2. Signal Forward Return + Benchmark Excess

### WATCH_POSITIVE

| signal         |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_excess_vs_QQQ |   excess_win_rate_vs_QQQ |   avg_excess_vs_SPY |   excess_win_rate_vs_SPY |   avg_excess_vs_SMH |   excess_win_rate_vs_SMH |
|:---------------|---------------:|------:|----------:|-------------:|-----------:|--------------------:|-------------------------:|--------------------:|-------------------------:|--------------------:|-------------------------:|
| WATCH_POSITIVE |              1 | 16770 |  0.003232 |     0.00245  |   0.538939 |            0.001513 |                 0.511747 |            0.001717 |                 0.516398 |            0.000288 |                 0.485271 |
| WATCH_POSITIVE |              3 | 16751 |  0.00895  |     0.006772 |   0.56325  |            0.004666 |                 0.535192 |            0.005219 |                 0.53561  |            0.000758 |                 0.483673 |
| WATCH_POSITIVE |              5 | 16734 |  0.012188 |     0.009061 |   0.572368 |            0.00713  |                 0.538485 |            0.007573 |                 0.536931 |            0.000793 |                 0.478666 |
| WATCH_POSITIVE |             10 | 16721 |  0.023047 |     0.01579  |   0.582142 |            0.013411 |                 0.544345 |            0.014704 |                 0.550505 |            0.001085 |                 0.471024 |
| WATCH_POSITIVE |             20 | 16712 |  0.039959 |     0.02256  |   0.580122 |            0.023456 |                 0.534945 |            0.026197 |                 0.538416 |            0.003832 |                 0.474809 |

### PULLBACK_WATCH

| signal         |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_excess_vs_QQQ |   excess_win_rate_vs_QQQ |   avg_excess_vs_SPY |   excess_win_rate_vs_SPY |   avg_excess_vs_SMH |   excess_win_rate_vs_SMH |
|:---------------|---------------:|------:|----------:|-------------:|-----------:|--------------------:|-------------------------:|--------------------:|-------------------------:|--------------------:|-------------------------:|
| PULLBACK_WATCH |              1 | 20561 |  0.001277 |     0.001274 |   0.520549 |            0.000601 |                 0.505423 |            0.000916 |                 0.513837 |           -0.000522 |                 0.481737 |
| PULLBACK_WATCH |              3 | 20556 |  0.005039 |     0.003429 |   0.531134 |            0.002346 |                 0.510605 |            0.003152 |                 0.514838 |           -0.000242 |                 0.484481 |
| PULLBACK_WATCH |              5 | 20551 |  0.008817 |     0.006536 |   0.548878 |            0.003964 |                 0.511265 |            0.005515 |                 0.51978  |           -0.000117 |                 0.474624 |
| PULLBACK_WATCH |             10 | 20531 |  0.01875  |     0.012007 |   0.558375 |            0.009312 |                 0.516341 |            0.011557 |                 0.52881  |            0.000909 |                 0.473723 |
| PULLBACK_WATCH |             20 | 20509 |  0.03684  |     0.020375 |   0.570871 |            0.017504 |                 0.510313 |            0.022596 |                 0.532352 |            0.00061  |                 0.468282 |

### BB_SQUEEZE

| signal     |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_excess_vs_QQQ |   excess_win_rate_vs_QQQ |   avg_excess_vs_SPY |   excess_win_rate_vs_SPY |   avg_excess_vs_SMH |   excess_win_rate_vs_SMH |
|:-----------|---------------:|------:|----------:|-------------:|-----------:|--------------------:|-------------------------:|--------------------:|-------------------------:|--------------------:|-------------------------:|
| BB_SQUEEZE |              1 | 28864 |  0.001229 |     0.000693 |   0.514794 |            0.000747 |                 0.491408 |            0.000891 |                 0.500901 |            0.00015  |                 0.480114 |
| BB_SQUEEZE |              3 | 28842 |  0.003659 |     0.002338 |   0.526177 |            0.002057 |                 0.496255 |            0.002521 |                 0.507004 |            0.00042  |                 0.476597 |
| BB_SQUEEZE |              5 | 28820 |  0.006052 |     0.003523 |   0.531749 |            0.003278 |                 0.492228 |            0.004028 |                 0.502359 |            0.001017 |                 0.476856 |
| BB_SQUEEZE |             10 | 28755 |  0.013331 |     0.006555 |   0.539767 |            0.007165 |                 0.490106 |            0.008599 |                 0.500991 |            0.002853 |                 0.474109 |
| BB_SQUEEZE |             20 | 28713 |  0.034932 |     0.018992 |   0.577508 |            0.017881 |                 0.508272 |            0.021984 |                 0.520357 |            0.006994 |                 0.472121 |

### OVERHEAT_BREAKOUT_CONTINUATION

| signal                         |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_excess_vs_QQQ |   excess_win_rate_vs_QQQ |   avg_excess_vs_SPY |   excess_win_rate_vs_SPY |   avg_excess_vs_SMH |   excess_win_rate_vs_SMH |
|:-------------------------------|---------------:|------:|----------:|-------------:|-----------:|--------------------:|-------------------------:|--------------------:|-------------------------:|--------------------:|-------------------------:|
| OVERHEAT_BREAKOUT_CONTINUATION |              1 |  5852 |  0.002477 |     0.000429 |   0.507519 |            0.001806 |                 0.478127 |            0.001908 |                 0.484279 |            0.001774 |                 0.490772 |
| OVERHEAT_BREAKOUT_CONTINUATION |              3 |  5838 |  0.005556 |     0.002868 |   0.529633 |            0.003749 |                 0.500514 |            0.003819 |                 0.509935 |            0.003106 |                 0.485612 |
| OVERHEAT_BREAKOUT_CONTINUATION |              5 |  5816 |  0.010696 |     0.004993 |   0.544188 |            0.006808 |                 0.502579 |            0.007326 |                 0.508253 |            0.003778 |                 0.477476 |
| OVERHEAT_BREAKOUT_CONTINUATION |             10 |  5780 |  0.022076 |     0.012476 |   0.576125 |            0.012187 |                 0.506747 |            0.014278 |                 0.518339 |            0.005108 |                 0.466955 |
| OVERHEAT_BREAKOUT_CONTINUATION |             20 |  5738 |  0.043393 |     0.022388 |   0.595678 |            0.026482 |                 0.517951 |            0.030057 |                 0.537818 |            0.009233 |                 0.466713 |

### OVERHEAT_EXHAUSTION_RISK

| signal                   |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_excess_vs_QQQ |   excess_win_rate_vs_QQQ |   avg_excess_vs_SPY |   excess_win_rate_vs_SPY |   avg_excess_vs_SMH |   excess_win_rate_vs_SMH |
|:-------------------------|---------------:|------:|----------:|-------------:|-----------:|--------------------:|-------------------------:|--------------------:|-------------------------:|--------------------:|-------------------------:|
| OVERHEAT_EXHAUSTION_RISK |              1 |   409 |  0.000379 |     0.00052  |   0.518337 |           -0.000368 |                 0.459658 |            0.000112 |                 0.503667 |           -0.001453 |                 0.479218 |
| OVERHEAT_EXHAUSTION_RISK |              3 |   407 |  0.002236 |     0.000374 |   0.511057 |            0.001708 |                 0.486486 |            0.001602 |                 0.479115 |            0.000712 |                 0.501229 |
| OVERHEAT_EXHAUSTION_RISK |              5 |   403 |  0.004782 |     0.000526 |   0.503722 |            0.003701 |                 0.486352 |            0.003803 |                 0.508685 |            0.002056 |                 0.486352 |
| OVERHEAT_EXHAUSTION_RISK |             10 |   399 |  0.009869 |     0.00259  |   0.541353 |            0.005021 |                 0.458647 |            0.007363 |                 0.491228 |            0.002253 |                 0.458647 |
| OVERHEAT_EXHAUSTION_RISK |             20 |   383 |  0.031801 |     0.021725 |   0.613577 |            0.020126 |                 0.522193 |            0.022822 |                 0.548303 |            0.008055 |                 0.498695 |

### OVERHEAT_UNCLASSIFIED

| signal                |   horizon_days |   obs |   avg_ret |   median_ret |   win_rate |   avg_excess_vs_QQQ |   excess_win_rate_vs_QQQ |   avg_excess_vs_SPY |   excess_win_rate_vs_SPY |   avg_excess_vs_SMH |   excess_win_rate_vs_SMH |
|:----------------------|---------------:|------:|----------:|-------------:|-----------:|--------------------:|-------------------------:|--------------------:|-------------------------:|--------------------:|-------------------------:|
| OVERHEAT_UNCLASSIFIED |              1 |  6346 |  0.00088  |     0.000135 |   0.501576 |            0.000386 |                 0.481563 |            0.000442 |                 0.483769 |            0.000102 |                 0.483139 |
| OVERHEAT_UNCLASSIFIED |              3 |  6306 |  0.004886 |     0.002157 |   0.527751 |            0.002694 |                 0.493181 |            0.003201 |                 0.497938 |            0.000857 |                 0.49001  |
| OVERHEAT_UNCLASSIFIED |              5 |  6266 |  0.009681 |     0.005003 |   0.552186 |            0.005449 |                 0.503511 |            0.006669 |                 0.516438 |            0.001803 |                 0.487073 |
| OVERHEAT_UNCLASSIFIED |             10 |  6145 |  0.023916 |     0.013931 |   0.597071 |            0.013487 |                 0.52498  |            0.0167   |                 0.543206 |            0.004915 |                 0.491782 |
| OVERHEAT_UNCLASSIFIED |             20 |  5929 |  0.047083 |     0.032159 |   0.63434  |            0.030395 |                 0.555574 |            0.033902 |                 0.570417 |            0.011922 |                 0.491483 |


## 3. TopN Strategy Benchmark Excess

| strategy             |   obs |   avg_net_ret |   median_net_ret |   win_rate |   ret_std |   avg_excess_vs_QQQ |   excess_win_rate_vs_QQQ |   avg_excess_vs_SPY |   excess_win_rate_vs_SPY |   avg_excess_vs_SMH |   excess_win_rate_vs_SMH |
|:---------------------|------:|--------------:|-----------------:|-----------:|----------:|--------------------:|-------------------------:|--------------------:|-------------------------:|--------------------:|-------------------------:|
| TECH_SCORE_TOP5_H3   |  1417 |      0.004366 |         0.004005 |   0.53705  |  0.043134 |            0.002002 |                 0.491179 |            0.00246  |                 0.503881 |           -0.000361 |                 0.47283  |
| TECH_SCORE_TOP5_H5   |  1415 |      0.007729 |         0.006329 |   0.559717 |  0.055861 |            0.003825 |                 0.504594 |            0.004571 |                 0.527208 |           -0.000101 |                 0.483392 |
| TECH_SCORE_TOP5_H10  |  1410 |      0.016541 |         0.009562 |   0.575177 |  0.080402 |            0.008976 |                 0.516312 |            0.010381 |                 0.531915 |            0.001186 |                 0.477305 |
| TECH_SCORE_TOP5_H20  |  1400 |      0.035011 |         0.021557 |   0.584286 |  0.118089 |            0.020587 |                 0.537857 |            0.023188 |                 0.546429 |            0.005474 |                 0.490714 |
| TECH_SCORE_TOP10_H3  |  1417 |      0.003834 |         0.003834 |   0.538462 |  0.03896  |            0.001469 |                 0.494001 |            0.001927 |                 0.508821 |           -0.000893 |                 0.48765  |
| TECH_SCORE_TOP10_H5  |  1415 |      0.007105 |         0.007941 |   0.570318 |  0.049906 |            0.003201 |                 0.515194 |            0.003947 |                 0.544876 |           -0.000725 |                 0.485512 |
| TECH_SCORE_TOP10_H10 |  1410 |      0.016215 |         0.014949 |   0.596454 |  0.07087  |            0.00865  |                 0.541135 |            0.010055 |                 0.563121 |            0.00086  |                 0.492199 |
| TECH_SCORE_TOP10_H20 |  1400 |      0.035136 |         0.027003 |   0.604286 |  0.102224 |            0.020712 |                 0.572857 |            0.023313 |                 0.595714 |            0.005599 |                 0.509286 |
| TECH_SCORE_TOP15_H3  |  1417 |      0.003667 |         0.004451 |   0.546224 |  0.037579 |            0.001303 |                 0.501059 |            0.001761 |                 0.51729  |           -0.00106  |                 0.49259  |
| TECH_SCORE_TOP15_H5  |  1415 |      0.007034 |         0.007577 |   0.574558 |  0.04776  |            0.00313  |                 0.522261 |            0.003876 |                 0.54417  |           -0.000796 |                 0.485512 |
| TECH_SCORE_TOP15_H10 |  1410 |      0.015744 |         0.014231 |   0.599291 |  0.067601 |            0.008179 |                 0.563121 |            0.009584 |                 0.587943 |            0.000389 |                 0.498582 |
| TECH_SCORE_TOP15_H20 |  1400 |      0.033553 |         0.026356 |   0.627857 |  0.096699 |            0.019129 |                 0.583571 |            0.02173  |                 0.598571 |            0.004015 |                 0.515    |

## 4. Interpretation

- `OVERHEAT_BREAKOUT_CONTINUATION` means overheat with volume/price confirmation. It may be momentum continuation rather than a sell/avoid signal.
- `OVERHEAT_EXHAUSTION_RISK` means extreme RSI/KDJ heat with weak volume confirmation. This is the real chase-risk candidate.
- `WATCH_POSITIVE` and `PULLBACK_WATCH` remain timing-watch signals, not official buy signals.
- This patch is diagnostic only and does not change official daily decisions.

## 5. Outputs

- DETAIL: `D:\us-tech-quant\outputs\v18\technical_timing_backtest\V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_DETAIL.csv`
- SIGNAL_SUMMARY: `D:\us-tech-quant\outputs\v18\technical_timing_backtest\V18_6B_R1_CURRENT_SIGNAL_EXCESS_SUMMARY.csv`
- STRATEGY_SUMMARY: `D:\us-tech-quant\outputs\v18\technical_timing_backtest\V18_6B_R1_CURRENT_TOPN_EXCESS_STRATEGY_SUMMARY.csv`
