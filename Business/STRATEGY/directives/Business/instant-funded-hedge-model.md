---
name: instant-funded-hedge-model
description: |
  Hedge model for instant-funded FX prop accounts. These accounts charge a higher
  upfront fee in exchange for immediate funded access, so the model focuses on
  first-payout recovery under static or trailing drawdown plus optional
  consistency constraints.
---

# Instant Funded Prop Firm Hedge Model

## Objective

Quantify the economics of hedging instant-funded prop accounts using a deterministic
insurance model. Unlike standard challenge accounts, instant-funded accounts skip
the evaluation phase: you pay an inflated upfront fee and begin in the funded
state immediately.

That changes the question from:

- "Can I pass the challenge profitably?"

to:

- "After paying the inflated fee upfront, can I hedge the funded account to
  recover that fee and still leave positive value on the first payout?"

## Structural Differences from Challenge Accounts

1. **No evaluation phase** - there is no phase-one or phase-two target to pass
2. **Upfront fee is the full insured base** - the fee is paid before any funded payout exists
3. **Drawdown may be static or trailing** - some instant accounts use balance-based static DD, others use highest-balance or highest-equity trailing DD
4. **Consistency rules may still apply** - even without an evaluation phase, some firms can restrict how concentrated funded profits may be
5. **Payout timing matters immediately** - payout frequency directly affects how fast the upfront fee can be recovered

## When to Use This Skill

- When evaluating instant-funded account offers on PropFirmMatch
- When comparing instant-funded accounts versus classic challenge accounts
- When deciding whether a higher upfront fee is justified by immediate funded access
- When stress-testing instant-funded offers with trailing DD or consistency rules
- When producing research or positioning content around first-payout recovery

## Input Specification

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| Data file | JSON | Yes | Scraped FX challenge data from `propmatch_scraper.py --action scrape-challenges` |
| filter | string | Yes | Keep rows where `steps_label = "Instant"` |
| first_payout_target_pct | float | No | Gross funded profit target before withdrawal split (default: `0.05` = 5%) |
| spread_cost_pct | float | No | Round-trip hedge friction as a percent of notional (default: `0.0003`) |
| base_trading_days | int | No | Minimum funded trading days assumed to reach first payout (default: `5`) |
| consistency_threshold | float | No | Optional override for consistency-rule stress tests |

## Instant-Funded Data Schema

Current PropFirmMatch instant-funded rows are already present inside the main FX
challenge scrape. Typical fields include:

| Field | Type | Example |
|-------|------|---------|
| firm | string | "FundingPips" |
| account_size | int | 5000 |
| steps | int | 1 |
| steps_label | string | "Instant" |
| daily_drawdown_pct | float | 3.0 |
| max_drawdown_pct | float | 5.0 |
| drawdown_type | string | "Balance/Equity - Highest at EOD" |
| profit_split_pct | float | 95.0 |
| payout_timing | string | "Bi-weekly" |
| fee_discounted | float | 69.0 |
| fee_original | float | 69.0 |
| currency | string | "USD" |

Optional future enrichment may also add explicit rule fields such as consistency
limits. The notebook should treat those as optional, defaulting to no rule when
they are absent.

## Drawdown Type Eligibility Filter

**MANDATORY PRE-FILTER:** Before modelling any instant-funded offer, classify its `drawdown_type` and apply the following gate:

| `drawdown_type` value | Hedgeable? | Action |
|---|---|---|
| `Balance - EOD` | Yes | Full deterministic model |
| `Balance/Equity - Highest at EOD` | Mostly yes | Model with EOD-close-only assumption |
| `Equity - Intraday` / real-time equity trailing | **No** | **Exclude — do not model, flag as incompatible** |

### Why Intraday Equity Trailing DD is Unhedgeable

A deterministic hedge requires that at the moment of breach, the hedge recovers the full cost stack `L`. This requires:

    hedge_notional = L / distance_to_breach

With intraday equity trailing, `distance_to_breach` is a **stochastic process that can only decrease** — it ratchets down on every intraday equity high and never recovers within the session, even if the account closes flat or up.

**The path-dependency trap:** Consider a single trading day:
- Session open: balance $100K, DD floor $92K, distance = $8K
- Intraday high: equity $105K → floor ratchets to $96,600, distance = $8,400
- Intraday retrace: equity closes at $101K → floor stays at $96,600, **distance = $4,400**
- Net P&L for the day: +$1K — but DD room halved

The account ended profitable but consumed half its remaining breach distance at no cost to net performance. The hedge sized for $8K recovers correctly on a clean trend day but under-recovers on any day with intraday peaks that retrace.

**Why no position management strategy fixes this:**
- **Static sizing at open** → under-recovers when floor ratchets before breach
- **Dynamic intraday resizing** → pays spread on every ratchet event; violates funded account activity/consistency rules
- **Worst-case sizing** → cost explodes; EV goes deeply negative
- **Single daily candle / fast pass** → reduces variance exposure but eliminates the hedge (both sides correlate, not offset); no longer arbitrage
- **Martingale** → banned on prop firms; doesn't resolve path dependency regardless

The correct hedge cost for an intraday equity trailing product is **path-dependent on intraday volatility**, not computable from net profit targets alone. It can only be bounded, not pinned. In expectation across realistic path distributions, it is far higher than the static model suggests.

**Practical result (FundingPips Instant Standard, $10K, 4% daily trailing + 8% total trailing with lock at +4% profit):**
- Static 8% DD model: $161 total cost — wrong, understates by 2.52×
- Smart trailing model (EOD approximation): $406 — still an underestimate; ignores intraday ratcheting
- True cost: unquantifiable without full intraday price path
- Only $5K and $10K variants fit a $500 budget under the EOD approximation, and both have negative to break-even EV

**Do not present intraday equity trailing products as hedgeable.** They are a different product category.

---

## Model Framework

### Core State Variable

Let `L` be the insured cost stack. For instant-funded accounts, the stack starts
at the upfront fee:

    L_0 = fee_upfront

There is no challenge phase before funding.

### Static Drawdown Case

If the funded account uses a fixed balance-based DD, hedge sizing can remain
linear over the payout path.

For account size `S`, max DD ratio `d`, payout path target `P`, and split `s`:

    hedge_notional = L_0 / d
    hedge_loss = hedge_notional * P
    total_cost = L_0 + hedge_loss + friction
    funded_payout = S * payout_target_pct * s
    EV = funded_payout - total_cost

This is cheaper than trailing DD because the blow-up line does not move upward as
equity makes new highs.

### Trailing Drawdown Case

If the instant-funded account uses highest-balance or highest-equity drawdown,
the insured stack compounds while you trade toward the first payout.

Walk the funded profit path in `N` increments:

    daily_profit = payout_path / N
    For each day:
        hedge_size = L / d
        hedge_loss = daily_profit * L / DD_dollars
        L = L + hedge_loss + friction

Trailing DD is structurally more expensive because the drawdown floor rises with
the high-water mark.

### Consistency Rule Penalty

If a rule says no single day can exceed `q` of total funded profit, then:

    min_trading_days = ceil(1 / q)

The notebook should set:

    trading_days = max(base_trading_days, min_trading_days)

This increases spread drag and, under trailing DD, increases compounding events.

### Recovery Metrics

Rank instant-funded offers by:

| Metric | Formula | Purpose |
|--------|---------|---------|
| EV | funded_payout - total_cost | Absolute first-payout profitability |
| Break-even payout | total_cost / split | Gross payout needed to recover the fee stack |
| Break-even pct | break-even payout / account_size | Recovery difficulty as % of account |
| Capital efficiency | EV / capital_required | Return on deployed hedge capital |
| Recovery cycles | total_cost / funded_payout | How many similar payouts are needed to recover full cost |

## Execution Scripts

- `executions/propmatch_scraper.py --action scrape-challenges` - FX challenge data including `steps_label = Instant`
- `resources/PropFirmData/instant_funded_hedge_model.ipynb` - Interactive notebook for instant-funded accounts

## Resources

- `resources/PropFirmData/propmatch_challenges_*.json` - Scraped FX challenge data with instant-funded rows included
- `directives/Business/prop-firm-hedge-arbitrage.md` - Base FX challenge modelling directive
- `resources/Product/hedging-explained.md` - Hedge mechanics reference

## Definition of Done

- [ ] Latest FX scrape contains instant-funded rows with `steps_label = "Instant"`
- [ ] **Drawdown type filter applied first** — intraday equity trailing rows excluded before any modelling
- [ ] Notebook filters only instant-funded offers and normalises their drawdown types
- [ ] Static and trailing DD are modelled separately
- [ ] Missing consistency fields default cleanly to no-rule instead of breaking the model
- [ ] Notebook ranks accounts by first-payout EV and break-even payout percentage
- [ ] Sensitivity analysis covers payout target and consistency-rule stress testing
- [ ] Outputs are saved to `resources/PropFirmData/`