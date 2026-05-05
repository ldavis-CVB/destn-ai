# AI Traffic Dashboard — Setup Guide

**Your GA4 Property:** 260587494
**Your Site:** wilmingtonandbeaches.com
**Conversion Event:** click (website clicks)

---

## Step 1 — Install Python dependencies

```bash
cd ai-geo-dashboard
pip install -r requirements.txt
```

---

## Step 2 — Create a GA4 Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Google Analytics Data API**
4. Go to **IAM & Admin → Service Accounts → Create Service Account**
5. Name it `ai-dashboard-reader`, grant no roles at project level
6. Click the service account → **Keys → Add Key → JSON** → download it
7. Place the JSON file at: `ai-geo-dashboard/credentials/service_account.json`

## Step 3 — Grant GA4 access to the service account

1. Open [GA4](https://analytics.google.com/) → Property 260587494
2. **Admin → Property Access Management → + → Add users**
3. Paste the service account email (ends in `@...iam.gserviceaccount.com`)
4. Role: **Viewer** → Save

---

## Step 4 — Sync data

```bash
# Copy and fill in .env
cp .env.example .env

# Run the sync
cd pipeline
python ga4_client.py 260587494 ../credentials/service_account.json
```

---

## Step 5 — Launch dashboard

```bash
cd dashboard
streamlit run app.py
```

Opens at: http://localhost:8501

---

## What the dashboard tracks

- Sessions arriving from ChatGPT, Perplexity, Claude, Copilot, Gemini, etc.
- Geographic breakdown (country, state, city)
- Which pages AI tools are sending people to
- Website click conversions from AI visitors
- AI traffic share vs. all traffic over time
