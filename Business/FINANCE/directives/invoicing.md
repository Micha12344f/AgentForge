# Invoicing

> Invoice generation for IB commission payouts from brokers.

## Invoice Template Fields

| Field | Source |
|-------|--------|
| Invoice Number | Auto-incremented (HEIB-YYYY-NNN) |
| Date | Issue date |
| Broker Name | Vantage Markets / BlackBull Markets |
| Period | Commission period (month/year) |
| Referred Accounts | Count from IB report |
| Total Lots Traded | From IB report |
| Commission Rate | Per-lot rate from IB agreement |
| Gross Commission | Total commission amount |
| Payment Terms | As per IB agreement |
| Bank Details | Tide bank account |

## Process

1. `ib_report_aggregator.py` produces reconciled commission data
2. `invoice_generator.py` creates invoice document
3. Invoice sent to broker finance department
4. Payment tracked until received in Tide
