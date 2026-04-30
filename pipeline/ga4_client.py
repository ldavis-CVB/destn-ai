"""
GA4 Data API client — pulls session/referral data and stores it locally.
Requires: google-analytics-data python package + service account JSON key.

Auth priority (first match wins):
  1. GA4_CREDENTIALS_PATH  — path to a service account JSON already on disk
  2. GA4_CREDENTIALS_B64   — base64-encoded service account JSON (Railway env var)
  3. OAuth token            — local dev fallback via oauth_setup.py
"""

import os
import base64
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    FilterExpression,
    Filter,
    FilterExpressionList,
)
from ai_sources import get_all_domains, classify_referrer

DB_PATH = Path(__file__).parent.parent / "data" / "traffic.db"


def get_client() -> BetaAnalyticsDataClient:
    """Return an authenticated GA4 client, preferring service account over OAuth."""
    creds_path = os.getenv("GA4_CREDENTIALS_PATH")

    # If not set, try decoding the base64 env var (Railway)
    if not creds_path:
        b64 = os.getenv("GA4_CREDENTIALS_B64")
        if b64:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            tmp.write(base64.b64decode(b64))
            tmp.close()
            creds_path = tmp.name
            os.environ["GA4_CREDENTIALS_PATH"] = creds_path  # cache for this process

    if creds_path and Path(creds_path).exists():
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
        print(f"  Using service account: {creds_path}")
    else:
        # Local dev fallback — requires interactive OAuth setup
        from oauth_setup import get_oauth_credentials
        creds = get_oauth_credentials()
        print("  Using OAuth credentials (local dev)")

    return BetaAnalyticsDataClient(credentials=creds)


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            source_domain TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_category TEXT NOT NULL,
            country TEXT,
            region TEXT,
            city TEXT,
            landing_page TEXT,
            sessions INTEGER DEFAULT 0,
            engaged_sessions INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            fetched_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            total_ai_sessions INTEGER DEFAULT 0,
            total_sessions INTEGER DEFAULT 0,
            ai_share_pct REAL DEFAULT 0,
            fetched_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON ai_traffic(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON ai_traffic(source_name)")
    conn.commit()
    conn.close()


def fetch_ai_traffic(
    client: BetaAnalyticsDataClient,
    property_id: str,
    start_date: str = "30daysAgo",
    end_date: str = "today",
    conversion_event: str = "generate_lead",
):
    """Pull session-level data filtered to known AI referrers."""
    domains = get_all_domains()

    # Build OR filter across all AI domains
    domain_filters = [
        Filter(
            field_name="sessionSource",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.CONTAINS,
                value=domain,
            ),
        )
        for domain in domains
    ]

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[
            Dimension(name="date"),
            Dimension(name="sessionSource"),
            Dimension(name="country"),
            Dimension(name="region"),
            Dimension(name="city"),
            Dimension(name="landingPage"),
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="conversions"),
        ],
        dimension_filter=FilterExpression(
            or_group=FilterExpressionList(expressions=[
                FilterExpression(filter=f) for f in domain_filters
            ])
        ),
        limit=10000,
    )

    response = client.run_report(request)
    rows = []
    for row in response.rows:
        dims = [d.value for d in row.dimension_values]
        mets = [m.value for m in row.metric_values]
        source_info = classify_referrer(dims[1])
        if not source_info:
            continue
        rows.append({
            "date": dims[0],
            "source_domain": dims[1],
            "source_name": source_info["name"],
            "source_category": source_info["category"],
            "country": dims[2],
            "region": dims[3],
            "city": dims[4],
            "landing_page": dims[5],
            "sessions": int(mets[0]),
            "engaged_sessions": int(mets[1]),
            "conversions": int(float(mets[2])),
        })
    return rows


def fetch_total_sessions(
    client: BetaAnalyticsDataClient,
    property_id: str,
    start_date: str = "30daysAgo",
    end_date: str = "today",
):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="sessions")],
        limit=400,
    )
    response = client.run_report(request)
    return {
        row.dimension_values[0].value: int(row.metric_values[0].value)
        for row in response.rows
    }


def store_results(rows: list[dict], total_by_date: dict):
    conn = sqlite3.connect(DB_PATH)
    fetched_at = datetime.utcnow().isoformat()

    # Clear existing data for the date range being refreshed
    if rows:
        dates = {r["date"] for r in rows}
        placeholders = ",".join("?" * len(dates))
        conn.execute(f"DELETE FROM ai_traffic WHERE date IN ({placeholders})", list(dates))

    conn.executemany("""
        INSERT INTO ai_traffic
            (date, source_domain, source_name, source_category, country, region, city,
             landing_page, sessions, engaged_sessions, conversions, fetched_at)
        VALUES
            (:date, :source_domain, :source_name, :source_category, :country, :region, :city,
             :landing_page, :sessions, :engaged_sessions, :conversions, :fetched_at)
    """, [{**r, "fetched_at": fetched_at} for r in rows])

    # Compute per-date AI totals vs overall
    ai_by_date: dict[str, int] = {}
    for r in rows:
        ai_by_date[r["date"]] = ai_by_date.get(r["date"], 0) + r["sessions"]

    summary_rows = []
    for date, total in total_by_date.items():
        ai = ai_by_date.get(date, 0)
        summary_rows.append({
            "date": date,
            "total_ai_sessions": ai,
            "total_sessions": total,
            "ai_share_pct": round(ai / total * 100, 2) if total else 0,
            "fetched_at": fetched_at,
        })

    if summary_rows:
        dates = [r["date"] for r in summary_rows]
        placeholders = ",".join("?" * len(dates))
        conn.execute(f"DELETE FROM daily_summary WHERE date IN ({placeholders})", dates)
        conn.executemany("""
            INSERT INTO daily_summary (date, total_ai_sessions, total_sessions, ai_share_pct, fetched_at)
            VALUES (:date, :total_ai_sessions, :total_sessions, :ai_share_pct, :fetched_at)
        """, summary_rows)

    conn.commit()
    conn.close()
    return len(rows)


def run_sync(property_id: str, conversion_event: str = "click"):
    print(f"Syncing GA4 property {property_id}...")
    init_db()
    client = get_client()
    rows = fetch_ai_traffic(client, property_id, conversion_event=conversion_event)
    totals = fetch_total_sessions(client, property_id)
    count = store_results(rows, totals)
    print(f"Stored {count} AI traffic rows.")
    return count


if __name__ == "__main__":
    import sys
    prop_id = os.getenv("GA4_PROPERTY_ID", "260587494")
    conv = os.getenv("GA4_CONVERSION_EVENT", "click")
    run_sync(prop_id, conv)
