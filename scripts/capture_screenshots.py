"""
Capture screenshots of the running OSS Assurance Web Console.
Usage:  python scripts/capture_screenshots.py
Requires: playwright (pip install playwright && python -m playwright install chromium)
App must be running on http://localhost:8080 / http://localhost:8010
"""

import os
import time
import json
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

OUT_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

UI_URL  = "http://localhost:8080"
BFF_URL = "http://localhost:8010"

SAMPLE_LOGS = (
    "2026-04-29T10:00:00,ERROR,BILLING_SYSTEM,Database connection timeout\n"
    "2026-04-29T10:00:03,ERROR,BILLING_SYSTEM,Failed to update CDR record\n"
    "2026-04-29T10:00:06,WARN,NETWORK_MONITOR,Packet loss detected on NE-07\n"
    "2026-04-29T10:00:09,ERROR,BILLING_SYSTEM,Retry limit exceeded – CDR dropped\n"
    "2026-04-29T10:00:12,ERROR,SERVICE_ASSURANCE,SLA timer expired – ticket auto-escalated\n"
    "2026-04-29T10:00:15,WARN,NETWORK_MONITOR,High latency on backhaul link BH-04\n"
    "2026-04-29T10:00:18,INFO,PROVISIONING,Network element NE-07 registered\n"
)

def take(page, name: str, full_page: bool = False):
    path = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    print(f"  saved: {path.name}")
    return path


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2,         # retina quality
        )
        page = ctx.new_page()

        # ── 1. Landing page (empty state) ───────────────────────
        print("[1] Landing page …")
        page.goto(UI_URL, wait_until="networkidle")
        time.sleep(0.5)
        take(page, "01_landing_page")

        # ── 2. Logs pasted, ready to analyze ────────────────────
        print("[2] Paste logs …")
        page.fill("#rawLogs", SAMPLE_LOGS)
        time.sleep(0.3)
        take(page, "02_logs_pasted")

        # ── 3. Click Analyze & Index, wait for session badge ────
        print("[3] Analyze & Index …")
        page.click("#analyzeBtn")
        try:
            page.wait_for_selector("#sessionBadge .badge-ok", timeout=60_000)
        except PWTimeout:
            page.wait_for_selector("#analyzeOutput.visible", timeout=60_000)
        time.sleep(0.8)
        take(page, "03_analyze_complete", full_page=True)

        # ── 4. First chat question (fresh LLM response) ─────────
        print("[4] First question …")
        page.fill("#question", "What abnormal behavior do you see in these logs?")
        page.click("#askBtn")
        try:
            page.wait_for_selector(".cache-indicator", timeout=90_000)
        except PWTimeout:
            time.sleep(5)
        time.sleep(0.8)
        take(page, "04_chat_fresh_response", full_page=True)

        # ── 5. Same question again → exact cache hit ────────────
        print("[5] Exact cache hit …")
        page.fill("#question", "What abnormal behavior do you see in these logs?")
        page.click("#askBtn")
        try:
            page.wait_for_selector(".cache-indicator-hit", timeout=30_000)
        except PWTimeout:
            time.sleep(3)
        time.sleep(0.5)
        take(page, "05_chat_exact_cache_hit", full_page=True)

        # ── 6. Paraphrased question → similar cache hit ──────────
        print("[6] Similar / intent cache hit …")
        page.fill("#question", "What anomalies are present in the log output?")
        page.click("#askBtn")
        try:
            page.wait_for_selector(".cache-indicator-similar", timeout=60_000)
        except PWTimeout:
            time.sleep(5)
        time.sleep(0.5)
        take(page, "06_chat_similar_cache_hit", full_page=True)

        # ── 7. Full page scroll – showing metrics badge ──────────
        print("[7] Full page metrics view …")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.4)
        take(page, "07_token_cost_metrics", full_page=True)

        browser.close()

    print(f"\nDone — {len(list(OUT_DIR.glob('*.png')))} screenshots saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
