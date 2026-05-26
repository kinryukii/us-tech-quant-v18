# V18.4F Forward Tracker Factor Coverage

生成时间：2026-05-18 21:39:12

## 1. 结论

- WORLDQUANT_FACTOR_COUNT: `6`
- FACTOR_OUTPUT_AVAILABLE_COUNT: `6`
- FORWARD_COVERED_COUNT: `6`
- FORWARD_MISSING_COUNT: `0`
- BEST_FACTOR_OUTPUT_FILE: `D:\us-tech-quant\outputs\v18\factor_pack\V18_3D_R2_CURRENT_RAW105_FACTOR_PACK_RANKING.csv`
- EXPANDED_FORWARD_SNAPSHOT: `D:\us-tech-quant\state\v18\V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv`
- EXPANDED_FORWARD_SNAPSHOT_ROWS: `105`

## 2. 覆盖表

| factor | factor output files | forward files | status |
|---|---:|---:|---|
| F006 | 28 | 51 | FORWARD_COVERED |
| F007 | 29 | 119 | FORWARD_COVERED |
| F008 | 28 | 51 | FORWARD_COVERED |
| F009 | 28 | 52 | FORWARD_COVERED |
| F010 | 28 | 51 | FORWARD_COVERED |
| F011 | 28 | 51 | FORWARD_COVERED |

## 3. 解释

V18.4F 不改变 official decision。它只检查 F006-F011 是否被 forward / tracker / outcome / promotion 文件覆盖。

如果 FORWARD_MISSING_COUNT 大于 0，说明现有 V18.4A forward tracker 没有完整捕获所有 WorldQuant 风格因子。

本脚本生成旁路扩展快照 V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv，用来保存当前 F006-F011 的 ticker-level 因子值，后续可以接入 V18.4A tracker 或 promotion evaluator。

## 4. 输出文件

- COVERAGE_CSV: `D:\us-tech-quant\outputs\v18\factor_audit\V18_4F_FORWARD_FACTOR_COVERAGE_20260518_213906.csv`
- COVERAGE_MD: `D:\us-tech-quant\outputs\v18\factor_audit\V18_4F_FORWARD_FACTOR_COVERAGE_20260518_213906.md`
- EXPANDED_FORWARD_SNAPSHOT: `D:\us-tech-quant\state\v18\V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv`
