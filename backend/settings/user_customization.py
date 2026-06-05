import json

def get_user_customization() -> str:
    try:
        with open('settings.json', 'r') as f:
            settings: dict = json.load(f)
            return settings.get("theme", "light")
    except Exception as e:
        return "light"

def set_update_user_customization(theme: str) -> None:
    try:
        with open('settings.json','w') as f:
            settings: dict = {"theme": theme}
            json.dump(settings, f)
    except Exception as e:
        pass