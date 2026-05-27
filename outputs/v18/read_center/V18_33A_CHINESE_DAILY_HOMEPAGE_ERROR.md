# V18.33A Chinese Daily Operator Homepage Error

STATUS: FAIL_V18_33A_CHINESE_DAILY_HOMEPAGE_FAILED

```text
'forward_return_ready'

Traceback (most recent call last):
  File "D:\us-tech-quant\scripts\v18\v18_33A_chinese_daily_operator_homepage.py", line 724, in main
    return run(parse_args())
  File "D:\us-tech-quant\scripts\v18\v18_33A_chinese_daily_operator_homepage.py", line 653, in run
    home_text = make_homepage(values_out, system, table_rows, missing_name_count)
  File "D:\us-tech-quant\scripts\v18\v18_33A_chinese_daily_operator_homepage.py", line 469, in make_homepage
    if values["forward_return_ready"] or system["daily_status"].startswith("WARN_"):
       ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'forward_return_ready'
```
