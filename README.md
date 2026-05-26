# US Tech Quant V18

A research-oriented quantitative analysis system for U.S. technology-related equities.

This repository contains a Python + PowerShell based quant research pipeline focused on daily candidate generation, signal freezing, forward evidence tracking, experiment registration, portfolio preview, and risk preview. The system is designed as a research and decision-support framework, not as an automated trading bot.

## Current Baseline

Latest stable research baselines:

- `V18.38D` — Qlib-style research tracking baseline
- `V18.39D` — LEAN-inspired signal / portfolio / risk baseline

Current core state:

- Current full candidate universe: `318`
- Latest signal freeze count: `318`
- Alpha signal objects: `318`
- Portfolio preview rows: `1832`
- Risk preview scenario-capital rows: `20`
- Auto trading: `DISABLED`
- Auto selling: `DISABLED`
- Broker API usage: `DISABLED`
- Order execution: `DISABLED`

## Project Goal

The goal of this project is to build a transparent, auditable, daily quant research workflow that can:

1. Maintain a current candidate universe.
2. Generate ranked equity candidates.
3. Freeze daily signals for forward testing.
4. Track whether forward outcomes have matured.
5. Register and compare research experiments.
6. Normalize ranked candidates into structured alpha signal objects.
7. Preview theoretical portfolio targets under simulated capital levels.
8. Preview portfolio-level risk without placing trades.
9. Produce human-readable daily operator reports.

The system prioritizes transparency, reproducibility, and safety over automation.

## What This Project Is Not

This repository is **not**:

- An automated trading system
- A broker-connected execution system
- A financial advisory product
- A guarantee of trading performance
- A black-box signal generator

No module in the current baseline sends orders, uses real account cash, connects to a broker API, or modifies real holdings.

## Architecture Overview

The current V18 architecture can be understood in two major layers.

### 1. Qlib-Style Research Tracking Layer

This layer focuses on evidence, experiment tracking, and daily research status.

Key modules:

- `V18.38A Forward Evidence Dashboard`
  - Tracks whether 1D / 3D / 5D / 10D / 20D forward outcomes are available.
  - Summarizes paper trading, shadow portfolios, signal freeze, and benchmark readiness.

- `V18.38B Research Experiment Registry`
  - Registers paper trading experiments, shadow portfolio experiments, strategy motifs, benchmarks, and pending research tasks.
  - Helps prevent research outputs from becoming scattered and untraceable.

- `V18.38C-R1 Command Status Normalization`
  - Separates current blocking issues from historical legacy warnings.
  - Produces a daily operator status judgment.

- `V18.38D Stable Snapshot`
  - Captures the V18.38 research tracking baseline.

### 2. LEAN-Inspired Signal / Portfolio / Risk Layer

This layer is inspired by the conceptual structure of QuantConnect LEAN:

```text
Alpha Signal → Portfolio Construction Preview → Risk Management Preview
