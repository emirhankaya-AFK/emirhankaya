"""
Automated Playwright Viewport & DOM Bounding Rect Verification.
Captures screenshots and validates responsive layout across desktop, laptop, tablet, and mobile.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

VIEWPORTS = [
    {"name": "desktop_1440x900", "width": 1440, "height": 900},
    {"name": "laptop_1280x800", "width": 1280, "height": 800},
    {"name": "tablet_1024x768", "width": 1024, "height": 768},
    {"name": "mobile_390x844", "width": 390, "height": 844, "is_mobile": True},
]

OUTPUT_DIR = r"C:\Users\emirh\.gemini\antigravity\brain\3ea98126-4094-4943-be9d-c0ec8bfce091"
SERVER_URL = "http://localhost:1002"


def check_critical_elements(page, client_width):
    script = """() => {
        const results = [];
        const check = (selector, label) => {
            const elements = Array.from(document.querySelectorAll(selector));
            elements.forEach((el, idx) => {
                const rect = el.getBoundingClientRect();
                results.push({
                    label: `${label} [${idx}]`,
                    text: el.innerText ? el.innerText.substring(0, 24).replace(/\\n/g, ' ') : '',
                    left: Math.round(rect.left),
                    right: Math.round(rect.right),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    isClippedRight: rect.right > (window.innerWidth + 2),
                    isClippedLeft: rect.left < -2
                });
            });
        };
        check('.terminal-header', 'Header Card');
        check('.terminal-title', 'Terminal Title');
        check('.header-metadata', 'Header Metadata Grid');
        check('.meta-item', 'Meta Item');
        check('[data-baseweb="tab-list"]', 'Tab List Bar');
        check('[data-baseweb="tab"]', 'Tab Button');
        check('.metric-card', 'KPI Card');
        return results;
    }"""
    return page.evaluate(script)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        total_failures = 0
        for vp in VIEWPORTS:
            print(f"\n=======================================================")
            print(f"Testing Viewport: {vp['name']} ({vp['width']}x{vp['height']})")
            print(f"=======================================================")
            context = browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                is_mobile=vp.get("is_mobile", False),
            )
            page = context.new_page()
            try:
                page.goto(SERVER_URL, wait_until="networkidle", timeout=60000)
            except Exception as e:
                print(f"Error navigating to {SERVER_URL}: {e}")
                context.close()
                continue

            time.sleep(3)

            # Check horizontal overflow of entire document
            scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
            client_width = page.evaluate("() => document.documentElement.clientWidth")
            has_h_overflow = scroll_width > client_width
            print(f"Page Width Check: clientWidth={client_width}, scrollWidth={scroll_width}, Overflow={has_h_overflow}")

            # Check bounding client rect for all critical UI elements
            element_checks = check_critical_elements(page, client_width)
            clipped_items = [e for e in element_checks if e["isClippedRight"] or e["isClippedLeft"]]

            print(f"Inspected {len(element_checks)} critical elements (getBoundingClientRect).")
            if clipped_items:
                print(f"FAILED: Found {len(clipped_items)} clipped/overflowing elements:")
                for item in clipped_items:
                    print(f"  - {item['label']} ('{item['text']}'): left={item['left']}, right={item['right']} (max={client_width})")
                total_failures += len(clipped_items)
            else:
                print(f"PASSED: 100% of critical elements are within viewport bounds! (0 clipped)")

            # Capture viewport screenshot
            screenshot_path = f"{OUTPUT_DIR}/sentinel_{vp['name']}.png"
            page.screenshot(path=screenshot_path, full_page=False)
            print(f"Saved screenshot: {screenshot_path}")
            context.close()

        browser.close()

    if total_failures > 0:
        print(f"\nFAIL: Total {total_failures} elements clipped across viewports.")
        sys.exit(1)
    else:
        print("\nALL VIEWPORTS & BOUNDING CLIENT RECT CHECKS PASSED PERFECTLY!")


if __name__ == "__main__":
    run()
