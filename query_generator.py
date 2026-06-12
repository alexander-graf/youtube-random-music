import random

GENRES = [
    # Electronica & Chill
    "Ambient", "Lofi Beats", "Synthwave", "Vaporwave", "IDM", "Trip-Hop",
    "Dub Techno", "Deep House", "Minimal Techno", "Microhouse", "Ambient Techno",
    "Glitch Hop", "Chillhop", "Folktronica", "Outrun", "Space Ambient",
    "Barber Beats", "Mallsoft", "Dreampunk", "Chiptune", "Downtempo", "Future Garage",
    
    # Rock & Metal (Alternative/Indie/Psych)
    "Shoegaze", "Post-Rock", "Math Rock", "Psychedelic Rock", "Krautrock",
    "Desert Rock", "Post-Punk", "Goth Rock", "Garage Rock", "Post-Metal",
    "Dream Pop", "Indie Pop", "Slowcore", "Sadcore", "Space Rock", "Stoner Rock",
    "Surf Rock", "Noise Rock", "No Wave", "Alternative Rock", "Blackgaze",
    "Doom Metal", "Sludge Metal", "Deathrock",
    
    # Folk & Acoustic
    "Indie Folk", "Neofolk", "Pagan Folk", "Chamber Pop", "Folk Horror",
    "Folk Rock", "Freak Folk", "Bluegrass", "Singer-Songwriter", "Americana",
    
    # Jazz & Blues
    "Acid Jazz", "Darkjazz", "Jazz Hop", "Avant-Garde Jazz", "Free Jazz",
    "Nu-Jazz", "Ethio-Jazz", "Hard Bop", "Cool Jazz", "Delta Blues",
    
    # Soul, Funk & World
    "Afrobeat", "Bossa Nova", "Samba", "Tropicália", "City Pop", "Highlife",
    "Ska", "Rocksteady", "Dub Reggae", "Balkan Beat", "Anatolian Rock", "Chicha",
    "Cumbia", "Latin Jazz", "Desert Blues", "G-Funk", "P-Funk", "Neo-Soul",
    
    # Experimental & Niche
    "Dungeon Synth", "Ethereal Wave", "Minimal Synth", "Minimal Wave", "Minimalism",
    "Neo-Classical", "Dark Ambient", "Drone Music", "Avant-Garde", "Plunderphonics",
    "Noise Music", "Breakcore", "Art Punk", "Riot Grrrl", "Twee Pop", "Baroque Pop"
]

ADJECTIVES = [
    "obscure", "rare", "underrated", "forgotten", "vintage", "lost", "bedroom",
    "dreamy", "hidden", "raw", "melancholy", "cozy", "cinematic", "misty", "ethereal",
    "atmospheric", "unknown", "experimental", "lofi", "deep", "mystic", "nostalgic",
    "underground", "niche", "psychedelic"
]

FORMATS = [
    "demo", "cassette", "tape", "vinyl", "session", "record", "tracks", "jams",
    "beats", "tapes", "grooves", "sounds", "landscapes", "vibes", "album", "EP"
]

def generate_random_query():
    """Generates a random query focused on finding rare/obscure music."""
    structure = random.choice([
        # Structure 1: Adjective + Genre + Format (e.g. "obscure synthwave tape")
        lambda: f"{random.choice(ADJECTIVES)} {random.choice(GENRES)} {random.choice(FORMATS)}",
        # Structure 2: Genre + Format (e.g. "math rock vinyl")
        lambda: f"{random.choice(GENRES)} {random.choice(FORMATS)}",
        # Structure 3: Adjective + Genre (e.g. "rare darkjazz")
        lambda: f"{random.choice(ADJECTIVES)} {random.choice(GENRES)}",
        # Structure 4: Just a random genre
        lambda: random.choice(GENRES)
    ])
    return structure()

if __name__ == "__main__":
    # Print a few examples
    for _ in range(5):
        print(generate_random_query())
