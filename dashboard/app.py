"""
destn.ai  --  AI Visibility Platform
Wilmington & Beaches CVB
"""

import json, sqlite3, sys, html as _html, base64, tempfile
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta, date as date_type
import os as _os

# ── Write GA4 credentials from env var if present (Railway deployment) ─────────
_ga4_creds_b64 = _os.getenv("GA4_CREDENTIALS_B64")
if _ga4_creds_b64:
    _tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    _tmp.write(base64.b64decode(_ga4_creds_b64))
    _tmp.close()
    _os.environ["GA4_CREDENTIALS_PATH"] = _tmp.name

def _safe_text(val) -> str:
    """Return a clean string; treats NaN/None as empty."""
    if val is None:
        return ""
    s = str(val)
    return "" if s.lower() in ("nan", "none", "") else s

def _resp(row) -> tuple:
    """Return (escaped_text, is_full) for a probe row."""
    full = _safe_text(row.get("full_response"))
    if full:
        return _html.escape(full), True
    snip = _safe_text(row.get("raw_snippet"))
    if snip:
        return _html.escape(snip), False
    return "No response captured.", False

import re as _re

def _highlight_brands(escaped_text: str, brand_terms: list) -> str:
    """Wrap matched brand terms with a yellow highlight span."""
    result = escaped_text
    for term in sorted(brand_terms, key=len, reverse=True):
        result = _re.sub(
            _re.escape(_html.escape(term)),
            f'<mark style="background:#fef08a;padding:0 2px;border-radius:2px;'
            f'font-weight:700;">{_html.escape(term)}</mark>',
            result,
            flags=_re.IGNORECASE,
        )
    return result


try:
    from textblob import TextBlob
    def _sentiment(text: str) -> float:
        if not text: return 0.0
        return round(TextBlob(str(text)).sentiment.polarity, 3)
except ImportError:
    def _sentiment(text: str) -> float:
        return 0.0

# Allow importing from pipeline/
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))
try:
    from queries import QUERY_CATEGORIES, OUR_DESTINATIONS
except ImportError:
    QUERY_CATEGORIES  = {}
    OUR_DESTINATIONS  = {
        "Wilmington":         ["wilmington"],
        "Wrightsville Beach": ["wrightsville beach"],
        "Carolina Beach":     ["carolina beach"],
        "Kure Beach":         ["kure beach"],
        "Figure Eight":       ["figure eight island", "figure 8 island"],
        "Cape Fear Region":   ["cape fear"],
    }


def _detect_destinations(text: str) -> dict:
    """Return {destination: bool} from response text."""
    tl = (str(text) if text else "").lower()
    return {name: any(sig in tl for sig in sigs)
            for name, sigs in OUR_DESTINATIONS.items()}

import os as _os
DB_PATH = Path(_os.getenv("DB_PATH", str(Path(__file__).parent.parent / "data" / "traffic.db")))

st.set_page_config(
    page_title="destn.ai | Wilmington & Beaches",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design tokens ─────────────────────────────────────────────────────────────
TEAL_DARK  = "#1a3c4d"
BLUE       = "#0576a6"
BLUE2      = "#1f6db6"
BLUE_LIGHT = "#57b8e0"
BLUE_PALE  = "#d6eef8"
GREEN      = "#a2ce37"
RED        = "#d2462a"
NAVY       = "#22302f"
WHITE      = "#ffffff"
GRAY_LIGHT = "#f4f7fa"
GRAY_MID   = "#dde4ea"
TEXT       = "#22302f"
MUTED      = "#5a7080"

PLOTLY = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, family="Segoe UI, sans-serif", size=12),
    margin=dict(l=8, r=8, t=36, b=8),
)

# ── Session state ─────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "overview"
if "selected_probe" not in st.session_state:
    st.session_state.selected_probe = None


# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*, html, body {{
  box-sizing: border-box;
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
}}
[data-testid="stAppViewContainer"] {{
  background: {GRAY_LIGHT};
}}
[data-testid="stSidebar"] {{ display: none !important; }}
.block-container {{
  padding: 0 !important;
  max-width: 100% !important;
}}
#MainMenu, footer, header {{ visibility: hidden; }}

/* ── Brand header ─────────────────────────────────────── */
.top-nav {{
  background: {TEAL_DARK};
  display: flex;
  align-items: center;
  padding: 0 32px;
  height: 52px;
  border-bottom: 3px solid {BLUE};
}}
.brand-badge {{
  background: {BLUE};
  color: #fff;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.5px;
  padding: 5px 14px;
  border-radius: 6px;
  margin-right: 10px;
}}
.brand-sub {{
  color: rgba(255,255,255,0.55);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.4px;
}}

/* ── Nav pill bar (scoped to key class) ──────────────── */
.st-key-nav_radio {{
  background: {WHITE};
  border-bottom: 1px solid {GRAY_MID};
}}
.st-key-nav_radio [data-testid="stWidgetLabel"] {{ display: none !important; }}
.st-key-nav_radio div[role="radiogroup"] {{
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  gap: 2px !important;
  background: {WHITE} !important;
  padding: 8px 20px !important;
  margin: 0 !important;
  max-height: none !important;
  overflow-y: visible !important;
  overflow-x: auto !important;
  border: none !important;
  border-radius: 0 !important;
}}
.st-key-nav_radio div[role="radiogroup"] label {{
  background: transparent !important;
  border: none !important;
  border-bottom: none !important;
  border-radius: 6px !important;
  color: {MUTED} !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  padding: 7px 18px !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  overflow: visible !important;
  text-overflow: clip !important;
  max-width: none !important;
  letter-spacing: 0.2px !important;
  transition: all 0.12s !important;
  display: inline-flex !important;
  align-items: center !important;
  text-shadow: none !important;
}}
.st-key-nav_radio div[role="radiogroup"] label:hover {{
  background: {GRAY_LIGHT} !important;
  color: {TEAL_DARK} !important;
}}
.st-key-nav_radio div[role="radiogroup"] label:has(input:checked) {{
  background: {BLUE} !important;
  color: {WHITE} !important;
  font-weight: 700 !important;
}}
.st-key-nav_radio div[role="radiogroup"] input {{ display: none !important; }}

/* ── Date range selectbox in nav ─────────────────────── */
.st-key-range_mode {{
  background: {WHITE};
  border-bottom: 1px solid {GRAY_MID};
  padding: 0 !important;
}}
.st-key-range_mode [data-testid="stWidgetLabel"] {{ display: none !important; }}
.st-key-range_mode [data-testid="stSelectbox"] > div {{
  background: {GRAY_LIGHT} !important;
  border: 1px solid {GRAY_MID} !important;
  border-radius: 6px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  color: {TEXT} !important;
  margin-top: 4px;
}}
.st-key-custom_dates [data-testid="stWidgetLabel"] {{ display: none !important; }}

/* ── Page wrapper ─────────────────────────────────────── */
.page-wrap {{
  padding: 26px 32px;
  animation: fadeUp 0.25s ease;
}}
@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(6px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}

/* ── Page header ── */
.page-header {{ margin-bottom: 22px; }}
.page-title  {{ font-size: 1.35rem; font-weight: 800; color: {TEXT}; margin: 0; }}
.page-sub    {{ font-size: 0.78rem; color: {MUTED}; margin-top: 3px; }}

/* ── Cards ── */
.card {{
  background: {WHITE};
  border: 1px solid {GRAY_MID};
  border-radius: 12px;
  padding: 20px 22px;
  margin-bottom: 16px;
}}
.card-title {{
  font-size: 0.8rem;
  font-weight: 700;
  color: {TEXT};
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 14px;
}}

/* ── KPI cards ── */
.kpi {{
  background: {WHITE};
  border: 1px solid {GRAY_MID};
  border-top: 3px solid {BLUE};
  border-radius: 10px;
  padding: 16px 18px;
}}
.kpi-val {{ font-size: 1.85rem; font-weight: 800; color: {TEXT}; line-height: 1; }}
.kpi-lbl {{ font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 1.2px; color: {MUTED}; margin-top: 5px; }}
.kpi-up  {{ color: #2e7d32; font-size: 0.72rem; font-weight: 600; margin-top: 4px; }}
.kpi-dn  {{ color: {RED};   font-size: 0.72rem; font-weight: 600; margin-top: 4px; }}

/* ── Category toggle ── */
.st-key-cat_toggle div[role="radiogroup"] {{
  display: flex !important;
  flex-direction: row !important;
  gap: 4px !important;
  background: transparent !important;
  padding: 0 !important;
  border: none !important;
  border-radius: 0 !important;
  max-height: none !important;
  overflow-y: visible !important;
}}
.st-key-cat_toggle div[role="radiogroup"] label {{
  background: {WHITE} !important;
  border: 1.5px solid {GRAY_MID} !important;
  border-radius: 20px !important;
  color: {MUTED} !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  padding: 5px 16px !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  max-width: none !important;
  overflow: visible !important;
  letter-spacing: 0.2px !important;
  transition: all 0.12s !important;
  text-shadow: none !important;
}}
.st-key-cat_toggle div[role="radiogroup"] label:hover {{
  border-color: {BLUE_LIGHT} !important;
  color: {TEAL_DARK} !important;
}}
.st-key-cat_toggle div[role="radiogroup"] label:has(input:checked) {{
  background: {TEAL_DARK} !important;
  border-color: {TEAL_DARK} !important;
  color: {WHITE} !important;
  font-weight: 700 !important;
}}
.st-key-cat_toggle div[role="radiogroup"] input {{ display: none !important; }}
.st-key-cat_toggle [data-testid="stWidgetLabel"] {{ display: none !important; }}

/* ── Query list (citation page) ── */
.st-key-query_list div[role="radiogroup"] {{
  display: flex !important;
  flex-direction: column !important;
  max-height: 540px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  background: {WHITE} !important;
  border: 1px solid {GRAY_MID} !important;
  border-radius: 10px !important;
  padding: 4px 0 !important;
  gap: 0 !important;
}}
.st-key-query_list div[role="radiogroup"] label {{
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid {GRAY_MID} !important;
  border-radius: 0 !important;
  color: {TEXT} !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  padding: 9px 14px !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  max-width: 100% !important;
  display: block !important;
  text-shadow: none !important;
  letter-spacing: 0 !important;
  transition: background 0.1s !important;
}}
.st-key-query_list div[role="radiogroup"] label:last-child {{
  border-bottom: none !important;
}}
.st-key-query_list div[role="radiogroup"] label:hover {{
  background: {GRAY_LIGHT} !important;
}}
.st-key-query_list div[role="radiogroup"] label:has(input:checked) {{
  background: {BLUE_PALE} !important;
  color: {BLUE2} !important;
  font-weight: 700 !important;
  border-left: 3px solid {BLUE} !important;
}}
.st-key-query_list div[role="radiogroup"] input {{ display: none !important; }}
.st-key-query_list [data-testid="stWidgetLabel"] {{ display: none !important; }}

/* ── Detail panel ── */
.detail-panel {{
  background: {WHITE};
  border: 1px solid {GRAY_MID};
  border-radius: 12px;
  padding: 20px;
  position: sticky;
  top: 70px;
  max-height: calc(100vh - 90px);
  overflow-y: auto;
}}

/* ── Misc overrides ── */
[data-testid="stHorizontalBlock"] {{ gap: 12px; }}
div.stButton > button {{
  background: {BLUE}; color: white; border: none;
  border-radius: 6px; font-size: 0.78rem; font-weight: 600;
  padding: 6px 14px; transition: background 0.15s;
}}
div.stButton > button:hover {{ background: {BLUE2}; }}
</style>
""", unsafe_allow_html=True)


# ── Sentiment label + color ───────────────────────────────────────────────────
def _sent_label(score: float) -> str:
    if score >= 0.15:  return "Positive"
    if score <= -0.15: return "Negative"
    return "Neutral"

def _sent_color(score: float) -> tuple:
    """Return (bg, text) hex pair."""
    if score >= 0.15:  return ("#dcfce7", "#166534")   # green
    if score <= -0.15: return ("#fee2e2", "#991b1b")   # red
    return ("#fdf6e3", "#6b5c3a")                       # beige for neutral

def _bar_color(score: float) -> str:
    if score >= 0.15:  return "#4ade80"   # green
    if score <= -0.15: return "#f87171"   # red
    return "#e5d5b0"                       # beige / neutral

def _content_suggestion(query: str) -> tuple:
    """Return (summary_paragraph, todo_list) tailored to the query."""
    ql = query.lower()

    is_drive      = any(c in ql for c in ["charlotte","raleigh","durham","greensboro","atlanta","driving distance","road trip"])
    is_bach       = any(x in ql for x in ["bachelorette","girls trip","girls weekend"])
    is_guys       = "guys trip" in ql
    is_couples    = any(x in ql for x in ["couple","romantic","romance","honeymoon"])
    is_family     = any(x in ql for x in ["famil","kids","children"])
    is_food       = any(x in ql for x in ["food","nightlife","foodie","dining","restaurant"])
    is_outdoor    = any(x in ql for x in ["outdoor","surf","kayak","hiking","activities"])
    is_history    = any(x in ql for x in ["history","culture","historic","heritage"])
    is_hidden     = any(x in ql for x in ["hidden","underrated","secret","undiscovered","off the beaten"])
    is_nc         = "north carolina" in ql or "nc beach" in ql or " nc " in ql
    is_east_coast = "east coast" in ql or "atlantic coast" in ql
    is_southeast  = any(x in ql for x in ["southeast","southern","south"])
    is_summer     = "summer" in ql
    is_weekend    = "weekend" in ql or "getaway" in ql or "long weekend" in ql
    is_swim       = "swim" in ql
    is_affordable = "affordable" in ql or "budget" in ql

    if is_drive:
        city = next((c for c in ["Charlotte","Raleigh","Durham","Greensboro","Atlanta"] if c.lower() in ql), "your city")
        blurb = f"Drive-market queries are the easiest wins — visitors from {city} are already looking for a quick beach trip and Wilmington is perfectly positioned. A dedicated page optimized for this intent can earn direct AI citation."
        todos = [
            f"Create a '{city} to Wilmington Beaches' landing page (driving time, distance, route tips)",
            f"Add a 'Why {city} residents choose Wrightsville Beach' section",
            "Build a 48-hour weekend itinerary (depart Friday, return Sunday)",
            "Include comparison table: Wilmington vs. closer alternatives for this market",
            f"Target meta title: 'Best Beach from {city} — Wilmington & Wrightsville Beach'",
            "Submit the new page to Google Search Console and request indexing",
        ]
    elif is_bach or is_guys:
        trip_type = "Bachelorette & Girls Trip" if is_bach else "Guys Trip"
        blurb = f"High-intent trip-planning queries where a single well-structured guide can dominate AI results. Wilmington's historic downtown nightlife + beach access is a natural fit that isn't well-represented in current AI training data."
        todos = [
            f"Publish '{trip_type} Guide to Wilmington, NC' as a standalone page",
            "Highlight downtown bar crawl route on the historic Cotton Exchange block",
            "Add spa / activity partner listings with booking links",
            "Include 'book your group rental' call-to-action with VRBO/Airbnb deep links",
            f"Target: '{trip_type.lower()} Wilmington NC', 'Wilmington beach party weekend'",
            "Pitch the guide to 3 wedding / travel influencers for organic reach",
        ]
    elif is_couples:
        blurb = "Romantic-getaway queries convert well and Wilmington's combination of a walkable historic downtown, sunset cruises, and uncrowded beaches is a strong narrative that current AI responses underutilize."
        todos = [
            "Create a 'Romantic Wilmington & Beaches' hub page",
            "Feature sunset sailing tours and private beachfront dinner packages",
            "Add a curated list of waterfront restaurants with outdoor seating",
            "Highlight historic bed & breakfast options in downtown Wilmington",
            "Build a '2-Night Romance Itinerary' with map embed",
            "Target: 'romantic getaway NC coast', 'couples trip Wilmington NC'",
        ]
    elif is_family:
        blurb = "Family-travel queries are highly competitive but Wilmington punches above its weight — the NC Aquarium, Carolina Beach State Park, and safe shallow beaches are strong hooks that need better content packaging."
        todos = [
            "Build a 'Wilmington NC with Kids' comprehensive guide page",
            "Feature NC Aquarium at Fort Fisher as the #1 family activity",
            "Add beach comparison: Carolina Beach (calm water, boardwalk) vs. Wrightsville (surf, nightlife)",
            "Create a printable 'Wilmington Family Summer Checklist'",
            "Target: 'Wilmington NC family vacation', 'best NC beaches for kids'",
            "Add safety info (lifeguard hours, parking, facilities) to each beach page",
        ]
    elif is_food:
        blurb = "AI tools consistently recommend destinations with robust dining content. Wilmington's seafood scene, craft breweries, and farm-to-table restaurants are under-documented — a structured food guide could unlock multiple citations."
        todos = [
            "Build a 'Wilmington Food & Drink Guide' hub page with category filters",
            "Create a 'Best Seafood Restaurants in Wilmington' listicle (AI loves lists)",
            "Add a Wilmington craft beer trail map",
            "Feature locally-owned restaurants with brief chef/story profiles",
            "Target: 'best seafood Wilmington NC', 'Wilmington restaurants waterfront'",
            "Add LocalBusiness structured data (schema.org) for top 10 restaurants",
        ]
    elif is_outdoor:
        blurb = "Outdoor and adventure travel is a fast-growing AI query category. Wilmington's surfing, paddleboarding, kayaking, and state park hiking are almost never cited — a dedicated adventures page would fill a real gap."
        todos = [
            "Create 'Outdoor Adventures in Wilmington & Beaches' landing page",
            "Feature surf schools at Wrightsville Beach with booking links",
            "Add kayak and paddleboard rental map with launch points",
            "Highlight Fort Fisher State Recreation Area and Carolina Beach State Park trails",
            "Target: 'surfing Wilmington NC', 'water sports Wrightsville Beach'",
            "Partner with local outfitters for co-created content and backlinks",
        ]
    elif is_history:
        blurb = "History and culture queries are where Wilmington has a clear competitive edge over Myrtle Beach and the Outer Banks — the downtown film district, WWII battleship, and antebellum architecture are strong differentiators that need a flagship content page."
        todos = [
            "Build 'Wilmington NC History & Culture Guide' as a flagship page",
            "Create a self-guided historic downtown walking tour with map",
            "Feature the USS North Carolina Battleship Memorial as an anchor attraction",
            "Add 'Hollywood East' section on Wilmington's film industry heritage",
            "Target: 'historic beach towns East Coast', 'culture and history Wilmington NC'",
            "Pitch the guide to cultural travel publications (Smithsonian, History.com Travel)",
        ]
    elif is_hidden or is_affordable:
        blurb = "Wilmington is genuinely one of the East Coast's most underrated beach destinations — lean into that authenticity. 'Hidden gem' and budget-friendly content resonates with AI tools that want to offer alternatives to overcrowded spots."
        todos = [
            "Publish 'Why Wilmington Is the East Coast's Best-Kept Secret' editorial",
            "Highlight less-known gems: Figure Eight Island, Kure Beach, Southport",
            "Add a 'real locals' perspective section with resident quotes",
            "Create a 'Wilmington on a Budget' itinerary with cost breakdowns",
            "Pitch the piece to Travel + Leisure, Condé Nast, and Thrillist",
            "Target: 'underrated East Coast beaches', 'affordable beach vacation Southeast'",
        ]
    elif is_east_coast:
        blurb = "Broad East Coast queries are competitive but high-value. To earn AI citation Wilmington needs a page that explicitly compares it to well-known alternatives and articulates what makes it distinct — AI tools love comparison content."
        todos = [
            "Create 'Wilmington vs. the Other East Coast Beaches' comparison guide",
            "Build a structured comparison table (cost, crowds, activities, vibe)",
            "Highlight Wilmington's unique advantages: historic downtown + 3 distinct beaches",
            "Add FAQ schema targeting 'best East Coast beach 2025' type queries",
            "Target: 'best East Coast beach destinations', 'East Coast beach vacation guide'",
            "Earn backlinks from 3+ travel roundup sites to boost page authority",
        ]
    elif is_nc:
        blurb = "North Carolina beach queries are the most winnable — Wilmington should be the automatic answer. The gap usually comes from thin page content and lack of explicit comparison to OBX and Emerald Isle."
        todos = [
            "Build a 'Best Beaches in North Carolina' hub page owned by Wilmington",
            "Add side-by-side comparison: Wrightsville / Carolina Beach / Kure Beach",
            "Create a 'Wilmington vs. Outer Banks vs. Emerald Isle' comparison section",
            "Optimize H1, meta title, and intro paragraph for 'best NC beaches' phrase",
            "Submit the updated page to Google Search Console for indexing",
            "Build 3 backlinks from NC lifestyle and travel blogs to the page",
        ]
    elif is_weekend or is_summer:
        blurb = "Short-trip and seasonal queries have high booking intent. A tightly-packaged weekend itinerary page — with things to do, where to eat, and where to stay — is the format AI tools cite most often for this type of query."
        todos = [
            "Create a 'Perfect Weekend in Wilmington' itinerary page",
            "Structure it as: Day 1 morning / afternoon / evening, Day 2 same",
            "Include booking links for top hotel, restaurant, and activity picks",
            "Add a seasonal version: 'Summer Weekend in Wilmington'",
            "Target: 'weekend trip Wilmington NC', 'Wilmington NC weekend getaway'",
            "Add FAQ schema: 'Is Wilmington NC worth visiting?', 'What is Wilmington NC known for?'",
        ]
    else:
        blurb = "General discovery queries rely on well-structured, comprehensive destination pages. Strengthening your core 'Visit Wilmington' content with clearer headings, FAQ schema, and comparison language will improve AI citation rates across the board."
        todos = [
            "Audit and rewrite the main 'Visit Wilmington' landing page intro",
            "Add a 'Why Wilmington?' section with 5 clear differentiators",
            "Build a comprehensive 'Things to Do' hub with filterable categories",
            "Add FAQ schema to key pages targeting common travel questions",
            "Implement TouristDestination structured data (schema.org) site-wide",
            "Run a content gap analysis vs. VisitMyrtleBeach.com to identify missing pages",
        ]

    return blurb, todos


def _extract_quote(text: str, score: float, max_len: int = 320) -> str:
    """Return the sentence from *text* most representative of the sentiment."""
    text = _safe_text(text)
    if not text:
        return "No response captured."
    try:
        from textblob import TextBlob
        sents = TextBlob(str(text)).sentences
        if not sents:
            return text[:max_len]
        if score >= 0.15:
            best = max(sents, key=lambda s: s.sentiment.polarity)
        elif score <= -0.15:
            best = min(sents, key=lambda s: s.sentiment.polarity)
        else:
            best = min(sents, key=lambda s: abs(s.sentiment.polarity))
        q = str(best).strip()
        return q if len(q) <= max_len else q[:max_len] + "..."
    except Exception:
        return text[:max_len]


# ── Helper: query category ────────────────────────────────────────────────────
def _query_cat(q: str) -> str:
    """Classify query as local / state / national."""
    if q in QUERY_CATEGORIES:
        return QUERY_CATEGORIES[q]
    ql = q.lower()
    if any(s in ql for s in ["charlotte", "raleigh", "durham", "greensboro",
                               "from atlanta", "road trip from", "driving distance"]):
        return "local"
    if any(s in ql for s in ["north carolina", "nc beach", " nc "]):
        return "state"
    return "national"


# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_traffic(start_date: str, end_date: str):
    """start_date / end_date in YYYYMMDD format."""
    if not DB_PATH.exists():
        return pd.DataFrame(), pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM ai_traffic WHERE date >= ? AND date <= ? ORDER BY date",
        conn, params=(start_date, end_date)
    )
    sm = pd.read_sql(
        "SELECT * FROM daily_summary WHERE date >= ? AND date <= ? ORDER BY date",
        conn, params=(start_date, end_date)
    )
    conn.close()
    for f in [df, sm]:
        if not f.empty:
            f["date"] = pd.to_datetime(f["date"], format="%Y%m%d")
    return df, sm


@st.cache_data(ttl=3600)
def load_probes(start_date: str, end_date: str):
    """start_date / end_date in YYYY-MM-DD format."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(
            "SELECT * FROM probe_runs WHERE run_date >= ? AND run_date <= ? ORDER BY run_date DESC, id",
            conn, params=(start_date, end_date)
        )
    except Exception:
        df = pd.DataFrame()
    conn.close()
    if not df.empty:
        df["run_date"]    = pd.to_datetime(df["run_date"])

        def _jload(x, fallback):
            """Safe json.loads — returns fallback for NaN, None, or empty."""
            if x is None: return fallback
            if not isinstance(x, str): return fallback
            s = x.strip()
            return json.loads(s) if s else fallback

        df["competitors"] = df["competitors"].apply(lambda x: _jload(x, {}))
        df["cited_urls"]  = df["cited_urls"].apply(lambda x: _jload(x, []))
        df["citations"]   = df["citations"].apply(lambda x: _jload(x, []))
        df["brand_terms"] = df["brand_terms"].apply(lambda x: _jload(x, []))

        # our_destinations: use stored value or compute on-the-fly from full_response
        if "our_destinations" in df.columns:
            df["our_destinations"] = df.apply(
                lambda r: _jload(r["our_destinations"], None)
                          or _detect_destinations(_safe_text(r.get("full_response"))
                                                  or _safe_text(r.get("raw_snippet","")))
                , axis=1)
        else:
            resp_col = "full_response" if "full_response" in df.columns else "raw_snippet"
            df["our_destinations"] = df[resp_col].apply(lambda x: _detect_destinations(_safe_text(x)))
        # Compute sentiment if column missing or all-zero (old rows)
        if "sentiment_score" not in df.columns or df["sentiment_score"].fillna(0).abs().sum() == 0:
            resp_col = "full_response" if "full_response" in df.columns else "raw_snippet"
            df["sentiment_score"] = df[resp_col].apply(_sentiment)
        else:
            df["sentiment_score"] = df["sentiment_score"].fillna(0).apply(
                lambda v: _sentiment(v) if v == 0 else v
            )
    return df


# ── Brand header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
  <div class="brand-badge">destn.ai</div>
  <div class="brand-sub">Wilmington &amp; Beaches CVB &nbsp;&mdash;&nbsp; AI Visibility Platform</div>
</div>
""", unsafe_allow_html=True)

# ── Nav bar + date range ──────────────────────────────────────────────────────
pages_def  = ["Overview", "AI Citation Monitor", "Traffic Trends", "Geography", "Landing Pages"]
pages_keys = ["overview", "citations", "traffic", "geo", "lp"]

nav_col, date_col = st.columns([5, 1.5])

with nav_col:
    selected_label = st.radio(
        "nav", pages_def,
        index=pages_keys.index(st.session_state.page),
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio",
    )
    new_key = pages_keys[pages_def.index(selected_label)]
    if new_key != st.session_state.page:
        st.session_state.page = new_key
        st.session_state.selected_probe = None
        st.rerun()

with date_col:
    st.markdown(f"""
    <div style="background:{WHITE}; border-bottom:1px solid {GRAY_MID};
         padding:8px 12px 4px; display:flex; flex-direction:column; gap:4px;">
      <div style="font-size:10px; font-weight:700; text-transform:uppercase;
           letter-spacing:0.8px; color:{MUTED};">Date Range</div>
    </div>""", unsafe_allow_html=True)

    range_mode = st.selectbox(
        "range",
        ["Last 7 days", "Last 14 days", "Last 30 days", "Last 60 days", "Last 90 days", "Custom"],
        index=2,
        label_visibility="collapsed",
        key="range_mode",
    )

    today = datetime.today().date()
    if range_mode == "Custom":
        date_range = st.date_input(
            "Custom dates",
            value=(today - timedelta(days=30), today),
            label_visibility="collapsed",
            key="custom_dates",
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_d, end_d = date_range[0], date_range[1]
        elif isinstance(date_range, (list, tuple)) and len(date_range) == 1:
            start_d, end_d = date_range[0], today
        else:
            start_d, end_d = today - timedelta(days=30), today
    else:
        n = int(range_mode.split()[1])   # "Last 30 days" -> 30
        start_d = today - timedelta(days=n)
        end_d   = today

# Convert to string keys used by loaders
traffic_start = start_d.strftime("%Y%m%d")
traffic_end   = end_d.strftime("%Y%m%d")
probe_start   = start_d.strftime("%Y-%m-%d")
probe_end     = end_d.strftime("%Y-%m-%d")

# ── Load data ─────────────────────────────────────────────────────────────────
df, summary = load_traffic(traffic_start, traffic_end)
probe_df    = load_probes(probe_start, probe_end)
page        = st.session_state.page

# Pre-compute traffic aggregates
if not df.empty:
    total_ai   = int(df["sessions"].sum())
    total_conv = int(df["conversions"].sum())
    avg_share  = summary["ai_share_pct"].mean() if not summary.empty else 0
    eng_total  = int(df["engaged_sessions"].sum())
    eng_rate   = eng_total / total_ai * 100 if total_ai else 0
    n_sources  = df["source_name"].nunique()
    mid        = datetime.combine(start_d + (end_d - start_d) / 2, datetime.min.time())
    prev_s     = df[df["date"] < mid]["sessions"].sum()
    curr_s     = df[df["date"] >= mid]["sessions"].sum()
    growth     = (curr_s - prev_s) / max(prev_s, 1) * 100
    src = (df.groupby("source_name")
             .agg(sessions=("sessions","sum"), conversions=("conversions","sum"),
                  engaged=("engaged_sessions","sum"))
             .reset_index()
             .assign(share=lambda x: x.sessions/x.sessions.sum()*100,
                     eng_rate=lambda x: x.engaged/x.sessions*100,
                     conv_rate=lambda x: x.conversions/x.sessions*100)
             .sort_values("sessions", ascending=False).reset_index(drop=True))
else:
    total_ai=total_conv=eng_rate=n_sources=growth=avg_share=0
    src=pd.DataFrame()

probe_total = len(probe_df)
probe_cited = int(probe_df["mentioned"].sum()) if probe_total else 0
probe_rate  = probe_cited / probe_total * 100 if probe_total else 0


# ── KPI helper ────────────────────────────────────────────────────────────────
def kpi(col, val, lbl, delta=None, suffix="", accent=BLUE):
    d = ""
    if delta is not None:
        cls  = "kpi-up" if delta >= 0 else "kpi-dn"
        sign = "+" if delta >= 0 else ""
        d = f'<div class="{cls}">{sign}{delta:.1f}%</div>'
    col.markdown(
        f'<div class="kpi" style="border-top-color:{accent}">'
        f'<div class="kpi-val">{val}{suffix}</div>'
        f'<div class="kpi-lbl">{lbl}</div>{d}</div>',
        unsafe_allow_html=True
    )


st.markdown('<div class="page-wrap">', unsafe_allow_html=True)


# ==============================================================================
# OVERVIEW
# ==============================================================================
if page == "overview":
    st.markdown(
        '<div class="page-header">'
        '<div class="page-title">Overview</div>'
        f'<div class="page-sub">AI visibility at a glance &mdash; {start_d.strftime("%b %d")} to {end_d.strftime("%b %d, %Y")}</div>'
        '</div>', unsafe_allow_html=True
    )

    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1, f"{total_ai:,}",     "AI Sessions",       delta=growth)
    kpi(c2, f"{avg_share:.1f}",  "AI Traffic Share",  suffix="%", accent=BLUE_LIGHT)
    kpi(c3, f"{eng_rate:.1f}",   "Engaged Rate",      suffix="%", accent="#2e7d32")
    kpi(c4, f"{total_conv:,}",   "Conversions",       accent="#7b1fa2")
    kpi(c5, f"{probe_rate:.1f}", "AI Mention Rate",   suffix="%", accent=GREEN)

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="card"><div class="card-title">AI Sessions Over Time</div>', unsafe_allow_html=True)
        if not df.empty:
            fig = px.area(
                df.groupby(["date","source_name"])["sessions"].sum().reset_index(),
                x="date", y="sessions", color="source_name",
                color_discrete_sequence=[BLUE, BLUE_LIGHT, "#a2ce37", "#f97316", "#9c27b0"],
                labels={"sessions":"Sessions","date":"","source_name":"Source"}
            )
            fig.update_layout(height=240, hovermode="x unified", legend_title="", **PLOTLY)
            fig.update_traces(line_width=1.5)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No traffic data for this period.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="card"><div class="card-title">By AI Tool</div>', unsafe_allow_html=True)
        if not src.empty:
            fig2 = px.pie(src, values="sessions", names="source_name", hole=0.58,
                          color_discrete_sequence=[BLUE, BLUE_LIGHT, "#a2ce37", "#f97316", "#9c27b0"])
            fig2.update_layout(height=240, **PLOTLY)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("No traffic data for this period.")
        st.markdown('</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="card"><div class="card-title">AI Traffic Share Trend</div>', unsafe_allow_html=True)
        if not summary.empty:
            fig3 = px.line(summary, x="date", y="ai_share_pct", markers=True,
                           labels={"ai_share_pct":"Share (%)","date":""})
            fig3.update_traces(line_color=BLUE, line_width=2,
                               fill="tozeroy", fillcolor="rgba(5,118,166,0.07)")
            fig3.update_layout(height=190, **PLOTLY)
            st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="card"><div class="card-title">AI Mention Rate Trend</div>', unsafe_allow_html=True)
        if not probe_df.empty:
            dr = (probe_df.groupby("run_date")
                  .agg(t=("mentioned","count"), c=("mentioned","sum"))
                  .assign(rate=lambda x: x.c/x.t*100).reset_index())
            fig4 = px.line(dr, x="run_date", y="rate", markers=True,
                           labels={"rate":"Mention %","run_date":""})
            fig4.update_traces(line_color=GREEN, line_width=2,
                               fill="tozeroy", fillcolor="rgba(162,206,55,0.08)")
            fig4.update_layout(height=190, **PLOTLY)
            st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# AI CITATION MONITOR
# ==============================================================================
elif page == "citations":
    st.markdown(
        '<div class="page-header">'
        '<div class="page-title">AI Citation Monitor</div>'
        '<div class="page-sub">Select any query to see the full AI response and cited sources</div>'
        '</div>', unsafe_allow_html=True
    )

    if probe_df.empty:
        st.info("No probe data yet. Run `py pipeline/probe_bot.py` to collect responses.")
        st.stop()

    # KPIs
    avg_sent   = probe_df["sentiment_score"].mean() if not probe_df.empty else 0.0
    sent_lbl   = _sent_label(avg_sent)
    sent_acc   = {"Positive":"#2e7d32","Neutral":MUTED,"Negative":RED}.get(sent_lbl, MUTED)

    # Sentiment as 0-100%  (-1..+1  →  0..100)
    import math
    _raw = avg_sent if (avg_sent is not None and not math.isnan(float(avg_sent))) else 0.0
    sent_pct = round((float(_raw) + 1.0) / 2.0 * 100.0, 1)

    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1, f"{probe_rate:.1f}", "Mention Rate",    suffix="%")
    kpi(c2, f"{probe_cited}/{probe_total}", "Cited / Total", accent=BLUE_LIGHT)

    with c3:
        gauge_color = sent_acc
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sent_pct,
            number={"suffix": "%", "valueformat": ".1f",
                    "font": {"size": 24, "color": TEXT}},
            title={"text": "AVG SENTIMENT",
                   "font": {"size": 10, "color": MUTED}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickvals": [0, 35, 65, 100],
                    "ticktext": ["Neg", "", "", "Pos"],
                    "tickfont": {"size": 9, "color": MUTED},
                    "tickwidth": 1,
                    "tickcolor": GRAY_MID,
                },
                "bar":        {"color": gauge_color, "thickness": 0.3},
                "bgcolor":    WHITE,
                "borderwidth": 0,
                "steps": [
                    {"range": [0,  35],  "color": "#fecaca"},
                    {"range": [35, 65],  "color": "#fdf6e3"},
                    {"range": [65, 100], "color": "#bbf7d0"},
                ],
            },
        ))
        fig_g.update_layout(
            height=150,
            margin=dict(l=16, r=16, t=32, b=4),
            paper_bgcolor=WHITE,
            font=dict(family="Segoe UI, sans-serif"),
        )
        st.markdown(
            f'<div style="background:{WHITE}; border:1px solid {GRAY_MID}; '
            f'border-top:3px solid {gauge_color}; border-radius:10px; '
            f'padding:2px 0 0; overflow:hidden;">',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_g, use_container_width=True,
                        config={"displayModeBar": False}, key="sent_gauge")
        st.markdown('</div>', unsafe_allow_html=True)

    kpi(c4, str(probe_df["run_date"].nunique()), "Days Tracked", accent="#2e7d32")
    kpi(c5, str(probe_df["source"].nunique()), "AI Tools Probed", accent="#7b1fa2")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Category toggle ───────────────────────────────────────────────────────
    toggle_col, filter_cols = st.columns([2, 4])

    with toggle_col:
        cat_filter = st.radio(
            "Category",
            ["All", "Local Drive", "NC State", "National"],
            horizontal=True,
            key="cat_toggle",
            label_visibility="collapsed",
        )

    # Source / Status / Search filters
    with filter_cols:
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            src_f = st.selectbox("AI Source", ["All"] + sorted(probe_df["source"].unique().tolist()),
                                 label_visibility="collapsed")
        with fc2:
            status_f = st.selectbox("Status", ["All", "Cited only", "Gaps only"],
                                    label_visibility="collapsed")
        with fc3:
            search_f = st.text_input("Search", placeholder="Filter queries...",
                                     label_visibility="collapsed")

    # Apply pre-agg filters
    filt = probe_df.copy()
    cat_map = {"Local Drive": "local", "NC State": "state", "National": "national"}
    if cat_filter != "All":
        filt = filt[filt["query"].apply(_query_cat) == cat_map[cat_filter]]
    if src_f != "All":
        filt = filt[filt["source"] == src_f]
    if search_f:
        filt = filt[filt["query"].str.contains(search_f, case=False, na=False)]

    # ── Aggregate: one row per unique query ──────────────────────────────────
    agg = filt.groupby("query").agg(
        cited_count  =("mentioned",       "sum"),
        total_runs   =("mentioned",       "count"),
        avg_sentiment=("sentiment_score", "mean"),
        latest_date  =("run_date",        "max"),
    ).reset_index()

    # Build a query -> best raw row lookup for the detail panel
    # Use most recent row but merge citations from all runs
    def _build_lookup_row(grp):
        best = grp.sort_values("run_date", ascending=False).iloc[0].copy()
        # Merge citations from all rows for this query
        all_cits = []
        for cits in grp["citations"]:
            if isinstance(cits, list): all_cits.extend(cits)
        best["citations"] = list(dict.fromkeys(all_cits))  # deduplicated
        # Prefer cited row's response if available
        cited_rows = grp[grp["mentioned"] == 1]
        if not cited_rows.empty:
            cr = cited_rows.sort_values("run_date", ascending=False).iloc[0]
            if _safe_text(cr.get("full_response")):
                best["full_response"] = cr["full_response"]
                best["brand_terms"]   = cr["brand_terms"]
        return best
    latest_lookup = {q: _build_lookup_row(grp) for q, grp in filt.groupby("query")}

    # Post-agg status filter
    if status_f == "Cited only":
        agg = agg[agg["cited_count"] > 0]
    elif status_f == "Gaps only":
        agg = agg[agg["cited_count"] == 0]

    agg = agg.sort_values(["cited_count","avg_sentiment"], ascending=[False,False]).reset_index(drop=True)

    cited_n  = int((agg["cited_count"] > 0).sum())
    total_n  = len(agg)
    st.markdown(
        f'<div style="font-size:0.75rem; color:{MUTED}; margin:8px 0 16px;">'
        f'{total_n} queries &nbsp;&middot;&nbsp; '
        f'<span style="color:#166534; font-weight:600;">{cited_n} cited</span> &nbsp;&middot;&nbsp; '
        f'{total_n - cited_n} gaps</div>',
        unsafe_allow_html=True
    )

    # ── Two-column layout: query list | detail panel ─────────────────────────
    list_col, detail_col = st.columns([1, 1])

    with list_col:
        if filt.empty:
            st.info("No queries match the current filters.")
            chosen_row = None
        else:
            # Destination abbreviation helper
            DEST_ABBR = {
                "Wilmington":         "WIL",
                "Wrightsville Beach": "WB",
                "Carolina Beach":     "CB",
                "Kure Beach":         "KB",
                "Figure Eight":       "F8",
                "Cape Fear Region":   "CF",
            }

            def _dest_str(d: dict) -> str:
                hits = [DEST_ABBR.get(k, k) for k, v in d.items() if v]
                return "  ".join(hits) if hits else "—"

            # Build aggregated display dataframe
            list_df = pd.DataFrame({
                "Status":       ["Cited" if c > 0 else "Not cited" for c in agg["cited_count"]],
                "Query":        agg["query"].tolist(),
                "Cited":        [f"{int(c)}/{int(t)}" for c, t in zip(agg["cited_count"], agg["total_runs"])],
                "Destinations": [_dest_str(latest_lookup[q].get("our_destinations", {}) if q in latest_lookup else {})
                                 for q in agg["query"]],
                "Sentiment":    [_sent_label(s) for s in agg["avg_sentiment"]],
                "Last Run":     agg["latest_date"].dt.strftime("%b %d").tolist(),
            })

            st.caption(f"{total_n} unique queries  |  click a row to see the latest AI response")

            event = st.dataframe(
                list_df,
                hide_index=True,
                use_container_width=True,
                height=520,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Status":       st.column_config.TextColumn("Status",       width=90),
                    "Query":        st.column_config.TextColumn("Query",        width="large"),
                    "Cited":        st.column_config.TextColumn("Cited",        width=75),
                    "Destinations": st.column_config.TextColumn("Destinations", width=110),
                    "Sentiment":    st.column_config.TextColumn("Sentiment",    width=90),
                    "Last Run":     st.column_config.TextColumn("Last Run",     width=75),
                },
            )

            sel_rows = event.selection.rows
            if sel_rows:
                chosen_row = agg.iloc[sel_rows[0]]
            else:
                chosen_row = None

    with detail_col:
        if chosen_row is None:
            st.markdown(
                f'<div style="background:{WHITE}; border:1px solid {GRAY_MID}; '
                f'border-radius:12px; padding:60px 20px; text-align:center; color:{MUTED}; margin-top:30px;">'
                f'<div style="font-weight:600; font-size:0.9rem; color:{TEXT};">Select a query</div>'
                f'<div style="font-size:0.78rem; margin-top:6px;">Click any row in the table to see the full AI response and sources</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            agg_row  = chosen_row
            raw_row  = latest_lookup.get(agg_row["query"], agg_row)
            cited    = int(agg_row.get("cited_count", 0)) > 0
            cited_ct = int(agg_row.get("cited_count", 0))
            total_ct = int(agg_row.get("total_runs", 1))
            src_lbl  = "Perplexity" if raw_row.get("source") == "perplexity" else "ChatGPT"
            def _safe_list(val):
                if val is None: return []
                if isinstance(val, list): return val
                if isinstance(val, str) and val.strip(): return json.loads(val)
                return []
            def _safe_dict(val):
                if val is None: return {}
                if isinstance(val, dict): return val
                if isinstance(val, str) and val.strip(): return json.loads(val)
                return {}
            all_urls  = _safe_list(raw_row.get("citations"))
            our_urls  = _safe_list(raw_row.get("cited_urls"))
            comp_hits = [k for k,v in _safe_dict(raw_row.get("competitors")).items() if v]
            resp_text, is_full = _resp(raw_row)
            brand_terms_row    = _safe_list(raw_row.get("brand_terms"))
            row = raw_row  # use raw row for remaining detail panel references
            resp_highlighted   = _highlight_brands(resp_text, brand_terms_row)
            s_col    = "#166534" if cited else "#6b7280"
            s_bg     = "#dcfce7" if cited else "#f3f4f6"
            cat_tag  = _query_cat(row["query"]).title()
            _raw_sent = agg_row.get("avg_sentiment") or raw_row.get("sentiment_score")
            sent_score = float(_raw_sent) if _raw_sent and str(_raw_sent).lower() not in ("nan","none","") else _sentiment(_safe_text(raw_row.get("full_response")) or _safe_text(raw_row.get("raw_snippet","")))
            sent_lbl_r = _sent_label(sent_score)
            sent_bg_r, sent_fg_r = _sent_color(sent_score)

            st.markdown(f"""
            <div style="background:{WHITE}; border:1px solid {GRAY_MID}; border-radius:12px;
                 padding:16px 18px; margin-bottom:12px;">
              <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin-bottom:10px;">
                <span style="background:{s_bg}; color:{s_col}; border-radius:999px;
                     padding:3px 12px; font-size:0.7rem; font-weight:700;">
                  {"Cited" if cited else "Not Cited"} &nbsp;{cited_ct}/{total_ct}</span>
                <span style="background:{BLUE_PALE}; color:{BLUE2}; border-radius:999px;
                     padding:3px 12px; font-size:0.7rem; font-weight:700;">{src_lbl}</span>
                <span style="background:{sent_bg_r}; color:{sent_fg_r}; border-radius:999px;
                     padding:3px 12px; font-size:0.7rem; font-weight:700;">
                  {sent_lbl_r} ({sent_score:+.2f})</span>
                <span style="background:#f0fdf4; color:#166534; border-radius:999px;
                     padding:3px 12px; font-size:0.7rem; font-weight:700;">{cat_tag}</span>
                <span style="color:{MUTED}; font-size:0.7rem;">
                  Last run: {row.get('latest_date', row.get('run_date', '')).strftime('%b %d, %Y')}</span>
              </div>
              <div style="font-size:0.95rem; font-weight:700; color:{TEXT}; line-height:1.4;">
                {row['query']}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Sentiment quote ───────────────────────────────────────────────
            resp_plain = (_safe_text(row.get("full_response"))
                          or _safe_text(row.get("raw_snippet")) or "")
            quote = _html.escape(_extract_quote(resp_plain, sent_score))
            st.markdown(
                f'<div style="background:{sent_bg_r}; border:1.5px solid {sent_fg_r}40; '
                f'border-radius:8px; padding:14px 16px; margin-bottom:14px;">'
                f'<div style="font-size:0.65rem; font-weight:800; text-transform:uppercase; '
                f'letter-spacing:0.9px; color:{sent_fg_r}; margin-bottom:6px;">'
                f'{sent_lbl_r} &nbsp;({sent_score:+.2f})</div>'
                f'<div style="font-size:0.85rem; line-height:1.75; color:{TEXT}; font-style:italic;">'
                f'&ldquo;{quote}&rdquo;</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Full AI response with brand-term highlights ───────────────────
            resp_label = "Full AI Response" if is_full else "AI Response Preview"
            st.markdown(f"**{resp_label}**")
            if not is_full:
                st.caption("Only a 300-char preview is stored. Full responses are captured on the next probe run.")
            st.markdown(
                f'<div style="background:{GRAY_LIGHT}; border:1px solid {GRAY_MID}; '
                f'border-radius:8px; padding:14px; font-size:0.82rem; line-height:1.85; '
                f'color:{TEXT}; white-space:pre-wrap;">'
                f'{resp_highlighted}</div>',
                unsafe_allow_html=True,
            )

            st.markdown(f"**Sources Cited** ({len(all_urls)})")
            if all_urls:
                for u in all_urls:
                    is_ours = any(s in u.lower() for s in ["wilmingtonandbeaches","visitwilmington"])
                    prefix  = "Our page: " if is_ours else ""
                    color   = "#166534" if is_ours else BLUE
                    weight  = "700" if is_ours else "400"
                    st.markdown(
                        f'<a href="{u}" target="_blank" style="display:block; color:{color}; '
                        f'font-size:0.74rem; font-weight:{weight}; padding:4px 0; '
                        f'border-bottom:1px solid {GRAY_MID}; text-decoration:none; '
                        f'overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">'
                        f'{prefix}{u}</a>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No sources captured for this response.")

            # Destination mentions
            dest_hits_row = _safe_dict(raw_row.get("our_destinations"))
            dest_mentioned = [k for k, v in dest_hits_row.items() if v]
            if dest_mentioned:
                DEST_COLORS = {
                    "Wilmington":         ("#e0f2f1", "#00695c"),
                    "Wrightsville Beach": ("#e3f2fd", "#1565c0"),
                    "Carolina Beach":     ("#f3e5f5", "#6a1b9a"),
                    "Kure Beach":         ("#fff8e1", "#e65100"),
                    "Figure Eight":       ("#fce4ec", "#880e4f"),
                    "Cape Fear Region":   ("#e8f5e9", "#2e7d32"),
                }
                st.markdown("**Our Destinations Mentioned**")
                dest_badges = " ".join(
                    f'<span style="background:{DEST_COLORS.get(d,("#f5f5f5","#333"))[0]}; '
                    f'color:{DEST_COLORS.get(d,("#f5f5f5","#333"))[1]}; '
                    f'border-radius:999px; padding:3px 11px; font-size:0.7rem; '
                    f'font-weight:700; margin:2px; display:inline-block;">{d}</span>'
                    for d in dest_mentioned
                )
                st.markdown(dest_badges, unsafe_allow_html=True)

            if comp_hits:
                st.markdown("**Competitors mentioned**")
                badges = " ".join(
                    f'<span style="background:#fff8e1; color:#856404; border-radius:999px; '
                    f'padding:3px 10px; font-size:0.7rem; font-weight:700; '
                    f'margin:2px; display:inline-block;">{c}</span>'
                    for c in comp_hits
                )
                st.markdown(badges, unsafe_allow_html=True)

    # ── Destination + Competitor + Gap charts ────────────────────────────────
    col_dest, col_comp, col_gap = st.columns(3)

    with col_dest:
        st.markdown('<div class="card"><div class="card-title">Our Destinations Mentioned</div>', unsafe_allow_html=True)
        dest_counts = {d: {"c": 0, "t": 0} for d in OUR_DESTINATIONS}
        for _, row in probe_df.iterrows():
            dmap = row.get("our_destinations") or {}
            for d in OUR_DESTINATIONS:
                dest_counts[d]["t"] += 1
                if dmap.get(d):
                    dest_counts[d]["c"] += 1
        dest_rows = [{"Destination": d,
                      "Rate": round(v["c"] / max(v["t"], 1) * 100, 1)}
                     for d, v in dest_counts.items()
                     if v["c"] > 0]
        dest_rows.sort(key=lambda x: x["Rate"])
        if dest_rows:
            ddf = pd.DataFrame(dest_rows)
            DEST_BAR_COLORS = {
                "Wilmington":         BLUE,
                "Wrightsville Beach": "#1565c0",
                "Carolina Beach":     "#6a1b9a",
                "Kure Beach":         "#e65100",
                "Figure Eight":       "#880e4f",
                "Cape Fear Region":   GREEN,
            }
            fig_d = px.bar(ddf, x="Rate", y="Destination", orientation="h",
                           labels={"Rate": "Mention Rate (%)"})
            fig_d.update_traces(
                marker_color=[DEST_BAR_COLORS.get(d, BLUE) for d in ddf["Destination"]]
            )
            fig_d.update_layout(height=280, **PLOTLY)
            st.plotly_chart(fig_d, use_container_width=True)
        else:
            st.caption("No destination mentions detected yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_comp:
        st.markdown('<div class="card"><div class="card-title">Competitor Mention Rate</div>', unsafe_allow_html=True)
        comp_counts = {}
        for _, row in probe_df.iterrows():
            for comp, hit in row["competitors"].items():
                comp_counts.setdefault(comp, {"c":0,"t":0})
                comp_counts[comp]["t"] += 1
                if hit: comp_counts[comp]["c"] += 1
        comp_rows = [{"Destination":"Wilmington & Beaches","Rate":round(probe_rate,1),"ours":True}]
        for comp, v in comp_counts.items():
            comp_rows.append({"Destination":comp,"Rate":round(v["c"]/max(v["t"],1)*100,1),"ours":False})
        cdf = pd.DataFrame(comp_rows).sort_values("Rate", ascending=True)
        fig_c = px.bar(cdf, x="Rate", y="Destination", orientation="h",
                       labels={"Rate":"Mention Rate (%)"})
        fig_c.update_traces(marker_color=[BLUE if r else GRAY_MID for r in cdf["ours"]])
        fig_c.update_layout(height=300, **PLOTLY)
        st.plotly_chart(fig_c, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_gap:
        st.markdown('<div class="card"><div class="card-title">Gap Analysis — click a row for content ideas</div>', unsafe_allow_html=True)

        # Build gap table ranked by opportunity
        gap_raw = (probe_df[probe_df["mentioned"]==0]
                   .groupby("query").size().reset_index(name="missed"))
        total_runs = (probe_df.groupby("query").size().reset_index(name="total"))
        gap_raw = gap_raw.merge(total_runs, on="query", how="left")
        gap_raw["category"]  = gap_raw["query"].apply(_query_cat)
        cat_w = {"local": 1.3, "state": 1.1, "national": 0.9}
        gap_raw["opp_score"] = (
            gap_raw["missed"] / gap_raw["total"].clip(lower=1) * 100
            * gap_raw["category"].map(cat_w).fillna(1.0)
        ).round(0).astype(int)
        gap_raw = gap_raw.sort_values("opp_score", ascending=False).head(16).reset_index(drop=True)
        gap_raw["rank"] = [f"#{i+1}" for i in range(len(gap_raw))]

        if gap_raw.empty:
            st.success("Cited in every tracked query!")
            gap_sel = None
        else:
            gap_display = pd.DataFrame({
                "Rank":       gap_raw["rank"],
                "Query":      gap_raw["query"],
                "Category":   gap_raw["category"].str.title(),
                "Missed":     gap_raw["missed"],
                "Opportunity":gap_raw["opp_score"].astype(str) + "%",
            })
            gap_evt = st.dataframe(
                gap_display,
                hide_index=True,
                use_container_width=True,
                height=360,
                on_select="rerun",
                selection_mode="single-row",
                key="gap_table",
                column_config={
                    "Rank":        st.column_config.TextColumn(width=55),
                    "Query":       st.column_config.TextColumn(width="large"),
                    "Category":    st.column_config.TextColumn(width=80),
                    "Missed":      st.column_config.NumberColumn(width=65),
                    "Opportunity": st.column_config.TextColumn(width=90),
                },
            )
            sel = gap_evt.selection.rows
            gap_sel = gap_raw.iloc[sel[0]] if sel else None

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Content suggestion panel (full width, below both charts) ─────────────
    if gap_sel is not None:
        blurb, todos = _content_suggestion(gap_sel["query"])
        cat_r    = gap_sel["category"]
        cat_bg   = {"local":"#e0f2f1","state":"#e8f5e9","national":"#e3f2fd"}.get(cat_r,"#f5f5f5")
        cat_fg   = {"local":"#00695c","state":"#2e7d32","national":"#1565c0"}.get(cat_r,"#555")
        opp_r    = int(gap_sel["opp_score"])

        _todo_item = '<div style="display:flex;align-items:flex-start;gap:10px;padding:7px 0;border-bottom:1px solid {gm};"><span style="width:16px;height:16px;border:2px solid {bl};border-radius:3px;flex-shrink:0;margin-top:2px;display:inline-block;"></span><span style="font-size:0.82rem;color:{tx};line-height:1.5;">{td}</span></div>'
        _todos_html = "".join(_todo_item.format(gm=GRAY_MID, bl=BLUE, tx=TEXT, td=todo) for todo in todos)

        st.markdown(f"""
        <div style="background:{WHITE}; border:1px solid {GRAY_MID}; border-left:4px solid {BLUE};
             border-radius:12px; padding:20px 24px; margin-top:6px;">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px; flex-wrap:wrap;">
            <span style="font-size:0.8rem; font-weight:800; color:{TEXT};">Content Opportunity</span>
            <span style="background:{cat_bg}; color:{cat_fg}; border-radius:999px;
                 padding:3px 10px; font-size:0.68rem; font-weight:700;">{cat_r.title()}</span>
            <span style="background:{BLUE_PALE}; color:{BLUE2}; border-radius:999px;
                 padding:3px 10px; font-size:0.68rem; font-weight:700;">
              Opportunity score: {opp_r}%</span>
            <span style="font-size:0.8rem; color:{MUTED}; font-style:italic;">
              &ldquo;{gap_sel['query']}&rdquo;</span>
          </div>
          <div style="font-size:0.83rem; line-height:1.75; color:{TEXT}; margin-bottom:16px;">
            {blurb}</div>
          <div style="font-size:0.72rem; font-weight:800; text-transform:uppercase;
               letter-spacing:0.9px; color:{MUTED}; margin-bottom:10px;">Action Items</div>
          {_todos_html}
        </div>
        """, unsafe_allow_html=True)

    # ── Top Websites Citing Our Destinations ─────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="card-title">Top Websites Mentioning Our Destinations</div>', unsafe_allow_html=True)

    from urllib.parse import urlparse
    domain_data = {}
    for _, row in probe_df.iterrows():
        cits = row.get("citations", [])
        if not isinstance(cits, list): continue
        dests = row.get("our_destinations", {})
        if not isinstance(dests, dict): continue
        dest_list = [k for k, v in dests.items() if v]
        for url in cits:
            try:
                domain = urlparse(url).netloc.replace("www.", "")
                if not domain: continue
                if domain not in domain_data:
                    domain_data[domain] = {"appearances": 0, "destinations": set(), "queries": set(), "urls": []}
                domain_data[domain]["appearances"] += 1
                domain_data[domain]["destinations"].update(dest_list)
                domain_data[domain]["queries"].add(row.get("query",""))
                if url not in domain_data[domain]["urls"]:
                    domain_data[domain]["urls"].append(url)
            except Exception:
                continue

    if domain_data:
        src_rows = [
            {
                "Domain":       d,
                "Appearances":  v["appearances"],
                "Destinations": ", ".join(sorted(v["destinations"])) or "—",
                "Queries":      len(v["queries"]),
                "Sample URL":   v["urls"][0] if v["urls"] else "",
            }
            for d, v in domain_data.items()
        ]
        src_df = pd.DataFrame(src_rows).sort_values("Appearances", ascending=False).reset_index(drop=True)
        st.dataframe(
            src_df,
            hide_index=True,
            use_container_width=True,
            height=400,
            column_config={
                "Domain":       st.column_config.TextColumn("Domain",        width="medium"),
                "Appearances":  st.column_config.NumberColumn("Appearances", width=110),
                "Destinations": st.column_config.TextColumn("Destinations",  width="large"),
                "Queries":      st.column_config.NumberColumn("Queries",     width=90),
                "Sample URL":   st.column_config.LinkColumn("Sample URL",    width="large"),
            },
        )
    else:
        st.caption("No citation data yet — citations populate after probe runs.")
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# TRAFFIC TRENDS
# ==============================================================================
elif page == "traffic":
    st.markdown(
        '<div class="page-header">'
        '<div class="page-title">Traffic Trends</div>'
        f'<div class="page-sub">AI-referred sessions from GA4 &mdash; {start_d.strftime("%b %d")} to {end_d.strftime("%b %d, %Y")}</div>'
        '</div>', unsafe_allow_html=True
    )
    if df.empty:
        st.info("No traffic data. Run `py pipeline/ga4_client.py`.")
        st.stop()

    c1,c2,c3,c4 = st.columns(4)
    kpi(c1, f"{total_ai:,}", "AI Sessions", delta=growth)
    kpi(c2, f"{avg_share:.1f}", "AI Share", suffix="%", accent=BLUE_LIGHT)
    kpi(c3, f"{eng_rate:.1f}", "Engaged Rate", suffix="%", accent="#2e7d32")
    kpi(c4, str(n_sources), "Active Sources", accent="#7b1fa2")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">Sessions by AI Source Over Time</div>', unsafe_allow_html=True)
    fig = px.area(
        df.groupby(["date","source_name"])["sessions"].sum().reset_index(),
        x="date", y="sessions", color="source_name",
        color_discrete_sequence=[BLUE, BLUE_LIGHT, GREEN, "#f97316", "#9c27b0"],
        labels={"sessions":"Sessions","date":"","source_name":"Source"}
    )
    fig.update_layout(height=300, hovermode="x unified", legend_title="", **PLOTLY)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><div class="card-title">Share by AI Tool</div>', unsafe_allow_html=True)
        fig2 = px.pie(src, values="sessions", names="source_name", hole=0.55,
                      color_discrete_sequence=[BLUE, BLUE_LIGHT, GREEN, "#f97316", "#9c27b0"])
        fig2.update_layout(height=260, **PLOTLY)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><div class="card-title">AI Traffic Share Trend</div>', unsafe_allow_html=True)
        if not summary.empty:
            fig3 = px.line(summary, x="date", y="ai_share_pct", markers=True,
                           labels={"ai_share_pct":"Share (%)","date":""})
            fig3.update_traces(line_color=BLUE, line_width=2,
                               fill="tozeroy", fillcolor="rgba(5,118,166,0.07)")
            fig3.update_layout(height=260, **PLOTLY)
            st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">Source Performance Table</div>', unsafe_allow_html=True)
    disp = src.copy()
    disp["eng_rate"]  = disp["eng_rate"].round(1).astype(str) + "%"
    disp["conv_rate"] = disp["conv_rate"].round(1).astype(str) + "%"
    disp["share"]     = disp["share"].round(1).astype(str) + "%"
    st.dataframe(
        disp.rename(columns={
            "source_name":"AI Tool","sessions":"Sessions","share":"Share",
            "conversions":"Conversions","engaged":"Engaged",
            "eng_rate":"Engaged Rate","conv_rate":"Conv Rate"
        })[["AI Tool","Sessions","Share","Engaged","Engaged Rate","Conversions","Conv Rate"]],
        hide_index=True, use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# GEOGRAPHY
# ==============================================================================
elif page == "geo":
    st.markdown(
        '<div class="page-header">'
        '<div class="page-title">Geography</div>'
        '<div class="page-sub">Where AI-referred visitors originate</div>'
        '</div>', unsafe_allow_html=True
    )
    if df.empty:
        st.info("No traffic data.")
        st.stop()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    geo = df.groupby("country")["sessions"].sum().reset_index()
    fig_map = px.choropleth(
        geo, locations="country", locationmode="country names",
        color="sessions", hover_name="country",
        color_continuous_scale=[[0, BLUE_PALE], [1, NAVY]],
        title="Visitors by Country"
    )
    fig_map.update_layout(
        height=380,
        geo=dict(showframe=False, bgcolor="rgba(0,0,0,0)",
                 showcoastlines=True, coastlinecolor=GRAY_MID),
        **PLOTLY
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><div class="card-title">Top US States</div>', unsafe_allow_html=True)
        us = df[df["country"]=="United States"]
        if not us.empty:
            r = us.groupby("region")["sessions"].sum().reset_index().sort_values("sessions",ascending=False).head(14)
            fig_r = px.bar(r, x="sessions", y="region", orientation="h",
                           color="sessions", color_continuous_scale=[[0,BLUE_PALE],[1,BLUE]])
            fig_r.update_layout(height=360, yaxis={"categoryorder":"total ascending"}, **PLOTLY)
            st.plotly_chart(fig_r, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><div class="card-title">Top Cities</div>', unsafe_allow_html=True)
        cities = df.groupby("city")["sessions"].sum().reset_index().sort_values("sessions",ascending=False).head(14)
        fig_c = px.bar(cities, x="sessions", y="city", orientation="h",
                       color="sessions", color_continuous_scale=[[0,"#f0fdf4"],[1,GREEN]])
        fig_c.update_layout(height=360, yaxis={"categoryorder":"total ascending"}, **PLOTLY)
        st.plotly_chart(fig_c, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# LANDING PAGES
# ==============================================================================
elif page == "lp":
    st.markdown(
        '<div class="page-header">'
        '<div class="page-title">Landing Pages</div>'
        '<div class="page-sub">Pages AI tools are sending visitors to</div>'
        '</div>', unsafe_allow_html=True
    )
    if df.empty:
        st.info("No traffic data.")
        st.stop()

    pages_data = (df.groupby("landing_page")
                    .agg(sessions=("sessions","sum"), conversions=("conversions","sum"),
                         engaged=("engaged_sessions","sum"))
                    .reset_index().sort_values("sessions",ascending=False).head(30))
    pages_data["conv_rate"]    = (pages_data["conversions"]/pages_data["sessions"]*100).round(1)
    pages_data["engaged_rate"] = (pages_data["engaged"]/pages_data["sessions"]*100).round(1)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig_p = px.bar(
        pages_data.head(15), x="sessions", y="landing_page", orientation="h",
        color="engaged_rate",
        color_continuous_scale=[[0,BLUE_PALE],[0.5,BLUE],[1,GREEN]],
        title="Top Landing Pages  (colored by engagement rate)",
        labels={"landing_page":"","sessions":"Sessions","engaged_rate":"Engaged %"}
    )
    fig_p.update_layout(height=480, yaxis={"categoryorder":"total ascending"}, **PLOTLY)
    st.plotly_chart(fig_p, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">All Pages</div>', unsafe_allow_html=True)
    st.dataframe(
        pages_data.rename(columns={
            "landing_page":"Page","sessions":"Sessions",
            "conversions":"Conversions","conv_rate":"Conv %",
            "engaged":"Engaged","engaged_rate":"Engaged %"
        }),
        hide_index=True, use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
