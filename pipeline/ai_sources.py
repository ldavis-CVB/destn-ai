"""
AI referrer classification — maps known AI tool domains to display names and categories.
Add new sources here as they emerge.
"""

AI_SOURCES = {
    # Conversational AI
    "chatgpt.com": {"name": "ChatGPT", "category": "Conversational AI", "color": "#10a37f"},
    "chat.openai.com": {"name": "ChatGPT", "category": "Conversational AI", "color": "#10a37f"},
    "claude.ai": {"name": "Claude", "category": "Conversational AI", "color": "#d97706"},
    "gemini.google.com": {"name": "Gemini", "category": "Conversational AI", "color": "#4285f4"},
    "bard.google.com": {"name": "Gemini", "category": "Conversational AI", "color": "#4285f4"},

    # AI Search
    "perplexity.ai": {"name": "Perplexity", "category": "AI Search", "color": "#6366f1"},
    "copilot.microsoft.com": {"name": "Copilot", "category": "AI Search", "color": "#0078d4"},
    "bing.com": {"name": "Bing AI", "category": "AI Search", "color": "#0078d4"},

    # Other AI tools
    "you.com": {"name": "You.com", "category": "AI Search", "color": "#8b5cf6"},
    "phind.com": {"name": "Phind", "category": "AI Search", "color": "#ec4899"},
    "poe.com": {"name": "Poe", "category": "Conversational AI", "color": "#14b8a6"},
    "character.ai": {"name": "Character.AI", "category": "Conversational AI", "color": "#f59e0b"},
}

def classify_referrer(hostname: str) -> dict | None:
    """Return AI source info if hostname matches a known AI tool, else None."""
    if not hostname:
        return None
    hostname = hostname.lower().lstrip("www.")
    for domain, info in AI_SOURCES.items():
        if hostname == domain or hostname.endswith(f".{domain}"):
            return {"domain": domain, **info}
    return None

def get_all_domains() -> list[str]:
    return list(AI_SOURCES.keys())
