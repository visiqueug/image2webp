import requests
import platform
import sys
from packaging import version as vparse  # pip install packaging

# === KONFIGURATION ===
REPO = "visiqueug/image2webp"
ASSET_NAME = "vq-image2webp-windows.zip" if sys.platform.startswith("win") else "vq-image2webp-macos.zip"


def check_for_update(CURRENT_VERSION):
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        latest_version = data["tag_name"].lstrip("v")
        asset_url = next(
            a["browser_download_url"]
            for a in data["assets"]
            if a["name"] == ASSET_NAME
        )

        if vparse.parse(latest_version) > vparse.parse(CURRENT_VERSION):
            return asset_url, latest_version
    except Exception as e:
        print(f"[Updater] Keine Verbindung oder keine neuere Version: {e}")
    return None, None


def handle_replace_mode():
    # bleibt erhalten für mögliche spätere Nutzung
    if "--replace" in sys.argv and len(sys.argv) >= 3:
        pass
