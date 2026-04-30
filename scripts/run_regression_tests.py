#!/usr/bin/env python3
"""Cross-platform regression test runner.

Usage examples:
  python scripts/run_regression_tests.py
  python scripts/run_regression_tests.py --live-mode always
  python scripts/run_regression_tests.py --live-mode never
  python scripts/run_regression_tests.py --base-url http://localhost:8010
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


def run_cmd(args: list[str], env: dict[str, str] | None = None) -> int:
    proc = subprocess.run(args, env=env)
    return proc.returncode


def is_bff_healthy(base_url: str, timeout_seconds: int = 20) -> bool:
    req = urllib.request.Request(f"{base_url.rstrip('/')}/api/health", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            if resp.status != 200:
                return False
            payload = json.loads(resp.read().decode("utf-8"))
            return payload.get("status") == "ok"
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run regression tests across platforms")
    parser.add_argument(
        "--live-mode",
        choices=["auto", "always", "never"],
        default="auto",
        help="auto: run live tests only when BFF health is reachable; always: force live tests; never: skip live tests",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BFF_BASE_URL", "http://localhost:8010"),
        help="Base URL for BFF API used by live regression tests",
    )
    args = parser.parse_args()

    print("[1/3] Running fast unit regression tests...")
    rc = run_cmd([sys.executable, "-m", "unittest", "tests/test_cache_logic.py", "-v"])
    if rc != 0:
        return rc

    if args.live_mode == "never":
        print("[2/3] Live API regressions disabled (--live-mode never).")
        return 0

    should_run_live = args.live_mode == "always"
    if args.live_mode == "auto":
        print("[2/3] Checking BFF health for live API regressions...")
        should_run_live = is_bff_healthy(args.base_url)
        if not should_run_live:
            print(f"BFF not reachable at {args.base_url}. Skipping live API regressions.")
            return 0

    print("[3/3] Running live API regression tests...")
    env = os.environ.copy()
    env["RUN_LIVE_TESTS"] = "1"
    env["BFF_BASE_URL"] = args.base_url
    rc = run_cmd([sys.executable, "-m", "unittest", "tests/test_bff_api_live.py", "-v"], env=env)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
