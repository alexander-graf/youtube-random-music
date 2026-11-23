"""Zufallsbegriffe für die Suche und Ausschlusswörter gegen Nicht-Musik.

Die Listen hier sind nur Vorgaben. Was der Anwender in der App unter
„Begriffe…“ ändert, landet in begriffe.json (siehe storage.py) und hat Vorrang.
"""
import random
import re

import storage

DEFAULT_GENRES = [
    # Electronica & Chill
    "Ambient", "Lofi Beats", "Synthwave", "Vaporwave", "IDM", "Trip-Hop",
    "Dub Techno", "Deep House", "Minimal Techno", "Microhouse", "Ambient Techno",
    "Glitch Hop", "Chillhop", "Folktronica", "Outrun", "Space Ambient",
    "Mallsoft", "Dreampunk", "Chiptune", "Downtempo", "Future Garage",

    # Rock & Metal (Alternative/Indie/Psych)
    "Shoegaze", "Post-Rock", "Math Rock", "Psychedelic Rock", "Krautrock",
    "Desert Rock", "Post-Punk", "Goth Rock", "Garage Rock", "Post-Metal",
    "Dream Pop", "Indie Pop", "Slowcore", "Sadcore", "Space Rock", "Stoner Rock",
    "Surf Rock", "Noise Rock", "No Wave", "Blackgaze",
    "Doom Metal", "Sludge Metal", "Deathrock",

    # Folk & Acoustic
    "Indie Folk", "Neofolk", "Pagan Folk", "Chamber Pop", "Folk Horror",
    "Folk Rock", "Freak Folk", "Bluegrass", "Americana",

    # Jazz & Blues
    "Acid Jazz", "Darkjazz", "Jazz Hop", "Avant-Garde Jazz", "Free Jazz",
    "Nu-Jazz", "Ethio-Jazz", "Hard Bop", "Cool Jazz", "Delta Blues",

    # Soul, Funk & World
    "Afrobeat", "Bossa Nova", "Samba", "Tropicália", "City Pop", "Highlife",
    "Ska", "Rocksteady", "Dub Reggae", "Balkan Beat", "Anatolian Rock", "Chicha",
    "Cumbia", "Latin Jazz", "Desert Blues", "G-Funk", "P-Funk", "Neo-Soul",

    # Experimental & Niche
    "Dungeon Synth", "Ethereal Wave", "Minimal Synth", "Minimal Wave",
    "Neo-Classical", "Dark Ambient", "Drone", "Plunderphonics",
    "Breakcore", "Art Punk", "Riot Grrrl", "Twee Pop", "Baroque Pop",
]

# Wörter, die nach seltenen Aufnahmen klingen. Stimmungswörter wie „cozy“ oder
# „cinematic“ sind bewusst raus: die liefern vor allem 10-Stunden-Kanäle.
DEFAULT_ADJECTIVES = [
    "obscure", "rare", "underrated", "forgotten", "lost", "bedroom",
    "raw", "unknown", "underground", "private press", "unreleased", "self-released",
]

DEFAULT_FORMATS = [
    "demo", "cassette", "tape", "vinyl rip", "session", "7\"", "EP", "single",
    "live", "1970s", "1980s", "1990s",
]

# Titel mit diesen Wörtern sind fast nie Musik, sondern Videos *über* Musik.
DEFAULT_EXCLUDE = [
    "review", "reaction", "reacts", "reagiert", "tutorial", "lesson", "how to",
    "documentary", "doku", "dokumentation", "interview", "explained", "erklärt",
    "podcast", "top 10", "top 20", "top 50", "top 100", "ranking", "tier list",
    "best albums", "beste alben", "unboxing", "haul", "vlog", "#shorts",
    "type beat", "karambolage", "in 10 minuten", "lecture", "vortrag",
    "trailer", "teaser", "what is", "was ist", "history of", "geschichte des",
    "vinyl update", "record collection", "plattensammlung", "guitar lesson",
    "drum cover", "bass cover", "guitar cover", "playthrough", "gear",
]

DEFAULT_TERMS = {
    "genres": DEFAULT_GENRES,
    "adjektive": DEFAULT_ADJECTIVES,
    "formate": DEFAULT_FORMATS,
    "ausschluss": DEFAULT_EXCLUDE,
}


def load_terms():
    """Gespeicherte Begriffe, fehlende Listen mit Vorgaben aufgefüllt."""
    saved = storage.load_json(storage.TERMS_FILE, {})
    terms = {}
    for key, default in DEFAULT_TERMS.items():
        value = saved.get(key) if isinstance(saved, dict) else None
        terms[key] = [v for v in value if v.strip()] if isinstance(value, list) else list(default)
    return terms


def save_terms(terms):
    storage.save_json(storage.TERMS_FILE, terms)


def generate_random_query(terms=None):
    """Zufallssuche aus Beschreibung + Genre + Format, mit Genre als Pflichtteil."""
    terms = terms or load_terms()
    genres = terms["genres"] or DEFAULT_GENRES
    adjectives = terms["adjektive"]
    formats = terms["formate"]

    parts = [random.choice(genres)]
    if adjectives and random.random() < 0.6:
        parts.insert(0, random.choice(adjectives))
    if formats and random.random() < 0.5:
        parts.append(random.choice(formats))
    return " ".join(parts)


def build_exclude_matcher(words):
    """Regex, die ganze Wörter/Wortgruppen trifft („talk“ trifft nicht „Talking Heads“)."""
    words = [w.strip() for w in words if w.strip()]
    if not words:
        return None
    pattern = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{pattern})(?!\w)", re.IGNORECASE)


if __name__ == "__main__":
    for _ in range(8):
        print(generate_random_query())
