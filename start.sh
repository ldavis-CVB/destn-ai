#!/bin/sh

DB_PATH="${DB_PATH:-/app/data/traffic.db}"

# ── Probe bot: seed DB on first run ──────────────────────────────────────────
python -c "
import sqlite3, sys
try:
    conn = sqlite3.connect('$DB_PATH')
    count = conn.execute('SELECT COUNT(*) FROM probe_runs').fetchone()[0]
    conn.close()
    sys.exit(0 if count > 0 else 1)
except:
    sys.exit(1)
" 2>/dev/null || (echo "==> Seeding probe DB in background..." && python pipeline/probe_bot.py &)

# ── GA4 sync: run if service account credentials are available ────────────────
if [ -n "$GA4_CREDENTIALS_B64" ] || [ -n "$GA4_CREDENTIALS_PATH" ]; then
    echo "==> Syncing GA4 data in background..."
    python pipeline/ga4_client.py &
fi

exec python -m streamlit run dashboard/app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false
