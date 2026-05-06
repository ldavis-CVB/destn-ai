#!/bin/sh

DB_PATH="${DB_PATH:-/app/data/traffic.db}"
TODAY=$(date -u +%Y-%m-%d)

# ── Python scheduler: M-F probe at 7am ET, GA4 sync at 8am ET ────────────────
python pipeline/scheduler.py &
echo "==> Scheduler started (probe M-F 7am ET, GA4 sync M-F 8am ET)"

# ── Probe bot: seed on first run of the day ───────────────────────────────────
python -c "
import sqlite3, sys
try:
    conn = sqlite3.connect('$DB_PATH')
    count = conn.execute(
        \"SELECT COUNT(*) FROM probe_runs WHERE run_date = '$TODAY'\"
    ).fetchone()[0]
    conn.close()
    sys.exit(0 if count >= 30 else 1)
except:
    sys.exit(1)
" 2>/dev/null \
  && echo "==> Probe data already exists for $TODAY (skipping seed)" \
  || (echo "==> Running probe bot for $TODAY..." && python pipeline/probe_bot.py &)

# ── GA4 sync: run on startup if credentials available ────────────────────────
if [ -n "$GA4_OAUTH_TOKEN_B64" ] || [ -n "$GA4_CREDENTIALS_B64" ] || [ -n "$GA4_CREDENTIALS_PATH" ]; then
    echo "==> Syncing GA4 data in background..."
    python pipeline/ga4_client.py &
fi

exec python -m streamlit run dashboard/app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false
