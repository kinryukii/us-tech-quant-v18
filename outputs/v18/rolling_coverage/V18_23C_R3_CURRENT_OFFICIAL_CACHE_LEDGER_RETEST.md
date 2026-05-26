# V18.23C-R3 Official Cache Rolling Ledger Retest

Generated: 2026-05-21T15:15:59

## Scope
Local-only retest of V18.23C-R2 integrated full-history tickers against the official price cache, followed by rolling ledger updates for successful evidence only.

## Results
Integrated tickers: 51. Retest attempted: 51. Local price success: 51. Full-history ready: 51. Failed: 0.

## Coverage
Unique success within window before: 103.
Unique success within window after: 154.
Remaining stale/never-success: 170.
TRUE_5DAY_UNIQUE_COVERAGE_MET: FALSE.

## Safety
Only the rolling scan ledger and V18.23C-R3 outputs were modified. Official price cache files were read but not modified.

## Recommended Next Action
Continue rolling local-only retests/backfill for remaining stale or never-success tickers; do not promote factor claims or production until full ledger coverage and downstream readiness gates pass.
