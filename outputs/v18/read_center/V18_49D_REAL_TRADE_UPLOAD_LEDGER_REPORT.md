# V18.49D Real Trade Upload Ledger

V18.49D is a manual-upload workflow. Only user-provided upload CSV rows can become real trade ledger rows.

## Manual Workflow
- Upload directory: D:\us-tech-quant\state\v18\manual\real_trade_uploads
- Template: D:\us-tech-quant\state\v18\manual\real_trade_uploads\V18_REAL_TRADE_UPLOAD_TEMPLATE.csv
- Fill a separate CSV using the template columns, then rerun V18.49D.
- The template itself is ignored as a trade source.

## Upload Validation Summary
| UPLOAD_FILE_COUNT | UPLOADED_ROW_COUNT | VALID_TRADE_ROW_COUNT | INVALID_TRADE_ROW_COUNT | REVIEW_REQUIRED_ROW_COUNT |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 |

## Valid Trade Ledger Summary
No valid user-uploaded trade rows found.

## Review-Required Rows
No review-required rows.

## Rebuilt Position Book
No generated open positions.

## State Write
- State real position book written: FALSE
- Write requested: FALSE

## Safety
No broker API was used. No order was generated. No execution occurred. Official ranking, factor weights, Top20 selection, candidate scoring, and official buy/sell permissions are unchanged.

## Handoff
After user uploads are validated and the state real position book is intentionally written, rerun V18.49C to refresh real-position advice.

