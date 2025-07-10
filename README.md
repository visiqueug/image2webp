VISIQUE – Image to WebP Converter

Ein einfaches Python-GUI-Tool zur Konvertierung von Bildern (PNG, JPG, TIFF, AVIF etc.) ins WebP-Format – optimiert für Produktbilder im E-Commerce.

---

🔧 Lokale Einrichtung

# Projekt klonen

git clone https://github.com/dein-nutzername/image-2-webp.git
cd image-2-webp

# Virtuelle Umgebung erstellen

py -m venv venv

# Virtuelle Umgebung aktivieren

source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows

# Abhängigkeiten installieren

py -m pip install --upgrade pip
py -m pip install -r requirements.txt

# App starten

python main.py

---

🧪 macOS: App mit py2app bauen

python setup.py py2app

Die fertige App liegt danach unter:
dist/VISIQUE Image 2 WebP Converter.app

---

📦 Voraussetzungen

- Python 3.10 oder neuer
- Pillow
- py2app (nur für macOS-Builds)

---

Lizenz: MIT
Autor: VISIQUE GmbH – https://www.visique.de
