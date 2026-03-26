# PropFirmMatch Exploration

This folder stores outputs from the Strategy PropFirmMatch exploration skill.

## Purpose

Use these artifacts before changing the PropMatch scraper or extending the hedge
arbitrage pipeline. The goal is to preserve a current, inspectable record of:

- What PropFirmMatch surfaces exist
- How filters and pagination behave
- What table schemas appear on each surface
- Whether login-only custom columns are available

## Seed Artifacts Promoted From `tmp/`

- `propmatch_site_map.seed.json` — initial site map snapshot promoted from tmp

## Generated Artifacts

- `propmatch_site_map.latest.json`
- `propmatch_site_map_{timestamp}.json`
- `propmatch_filter_matrix_{timestamp}.json`
- `propmatch_deep_exploration_{timestamp}.json`
- `propmatch_custom_table_{timestamp}.json`
- Supporting screenshots, text dumps, and structure JSON files

## Notes

- Persistent Playwright login profiles remain in `tmp/` because they are transient working state, not Strategy resources.
- Long-lived research artifacts belong here, not in `tmp/`.