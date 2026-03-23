# Web Analytics

> GA4 setup, pageview tracking, event tracking, and conversion configuration.

## GA4 Property

- **Property**: Hedge Edge website (hedgedge.info)
- **Client**: `shared/google_analytics_client.py`
- **Config**: `Business/ANALYTICS/executions/web_analytics/ga4_config.py`

## Tracked Events

| Event | Trigger | Conversion? |
|-------|---------|------------|
| `page_view` | Every page load | No |
| `sign_up` | Account creation | Yes |
| `beta_claim` | Beta key claimed | Yes |
| `checkout_start` | Creem.io checkout initiated | Yes |
| `purchase` | Subscription activated | Yes |
| `cta_click` | CTA button clicked | No |
| `form_submit` | Any form submission | No |

## Reporting

- Daily summary via `get_daily_website_summary()`
- Traffic sources, top pages, device/geo breakdowns
- UTM campaign attribution linked to conversion events
