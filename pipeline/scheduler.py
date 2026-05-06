"""
Background scheduler for destn.ai
Runs probe bot M-F between 11:00-11:59 UTC (7am ET)
Runs GA4 sync M-F between 12:00-12:59 UTC (8am ET)
Checks once per hour — restarts cleanly on container reboot.
"""

import os
import subprocess
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", "/app/data/traffic.db"))
WORKDIR  = Path("/app")


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _utc_hour():
    return datetime.now(timezone.utc).hour


def _weekday():
    """0=Mon … 4=Fri, 5=Sat, 6=Sun"""
    return datetime.now(timezone.utc).weekday()


def probe_already_ran() -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute(
            "SELECT COUNT(*) FROM probe_runs WHERE run_date = ?", (_today(),)
        ).fetchone()[0]
        conn.close()
        return count >= 30
    except Exception:
        return False


def run_probe():
    print(f"[scheduler] Starting probe bot at {datetime.now(timezone.utc).isoformat()}", flush=True)
    result = subprocess.run(
        ["python", "pipeline/probe_bot.py"],
        cwd=str(WORKDIR),
    )
    print(f"[scheduler] Probe bot finished (exit {result.returncode})", flush=True)


def run_ga4():
    print(f"[scheduler] Starting GA4 sync at {datetime.now(timezone.utc).isoformat()}", flush=True)
    result = subprocess.run(
        ["python", "pipeline/ga4_client.py"],
        cwd=str(WORKDIR),
    )
    print(f"[scheduler] GA4 sync finished (exit {result.returncode})", flush=True)


def main():
    print("[scheduler] Started — checking every 30 minutes", flush=True)
    _probe_ran_today = False
    _ga4_ran_today   = False
    _last_date       = _today()

    while True:
        now_date = _today()

        # Reset flags on new day
        if now_date != _last_date:
            _probe_ran_today = False
            _ga4_ran_today   = False
            _last_date       = now_date

        hour    = _utc_hour()
        weekday = _weekday()
        is_weekday = weekday < 5  # Mon–Fri

        # Probe bot: 11am UTC (7am ET) on weekdays
        if is_weekday and hour == 11 and not _probe_ran_today:
            if not probe_already_ran():
                run_probe()
            _probe_ran_today = True

        # GA4 sync: 12pm UTC (8am ET) on weekdays
        if is_weekday and hour == 12 and not _ga4_ran_today:
            run_ga4()
            _ga4_ran_today = True

        time.sleep(1800)  # check every 30 minutes


if __name__ == "__main__":
    main()
