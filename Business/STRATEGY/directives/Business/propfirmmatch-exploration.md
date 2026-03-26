---
name: propfirmmatch-exploration
description: |
  Explores PropFirmMatch as a research surface before scraper development or
  refresh work. Use when Strategy needs to map pages, inspect filter behavior,
  validate table schemas, or discover hidden/custom columns that affect
  downstream PropMatch scraping and hedge modelling.
---

# PropFirmMatch Exploration

## Objective

Turn PropFirmMatch exploration into a repeatable Strategy skill. This skill maps
the site, captures page structures and screenshots, tests filter behavior, and
documents custom-table column availability before scraper updates or prop-firm
economics analysis.

## When to Use This Skill

- When PropMatch selectors break and the scraper needs fresh reconnaissance
- When a new PropMatch page or comparison surface should be incorporated into Strategy
- When Strategy needs evidence for how filters, pagination, and table schemas actually behave
- When custom-table columns like drawdown type or platforms may exist behind login
- When hedge-arbitrage modelling depends on fields that are not yet reliably scraped

## Execution Sequence

### Phase 1: Surface Mapping

**Script**: `executions/propmatch_site_explorer.py --action surface-map`

1. Open core PropFirmMatch surfaces in Chromium
2. Capture screenshots, page text, and lightweight table/button metadata
3. Persist a reusable site map snapshot into `resources/PropFirmMatchExploration/`

### Phase 2: Filter Matrix Discovery

**Script**: `executions/propmatch_site_explorer.py --action filter-matrix`

1. Re-open the main challenges table
2. Test Size, Steps, and Assets filters one option at a time
3. Record whether the interaction succeeds and how many rows remain visible
4. Save screenshots and a filter matrix JSON for scraper planning

### Phase 3: Deep Discovery

**Script**: `executions/propmatch_deep_explorer.py --action run`

1. Inspect pagination links and challenge table schemas
2. Sample firm-detail pages, rules pages, futures pages, and adjacent research surfaces
3. Save structured findings and text dumps for deeper selector or schema work

### Phase 4: Custom Table Discovery

**Script**: `executions/propmatch_custom_table_explorer.py --action run`

1. Use a persistent Playwright profile in `tmp/` for manual Google login if needed
2. Load the challenge table and locate the Customize/Columns control
3. Capture panel text, switches, and pre/post header states
4. Save the findings JSON and screenshots for future scraper upgrades

## Outputs

- `resources/PropFirmMatchExploration/propmatch_site_map.latest.json`
- `resources/PropFirmMatchExploration/propmatch_site_map_{timestamp}.json`
- `resources/PropFirmMatchExploration/propmatch_filter_matrix_{timestamp}.json`
- `resources/PropFirmMatchExploration/propmatch_deep_exploration_{timestamp}.json`
- `resources/PropFirmMatchExploration/propmatch_custom_table_{timestamp}.json`
- Supporting screenshots, page text dumps, and structure snapshots

## Relation To Hedge Arbitrage

Use this skill before changing `executions/propmatch_scraper.py` or when the
hedge-arbitrage pipeline needs new fields. Exploration de-risks scraper changes;
the hedge-arbitrage skill turns the scraped data into economics and rankings.

## Definition of Done

- [ ] Current PropFirmMatch surfaces are mapped into a reusable JSON snapshot
- [ ] Challenge filter behavior is documented with screenshots and row counts
- [ ] At least one deep exploration snapshot covers pagination, rules, firm pages, and adjacent surfaces
- [ ] Customize-table availability is captured with panel evidence or a documented failure mode
- [ ] Outputs are saved under `resources/PropFirmMatchExploration/` and usable for scraper maintenance