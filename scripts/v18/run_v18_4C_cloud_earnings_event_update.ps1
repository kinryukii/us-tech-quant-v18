param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$StateV16 = Join-Path $Root "state\v16"
$StateV18 = Join-Path $Root "state\v18"
$OutDir = Join-Path $Root "outputs\v18\ops"

New-Item -ItemType Directory -Force -Path $StateV16, $StateV18, $OutDir | Out-Null

$targets = @(
    (Join-Path $StateV16 "event_calendar.csv"),
    (Join-Path $StateV18 "cloud_earnings_event_calendar.csv")
)

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$events = @(
    [pscustomobject]@{
        event_date = "2026-05-27"
        ticker = "CRM"
        company = "Salesforce"
        event_name = "CRM Salesforce FY2027 Q1 earnings after market close"
        event_type = "CLOUD_EARNINGS"
        risk_level = "HIGH"
        action = "FREEZE_NEW_BUYS"
        source_quality = "OFFICIAL_CONFIRMED"
        notes = "Salesforce official IR: results after market close; major cloud/SaaS read-through."
        updated_at = $now
    },
    [pscustomobject]@{
        event_date = "2026-06-15"
        ticker = "ORCL"
        company = "Oracle"
        event_name = "ORCL Oracle FY2026 Q4 earnings mid-June watch window"
        event_type = "CLOUD_EARNINGS"
        risk_level = "HIGH"
        action = "TRIAL_ONLY"
        source_quality = "OFFICIAL_WINDOW_ESTIMATED_DATE"
        notes = "Oracle official FAQ says FY2026 Q4 earnings will be announced in mid-June 2026; date set to mid-month watch anchor until official date appears."
        updated_at = $now
    },
    [pscustomobject]@{
        event_date = "2026-07-22"
        ticker = "GOOGL"
        company = "Alphabet / Google Cloud"
        event_name = "GOOGL Alphabet Q2 2026 earnings estimated"
        event_type = "CLOUD_EARNINGS"
        risk_level = "HIGH"
        action = "TRIAL_ONLY"
        source_quality = "THIRD_PARTY_ESTIMATED"
        notes = "Estimated earnings date; replace with official Alphabet IR date once announced."
        updated_at = $now
    },
    [pscustomobject]@{
        event_date = "2026-07-29"
        ticker = "MSFT"
        company = "Microsoft / Azure"
        event_name = "MSFT Microsoft FY2026 Q4 earnings estimated"
        event_type = "CLOUD_EARNINGS"
        risk_level = "HIGH"
        action = "TRIAL_ONLY"
        source_quality = "THIRD_PARTY_ESTIMATED"
        notes = "Estimated earnings date; Microsoft IR currently says next earnings release will be announced soon."
        updated_at = $now
    },
    [pscustomobject]@{
        event_date = "2026-07-30"
        ticker = "AMZN"
        company = "Amazon / AWS"
        event_name = "AMZN Amazon Q2 2026 earnings estimated"
        event_type = "CLOUD_EARNINGS"
        risk_level = "HIGH"
        action = "TRIAL_ONLY"
        source_quality = "THIRD_PARTY_ESTIMATED"
        notes = "Estimated earnings date; replace with official Amazon IR date once announced."
        updated_at = $now
    }
)

function Ensure-Columns {
    param(
        [object[]]$Rows,
        [string[]]$Columns
    )

    $out = New-Object System.Collections.Generic.List[object]

    foreach ($r in $Rows) {
        $obj = [ordered]@{}
        foreach ($c in $Columns) {
            if ($r.PSObject.Properties.Name -contains $c) {
                $obj[$c] = $r.$c
            } else {
                $obj[$c] = ""
            }
        }
        $out.Add([pscustomobject]$obj) | Out-Null
    }

    return $out
}

foreach ($path in $targets) {
    $existing = @()

    if (Test-Path $path) {
        $existing = @(Import-Csv -LiteralPath $path)
    }

    $baseColumns = @(
        "event_date",
        "ticker",
        "company",
        "event_name",
        "event_type",
        "risk_level",
        "action",
        "source_quality",
        "notes",
        "updated_at"
    )

    $existingColumns = @()
    if ($existing.Count -gt 0) {
        $existingColumns = @($existing[0].PSObject.Properties.Name)
    }

    $allColumns = @($existingColumns + $baseColumns | Select-Object -Unique)

    $normalizedExisting = @(Ensure-Columns -Rows $existing -Columns $allColumns)
    $normalizedEvents = @(Ensure-Columns -Rows $events -Columns $allColumns)

    $map = @{}

    foreach ($r in $normalizedExisting) {
        $dateValue = ""
        if ($r.PSObject.Properties.Name -contains "event_date") { $dateValue = $r.event_date }
        elseif ($r.PSObject.Properties.Name -contains "date") { $dateValue = $r.date }

        $nameValue = ""
        if ($r.PSObject.Properties.Name -contains "event_name") { $nameValue = $r.event_name }
        elseif ($r.PSObject.Properties.Name -contains "event") { $nameValue = $r.event }

        $tickerValue = ""
        if ($r.PSObject.Properties.Name -contains "ticker") { $tickerValue = $r.ticker }

        $key = "$dateValue|$tickerValue|$nameValue"
        if (-not $map.ContainsKey($key)) {
            $map[$key] = $r
        }
    }

    foreach ($e in $normalizedEvents) {
        $key = "$($e.event_date)|$($e.ticker)|$($e.event_name)"
        $map[$key] = $e
    }

    $final = $map.Values | Sort-Object event_date, ticker, event_name
    $final | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $path

    Write-Host "EVENT_CALENDAR_UPDATED: $path"
    Write-Host "EVENT_COUNT: $($final.Count)"
}

$ReadMe = Join-Path $OutDir "V18_4C_CLOUD_EARNINGS_EVENTS_READ_FIRST.md"

@"
# V18.4C Cloud Earnings Events

生成时间：$now

## 已写入事件

| date | ticker | company | quality | action |
|---|---|---|---|---|
| 2026-05-27 | CRM | Salesforce | OFFICIAL_CONFIRMED | FREEZE_NEW_BUYS |
| 2026-06-15 | ORCL | Oracle | OFFICIAL_WINDOW_ESTIMATED_DATE | TRIAL_ONLY |
| 2026-07-22 | GOOGL | Alphabet / Google Cloud | THIRD_PARTY_ESTIMATED | TRIAL_ONLY |
| 2026-07-29 | MSFT | Microsoft / Azure | THIRD_PARTY_ESTIMATED | TRIAL_ONLY |
| 2026-07-30 | AMZN | Amazon / AWS | THIRD_PARTY_ESTIMATED | TRIAL_ONLY |

## 说明

- CRM 是官方确认日期，所以设为 FREEZE_NEW_BUYS。
- ORCL 是官方 mid-June 窗口，先用 2026-06-15 作为观察锚点。
- GOOGL / MSFT / AMZN 是第三方预估日期，先作为 TRIAL_ONLY，不作为硬封锁。
- 后续一旦官方 IR 公布正式日期，再覆盖更新。
"@ | Set-Content -Encoding UTF8 $ReadMe

Write-Host ""
Write-Host "=== V18.4C CLOUD EARNINGS EVENTS READY ==="
Write-Host "READ:"
Write-Host $ReadMe
