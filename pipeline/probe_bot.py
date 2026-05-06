"""
AI Probe Bot — Wilmington & Beaches CVB
Runs destination queries against Perplexity Sonar + ChatGPT web search.
Run daily:  py probe_bot.py
"""

import os
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

try:
    from textblob import TextBlob
    _HAS_BLOB = True
except ImportError:
    _HAS_BLOB = False

from queries import QUERIES, BRAND_SIGNALS, COMPETITORS, OUR_DESTINATIONS
from db import get_conn, execute, fetchone, PH, AI, DB_PATH, IS_POSTGRES

load_dotenv(Path(__file__).parent.parent / ".env")

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")


# ── DB setup ───────────────────────────────────────────────────────────────────
def init_probe_tables():
    conn = get_conn()
    execute(conn, f"""
        CREATE TABLE IF NOT EXISTS probe_runs (
            id           {AI},
            run_date     TEXT NOT NULL,
            source       TEXT NOT NULL,
            query        TEXT NOT NULL,
            mentioned    INTEGER DEFAULT 0,
            brand_terms  TEXT,
            citations    TEXT,
            cited_urls   TEXT,
            competitors  TEXT,
            raw_snippet  TEXT,
            full_response TEXT,
            fetched_at   TEXT NOT NULL
        )
    """)
    # Add columns for schema upgrades (IF NOT EXISTS works on PG + SQLite 3.37+)
    for col_def in [
        "ALTER TABLE probe_runs ADD COLUMN IF NOT EXISTS full_response TEXT",
        "ALTER TABLE probe_runs ADD COLUMN IF NOT EXISTS sentiment_score REAL DEFAULT 0",
        "ALTER TABLE probe_runs ADD COLUMN IF NOT EXISTS our_destinations TEXT",
    ]:
        try:
            execute(conn, col_def)
        except Exception:
            pass
    execute(conn, "CREATE INDEX IF NOT EXISTS idx_probe_date   ON probe_runs(run_date)")
    execute(conn, "CREATE INDEX IF NOT EXISTS idx_probe_source ON probe_runs(source)")
    execute(conn, "CREATE INDEX IF NOT EXISTS idx_probe_query  ON probe_runs(query)")
    conn.close()


# ── Sentiment ─────────────────────────────────────────────────────────────────
def get_sentiment(text: str) -> float:
    """Return polarity score -1.0 (negative) to +1.0 (positive)."""
    if not _HAS_BLOB or not text:
        return 0.0
    return round(TextBlob(str(text)).sentiment.polarity, 4)


# ── Citation detection ─────────────────────────────────────────────────────────
def detect_brand(text: str, citations: list[str]) -> tuple[bool, list[str]]:
    """Return (mentioned, matched_signals) checking response text + citation URLs."""
    text_lower = text.lower()
    all_content = text_lower + " " + " ".join(c.lower() for c in citations)
    matched = [s for s in BRAND_SIGNALS if s in all_content]
    return bool(matched), matched


def detect_competitors(text: str, citations: list[str]) -> dict[str, bool]:
    """Return dict of competitor -> mentioned."""
    all_content = (text + " " + " ".join(citations)).lower()
    return {
        name: any(sig in all_content for sig in signals)
        for name, signals in COMPETITORS.items()
    }


def detect_our_destinations(text: str, citations: list[str]) -> dict[str, bool]:
    """Return dict of our destination -> mentioned in response."""
    all_content = (text + " " + " ".join(citations)).lower()
    return {
        name: any(sig in all_content for sig in signals)
        for name, signals in OUR_DESTINATIONS.items()
    }


# ── Perplexity API ─────────────────────────────────────────────────────────────
def query_perplexity(query: str, retries: int = 3) -> dict:
    """Call Perplexity Sonar API and return parsed result.
    Retries up to `retries` times on 429 rate-limit with exponential backoff.
    """
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are a travel assistant. Give helpful, specific recommendations."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "max_tokens": 500,
        "return_citations": True,
        "return_related_questions": False,
    }

    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 15 * (2 ** attempt)))
                print(f"  [RATE LIMIT] waiting {wait}s before retry {attempt+1}/{retries}…")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            content   = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])
            return {"success": True, "content": content, "citations": citations}
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                wait = 10 * (2 ** attempt)
                print(f"  [ERROR] {e} — retrying in {wait}s…")
                time.sleep(wait)
            else:
                return {"success": False, "content": "", "citations": [], "error": str(e)}
    return {"success": False, "content": "", "citations": [], "error": "max retries exceeded"}


# ── Store result ───────────────────────────────────────────────────────────────
def store_result(run_date: str, source: str, query: str, result: dict):
    if not result["success"]:
        print(f"  [ERROR] {result.get('error','unknown')}")
        return

    content   = result["content"]
    citations = result["citations"]

    mentioned, brand_terms = detect_brand(content, citations)
    competitor_hits        = detect_competitors(content, citations)
    dest_hits              = detect_our_destinations(content, citations)
    sentiment              = get_sentiment(content)

    # Find any cited URLs that are ours
    our_urls = [u for u in citations if any(s in u.lower() for s in ["wilmingtonandbeaches", "visitwilmington"])]

    snippet = content[:300].replace("\n", " ")
    sent_tag = "+" if sentiment > 0.05 else ("-" if sentiment < -0.05 else "~")
    status   = "[CITED]    " if mentioned else "[not cited]"
    print(f"  {status}  sent:{sent_tag}{abs(sentiment):.2f}  |  {query[:50]}")

    try:
        conn = get_conn()
        execute(conn, f"""
            INSERT INTO probe_runs
                (run_date, source, query, mentioned, brand_terms, citations,
                 cited_urls, competitors, raw_snippet, full_response,
                 sentiment_score, our_destinations, fetched_at)
            VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH})
        """, (
            run_date,
            source,
            query,
            int(mentioned),
            json.dumps(brand_terms),
            json.dumps(citations),
            json.dumps(our_urls),
            json.dumps(competitor_hits),
            snippet,
            content,
            sentiment,
            json.dumps(dest_hits),
            datetime.utcnow().isoformat(),
        ))
        conn.close()
    except Exception as db_err:
        print(f"  [DB ERROR] {db_err}")


# ── Main run ───────────────────────────────────────────────────────────────────
# ── OpenAI web search ──────────────────────────────────────────────────────────
def query_openai(query: str) -> dict:
    """Call ChatGPT with web search tool and return parsed result."""
    if not OPENAI_API_KEY:
        return {"success": False, "content": "", "citations": [], "error": "No OpenAI key"}
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=query,
        )
        content   = ""
        citations = []
        for block in response.output:
            if hasattr(block, "content"):
                for part in block.content:
                    if hasattr(part, "text"):
                        content += part.text
                    if hasattr(part, "annotations"):
                        for ann in part.annotations:
                            if hasattr(ann, "url"):
                                citations.append(ann.url)
        return {"success": True, "content": content, "citations": citations}
    except Exception as e:
        return {"success": False, "content": "", "citations": [], "error": str(e)}


def run_probes(queries: list[str] = None, delay: float = 3.0, sources: list[str] = None):
    init_probe_tables()
    run_date = datetime.today().strftime("%Y-%m-%d")
    queries  = queries or QUERIES
    sources  = sources or (["perplexity", "chatgpt"] if OPENAI_API_KEY else ["perplexity"])

    print(f"\n{'='*60}")
    print(f"AI Probe Bot - Wilmington & Beaches CVB")
    print(f"Date: {run_date}  |  Queries: {len(queries)}  |  Sources: {', '.join(sources)}")
    print(f"{'='*60}\n")

    for source in sources:
        print(f"\n-- {source.upper()} --")
        cited = 0
        for i, query in enumerate(queries, 1):
            print(f"[{i:02d}/{len(queries)}]", end="  ")
            if source == "perplexity":
                result = query_perplexity(query)
            else:
                result = query_openai(query)
            store_result(run_date, source, query, result)
            if result.get("success") and detect_brand(result["content"], result["citations"])[0]:
                cited += 1
            if i < len(queries):
                time.sleep(delay)
        mention_rate = cited / len(queries) * 100
        print(f"\n{source.title()}: Cited in {cited}/{len(queries)} ({mention_rate:.1f}%)")

    print(f"\n{'='*60}")
    print(f"All done!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_probes()
