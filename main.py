import sys
import os
from pathlib import Path
from PIL import Image
import webbrowser

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QMessageBox,
    QVBoxLayout, QCheckBox, QHBoxLayout, QTextEdit
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
import ctypes

BASE_DIR = Path(__file__).resolve().parent
version = "2025.7.1"

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
        self.setAcceptDrops(True)
        self.setWindowTitle(f"VISIQUE - Image to WEBP Converter (v{version})")
        self.setStyleSheet("background-color: black; color: white;")

        layout = QVBoxLayout()

        # Logo
        logo_path = BASE_DIR / "logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(250, 63, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label = QLabel()
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
            logo_label.mousePressEvent = lambda event: webbrowser.open("https://www.visique.de")
            layout.addWidget(logo_label)

        title = QLabel("Image to WEBP Converter")
        title.setFont(QFont("Calibri", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version_label = QLabel(f"Version {version}")
        version_label.setFont(QFont("Calibri", 10))
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(version_label)

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
        self.toggle_log_btn.setStyleSheet("margin-top: 10px;")
        self.toggle_log_btn.clicked.connect(self.toggle_log_visibility)
        layout.addWidget(self.toggle_log_btn)

        # Log-Bereich (anfangs versteckt)
        log_label = QLabel("Log Output:")
        log_label.setFont(QFont("Calibri", 12, QFont.Weight.Bold))
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
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #FDCA40;
                color: #FDCA40;
                font-size: 14px;
                padding: 30px;
                border-radius: 10px;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        valid_files = [f for f in paths if f.lower().endswith((
            '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif', '.webp', '.avif'
        ))]
        if valid_files:
            self.files_dropped.emit(valid_files)
if __name__ == "__main__":
    app = QApplication(sys.argv)

    icon_path = BASE_DIR / "icon.icns"
    if icon_path.exists() and sys.platform == "darwin":
        app.setWindowIcon(QIcon(str(icon_path)))

    window = ImageConverter()
    window.show()
    sys.exit(app.exec())