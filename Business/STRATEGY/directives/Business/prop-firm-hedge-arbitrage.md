---
name: prop-firm-hedge-arbitrage
description: |
  Scrapes PropMatch challenge data, builds deterministic hedge arbitrage models for
  prop-firm challenges, and produces comparison matrices across account sizes
  (10K–200K). Use when analysing which prop firm challenges offer the best
  hedge-adjusted economics or preparing data-driven content around the Hedge Edge
  value proposition.
---

# Prop Firm Hedge Arbitrage

## Objective

Quantify the economic advantage of hedging prop firm challenges using a deterministic model. The hedge guarantees you pass every phase — it's arbitrage, not gambling. Scrape live challenge data from PropMatch and compute EV, break-even payout, and capital requirements. Output actionable comparison matrices that rank prop firms by profitability.

## When to Use This Skill

- When evaluating which prop firm challenges are most profitable to hedge
- When producing data-driven content for marketing (e.g., "Which $100K challenge has the best ROI with Hedge Edge?")
- When updating pricing/positioning based on current prop firm fee structures
- When a user asks about the mathematics behind the hedging strategy
- When refreshing the competitive landscape of prop firm challenge economics
- When preparing investor materials that demonstrate the product's value proposition

## Input Specification

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| sizes | string | No | Comma-separated account sizes to analyse (default: `10000,25000,50000,100000,200000`) |
| funded_target | float | No | Funded profit target as decimal (default: `0.08` — 8% of funded account) |
| spread_cost | float | No | Average spread cost per trade as decimal (default: `0.0003` — ~3 pips) |
| include_rules | bool | No | Whether to enrich data with PropMatch rules page (default: `false`) |

## Step-by-Step Process

### Phase 1: Data Collection (PropMatch Scraper)

**Script**: `executions/propmatch_scraper.py`

1. Launch headless Chromium via Playwright
2. Navigate to `https://propfirmmatch.com/prop-firm-challenges#table-scroll-target`
3. For each account size in the input set (10K, 25K, 50K, 100K, 200K):
   a. Apply the **Size** filter dropdown
   b. Wait for the challenge table to reload
   c. For each page (up to 5 pages):
      - Extract every row: firm name, rating, review count, account size, steps, profit targets per step, daily drawdown %, max drawdown %, leverage, profit split %, payout timing, fee (discounted + original)
      - Navigate to next page
   d. Respect 2-second delay between page loads
4. The FX table includes step types `1 Step`, `2 Steps`, `3 Steps`, and `Instant`
5. Treat `Instant` rows as a separate modelling domain: there is no evaluation phase, so the economic question becomes first-payout recovery after paying the inflated upfront fee
6. Optionally scrape `/prop-firm-rules` for hedging-allowed flags
7. Save structured JSON + CSV to `resources/PropFirmData/`

**Data fields extracted per challenge**:

| Field | Type | Example |
|-------|------|---------|
| firm | string | "The5ers" |
| rating | float | 4.8 |
| reviews | int | 1111 |
| account_size | int | 100000 |
| steps | int | 2 |
| profit_targets | list[float] | [8.0, 5.0] |
| daily_drawdown_pct | float | 5.0 |
| max_drawdown_pct | float | 10.0 |
| leverage | string | "1:100" |
| profit_split_pct | float | 80.0 |
| payout_timing | string | "14 Days" |
| fee_discounted | float | 517.75 |
| fee_original | float | 545.00 |
| currency | string | "USD" |

For instant-funded rows (`steps_label = "Instant"`), `profit_targets` will often be empty because there is no challenge target before funding. Those rows are modelled separately in `instant-funded-hedge-model.md` and `resources/PropFirmData/instant_funded_hedge_model.ipynb`.

### Phase 2: Phase-Based Fee-Insurance Modelling

**Script**: `executions/hedge_arbitrage_model.py`

The core mathematical framework — **fee-insurance, not drawdown capture**:

#### 2a — The Key Insight

The hedge guarantees you pass every phase. It's arbitrage — you always pass. The cost of the guarantee is the hedge losses accumulated through each phase. The only question: do you earn enough once funded to cover those costs?

#### 2b — Phase-by-Phase Hedge Sizing

For a challenge with phases (e.g., Phase 1 → Phase 2 → Funded):

**State variable**: `L_n` = cumulative cost stack entering phase n

```
L_1 = F                         (just the challenge fee)

Hedge size per phase:
  S_n = L_n / DD                (sized so DD-event recovers L_n)

You always PASS → hedge loses:
  hedge_loss_n = S_n × target_n + friction_n
  L_{n+1} = L_n + hedge_loss_n  (cost stack grows)
```

After all phases: total_cost = L_final (fee + all accumulated hedge losses)

#### 2c — Expected Value (Deterministic)

```
EV = (profit_split × account_size × funded_target_pct) − total_cost
```

No pass rate needed — the hedge makes passing a certainty.

#### 2d — Break-Even Payout

```
break_even_payout = total_cost / profit_split
break_even_pct = break_even_payout / account_size × 100
```

This tells you: what % of your funded account do you need to earn to cover all costs?

#### 2e — Capital Requirements

```
Capital = margin + buffer
Margin  = S_n / leverage         (hedge position margin)
Buffer  = S_n × DD × 1.5        (safety buffer)
```

Note: S_n = L_n / DD, so capital scales with the **insured base** (fees), NOT the prop account size.

#### 2f — Comparison Matrix

Rank all scraped challenges by:
- EV (funded payout minus total cost)
- Break-even payout (% of funded account needed to cover costs)
- Capital efficiency = EV / capital_required
- Cost efficiency = EV / fee

Group by account size tier. Output as markdown table + JSON.

### Phase 3: Report Generation

1. Produce per-size markdown reports with full workings
2. Produce a combined comparison matrix across all sizes
3. Save all outputs to `resources/PropFirmData/`
4. Log completion to Notion

## Execution Scripts

- `executions/propmatch_scraper.py` — Playwright-based PropMatch challenge scraper
- `executions/hedge_arbitrage_model.py` — Deterministic EV, break-even payout, funded target sensitivity, capital requirements, comparison matrix

## Resources

- `resources/PropFirmData/` — Scraped JSON data, model outputs, comparison matrices
- `resources/Product/hedging-explained.md` — Hedge mechanics reference
- `resources/hedge-edge-business-context.md` — Prop firm economics (fees, failure rates, payout splits)

## Definition of Done

- [ ] PropMatch scraper successfully extracts ≥10 challenges per account size
- [ ] All JSON fields populated with correct types (no nulls except optional rules)
- [ ] EV model produces non-trivial results for all challenge sizes
- [ ] Break-even payout % is positive and below funded target for profitable firms
- [ ] Capital requirements are positive and scale with account size
- [ ] Comparison matrix ranks challenges with all expected columns
- [ ] Hand-verified example matches (e.g., The5ers 100K: fee ≈ $518, target = 13%, DD = 10%, split = 80%)
- [ ] Full pipeline (scrape → model → compare → report) completes end-to-end
- [ ] All outputs saved to `resources/PropFirmData/` in both markdown and JSON

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Playwright not installed | Missing dependency | Run `pip install playwright && playwright install chromium` |
| PropMatch layout change | Site redesign breaks selectors | Update CSS selectors in scraper; selectors are centralised in SELECTORS dict |
| Empty table after filter | No challenges for that account size | Log warning and skip; do not fail the entire run |
| Rate limiting / 403 | Too many requests | Increase delay between pages; add exponential backoff |
| Negative EV for all firms | Spread cost or pass rate too pessimistic | Flag in report; suggest adjusting assumptions |
| Division by zero in break-even | Denominator is zero when funded value equals hedge loss | Guard with epsilon; report "N/A — break-even not achievable" |
