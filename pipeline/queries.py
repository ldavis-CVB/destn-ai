"""
60 destination probe queries for Wilmington & Beaches CVB.
Focused on state/regional discovery — where AI tools recommend destinations
without being asked specifically about Wilmington.
"""

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
    # ── North Carolina beaches ─────────────────────────────────────────────
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

    # ── East Coast ─────────────────────────────────────────────────────────
    "best beaches on the East Coast",
    "best beach towns on the East Coast",
    "top East Coast beach destinations",
    "most beautiful East Coast beaches",
    "best East Coast beaches for families",
    "underrated East Coast beach towns",
    "best East Coast beach vacation spots",
    "best small beach towns on the East Coast",
    "best East Coast beaches for couples",
    "East Coast beach towns with great food and nightlife",
    "best East Coast beach destinations for a long weekend",
    "most charming beach towns on the East Coast",
    "best beaches on the Atlantic Coast",
    "affordable East Coast beach vacations",
    "best East Coast beaches for surfing",

    # ── Southeast / South ──────────────────────────────────────────────────
    "best beaches in the South",
    "best beach towns in the Southeast",
    "top beach destinations in the Southeast US",
    "best southern beach vacations",
    "best beaches in the Southeast United States",
    "most beautiful beaches in the Southeast",
    "best beach getaways in the Southeast",
    "best beach towns in the southern US",
    "underrated southern beach destinations",
    "best coastal towns in the Southeast",
    "best beaches for families in the South",
    "best southern beach towns for couples",

    # ── Regional drive markets ─────────────────────────────────────────────
    "best beach from Charlotte NC",
    "closest beach to Charlotte NC",
    "best beach vacation from Raleigh NC",
    "closest beach to Raleigh NC",
    "best beach trip from Durham NC",
    "best beach road trip from Atlanta",
    "best beach vacation from Charlotte",
    "best beaches driving distance from Greensboro NC",

    # ── General discovery ──────────────────────────────────────────────────
    "best US beach towns to visit in 2025",
    "most underrated beach destinations in America",
    "best beach towns in the US for history and culture",
    "best beach towns in the US for foodies",
    "best beach destinations for a bachelorette trip",
    "best beach towns for a girls trip",
    "best beach towns for a guys trip",
    "best beach towns for a romantic getaway",
    "best beach towns with great downtown areas",
    "best beach destinations for outdoor activities",
]

# Category tags: "local" = drive-market queries, "state" = NC-specific, "national" = broader
QUERY_CATEGORIES = {
    **{q: "state"    for q in QUERIES[0:15]},   # North Carolina beaches
    **{q: "national" for q in QUERIES[15:42]},  # East Coast + Southeast/South
    **{q: "local"    for q in QUERIES[42:50]},  # Regional drive markets
    **{q: "national" for q in QUERIES[50:]},    # General US discovery
}
