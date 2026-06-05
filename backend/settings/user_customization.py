import json
from backend.utils import BASE_DIR

BASE_DIR.mkdir(parents=True, exist_ok=True)
try:
    with open(BASE_DIR / "settings.json", "x") as f:
        settings: dict = {"theme": "light"}
        json.dump(settings, f)
except FileExistsError:
    pass

def get_user_customization() -> str:
    try:
        with open(BASE_DIR / "settings.json", "r") as f:
            settings: dict = json.load(f)
            return settings.get("theme", "light")
    except Exception as e:
        return "light"

def set_update_user_customization(theme: str) -> None:
    try:
        with open(BASE_DIR / "settings.json", "w") as f:
            settings: dict = {"theme": theme}
            json.dump(settings, f)
    except Exception as e:
        pass
