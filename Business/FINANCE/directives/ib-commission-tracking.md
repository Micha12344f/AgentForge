# IB Commission Tracking

> Standard operating procedure for monitoring and reconciling IB (Introducing Broker) commissions.

## Brokers

| Broker | Portal | Scraper Script |
|--------|--------|----------------|
| Vantage Markets | IB portal dashboard | `scrape_vantage_ib.py` |
| BlackBull Markets | Partner portal | `scrape_blackbull_ib.py` |

## Process

1. **Monthly**: Broker publishes commission report on portal
2. **Scrape**: `scrape_vantage_ib.py` / `scrape_blackbull_ib.py` pull raw data
3. **Aggregate**: `ib_report_aggregator.py` reconciles across brokers
4. **Reconcile**: Compare against Supabase `ib_commissions` table
5. **Invoice**: `invoice_generator.py` creates payout invoice
6. **Record**: Deposit confirmed in Tide Bank → update records

## Metrics

| Metric | Definition |
|--------|-----------|
| Referred Accounts | Total accounts opened via IB links |
| Active Traders | Referred accounts with ≥1 trade this month |
| Gross Commission | Total commission accrued |
| Net Commission | After broker fees/adjustments |
| Commission per Lot | Average commission per traded lot |
