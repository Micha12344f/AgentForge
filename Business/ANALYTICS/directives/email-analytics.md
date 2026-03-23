# Email Analytics

> Email campaign performance tracking — deliverability, engagement, and conversion metrics.

## Data Sources

- **Resend API**: Real-time webhook events (sent, delivered, opened, clicked, bounced, complained)
- **Notion `campaigns` DB**: Campaign-level rollup metrics
- **Notion `email_sequences` DB**: Per-template performance
- **Notion `email_sends` DB**: Per-lead engagement scores

## Key Metrics

| Metric | Formula | Healthy Range |
|--------|---------|---------------|
| Delivery Rate | delivered / sent × 100 | >98% |
| Open Rate | opened / delivered × 100 | >25% |
| Click Rate | clicked / delivered × 100 | >3% |
| Bounce Rate | bounced / sent × 100 | <2% |
| Reply Rate | replied / delivered × 100 | >1% |
| Invisible Fail | sent − delivered − bounced | 0 ideal |

## Alert Triggers

- Delivery rate drops below 95% → investigate sender reputation
- Bounce rate exceeds 5% → pause campaign, clean list
- Invisible fails exceed 3% → escalate to ORCHESTRATOR
