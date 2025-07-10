VISIQUE - Image to WEBP Converter
=================================

Ein einfaches, lokales Conversion-Tool für Bilder in das WEBP-Format – speziell für den Einsatz im E-Commerce optimiert.
Mit optionaler quadratischer Darstellung (2048x2048) für Produktbilder.

Entwickelt mit Python 3.11+ und PyQt6.


🔧 FUNKTIONEN
-------------

- Drag & Drop Unterstützung für Bilddateien
- Verarbeitung kompletter Ordner oder einzelner Dateien
- Automatische Größenanpassung auf 2048x2048 px (optional)
- Umwandlung aller gängigen Bildformate in `.webp`
- Einfache GUI mit PyQt6
- Log-Ausgabe ein- und ausblendbar
- Öffnet Zielordner nach der Konvertierung automatisch im Finder
- Unterstützt Transparenz-Konvertierung (RGBA → RGB mit weißem Hintergrund)

Unterstützte Formate:
- PNG, JPG, JPEG, TIF, TIFF, BMP, GIF, WEBP, AVIF


📦 INSTALLATION
---------------

### Voraussetzung

- Python 3.11 oder höher
- Pip
- macOS (getestet auf Apple Silicon mit macOS 13+)

### Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**requirements.txt**
```
PyQt6
Pillow
```

### Start

```bash
python main.py
```


🚀 BUILD ALS MAC APP
---------------------

Mit PyInstaller lässt sich eine native `.app` für macOS erstellen.

### Vorbereitungen:

1. Installiere PyInstaller:

```bash
pip install pyinstaller
```

2. Baue die App:

```bash
pyinstaller --windowed --icon=icon.icns --add-data "logo.png:." main.py
```

### Ergebnis:

- Die App liegt anschließend unter `dist/main.app`
- Öffne sie mit Doppelklick oder:

```bash
open dist/main.app
```

Hinweis: Achte darauf, dass `logo.png` und `icon.icns` im gleichen Verzeichnis wie `main.py` liegen.


📁 DATEISTRUKTUR
----------------

```
project/
│
├── main.py
├── logo.png
├── icon.icns
├── requirements.txt
└── README.txt
```

💡 HINWEISE
-----------

- Das Tool nutzt `sys._MEIPASS`, um Ressourcen im `.app`-Bundle korrekt zu laden.
- Die Fenstergröße passt sich dynamisch an, wenn der Log angezeigt/versteckt wird.
- Die App speichert keine Dateien dauerhaft – es wird nur im gewählten Zielordner exportiert.


🛠 TODO / IDEEN
---------------

- Unterstützung für weitere Exportformate (z. B. AVIF)
- Fortschrittsanzeige pro Datei
- Dark/Light-Mode Umschaltung
- Mehrsprachigkeit (DE/EN)

---

(c) 2025 VISIQUE UG
