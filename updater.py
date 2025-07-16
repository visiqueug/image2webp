import requests
import zipfile
import shutil
import tempfile
import os
import sys
import subprocess
import time
import platform
from pathlib import Path
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


def find_executable(tmp_dir):
    system = platform.system().lower()

    if system == "windows":
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                if file.lower().endswith(".exe"):
                    return os.path.join(root, file)
    elif system == "darwin":
        for root, dirs, files in os.walk(tmp_dir):
            for name in dirs:
                if name.lower().endswith(".app"):
                    return os.path.join(root, name)
    return None


def download_and_replace(asset_url):
    print("[Updater] Update wird heruntergeladen...")
    tmp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tmp_dir, "update.zip")

    with requests.get(asset_url, stream=True) as r:
        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)

    new_binary = find_executable(tmp_dir)
    if not new_binary or not os.path.exists(new_binary):
        print("[Updater] Keine gültige Datei gefunden.")
        return

    current_binary = os.path.abspath(sys.argv[0])

    print(f"[Updater] Starte Ersatzprozess: {new_binary}")
    if sys.platform.startswith("win"):
        subprocess.Popen([new_binary, "--replace", current_binary])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", new_binary, "--args", "--replace", current_binary])

    sys.exit(0)


def handle_replace_mode():
    if "--replace" in sys.argv and len(sys.argv) >= 3:
        time.sleep(1.5)  # Give the main app time to close
        target = Path(sys.argv[2]).resolve()
        source = Path(sys.argv[0]).resolve()

        if sys.platform == "darwin":
            # macOS: in Contents/MacOS ausführen → zurück zur .app
            source = source.parents[3] if source.name == "main" else source
            target = target

        print(f"[Updater] Ersetze: {target} ← {source}")

        try:
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(source), str(target))
            os.chmod(str(target), 0o755)

            if sys.platform == "darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen([str(target)])

        except Exception as e:
            print(f"[Updater] Fehler beim Ersetzen: {e}")

        sys.exit(0)
