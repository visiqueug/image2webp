import sys
import os
from pathlib import Path
from PIL import Image
import webbrowser

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QMessageBox,
    QVBoxLayout, QCheckBox, QHBoxLayout, QTextEdit
)
from PyQt6.QtGui import QPixmap, QFontDatabase, QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
import ctypes

BASE_DIR = Path(__file__).resolve().parent
version = "2025.7.2"

def resource_path(relative_path):
    """Ressourcen kompatibel für PyInstaller laden"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def resize_image(img, max_size):
    if img.width > max_size or img.height > max_size:
        scaling_factor = min(max_size / img.width, max_size / img.height)
        new_size = (int(img.width * scaling_factor), int(img.height * scaling_factor))
        img = img.resize(new_size, Image.LANCZOS)
        return img, True
    return img, False

def convert_image_to_webp(input_path, output_path, max_size, square):
    try:
        with Image.open(input_path) as img:
            original_size = img.size

            if img.mode == 'P':
                img = img.convert('RGBA')

            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                white_bg = Image.new("RGB", img.size, (255, 255, 255))
                white_bg.paste(img, (0, 0), img)
                img = white_bg

            img, resized = resize_image(img, max_size)

            if square:
                square_size = 2048
                scaling_factor = min(square_size / img.width, square_size / img.height)
                new_width = int(img.width * scaling_factor)
                new_height = int(img.height * scaling_factor)
                resized_img = img.resize((new_width, new_height), Image.LANCZOS)

                square_img = Image.new("RGB", (square_size, square_size), (255, 255, 255))
                img_x = (square_size - new_width) // 2
                img_y = (square_size - new_height) // 2
                square_img.paste(resized_img, (img_x, img_y))
                img = square_img

            output_file_path = os.path.join(output_path, os.path.splitext(os.path.basename(input_path))[0] + ".webp")
            img.save(output_file_path, format="WEBP", quality=80)

            return f"{os.path.basename(input_path)} erfolgreich konvertiert ({original_size} → {img.size})"
    except Exception as e:
        return f"Fehler bei {os.path.basename(input_path)}: {e}"

class ImageConverter(QWidget):
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        valid = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif', '.webp', '.avif'))]
        if valid:
            self.process_images(valid)

    def __init__(self):
        super().__init__()

        # Fonts einbinden
        font_regular_path = BASE_DIR / "Roboto-Regular.ttf"
        font_semibold_path = BASE_DIR / "Roboto-SemiBold.ttf"

        font_ids = []
        for font_path in [font_regular_path, font_semibold_path]:
            if font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id != -1:
                    font_ids.append(font_id)
                else:
                    print(f"⚠️ Schrift konnte nicht geladen werden: {font_path.name}")
            else:
                print(f"⚠️ Datei nicht gefunden: {font_path.name}")

        # Optionale globale Standardschrift setzen
        if font_ids:
            family = QFontDatabase.applicationFontFamilies(font_ids[0])[0]
            QApplication.instance().setFont(QFont(family, 10))


        self.setAcceptDrops(True)
        self.setWindowTitle(f"VISIQUE - Image 2 WebP Converter (v{version})")
        self.setStyleSheet("color: white;")

        # Hintergrundbild als Label
        background = QLabel(self)
        background.setPixmap(QPixmap(resource_path("bg.jpg")))
        background.setScaledContents(True)
        background.setGeometry(self.rect())  # Nimmt komplette Fenstergröße


        layout = QVBoxLayout()

        layout.setContentsMargins(100, 20, 100, 25)

        version_label = QLabel(f"Version {version}")
        version_label.setFont(QFont("Roboto", 10))
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(version_label)

        # Logo
        logo_path =  Path(resource_path("logo.png"))
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(250, 63, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            logo_label = ClickableLabel("https://www.visique.de")
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
            
            layout.addWidget(logo_label)

        title = QLabel("Image 2 WebP Converter")
        title.setFont(QFont("Roboto", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(title)

        # Checkbox zentriert
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addStretch()
        self.square_checkbox = QCheckBox("Produktbild (quadratisch, 2048x2048) erstellen")
        self.square_checkbox.setStyleSheet("color: white; font-size: 14px;")
        checkbox_layout.addWidget(self.square_checkbox)
        checkbox_layout.addStretch()
        layout.addLayout(checkbox_layout)

        # Button-Layout horizontal
        button_layout = QHBoxLayout()
        btn_folder = QPushButton("Kompletten Ordner wählen")
        btn_files = QPushButton("Einzelne Bilder wählen")

        for btn in (btn_folder, btn_files):
            btn.setStyleSheet("""
                QPushButton {
                    margin: 15px 0;
                    background-color: #FDCA40;
                    color: black;
                    font-size: 14px;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #e6b800;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(40)

        btn_folder.clicked.connect(self.select_folder)
        btn_files.clicked.connect(self.select_files)

        button_layout.addStretch()
        button_layout.addWidget(btn_folder)
        button_layout.addSpacing(20)
        button_layout.addWidget(btn_files)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.process_images)
        layout.addWidget(self.drop_area)

        # Toggle-Button
        self.toggle_log_btn = QPushButton("Log anzeigen")
        self.toggle_log_btn.setCheckable(True)
        self.toggle_log_btn.setChecked(False)
        self.toggle_log_btn.setStyleSheet("""
            QPushButton {
                margin-top: 10px;
                border: none;
                background: none;
            }
        """)
        self.toggle_log_btn.clicked.connect(self.toggle_log_visibility)
        layout.addWidget(self.toggle_log_btn)

        # Log-Bereich (anfangs versteckt)
        log_label = QLabel("Log Output:")
        log_label.setFont(QFont("Roboto", 12, QFont.Weight.Bold))
        log_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.log_label = log_label
        layout.addWidget(log_label)
        log_label.setVisible(False)

        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setStyleSheet("background-color: #1e1e1e; color: white;")
        layout.addWidget(self.status_output)
        self.status_output.setVisible(False)

        self.setLayout(layout)

        # Layer: Hintergrund unten, Inhalt oben
        background.lower()

    def toggle_log_visibility(self):
        is_visible = self.toggle_log_btn.isChecked()
        self.status_output.setVisible(is_visible)
        self.log_label.setVisible(is_visible)
        self.toggle_log_btn.setText("Log verbergen" if is_visible else "Log anzeigen")

        self.adjustSize()

    def log(self, text):
        self.status_output.append(text)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Ordner auswählen")
        if folder:
            files = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif', '.webp', '.avif'))
            ]
            self.process_images(files)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Bilder auswählen", "",
                                                "Image files (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.gif *.webp *.avif)")
        if files:
            self.process_images(files)

    def process_images(self, file_paths):
        output_folder = QFileDialog.getExistingDirectory(self, "Export Ordner wählen")
        if not output_folder:
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            self.log(f"Export-Ordner erstellt: {output_folder}")

        for path in file_paths:
            self.log(f"Verarbeite {os.path.basename(path)} ...")
            msg = convert_image_to_webp(path, output_folder, max_size=2048, square=self.square_checkbox.isChecked())
            self.log(msg)

        QMessageBox.information(self, "Fertig", "Die Konvertierung ist abgeschlossen!")
        webbrowser.open(f"file:///{output_folder}")

class DropArea(QLabel):
    files_dropped = pyqtSignal(list)

    def __init__(self):
        super().__init__("Dateien hierher ziehen und ablegen")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_default_style()
        self.setAcceptDrops(True)

    def set_default_style(self):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #FDCA40;
                color: #FDCA40;
                font-size: 14px;
                padding: 30px;
                border-radius: 10px;
                background-color: transparent;
            }
        """)

    def set_highlight_style(self):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #FFFFFF;
                color: #FFFFFF;
                font-size: 14px;
                padding: 30px;
                border-radius: 10px;
                background-color: rgba(253, 202, 64, 0.2);
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.set_highlight_style()  # Visuellen Effekt aktivieren

    def dragLeaveEvent(self, event):
        self.set_default_style()  # Effekt zurücksetzen

    def dropEvent(self, event):
        self.set_default_style()  # Effekt zurücksetzen
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        valid_files = [f for f in paths if f.lower().endswith((
            '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif', '.webp', '.avif'
        ))]
        if valid_files:
            self.files_dropped.emit(valid_files)

class ClickableLabel(QLabel):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            webbrowser.open(self.url)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    icon_path = None
    if sys.platform == "darwin":
        icon_path = Path(resource_path("icon.icns"))
    elif sys.platform.startswith("win"):
        icon_path = Path(resource_path("icon.ico"))

    if icon_path and icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = ImageConverter()
    window.show()
    sys.exit(app.exec())