#!/usr/bin/env python3
"""
PropFirmMatch Deep Explorer — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Runs deeper PropFirmMatch discovery across pagination, challenge filters,
firm-detail pages, and rules surfaces.
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT_DIR = os.path.join(WORKSPACE, 'Business', 'STRATEGY', 'resources', 'PropFirmMatchExploration')


def ensure_out_dir() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)


def wait_load(page, timeout: int = 15000) -> None:
    try:
        page.wait_for_function(
            'document.querySelectorAll(".animate-pulse").length === 0',
            timeout=timeout,
        )
    except Exception:
        pass
    time.sleep(1.5)


def screenshot(page, name: str, full_page: bool = True) -> str:
    path = os.path.join(OUT_DIR, f'{name}.png')
    page.screenshot(path=path, full_page=full_page)
    return os.path.basename(path)


def dump_text(page, name: str, max_chars: int = 80000) -> str:
    text = page.inner_text('body')[:max_chars]
    path = os.path.join(OUT_DIR, f'{name}.txt')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)
    return os.path.basename(path)


def count_table_rows(page) -> int:
    return len(page.query_selector_all('table tbody tr'))


def get_challenge_header_count(page) -> int | None:
    try:
        body = page.inner_text('body')
    except Exception:
        return None

    match = re.search(r'Challenges\s+(\d+)', body)
    return int(match.group(1)) if match else None


def extract_table_data(page) -> dict:
    tables = page.query_selector_all('table')
    if not tables:
        return {'tables': 0}

    result: dict[str, object] = {'tables': len(tables)}
    for index, table in enumerate(tables[:3]):
        headers = []
        for header in table.query_selector_all('th'):
            try:
                headers.append(header.inner_text().strip())
            except Exception:
                headers.append('')

        rows = table.query_selector_all('tbody tr')
        samples: list[list[str]] = []
        for row in rows[:2]:
            cells = []
            for cell in row.query_selector_all('td'):
                try:
                    cells.append(cell.inner_text().strip()[:100])
                except Exception:
                    cells.append('')
            samples.append(cells)

        result[f'table_{index}_headers'] = headers
        result[f'table_{index}_row_count'] = len(rows)
        result[f'table_{index}_samples'] = samples
    return result


def click_filter(page, filter_name: str, option_text: str) -> bool:
    for selector in [
        f'button:has-text("{filter_name}")',
        f'[class*="filter"]:has-text("{filter_name}")',
        f'div:has-text("{filter_name}") >> button',
    ]:
        try:
            filter_btn = page.query_selector(selector)
        except Exception:
            filter_btn = None
        if not filter_btn:
            continue
        try:
            filter_btn.click()
            time.sleep(0.5)
            break
        except Exception:
            continue

    for selector in [
        f'button:has-text("{option_text}")',
        f'text="{option_text}"',
        f'[role="option"]:has-text("{option_text}")',
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
            wait_load(page)
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
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        viewport={'width': 1920, 'height': 1080},
    )
    page = context.new_page()
    page.add_init_script(
        'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    )
    return browser, context, page


def action_run(_: argparse.Namespace) -> None:
    from playwright.sync_api import sync_playwright

    ensure_out_dir()

    findings = {
        'explored_at': datetime.now(timezone.utc).isoformat(),
        'challenge_filters': {},
        'pagination': {},
        'rules': {},
        'firm_details': {},
        'other_pages': {},
    }

    with sync_playwright() as pw:
        browser, context, page = launch_page(pw)
        try:
            challenges_url = 'https://propfirmmatch.com/prop-firm-challenges#table-scroll-target'
            page.goto(challenges_url, wait_until='domcontentloaded', timeout=30000)
            wait_load(page)

            findings['challenge_filters']['default'] = {
                'header_count': get_challenge_header_count(page),
                'visible_rows': count_table_rows(page),
                'table_schema': extract_table_data(page),
                'screenshot': screenshot(page, 'deep_01_challenges_default', full_page=False),
            }

            sizes = ['$5K', '$10K', '$25K', '$50K', '$100K', '$200K', '$300K', '$500K']
            findings['challenge_filters']['sizes'] = {}
            for size in sizes:
                page.goto(challenges_url, wait_until='domcontentloaded', timeout=30000)
                wait_load(page)
                success = click_filter(page, 'Size', size)
                findings['challenge_filters']['sizes'][size] = {
                    'success': success,
                    'header_count': get_challenge_header_count(page),
                    'visible_rows': count_table_rows(page),
                }

            findings['challenge_filters']['steps'] = {}
            for step in ['1 Step', '2 Steps', '3 Steps', 'Instant']:
                page.goto(challenges_url, wait_until='domcontentloaded', timeout=30000)
                wait_load(page)
                success = click_filter(page, 'Steps', step)
                findings['challenge_filters']['steps'][step] = {
                    'success': success,
                    'header_count': get_challenge_header_count(page),
                    'visible_rows': count_table_rows(page),
                }

            page.goto(challenges_url, wait_until='domcontentloaded', timeout=30000)
            wait_load(page)
            pagination_links = []
            for link in page.query_selector_all('a[href*="page="]'):
                href = link.get_attribute('href') or ''
                if href and href not in pagination_links:
                    pagination_links.append(href)
            findings['pagination'] = {
                'links': pagination_links,
                'count': len(pagination_links),
            }

            rules_url = 'https://propfirmmatch.com/prop-firm-rules'
            page.goto(rules_url, wait_until='domcontentloaded', timeout=30000)
            wait_load(page)
            findings['rules'] = {
                'visible_rows': count_table_rows(page),
                'structure': extract_table_data(page),
                'text_dump': dump_text(page, 'deep_rules_page'),
                'screenshot': screenshot(page, 'deep_rules_page'),
            }

            firms = {
                'the5ers': 'https://propfirmmatch.com/prop-firms/the-5-ers',
                'fundednext': 'https://propfirmmatch.com/prop-firms/fundednext',
                'ftmo': 'https://propfirmmatch.com/prop-firms/ftmo',
            }
            for name, url in firms.items():
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                wait_load(page)
                findings['firm_details'][name] = {
                    'url': page.url,
                    'title': page.title(),
                    'table_schema': extract_table_data(page),
                    'text_dump': dump_text(page, f'firm_{name}'),
                    'screenshot': screenshot(page, f'firm_{name}'),
                }

            other_pages = {
                'ea_copy_platforms': 'https://propfirmmatch.com/prop-firm-ea-copy-trading-platforms',
                'spreads': 'https://propfirmmatch.com/prop-firm-spreads',
                'payouts': 'https://propfirmmatch.com/payouts',
                'futures': 'https://propfirmmatch.com/futures/prop-firm-challenges',
            }
            for name, url in other_pages.items():
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                wait_load(page)
                findings['other_pages'][name] = {
                    'url': page.url,
                    'title': page.title(),
                    'visible_rows': count_table_rows(page),
                    'table_schema': extract_table_data(page),
                    'screenshot': screenshot(page, f'other_{name}'),
                }
        finally:
            context.close()
            browser.close()

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(OUT_DIR, f'propmatch_deep_exploration_{timestamp}.json')
    with open(output_path, 'w', encoding='utf-8') as handle:
        json.dump(findings, handle, indent=2, ensure_ascii=False)

    print(f'Saved deep exploration to {output_path}')


def main() -> None:
    parser = argparse.ArgumentParser(description='PropFirmMatch Deep Explorer — Strategy Agent')
    parser.add_argument('--action', required=True, choices=['run'])
    args = parser.parse_args()
    action_run(args)


if __name__ == '__main__':
    main()