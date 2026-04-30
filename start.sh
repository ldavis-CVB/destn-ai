#!/bin/sh
set -e

DB_PATH="${DB_PATH:-/app/data/traffic.db}"

# If database has no probe data, run the probe bot once to seed it
if [ ! -f "$DB_PATH" ] || ! python -c "
import sqlite3, sys
try:
    conn = sqlite3.connect('$DB_PATH')
    count = conn.execute('SELECT COUNT(*) FROM probe_runs').fetchone()[0]
    conn.close()
    sys.exit(0 if count > 0 else 1)
except:
    sys.exit(1)
" 2>/dev/null; then
    echo "==> No probe data found. Running probe bot to seed database..."
    python pipeline/probe_bot.py
    echo "==> Probe bot complete. Starting dashboard..."
fi

exec python -m streamlit run dashboard/app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false
