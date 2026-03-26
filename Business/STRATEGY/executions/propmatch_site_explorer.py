#!/usr/bin/env python3
"""
PropFirmMatch Site Explorer — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maps PropFirmMatch surfaces, captures page structure, and explores challenge
filter states before scraper work.

Actions:
  --action surface-map   Crawl known PropFirmMatch surfaces and save a site map
  --action filter-matrix Explore challenge filter states and capture evidence
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT_DIR = os.path.join(WORKSPACE, 'Business', 'STRATEGY', 'resources', 'PropFirmMatchExploration')

PAGES = {
    'home': 'https://propfirmmatch.com/',
    'challenges': 'https://propfirmmatch.com/prop-firm-challenges#table-scroll-target',
    'best_sellers': 'https://propfirmmatch.com/best-sellers?type=all',
    'all_firms': 'https://propfirmmatch.com/all-prop-firms?tab=all',
    'rules': 'https://propfirmmatch.com/prop-firm-rules',
    'rule_changes': 'https://propfirmmatch.com/prop-firm-rule-changes',
    'ea_copy_platforms': 'https://propfirmmatch.com/prop-firm-ea-copy-trading-platforms',
    'payouts': 'https://propfirmmatch.com/payouts',
    'spreads': 'https://propfirmmatch.com/prop-firm-spreads',
    'reviews': 'https://propfirmmatch.com/prop-firm-reviews',
    'futures': 'https://propfirmmatch.com/futures/prop-firm-challenges',
}


def ensure_out_dir() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)


def wait_for_content(page, timeout: int = 20000) -> None:
    try:
        page.wait_for_function(
            'document.querySelectorAll(".animate-pulse").length === 0',
            timeout=timeout,
        )
    except Exception:
        pass

    try:
        page.wait_for_load_state('networkidle', timeout=5000)
    except Exception:
        pass

    time.sleep(1.5)


def screenshot(page, name: str, full_page: bool = True) -> str:
    path = os.path.join(OUT_DIR, f'{name}.png')
    page.screenshot(path=path, full_page=full_page)
    return os.path.basename(path)


def dump_text(page, name: str, max_chars: int = 50000) -> str:
    text = page.inner_text('body')[:max_chars]
    path = os.path.join(OUT_DIR, f'{name}.txt')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)
    return os.path.basename(path)


def dump_structure(page, name: str) -> dict:
    structure: dict[str, object] = {
        'title': page.title(),
        'table_rows': len(page.query_selector_all('table tbody tr')),
        'pagination_links': len(page.query_selector_all('a[href*="page="]')),
        'button_count': len(page.query_selector_all('button')),
        'select_count': len(page.query_selector_all('select')),
        'internal_links': len(page.query_selector_all('a[href*="propfirmmatch.com"], a[href^="/"]')),
    }

    button_texts: list[str] = []
    for button in page.query_selector_all('button')[:40]:
        try:
            text = button.inner_text().strip()
        except Exception:
            text = ''
        if text:
            button_texts.append(text[:80])
    structure['button_texts'] = button_texts

    tables: list[dict[str, object]] = []
    for table in page.query_selector_all('table')[:3]:
        headers = []
        for header in table.query_selector_all('th'):
            try:
                headers.append(header.inner_text().strip())
            except Exception:
                headers.append('')
        tables.append({
            'headers': headers,
            'rows': len(table.query_selector_all('tbody tr')),
        })
    structure['tables'] = tables

    path = os.path.join(OUT_DIR, f'{name}_structure.json')
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(structure, handle, indent=2, ensure_ascii=False)
    return structure


def click_filter_option(page, filter_name: str, option_text: str) -> bool:
    filter_btn = None
    for selector in [
        f'button:has-text("{filter_name}")',
        f'[class*="filter"]:has-text("{filter_name}")',
        f'text="{filter_name}"',
    ]:
        try:
            filter_btn = page.query_selector(selector)
        except Exception:
            filter_btn = None
        if filter_btn:
            break

    if not filter_btn:
        return False

    try:
        filter_btn.click()
        time.sleep(0.75)
    except Exception:
        return False

    for selector in [
        f'button:has-text("{option_text}")',
        f'[role="option"]:has-text("{option_text}")',
        f'text="{option_text}"',
        f'label:has-text("{option_text}")',
    ]:
        try:
            option = page.query_selector(selector)
        except Exception:
            option = None
        if not option:
            continue

        try:
            option.click()
            wait_for_content(page)
            return True
        except Exception:
            continue
    return False


def launch_page(pw):
    browser = pw.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled'],
    )
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
    )
    page = context.new_page()
    page.add_init_script(
        'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    )
    return browser, context, page


def action_surface_map(_: argparse.Namespace) -> None:
    from playwright.sync_api import sync_playwright

    ensure_out_dir()
    summary = {
        'explored_at': datetime.now(timezone.utc).isoformat(),
        'pages': {},
    }

    with sync_playwright() as pw:
        browser, context, page = launch_page(pw)
        try:
            for name, url in PAGES.items():
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                wait_for_content(page)
                structure = dump_structure(page, name)
                summary['pages'][name] = {
                    'url': page.url,
                    'title': page.title(),
                    'table_rows': structure['table_rows'],
                    'pagination_links': structure['pagination_links'],
                    'button_count': structure['button_count'],
                    'select_count': structure['select_count'],
                    'internal_links': structure['internal_links'],
                    'button_texts': structure['button_texts'],
                    'tables': structure['tables'],
                    'text_dump': dump_text(page, name),
                    'screenshot': screenshot(page, name),
                }
        finally:
            context.close()
            browser.close()

    latest_path = os.path.join(OUT_DIR, 'propmatch_site_map.latest.json')
    with open(latest_path, 'w', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    snapshot_path = os.path.join(OUT_DIR, f'propmatch_site_map_{timestamp}.json')
    with open(snapshot_path, 'w', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(f'Saved site map to {snapshot_path}')


def action_filter_matrix(_: argparse.Namespace) -> None:
    from playwright.sync_api import sync_playwright

    ensure_out_dir()
    findings = {
        'explored_at': datetime.now(timezone.utc).isoformat(),
        'url': PAGES['challenges'],
        'filters': {
            'sizes': {},
            'steps': {},
            'assets': {},
        },
    }

    sizes = ['$5K', '$10K', '$25K', '$50K', '$100K', '$200K', '$300K', '$500K']
    steps = ['1 Step', '2 Steps', '3 Steps', 'Instant']
    assets = ['FX', 'Crypto', 'Indices', 'Stocks', 'Commodities', 'All']

    with sync_playwright() as pw:
        browser, context, page = launch_page(pw)
        try:
            for group_name, options in [('sizes', sizes), ('steps', steps), ('assets', assets)]:
                filter_name = 'Size' if group_name == 'sizes' else 'Steps' if group_name == 'steps' else 'Assets'
                for option in options:
                    page.goto(PAGES['challenges'], wait_until='domcontentloaded', timeout=30000)
                    wait_for_content(page)
                    success = click_filter_option(page, filter_name, option)
                    findings['filters'][group_name][option] = {
                        'success': success,
                        'visible_rows': len(page.query_selector_all('table tbody tr')),
                        'screenshot': screenshot(
                            page,
                            f'filter_{group_name}_{option.replace("$", "").replace(" ", "_").lower()}',
                            full_page=False,
                        ),
                    }
        finally:
            context.close()
            browser.close()

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(OUT_DIR, f'propmatch_filter_matrix_{timestamp}.json')
    with open(output_path, 'w', encoding='utf-8') as handle:
        json.dump(findings, handle, indent=2, ensure_ascii=False)

    print(f'Saved filter matrix to {output_path}')


ACTIONS = {
    'surface-map': action_surface_map,
    'filter-matrix': action_filter_matrix,
}


def main() -> None:
    parser = argparse.ArgumentParser(description='PropFirmMatch Site Explorer — Strategy Agent')
    parser.add_argument('--action', required=True, choices=sorted(ACTIONS.keys()))
    args = parser.parse_args()
    ACTIONS[args.action](args)


if __name__ == '__main__':
    main()