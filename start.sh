#!/bin/sh

DB_PATH="${DB_PATH:-/app/data/traffic.db}"
TODAY=$(date -u +%Y-%m-%d)

# ── Python scheduler: M-F probe at 7am ET, GA4 sync at 8am ET ────────────────
python pipeline/scheduler.py &
echo "==> Scheduler started (probe M-F 7am ET, GA4 sync M-F 8am ET)"

# ── Probe bot: seed on first run of the day ───────────────────────────────────
python -c "
import sys, os
sys.path.insert(0, 'pipeline')
try:
    from db import get_conn, fetchone, PH
    conn = get_conn()
    row = fetchone(conn, f\"SELECT COUNT(*) FROM probe_runs WHERE run_date = {PH}\", ('$TODAY',))
    conn.close()
    count = row[0] if row else 0
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
