#!/bin/sh

DB_PATH="${DB_PATH:-/app/data/traffic.db}"

# If no probe data, seed the DB in the background so Streamlit starts immediately
python -c "
import sqlite3, sys
try:
    conn = sqlite3.connect('$DB_PATH')
    count = conn.execute('SELECT COUNT(*) FROM probe_runs').fetchone()[0]
    conn.close()
    sys.exit(0 if count > 0 else 1)
except:
    sys.exit(1)
" 2>/dev/null || (echo "==> Seeding DB in background..." && python pipeline/probe_bot.py &)

exec python -m streamlit run dashboard/app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false
