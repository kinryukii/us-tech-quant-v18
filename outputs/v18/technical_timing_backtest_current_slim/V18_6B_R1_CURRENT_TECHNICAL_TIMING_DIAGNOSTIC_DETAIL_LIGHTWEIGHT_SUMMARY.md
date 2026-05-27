# Lightweight Technical Timing Detail Summary

original_file: outputs/v18/technical_timing_backtest/V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_DETAIL.csv
original_size_mb: 166.158
row_count: 142295
column_count: 90
min_date: 2020-09-21
max_date: 2026-05-15
ticker_count: 105
archive_zip_path: archive/generated_outputs_compressed/technical_timing_backtest_current_details/V18_6B_R1_CURRENT_TECHNICAL_TIMING_DIAGNOSTIC_DETAIL.csv_20260519_151425.zip
archive_verified: True

## Numeric Column Aggregate Summary

| column | non_null_numeric_count | min | max | avg |
| --- | ---: | ---: | ---: | ---: |
| open | 142295 | 0.411 | 2039.040039 | 136.186881 |
| high | 142295 | 0.525 | 2073.98999 | 138.380049 |
| low | 142295 | 0.382 | 2015 | 133.946908 |
| close | 142295 | 0.412 | 2042.359985 | 136.243917 |
| volume | 142295 | 0 | 1543911000 | 16867217.643009 |
| ret_fwd_1 | 142190 | -0.467975 | 0.879412 | 0.001745 |
| ret_fwd_3 | 141980 | -0.50155 | 1.428977 | 0.005262 |
| ret_fwd_5 | 141770 | -0.521601 | 1.837456 | 0.008722 |
| ret_fwd_10 | 141245 | -0.59854 | 2.304527 | 0.017297 |
| ret_fwd_20 | 140195 | -0.748895 | 2.567961 | 0.033941 |
| bb_mid | 140300 | 0.63615 | 1869.679004 | 135.324581 |
| bb_std | 140300 | 0.008256 | 234.485447 | 6.02242 |
| bb_upper | 140300 | 0.864152 | 2135.146883 | 147.369422 |
| bb_lower | 140300 | 0.216154 | 1696.386627 | 123.27974 |
| bb_percent_b | 140300 | -0.523523 | 1.538086 | 0.552872 |
| bb_bandwidth | 140300 | 0.003274 | 1.880413 | 0.197716 |
| bb_bandwidth_q20 | 134105 | 0.004513 | 0.500703 | 0.12395 |
| rsi_14 | 140825 | 6.585806 | 98.438512 | 53.284333 |
| kdj_k | 140615 | 0.793377 | 98.705798 | 54.388959 |
| kdj_d | 139775 | 3.586837 | 97.058484 | 54.321987 |
| kdj_j | 139775 | -31.498841 | 141.522569 | 54.370353 |
| kdj_prev_k | 140510 | 0.793377 | 98.705798 | 54.383868 |
| kdj_prev_d | 139670 | 3.586837 | 97.058484 | 54.313669 |
| vol_ma5 | 141875 | 0 | 981141600 | 16862164.820236 |
| vol_ma20 | 140300 | 220 | 666486750 | 16854017.838939 |
| volume_ratio_5_20 | 140300 | 0 | 3.97808 | 1.007636 |
| overheat_penalty | 142295 | 0 | 40 | 4.318212 |
| pullback_timing_bonus | 142295 | 0 | 22 | 5.046207 |
| breakout_confirmation_bonus | 142295 | 0 | 9 | 1.026867 |
| technical_timing_score | 142295 | 10 | 76 | 51.754861 |

## Top 100 Rows By technical_timing_score

| date | ticker | technical_timing_score | close | volume | signal_watch_positive | signal_pullback_watch | signal_overheat_avoid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-10-28 | TER | 76 | 111.33000183105467 | 2672100 | True | False | False |
| 2024-10-25 | TER | 76 | 111.75 | 3573700 | True | False | False |
| 2024-10-24 | TER | 76 | 110.72000122070312 | 7148000 | True | False | False |
| 2024-10-29 | TER | 76 | 113.23999786376952 | 2284500 | True | False | False |
| 2022-01-25 | AVGO | 76 | 53.41400146484375 | 38158000 | True | False | False |
| 2024-10-31 | TER | 76 | 106.20999908447266 | 3392300 | True | False | False |
| 2024-10-30 | TER | 76 | 109.4800033569336 | 2861400 | True | False | False |
| 2022-11-04 | META | 76 | 90.79000091552734 | 55638100 | True | False | False |
| 2022-11-03 | META | 76 | 88.91000366210938 | 60664000 | True | False | False |
| 2024-08-06 | ETN | 76 | 277.6499938964844 | 3305000 | True | False | False |
| 2024-12-20 | ETN | 76 | 338.1199951171875 | 4862500 | True | False | False |
| 2024-10-23 | TER | 76 | 124.43000030517578 | 2821700 | True | False | False |
| 2024-12-24 | ETN | 76 | 341.5400085449219 | 507500 | True | False | False |
| 2024-12-23 | ETN | 76 | 337.7099914550781 | 1704600 | True | False | False |
| 2022-01-24 | AVGO | 76 | 54.15800094604492 | 54256000 | True | False | False |
| 2026-02-03 | ORCL | 76 | 154.6699981689453 | 43260100 | True | False | False |
| 2026-02-04 | ORCL | 76 | 146.6699981689453 | 42323400 | True | False | False |
| 2026-02-05 | ORCL | 76 | 136.47999572753906 | 42789000 | True | False | False |
| 2026-02-02 | ORCL | 76 | 160.05999755859375 | 47421000 | True | False | False |
| 2025-03-13 | TER | 76 | 85.33000183105469 | 4470500 | True | False | False |
| 2025-03-07 | TER | 76 | 108.54000091552734 | 2402800 | True | False | False |
| 2026-01-30 | ORCL | 76 | 164.5800018310547 | 27362400 | True | False | False |
| 2025-03-05 | ETN | 76 | 287.7300109863281 | 3752900 | True | False | False |
| 2025-02-26 | ETN | 76 | 297.3500061035156 | 4302800 | True | False | False |
| 2022-01-21 | AVGO | 76 | 53.323001861572266 | 38010000 | True | False | False |
| 2025-04-08 | ETN | 76 | 251.5 | 5127300 | True | False | False |
| 2026-02-06 | ORCL | 76 | 142.82000732421875 | 29962400 | True | False | False |
| 2026-02-09 | ORCL | 76 | 156.58999633789062 | 49936500 | True | False | False |
| 2025-01-31 | TER | 76 | 115.79000091552734 | 3706900 | True | False | False |
| 2023-10-31 | TER | 76 | 83.2699966430664 | 1540200 | True | False | False |
| 2023-10-30 | TER | 76 | 83.45999908447266 | 1656300 | True | False | False |
| 2023-10-27 | TER | 76 | 83.83999633789062 | 2015500 | True | False | False |
| 2023-11-01 | TER | 76 | 82.76000213623047 | 2091200 | True | False | False |
| 2022-05-16 | PANW | 76 | 78.02999877929688 | 11160600 | True | False | False |
| 2022-05-19 | PANW | 76 | 72.72833251953125 | 24239400 | True | False | False |
| 2022-05-20 | PANW | 76 | 79.77999877929688 | 35400000 | True | False | False |
| 2022-06-22 | META | 76 | 155.85000610351562 | 47267800 | True | False | False |
| 2023-01-10 | PANW | 76 | 67.09500122070312 | 9716400 | True | False | False |
| 2023-09-19 | TER | 76 | 97.79000091552734 | 2014300 | True | False | False |
| 2022-06-23 | META | 76 | 158.75 | 40499200 | True | False | False |
| 2023-10-26 | TER | 76 | 85.12000274658203 | 2954300 | True | False | False |
| 2023-10-25 | TER | 76 | 87.91000366210938 | 2722900 | True | False | False |
| 2022-06-24 | META | 76 | 170.16000366210938 | 68736000 | True | False | False |
| 2022-05-12 | PANW | 76 | 79.75166320800781 | 12362400 | True | False | False |
| 2024-08-01 | TER | 76 | 121.73999786376952 | 3950700 | True | False | False |
| 2021-08-17 | PANW | 76 | 60.96166610717773 | 4420800 | True | False | False |
| 2022-09-02 | AVGO | 76 | 50.02199935913086 | 40426000 | True | False | False |
| 2023-05-31 | ACM | 76 | 78.05000305175781 | 6592300 | True | False | False |
| 2024-08-06 | TER | 76 | 118.31999969482422 | 1623700 | True | False | False |
| 2024-08-05 | TER | 76 | 116.38999938964844 | 2725900 | True | False | False |
| 2024-08-02 | TER | 76 | 117.2699966430664 | 3522600 | True | False | False |
| 2022-05-09 | PANW | 76 | 76.58499908447266 | 18901200 | True | False | False |
| 2022-05-10 | PANW | 76 | 80.67333221435547 | 12334800 | True | False | False |
| 2022-05-11 | PANW | 76 | 77.77833557128906 | 12789000 | True | False | False |
| 2024-04-22 | TER | 76 | 97.76000213623048 | 2302900 | True | False | False |
| 2022-09-06 | AVGO | 76 | 49.81999969482422 | 24738000 | True | False | False |
| 2022-01-24 | PANW | 76 | 84.03500366210938 | 17531400 | True | False | False |
| 2024-04-23 | TER | 76 | 99.8499984741211 | 1927800 | True | False | False |
| 2023-05-24 | ETR | 76 | 49.48500061035156 | 2098400 | True | False | False |
| 2023-05-23 | ETR | 76 | 50.14500045776367 | 4431000 | True | False | False |
| 2021-10-06 | TQQQ | 76 | 31.51499938964844 | 234990800 | True | False | False |
| 2025-03-21 | META | 76 | 596.25 | 25015900 | True | False | False |
| 2023-05-30 | ETR | 76 | 48.3650016784668 | 2817200 | True | False | False |
| 2023-05-26 | ETR | 76 | 48.400001525878906 | 2114000 | True | False | False |
| 2023-05-25 | ETR | 76 | 48.61000061035156 | 3430600 | True | False | False |
| 2022-06-23 | ETR | 76 | 52.95500183105469 | 1939000 | True | False | False |
| 2022-06-22 | ETR | 76 | 52.31499862670898 | 1992200 | True | False | False |
| 2022-06-21 | ETR | 76 | 52.34999847412109 | 2817600 | True | False | False |
| 2023-12-18 | ORCL | 76 | 105.0 | 13473100 | True | False | False |
| 2023-01-09 | ETR | 76 | 54.22999954223633 | 3722200 | True | False | False |
| 2021-05-14 | TQQQ | 76 | 23.99250030517578 | 144263200 | True | False | False |
| 2021-03-09 | TQQQ | 76 | 21.405000686645508 | 173429200 | True | False | False |
| 2023-05-31 | ETR | 76 | 49.09999847412109 | 3863800 | True | False | False |
| 2022-01-28 | TQQQ | 76 | 28.184999465942383 | 334032400 | True | False | False |
| 2022-01-27 | TQQQ | 76 | 25.780000686645508 | 323528200 | True | False | False |
| 2022-01-26 | TQQQ | 76 | 26.575000762939453 | 415676200 | True | False | False |
| 2022-09-07 | ORCL | 76 | 74.48999786376953 | 5792600 | True | False | False |
| 2024-09-10 | ASML | 76 | 751.3800048828125 | 1524000 | True | False | False |
| 2024-09-11 | ASML | 76 | 800.1400146484375 | 2559100 | True | False | False |
| 2024-08-08 | JBL | 76 | 101.88999938964844 | 1069400 | True | False | False |
| 2025-04-04 | ASML | 76 | 605.5499877929688 | 4017000 | True | False | False |
| 2025-04-07 | ASML | 76 | 615.8400268554688 | 4179100 | True | False | False |
| 2025-04-08 | ASML | 76 | 595.3699951171875 | 2585200 | True | False | False |
| 2023-07-03 | ETR | 76 | 49.06999969482422 | 3206400 | True | False | False |
| 2022-01-25 | TQQQ | 76 | 26.625 | 347498000 | True | False | False |
| 2022-01-24 | TQQQ | 76 | 28.7450008392334 | 510169200 | True | False | False |
| 2023-10-04 | ETR | 76 | 45.5099983215332 | 3444600 | True | False | False |
| 2025-11-18 | ORCL | 76 | 220.4900054931641 | 21098300 | True | False | False |
| 2025-11-20 | ORCL | 76 | 210.69000244140625 | 27459600 | True | False | False |
| 2025-11-21 | ORCL | 76 | 198.75999450683597 | 44834100 | True | False | False |
| 2025-11-17 | ORCL | 76 | 219.8600006103516 | 16143800 | True | False | False |
| 2025-03-12 | ORCL | 76 | 150.88999938964844 | 15373900 | True | False | False |
| 2025-04-09 | ORCL | 76 | 139.69000244140625 | 17762000 | True | False | False |
| 2025-11-14 | ORCL | 76 | 222.8500061035156 | 36053800 | True | False | False |
| 2025-03-18 | TER | 76 | 88.87000274658203 | 3674800 | True | False | False |
| 2025-03-17 | TER | 76 | 90.16999816894533 | 3563000 | True | False | False |
| 2025-03-14 | TER | 76 | 86.73999786376953 | 5428900 | True | False | False |
| 2023-09-18 | ACM | 76 | 84.72000122070312 | 594700 | True | False | False |
| 2025-11-24 | ORCL | 76 | 200.27999877929688 | 31144700 | True | False | False |
| 2025-11-25 | ORCL | 76 | 197.02999877929688 | 29595000 | True | False | False |

## Latest Date Slice (2026-05-15, first 100 rows)

| date | ticker | technical_timing_score | close | volume | signal_watch_positive | signal_pullback_watch | signal_overheat_avoid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-15 | AAPL | 15 | 301.3951110839844 | 20811816 | False | False | True |
| 2026-05-15 | ACLS | 50 | 155.0449981689453 | 181148 | False | False | False |
| 2026-05-15 | ACM | 68 | 72.33999633789062 | 359908 | True | False | False |
| 2026-05-15 | ACMR | 54 | 62.65999984741211 | 694024 | False | False | False |
| 2026-05-15 | AEHR | 50 | 101.18499755859376 | 1130781 | False | False | False |
| 2026-05-15 | ALAB | 40 | 229.5050048828125 | 2920881 | False | False | False |
| 2026-05-15 | AMAT | 54 | 438.6600036621094 | 6274030 | False | False | False |
| 2026-05-15 | AMD | 30 | 433.6300048828125 | 13642689 | False | False | False |
| 2026-05-15 | AMKR | 58 | 70.86000061035156 | 1283258 | False | False | False |
| 2026-05-15 | AMZN | 50 | 262.1000061035156 | 18152776 | False | False | False |
| 2026-05-15 | ANET | 64 | 144.90499877929688 | 3659118 | False | True | False |
| 2026-05-15 | APH | 76 | 125.5500030517578 | 3704251 | True | False | False |
| 2026-05-15 | ARM | 50 | 212.0200042724609 | 5016075 | False | False | False |
| 2026-05-15 | ASML | 40 | 1517.43994140625 | 960809 | False | False | False |
| 2026-05-15 | AVGO | 40 | 426.2049865722656 | 7089566 | False | False | False |
| 2026-05-15 | BE | 40 | 281.7550048828125 | 4606692 | False | False | False |
| 2026-05-15 | BTDR | 40 | 13.09000015258789 | 3300060 | False | False | False |
| 2026-05-15 | CAMT | 68 | 170.53500366210938 | 227938 | True | False | False |
| 2026-05-15 | CARR | 50 | 64.57499694824219 | 1101888 | False | False | False |
| 2026-05-15 | CEG | 68 | 268.739990234375 | 1284365 | True | False | False |
| 2026-05-15 | CIEN | 40 | 570.0599975585938 | 729166 | False | False | False |
| 2026-05-15 | CIFR | 50 | 20.584999084472656 | 10634297 | False | False | False |
| 2026-05-15 | CLS | 58 | 363.4599914550781 | 796406 | False | False | False |
| 2026-05-15 | COHR | 50 | 387.0899963378906 | 3461784 | False | False | False |
| 2026-05-15 | COHU | 50 | 46.97999954223633 | 205156 | False | False | False |
| 2026-05-15 | CORZ | 50 | 23.815000534057617 | 3658281 | False | False | False |
| 2026-05-15 | CRDO | 58 | 175.77000427246094 | 2295669 | False | False | False |
| 2026-05-15 | CRM | 64 | 173.23500061035156 | 4919577 | False | True | False |
| 2026-05-15 | CRWD | 15 | 585.030029296875 | 1297376 | False | False | True |
| 2026-05-15 | CRWV | 58 | 109.12000274658205 | 9976245 | False | False | False |
| 2026-05-15 | CSCO | 19 | 116.55999755859376 | 15622231 | False | False | True |
| 2026-05-15 | D | 58 | 62.15800094604492 | 1513685 | False | False | False |
| 2026-05-15 | DDOG | 20 | 205.4499969482422 | 1786286 | False | False | True |
| 2026-05-15 | DELL | 50 | 242.02999877929688 | 1493880 | False | False | False |
| 2026-05-15 | ECL | 72 | 247.6300048828125 | 484392 | True | False | False |
| 2026-05-15 | ENTG | 64 | 133.3800048828125 | 1166324 | False | True | False |
| 2026-05-15 | ETN | 58 | 398.5150146484375 | 1310572 | False | False | False |
| 2026-05-15 | ETR | 64 | 110.2699966430664 | 995940 | False | True | False |
| 2026-05-15 | FIX | 40 | 1978.800048828125 | 151439 | False | False | False |
| 2026-05-15 | FLEX | 25 | 139.8300018310547 | 1259185 | False | False | True |
| 2026-05-15 | FLR | 64 | 44.935001373291016 | 690827 | False | True | False |
| 2026-05-15 | FN | 50 | 716.9299926757812 | 300055 | False | False | False |
| 2026-05-15 | FORM | 62 | 126.43499755859376 | 1570580 | False | False | False |
| 2026-05-15 | GEV | 58 | 1050.6998291015625 | 1047897 | False | False | False |
| 2026-05-15 | GLW | 50 | 196.875 | 7869735 | False | False | False |
| 2026-05-15 | GNRC | 50 | 263.6700134277344 | 251694 | False | False | False |
| 2026-05-15 | GOOGL | 50 | 396.0499877929688 | 8487731 | False | False | False |
| 2026-05-15 | HPE | 34 | 33.05500030517578 | 5244857 | False | False | False |
| 2026-05-15 | HUBB | 72 | 480.8500061035156 | 150269 | True | False | False |
| 2026-05-15 | ICHR | 40 | 72.83999633789062 | 334640 | False | False | False |
| 2026-05-15 | IGV | 50 | 91.08999633789062 | 11395079 | False | False | False |
| 2026-05-15 | INTC | 50 | 108.62000274658205 | 71742224 | False | False | False |
| 2026-05-15 | IRDM | 40 | 41.54999923706055 | 478709 | False | False | False |
| 2026-05-15 | IREN | 54 | 54.290000915527344 | 21910672 | False | False | False |
| 2026-05-15 | IYW | 30 | 239.57000732421875 | 303448 | False | False | False |
| 2026-05-15 | JBL | 50 | 343.2699890136719 | 250067 | False | False | False |
| 2026-05-15 | KEYS | 50 | 351.75 | 726281 | False | False | False |
| 2026-05-15 | KLAC | 50 | 1840.050048828125 | 345059 | False | False | False |
| 2026-05-15 | KLIC | 40 | 100.68000030517578 | 221759 | False | False | False |
| 2026-05-15 | LITE | 50 | 977.6699829101562 | 2680425 | False | False | False |
| 2026-05-15 | LRCX | 40 | 286.6300048828125 | 4801806 | False | False | False |
| 2026-05-15 | MCHP | 50 | 94.54499816894533 | 2342594 | False | False | False |
| 2026-05-15 | MDB | 30 | 309.8800048828125 | 472213 | False | False | False |
| 2026-05-15 | META | 58 | 612.49951171875 | 5307100 | False | False | False |
| 2026-05-15 | MKSI | 40 | 303.0 | 403128 | False | False | False |
| 2026-05-15 | MOD | 40 | 275.79998779296875 | 530028 | False | False | False |
| 2026-05-15 | MPWR | 50 | 1566.31005859375 | 167430 | False | False | False |
| 2026-05-15 | MRVL | 30 | 179.9499969482422 | 10808866 | False | False | False |
| 2026-05-15 | MSFT | 58 | 420.91009521484375 | 22111735 | False | False | False |
| 2026-05-15 | MU | 50 | 735.75 | 26976207 | False | False | False |
| 2026-05-15 | NET | 58 | 197.7550048828125 | 1114268 | False | False | False |
| 2026-05-15 | NOW | 50 | 94.43499755859376 | 16436890 | False | False | False |
| 2026-05-15 | NTAP | 40 | 119.33000183105467 | 706379 | False | False | False |
| 2026-05-15 | NVDA | 50 | 228.30999755859372 | 82304649 | False | False | False |
| 2026-05-15 | NVT | 40 | 168.52999877929688 | 516232 | False | False | False |
| 2026-05-15 | NXPI | 50 | 291.7699890136719 | 642728 | False | False | False |
| 2026-05-15 | ON | 30 | 113.79000091552734 | 3891477 | False | False | False |
| 2026-05-15 | ORCL | 40 | 192.3999938964844 | 6895143 | False | False | False |
| 2026-05-15 | PANW | 14 | 238.7949981689453 | 4500340 | False | False | True |
| 2026-05-15 | PLTR | 64 | 133.52000427246094 | 15189980 | False | True | False |
| 2026-05-15 | POWL | 50 | 289.2900085449219 | 240119 | False | False | False |
| 2026-05-15 | PWR | 50 | 771.0800170898438 | 444204 | False | False | False |
| 2026-05-15 | QCOM | 50 | 199.65499877929688 | 10619906 | False | False | False |
| 2026-05-15 | QQQ | 30 | 710.4000244140625 | 20875875 | False | False | False |
| 2026-05-15 | SANM | 50 | 235.3300018310547 | 270694 | False | False | False |
| 2026-05-15 | SMCI | 50 | 31.229999542236328 | 13796405 | False | False | False |
| 2026-05-15 | SMH | 40 | 560.469970703125 | 5150709 | False | False | False |
| 2026-05-15 | SNDK | 50 | 1412.0699462890625 | 8163352 | False | False | False |
| 2026-05-15 | SNOW | 40 | 157.0749969482422 | 3107011 | False | False | False |
| 2026-05-15 | SOXL | 40 | 169.00999450683594 | 38888113 | False | False | False |
| 2026-05-15 | SOXX | 40 | 513.6799926757812 | 4865711 | False | False | False |
| 2026-05-15 | SPY | 40 | 740.1525268554688 | 19380091 | False | False | False |
| 2026-05-15 | STX | 40 | 794.3200073242188 | 1065173 | False | False | False |
| 2026-05-15 | TER | 58 | 345.1300048828125 | 1376949 | False | False | False |
| 2026-05-15 | TQQQ | 30 | 75.79000091552734 | 47479723 | False | False | False |
| 2026-05-15 | TSLA | 40 | 425.5750122070313 | 23800624 | False | False | False |
| 2026-05-15 | TSM | 40 | 406.5849914550781 | 6073700 | False | False | False |
| 2026-05-15 | TXN | 25 | 305.6300048828125 | 2152376 | False | False | True |
| 2026-05-15 | VECO | 50 | 57.90250015258789 | 517116 | False | False | False |
| 2026-05-15 | VRT | 40 | 370.9599914550781 | 2059123 | False | False | False |
