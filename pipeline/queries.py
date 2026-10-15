"""
120 destination probe queries for Wilmington & Beaches CVB
(60 core discovery + 60 seasonal / event-focused).
Focused on state/regional discovery — where AI tools recommend destinations
without being asked specifically about Wilmington.
"""

import re


def signal_found(signal: str, content: str) -> bool:
    """Whole-word match of a lowercase signal in lowercase content.

    Plain substring matching miscounted mentions: "destin" matched
    "destination", and "carolina beach" matched "North Carolina beaches".
    """
    pattern = r"\b" + re.escape(signal) + r"\b"
    if signal == "carolina beach":
        pattern = r"(?<!north )(?<!south )" + pattern
    return re.search(pattern, content) is not None


# Your brand signals — any response containing these counts as a mention
BRAND_SIGNALS = [
    "wilmingtonandbeaches.com",
    "wilmington and beaches",
    "wilmington, nc",
    "wilmington nc",
    "wrightsville beach",
    "carolina beach",
    "kure beach",
    "figure eight island",
    "cape fear",
    "port city",
]

# Our destination signals — which specific beach/city is AI mentioning?
OUR_DESTINATIONS = {
    "Wilmington":         ["wilmington"],
    "Wrightsville Beach": ["wrightsville beach"],
    "Carolina Beach":     ["carolina beach"],
    "Kure Beach":         ["kure beach"],
    "Figure Eight":       ["figure eight island", "figure 8 island"],
    "Cape Fear Region":   ["cape fear"],
}

# Competitors to track
COMPETITORS = {
    "Myrtle Beach":   ["myrtle beach", "myrtlebeach.com"],
    "Outer Banks":    ["outer banks", "obx", "outerbanks.org"],
    "Virginia Beach": ["virginia beach", "virginiabeach.com"],
    "Hilton Head":    ["hilton head", "hiltonheadisland.org"],
    "Pawleys Island": ["pawleys island"],
    "Isle of Palms":  ["isle of palms"],
    "Emerald Isle":   ["emerald isle"],
    "Oak Island":     ["oak island"],
    "Tybee Island":   ["tybee island"],
    "30A / Destin":   ["30a", "destin", "seaside florida"],
}

QUERIES = [
    # ── LOCAL: Drive market queries (20) ──────────────────────────────────
    "best beach from Charlotte NC",
    "closest beach to Charlotte NC",
    "best beach weekend from Charlotte NC",
    "beaches within driving distance of Charlotte",
    "best beach vacation from Raleigh NC",
    "closest beach to Raleigh NC",
    "best beach day trip from Raleigh NC",
    "best beach getaway from Raleigh NC",
    "best beach trip from Durham NC",
    "closest beach to Durham NC",
    "best beaches driving distance from Greensboro NC",
    "best beach from Greensboro NC",
    "best beach from Winston-Salem NC",
    "closest beach to Winston-Salem NC",
    "best beach from Fayetteville NC",
    "closest beach to Fayetteville NC",
    "best beach from Chapel Hill NC",
    "best beach road trip from Asheville NC",
    "best beach vacation from Charlotte",
    "best beach trip from the NC piedmont",

    # ── REGIONAL: North Carolina / state-level queries (20) ───────────────
    "best beaches in North Carolina",
    "best beach towns in North Carolina",
    "top NC beach destinations",
    "most beautiful beaches in North Carolina",
    "best NC beaches for families",
    "best NC beach towns to visit in summer",
    "hidden gem beaches in North Carolina",
    "best beaches in North Carolina for swimming",
    "underrated beach towns in North Carolina",
    "where to go to the beach in North Carolina",
    "best coastal towns in North Carolina",
    "NC beach vacation guide",
    "most popular North Carolina beaches",
    "best North Carolina beaches for couples",
    "best beach weekend getaway in North Carolina",
    "best NC beach towns for nightlife",
    "best NC beach towns for foodies",
    "most charming small towns on the NC coast",
    "best NC beaches for surfing",
    "NC beach towns with a historic downtown",

    # ── NATIONAL: East Coast / Southeast / broad US queries (20) ──────────
    "best beaches on the East Coast",
    "best beach towns on the East Coast",
    "top East Coast beach destinations",
    "most beautiful East Coast beaches",
    "best East Coast beaches for families",
    "underrated East Coast beach towns",
    "best small beach towns on the East Coast",
    "best East Coast beaches for couples",
    "most charming beach towns on the East Coast",
    "best East Coast beach destinations for a long weekend",
    "best beaches in the South",
    "best beach towns in the Southeast",
    "best beaches in the Southeast United States",
    "underrated southern beach destinations",
    "best southern beach towns for couples",
    "best beach destinations for a bachelorette trip",
    "best beach towns for a girls trip",
    "best beach towns for a romantic getaway",
    "best beach destinations for outdoor activities",
    "best US beach towns to visit in 2025",

    # ── LOCAL: Seasonal / event drive-market queries (20) ─────────────────
    "fall beach weekend from Charlotte NC",
    "Thanksgiving beach getaway from Raleigh NC",
    "Christmas holiday beach trip from Charlotte",
    "New Year's Eve beach getaway from Raleigh",
    "spring break beach trip from Durham NC",
    "Mother's Day beach weekend from Greensboro NC",
    "Fourth of July fireworks beach trip from Charlotte NC",
    "Labor Day beach weekend from Raleigh NC",
    "beach music festival weekend from Winston-Salem",
    "fishing tournament beach trip from Fayetteville NC",
    "winter beach escape from Asheville NC",
    "off-season beach getaway from Chapel Hill NC",
    "beach town with a fall seafood festival near Raleigh",
    "Valentine's Day beach weekend from Charlotte NC",
    "fall break beach trip from Durham NC",
    "holiday lights and beach weekend from Greensboro NC",
    "beach weekend with outdoor concerts from Charlotte",
    "surf competition weekend road trip from Raleigh",
    "Memorial Day beach weekend from Winston-Salem NC",
    "kid-friendly beach trip during winter break from Charlotte NC",

    # ── REGIONAL: Seasonal / event NC queries (20) ────────────────────────
    "best fall festivals on the North Carolina coast",
    "North Carolina beach towns with Christmas boat parades",
    "where to see sea turtle nesting in North Carolina",
    "best NC beach towns for an oyster roast in winter",
    "best North Carolina beaches in the off-season",
    "events on the NC coast in October",
    "best North Carolina beach towns for New Year's Eve",
    "best places on the NC coast for a spring wedding",
    "best North Carolina beaches for fall fishing",
    "North Carolina coastal towns with farmers markets",
    "best NC coast towns for Fourth of July fireworks",
    "best North Carolina beaches for shelling in winter",
    "best NC beach towns for a fall food and wine festival",
    "best North Carolina coast towns for spring azalea gardens",
    "best North Carolina beaches for a Thanksgiving getaway",
    "North Carolina beach towns with summer outdoor concert series",
    "best NC coast destinations for a holiday shopping weekend",
    "North Carolina coastal towns with a film festival",
    "best North Carolina beaches for kayaking in the fall",
    "NC beach towns that host surf contests",

    # ── NATIONAL: Seasonal / event East Coast / Southeast queries (20) ────
    "best East Coast beach towns for a fall getaway",
    "best beach towns for Christmas on the East Coast",
    "best beach destinations for Thanksgiving in the Southeast",
    "East Coast beach towns for a New Year's Eve trip",
    "best beach towns for holiday lights in the Southeast",
    "quiet East Coast beaches for spring break",
    "best beach towns for a fall seafood festival",
    "East Coast beach towns with big Fourth of July celebrations",
    "best Southeast beaches to visit in October",
    "best East Coast beaches for a winter escape",
    "best southern beach towns for spring flower festivals",
    "where to see sea turtles hatch on the Atlantic coast",
    "best East Coast beach destinations for a fall fishing trip",
    "best East Coast beach towns for an off-season vacation",
    "East Coast beach towns with film festivals",
    "best East Coast beach towns for live music in summer",
    "best Southeast beach destinations for Labor Day weekend",
    "best East Coast beach towns for a fall wedding",
    "best beach towns for a December holiday family trip",
    "best East Coast beaches for a family spring break",
]

# Category tags: "local" = drive-market, "regional" = NC/state-level, "national" = broader US
QUERY_CATEGORIES = {
    **{q: "local"    for q in QUERIES[0:20]},   # Drive market queries
    **{q: "regional" for q in QUERIES[20:40]},  # NC / state-level queries
    **{q: "national" for q in QUERIES[40:60]},  # East Coast / Southeast / broad US
    **{q: "local"    for q in QUERIES[60:80]},   # Seasonal / event drive market
    **{q: "regional" for q in QUERIES[80:100]},  # Seasonal / event NC
    **{q: "national" for q in QUERIES[100:120]}, # Seasonal / event national
}
