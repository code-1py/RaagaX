import re

def clean_title(title: str) -> str:
    if not title:
        return "Unknown"

    # Remove common suffixes in brackets/parens
    # e.g. (Official Video), [4K], (Lyrics), (Audio), (Full HD)
    title = re.sub(r'\((?:official\s*(?:video|audio|music\s*video|lyric\s*video)?|lyrics?|full\s*(?:hd|video)|4k|hd|audio|visualizer|ft\.?.*?)\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\[(?:official\s*(?:video|audio|music\s*video)?|lyrics?|full\s*(?:hd|video)|4k|hd|audio)\]', '', title, flags=re.IGNORECASE)

    # Split on common separators — take the first part as the song name
    # e.g. "Tum Hi Ho - Aashiqui 2 | Arijit Singh | T-Series" → "Tum Hi Ho"
    parts = re.split(r'\s*[\|]\s*', title)  # split on |
    title = parts[0].strip()

    # Further split on " - " but only keep first part if it looks like a song name
    # Avoid splitting "AC-DC" or "Ice-T" type names (no spaces around dash)
    dash_parts = re.split(r'\s+-\s+', title)
    if len(dash_parts) > 1:
        title = dash_parts[0].strip()

    # Remove trailing/leading junk characters
    title = title.strip(' -|_•·')

    # Collapse multiple spaces
    title = re.sub(r'\s+', ' ', title)

    return title or "Unknown"