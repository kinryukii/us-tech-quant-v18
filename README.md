# US Tech Quant V18

US Tech Quant V18 is a research-oriented quantitative analysis system for U.S. technology-related equities.

The project is built around a Python and PowerShell daily research pipeline. It focuses on candidate generation, signal freezing, forward evidence tracking, experiment registration, alpha signal normalization, portfolio target preview, and risk preview.

This repository is designed for research and decision support. It is not an automated trading system.

## Current Baseline

Latest stable baselines:

- V18.38D: Qlib-style research tracking baseline
- V18.39D: LEAN-inspired signal, portfolio, and risk baseline

Current core state:

- Current full candidate universe: 318
- Latest signal freeze count: 318
- Alpha signal object count: 318
- Portfolio target preview rows: 1832
- Risk preview scenario-capital rows: 20
- Auto trading: disabled
- Auto selling: disabled
- Broker API usage: disabled
- Order execution: disabled

## Project Goal

The goal of this project is to build a transparent and auditable daily quant research workflow.

The system is designed to:

- Maintain a current U.S. technology-related equity candidate universe
- Generate ranked candidates
- Freeze daily signals for forward testing
- Track whether forward outcomes have matured
- Register and organize research experiments
- Convert ranked candidates into structured alpha signal objects
- Preview theoretical portfolio targets under simulated capital levels
- Preview portfolio-level risk without placing trades
- Produce human-readable daily operator reports

The project prioritizes transparency, reproducibility, and safety over automation.

## What This Project Is Not

This repository is not:

- An automated trading bot
- A broker-connected execution system
- A financial advisory product
- A guarantee of trading performance
- A black-box trading signal service

The current baseline does not send orders, does not use real account cash, does not connect to a broker API, and does not modify real holdings.

## Architecture Overview

The current V18 architecture has two main research layers.

## 1. Qlib-Style Research Tracking Layer

This layer focuses on research evidence, experiment tracking, and daily system status.

Key modules:

- V18.38A Forward Evidence Dashboard
  - Tracks whether 1D, 3D, 5D, 10D, and 20D forward outcomes are available.
  - Summarizes paper trading, shadow portfolios, signal freeze, and benchmark readiness.

- V18.38B Research Experiment Registry
  - Registers paper trading experiments, shadow portfolio experiments, strategy motifs, benchmarks, and pending research tasks.
  - Helps keep research outputs organized and traceable.

- V18.38C-R1 Command Status Normalization
  - Separates current blocking issues from historical legacy warnings.
  - Produces a daily operator status judgment.

- V18.38D Stable Snapshot
  - Captures the V18.38 research tracking baseline.

## 2. LEAN-Inspired Signal, Portfolio, and Risk Layer

This layer is inspired by the conceptual structure of QuantConnect LEAN.

The high-level flow is:

Alpha Signal to Portfolio Construction Preview to Risk Management Preview.

Key modules:

- V18.39A Alpha Signal Object Layer
  - Converts ranked candidates into structured alpha signal objects.
  - Produces fields such as direction, confidence, rank bucket, forward evidence status, freeze status, and operator hints.

- V18.39B Portfolio Target Preview
  - Generates theoretical portfolio target previews under simulated capital levels.
  - Supports scenarios such as Top20 equal weight, Top20 confidence weighted, Top50 capped, Top50 rank decay, and Full318 research-only watchlist.

- V18.39C Shadow Risk Model Preview
  - Reviews concentration, small-capital feasibility, price availability, forward evidence pending status, and data quality risk.
  - Does not place trades or create executable order files.

- V18.39D Stable Snapshot
  - Captures the V18.39 signal, portfolio, and risk baseline.

## Repository Structure

Main folders:

- `scripts/v18/`
  - Main Python modules and PowerShell wrappers for V18.

- `outputs/v18/`
  - Generated research outputs, CSV summaries, and operator-facing reports.

- `outputs/v18/read_center/`
  - Human-readable current reports and module-specific Markdown reports.

- `outputs/v18/ops/`
  - READ_FIRST files, operational summaries, status CSV files, and diagnostics.

- `outputs/v18/signals/`
  - Alpha signal object outputs.

- `outputs/v18/portfolio_preview/`
  - Portfolio target preview outputs.

- `outputs/v18/risk_preview/`
  - Shadow risk model preview outputs.

- `state/v18/`
  - Persistent research state, signal freeze ledger, and related non-broker state.

- `archive/stable/`
  - Stable snapshots used as local restore baselines.

- `configs/`
  - Configuration files.

- `docs/v18/`
  - V18 documentation and notes.

## Key Current Reports

Useful current reports:

- `outputs/v18/read_center/V18_CURRENT_COMMAND_STATUS_NORMALIZATION.md`
- `outputs/v18/read_center/V18_CURRENT_FORWARD_EVIDENCE_DASHBOARD.md`
- `outputs/v18/read_center/V18_CURRENT_RESEARCH_EXPERIMENT_REGISTRY.md`
- `outputs/v18/read_center/V18_CURRENT_ALPHA_SIGNAL_OBJECTS.md`
- `outputs/v18/read_center/V18_CURRENT_PORTFOLIO_TARGET_PREVIEW.md`
- `outputs/v18/read_center/V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md`
- `outputs/v18/read_center/V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md`

Important READ_FIRST files:

- `outputs/v18/ops/V18_38C_R1_READ_FIRST.txt`
- `outputs/v18/ops/V18_38D_READ_FIRST.txt`
- `outputs/v18/ops/V18_39A_READ_FIRST.txt`
- `outputs/v18/ops/V18_39B_READ_FIRST.txt`
- `outputs/v18/ops/V18_39C_READ_FIRST.txt`
- `outputs/v18/ops/V18_39D_READ_FIRST.txt`

## Typical Daily Research Command

Run from the project root on Windows PowerShell.

Step 1:

`Set-Location "D:\us-tech-quant"`

Step 2:

`.\.venv\Scripts\Activate.ps1`

Step 3:

Run the daily command center with the desired research flags.

Recommended research chain:

`powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_current_daily_command_center.ps1" -RunUniverseRollingScan -RunForwardTracker -RunManualFeedback -RunTradeReadinessRefresh -RunChineseHomepage -RunFreshnessGuard -RunForwardEvidenceDashboard -RunResearchExperimentRegistry -RunCommandStatusNormalization -RunAlphaSignalObjectLayer -RunPortfolioTargetPreview -RunShadowRiskModelPreview`

This command is intended for research and reporting. It does not enable broker execution.

## Safety Design

Current baseline safety markers:

- `AUTO_TRADE: DISABLED`
- `AUTO_SELL: DISABLED`
- `OFFICIAL_DECISION_IMPACT: NONE`
- `BROKER_API_USED: FALSE`
- `ORDER_EXECUTION_USED: FALSE`
- `REAL_ACCOUNT_USED: FALSE`

The current system does not:

- Send broker orders
- Create executable trade tickets
- Use real account balances
- Modify real holdings
- Automatically buy or sell securities

## Current Research Limitation

The forward outcome layer is currently waiting for future price data to mature.

Expected pending areas:

- 1D forward outcome
- 3D forward outcome
- 5D forward outcome
- 10D forward outcome
- 20D forward outcome
- Factor forward attribution
- Shadow portfolio league table
- Turnover and trading cost simulation

The system is already structured to evaluate these once enough future price data is available.

## Roadmap

Planned next research layers:

- V18.40A Factor Forward Attribution
  - Evaluate which implemented ranking factors have forward predictive power.

- V18.40B Shadow Portfolio League Table
  - Compare shadow portfolios against each other and against benchmarks.

- V18.40C Turnover and Trading Cost Simulator
  - Estimate whether strategy performance survives transaction costs and rebalancing friction.

- Manual account-state integration
  - Deferred for now.
  - Intended only for future decision support, not automatic execution.

## Development Philosophy

This project follows several principles:

- Prefer transparent logic over black-box signals.
- Preserve historical signal freezes for forward testing.
- Separate research outputs from trading execution.
- Keep daily operator reports human-readable.
- Distinguish current blocking failures from historical legacy warnings.
- Avoid automatic factor weight changes without evidence.
- Avoid broker integration until the research layer is mature.

## Disclaimer

This repository is for personal quantitative research and software engineering experimentation only.

Nothing in this repository is financial advice, investment advice, or a recommendation to buy, sell, or hold any security.

All outputs are research artifacts and should be independently reviewed before any real-world financial decision.

Past performance, simulated performance, paper trading results, and forward-test results do not guarantee future returns.
