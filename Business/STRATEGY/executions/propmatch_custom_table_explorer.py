#!/usr/bin/env python3
"""
PropFirmMatch Custom Table Explorer — Strategy Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Promoted from tmp prototypes to support manual login and Customize-column
discovery before scraper/schema updates.
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT_DIR = os.path.join(WORKSPACE, 'Business', 'STRATEGY', 'resources', 'PropFirmMatchExploration')
PROFILE_DIR = os.path.join(WORKSPACE, 'tmp', 'pw_profile_propmatch_custom_table')
CHALLENGES_URL = 'https://propfirmmatch.com/prop-firm-challenges'


def ensure_dirs() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PROFILE_DIR, exist_ok=True)


def wait_load(page, timeout: int = 20000) -> None:
    try:
        page.wait_for_function(
            'document.querySelectorAll(".animate-pulse").length === 0',
            timeout=timeout,
        )
    except Exception:
        pass
    time.sleep(2)


def screenshot(page, name: str) -> str:
    path = os.path.join(OUT_DIR, f'custom_{name}.png')
    page.screenshot(path=path, full_page=False)
    return os.path.basename(path)


def get_table_headers(page) -> list[str]:
    headers: list[str] = []
    for header in page.query_selector_all('table th'):
        try:
            headers.append(header.inner_text().strip())
        except Exception:
            headers.append('')
    return headers


def find_customize_button(page):
    for selector in [
        'button:has-text("Customize")',
        'a:has-text("Customize")',
        'button:has-text("Custom")',
        'button:has-text("Columns")',
        'button:has-text("Edit Columns")',
    ]:
        try:
            button = page.query_selector(selector)
        except Exception:
            button = None
        if button:
            return selector, button
    return None, None


def action_run(_: argparse.Namespace) -> None:
    from playwright.sync_api import sync_playwright

    ensure_dirs()
    result = {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'headers_before': [],
        'headers_after': [],
        'customize_found': False,
        'customize_selector': None,
        'panel_lines': [],
        'switches': [],
        'screenshots': [],
    }

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
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

        try:
            page.goto(CHALLENGES_URL, wait_until='domcontentloaded', timeout=30000)
            wait_load(page)
            result['screenshots'].append(screenshot(page, '00_initial_page'))

            login_button = None
            for selector in ['a:has-text("Log in")', 'button:has-text("Log in")', 'a[href*="login"]']:
                try:
                    login_button = page.query_selector(selector)
                except Exception:
                    login_button = None
                if login_button:
                    login_button.click()
                    time.sleep(3)
                    result['screenshots'].append(screenshot(page, '01_login_modal'))
                    break

            print('Complete Google login in the browser window if prompted. Waiting up to 180 seconds...')

            for _ in range(90):
                time.sleep(2)
                if 'propfirmmatch.com' not in page.url:
                    continue
                login_cta = page.query_selector('a:has-text("Log in"), button:has-text("Log in")')
                if not login_cta:
                    break

            page.goto(CHALLENGES_URL, wait_until='domcontentloaded', timeout=30000)
            wait_load(page)
            try:
                page.wait_for_selector('table th', timeout=15000)
            except Exception:
                time.sleep(5)

            result['headers_before'] = get_table_headers(page)

            selector, customize_btn = find_customize_button(page)
            result['customize_selector'] = selector
            result['customize_found'] = customize_btn is not None

            if customize_btn:
                customize_btn.click()
                time.sleep(3)
                result['screenshots'].append(screenshot(page, '02_customize_opened'))

                panel_text = ''
                for sel in [
                    '[role="dialog"]',
                    '[class*="modal"]',
                    '[class*="drawer"]',
                    '[class*="sidebar"]',
                    '[class*="panel"]',
                    '[class*="popover"]',
                    '[data-state="open"]',
                ]:
                    try:
                        for panel in page.query_selector_all(sel):
                            text = panel.inner_text().strip()
                            if len(text) > len(panel_text):
                                panel_text = text
                    except Exception:
                        continue

                if panel_text:
                    result['panel_lines'] = [line.strip() for line in panel_text.split('\n') if line.strip()][:200]

                switches = []
                for sel in ['[role="switch"]', 'input[type="checkbox"]', '[class*="toggle"]', '[class*="switch"]']:
                    try:
                        elements = page.query_selector_all(sel)
                    except Exception:
                        elements = []
                    for element in elements[:60]:
                        try:
                            parent = element.query_selector('xpath=..')
                            label = parent.inner_text().strip()[:120] if parent else ''
                        except Exception:
                            label = ''
                        switches.append({
                            'selector': sel,
                            'label': label,
                            'aria_checked': element.get_attribute('aria-checked') or '',
                            'data_state': element.get_attribute('data-state') or '',
                        })
                result['switches'] = switches

                try:
                    page.keyboard.press('Escape')
                    time.sleep(1)
                except Exception:
                    pass

            result['headers_after'] = get_table_headers(page)
            result['screenshots'].append(screenshot(page, '03_post_customize_state'))
        finally:
            context.close()

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(OUT_DIR, f'propmatch_custom_table_{timestamp}.json')
    with open(output_path, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)

    print(f'Saved custom table exploration to {output_path}')


def main() -> None:
    parser = argparse.ArgumentParser(description='PropFirmMatch Custom Table Explorer — Strategy Agent')
    parser.add_argument('--action', required=True, choices=['run'])
    args = parser.parse_args()
    action_run(args)


if __name__ == '__main__':
    main()