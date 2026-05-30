# V17.7B-R1 Universe Semantic Audit

Generated: 2026-05-30 22:36:05

## 1. Main Conclusion

UNIVERSE_SEMANTIC_STATUS: OK_DYNAMIC_COUNTS

本层不改变交易策略，只修正 universe 数量口径，防止把 66 误读成原始池数量。

当前正确口径：

RAW_UNIVERSE_COUNT: 105
CLASSIFIED_UNIVERSE_COUNT: 105
MAIN_COMPUTE_UNIVERSE_COUNT: 105
SECOND_STAGE_CANDIDATE_COUNT: 20
RAW_PRICE_OK_COUNT: 105
RAW_PRICE_FAIL_COUNT: 0

## 2. Count Summary

| item | count | meaning |
|---|---:|---|
| RAW_UNIVERSE_COUNT | 105 | 原始股票池总数 |
| CLASSIFIED_UNIVERSE_COUNT | 105 | 已进入分类/审计文件的数量 |
| MAIN_COMPUTE_UNIVERSE_COUNT | 105 | 进入主计算/执行前置层的数量；这就是之前看到的 66 |
| SECOND_STAGE_CANDIDATE_COUNT | 20 | 重点候选池数量 |
| CLASSIFIED_ONLY_NOT_MAIN_COMPUTE_COUNT | 0 | 已分类但未进入主计算层 |
| MAIN_COMPUTE_NOT_SECOND_STAGE_COUNT | 85 | 进入主计算但未进入 second stage |
| SECOND_STAGE_COUNT | 20 | second stage 候选 |
| RAW_ONLY_NOT_CLASSIFIED_COUNT | 0 | 原始池中未分类数量 |
| RAW_PRICE_OK_COUNT | 105 | 原始池中价格可用数量 |
| RAW_PRICE_FAIL_COUNT | 0 | 原始池中价格失败数量 |

## 3. Semantic Layer Counts

| semantic_layer | count |
|---|---:|
| MAIN_COMPUTE_UNIVERSE | 85 |
| SECOND_STAGE_CANDIDATE | 20 |

## 4. Correct Interpretation

以后不要说：只有 66 个股票参与系统。

更准确的说法是：原始池 105 个全部参与价格审计和分类；其中 66 个进入主计算/执行前置层；10 个进入 second stage 重点候选层。

## 5. Output Files

- Semantic audit CSV: D:\us-tech-quant\outputs\v17\raw_universe_audit\v17_7B_universe_semantic_audit.csv
- Summary: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7B_UNIVERSE_SEMANTIC_AUDIT.md
- Read first: D:\us-tech-quant\outputs\v17\raw_universe_audit\V17_7B_READ_FIRST.txt

