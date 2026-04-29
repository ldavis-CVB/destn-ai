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
]

# Category tags: "local" = drive-market, "regional" = NC/state-level, "national" = broader US
QUERY_CATEGORIES = {
    **{q: "local"    for q in QUERIES[0:20]},   # Drive market queries
    **{q: "regional" for q in QUERIES[20:40]},  # NC / state-level queries
    **{q: "national" for q in QUERIES[40:60]},  # East Coast / Southeast / broad US
}
