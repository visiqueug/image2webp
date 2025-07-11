import sys
import os
from pathlib import Path
from PIL import Image
from ftplib import FTP
import requests
import json
import webbrowser
from openai import OpenAI
import base64

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QMessageBox,
    QVBoxLayout, QCheckBox, QHBoxLayout, QTextEdit,
    QMenuBar, QMenu, QDialog, QFormLayout, QLineEdit, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFontDatabase, QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
import ctypes

BASE_DIR = Path(__file__).resolve().parent
version = "2025.7.3"

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

class ApiSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Verbindungen")
        layout = QFormLayout()

        self.chatgpt_token = QLineEdit()
        self.shopify_domain = QLineEdit()
        self.shopify_token = QLineEdit()
        self.ftp_server = QLineEdit()
        self.ftp_user = QLineEdit()
        self.ftp_pass = QLineEdit()
        self.ftp_dir = QLineEdit()

        settings = QSettings("VISIQUE", "WebPConverter")

        # --- ChatGPT ---
        layout.addRow(self.make_section_label("ChatGPT"))

        self.chatgpt_token = QLineEdit()
        self.chatgpt_token.setEchoMode(QLineEdit.EchoMode.Password)
        stored_chatgpt = settings.value("chatgpt_token", "")
        if stored_chatgpt:
            self.chatgpt_token.setPlaceholderText("••••••••••••")
        layout.addRow("API Token:", self.chatgpt_token)

        # --- Shopify ---
        layout.addRow(self.make_section_label("Shopify"))

        self.shopify_domain = QLineEdit()
        self.shopify_domain.setText(settings.value("shopify_domain", ""))
        layout.addRow("Domain:", self.shopify_domain)

        self.shopify_token = QLineEdit()
        self.shopify_token.setEchoMode(QLineEdit.EchoMode.Password)
        stored_shopify = settings.value("shopify_token", "")
        if stored_shopify:
            self.shopify_token.setPlaceholderText("••••••••••••")
        layout.addRow("API Token:", self.shopify_token)

        # --- FTP ---
        layout.addRow(self.make_section_label("FTP"))

        self.ftp_server = QLineEdit()
        self.ftp_server.setText(settings.value("ftp_server", ""))
        layout.addRow("Server:", self.ftp_server)

        self.ftp_user = QLineEdit()
        self.ftp_user.setText(settings.value("ftp_user", ""))
        layout.addRow("Benutzername:", self.ftp_user)

        self.ftp_pass = QLineEdit()
        self.ftp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        stored_ftp_pass = settings.value("ftp_pass", "")
        if stored_ftp_pass:
            self.ftp_pass.setPlaceholderText("••••••••••••")
        layout.addRow("Passwort:", self.ftp_pass)

        self.ftp_dir = QLineEdit()
        self.ftp_dir.setText(settings.value("ftp_dir", ""))
        layout.addRow("FTP Folder:", self.ftp_dir)

        # --- Speichern Button ---
        btn_save = QPushButton("Speichern")
        btn_save.setStyleSheet("""
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
        btn_save.clicked.connect(self.save_settings)
        layout.addRow(btn_save)

        self.setLayout(layout)

    def make_section_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 4px; color: #FDCA40;")
        return label
    

    def save_settings(self):
        settings = QSettings("VISIQUE", "WebPConverter")

        if self.chatgpt_token.text():
            settings.setValue("chatgpt_token", self.chatgpt_token.text())
        if self.shopify_token.text():
            settings.setValue("shopify_token", self.shopify_token.text())
        if self.ftp_pass.text():
            settings.setValue("ftp_pass", self.ftp_pass.text())

        settings.setValue("shopify_domain", self.shopify_domain.text())
        settings.setValue("ftp_server", self.ftp_server.text())
        settings.setValue("ftp_user", self.ftp_user.text())
        settings.setValue("ftp_dir", self.ftp_dir.text())

        QMessageBox.information(self, "Gespeichert", "Die Einstellungen wurden erfolgreich gespeichert.")
        self.accept()

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

        font_regular_path = BASE_DIR / "Roboto-Regular.ttf"
        font_semibold_path = BASE_DIR / "Roboto-SemiBold.ttf"
        font_ids = []
        for font_path in [font_regular_path, font_semibold_path]:
            if font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id != -1:
                    font_ids.append(font_id)
        if font_ids:
            family = QFontDatabase.applicationFontFamilies(font_ids[0])[0]
            QApplication.instance().setFont(QFont(family, 10))

        self.setAcceptDrops(True)
        self.setWindowTitle(f"VISIQUE - Image 2 WebP Converter")
        self.setFixedSize(750, 450)
        self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())
        self.setStyleSheet("background-color: black; color: white;")

        self.background = QLabel(self)
        self.background.setPixmap(QPixmap(resource_path("bg.jpg")))
        self.background.setScaledContents(True)
        self.background.setGeometry(self.rect())
        self.background.lower()

        layout = QVBoxLayout()
        layout.setContentsMargins(100, 20, 100, 25)

        menubar = QMenuBar(self)
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #A80854;
                color: white;
                font-size: 14px;
            }

            QMenuBar::item {
                background: transparent;
                padding: 4px 12px;
            }

            QMenuBar::item:selected {
                background-color: #FDCA40;
                color: black;
            }

            QMenu {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #FDCA40;
            }

            QMenu::item {
                padding: 6px 20px;
            }

            QMenu::item:selected {
                background-color: #FDCA40;
                color: black;
            }
        """)

        # Menü "Einstellungen"
        menu = menubar.addMenu("Einstellungen")
        api_action = menu.addAction("Verbindungen")
        api_action.triggered.connect(self.open_api_settings)

        # Spacer nach links (optional, wenn das Menü zentriert wirken soll)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        menubar.setCornerWidget(spacer, Qt.Corner.TopLeftCorner)

        # Versionsanzeige ganz rechts
        version_label = QLabel(f"v{version}")
        version_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                padding-top: 5px;
                padding-right: 10px;
                background: transparent;
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        menubar.setCornerWidget(version_label, Qt.Corner.TopRightCorner)

        layout.setMenuBar(menubar)

        # Logo
        logo_path =  Path(resource_path("logo.png"))
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(250, 63, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            logo_label = ClickableLabel("https://www.visique.de")
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
            
            layout.addWidget(logo_label)

        title = QLabel("Image 2 WebP Converter")
        title.setFont(QFont("Roboto", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
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

        # Buttons definieren
        btn_folder = QPushButton("Kompletten Ordner wählen")
        btn_files = QPushButton("Einzelne Bilder wählen")
        buttons = [btn_folder, btn_files]

        # Prüfe, ob FTP-Daten vorhanden sind → optionalen Button anhängen
        settings = QSettings("VISIQUE", "WebPConverter")
        if all(settings.value(key, "") for key in ["ftp_server", "ftp_user", "ftp_pass"]):
            btn_ftp_upload = QPushButton("FTP Upload")
            btn_ftp_upload.clicked.connect(self.handle_ftp_upload)
            buttons.append(btn_ftp_upload)

        # Styling und Verhalten für alle Buttons
        for btn in buttons:
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

        # Aktionen verbinden
        btn_folder.clicked.connect(self.select_folder)
        btn_files.clicked.connect(self.select_files)

        # Buttons ins Layout einfügen
        button_layout.addStretch()
        for i, btn in enumerate(buttons):
            button_layout.addWidget(btn)
            if i < len(buttons) - 1:
                button_layout.addSpacing(20)
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
        log_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.log_label = log_label
        layout.addWidget(log_label)
        log_label.setVisible(False)

        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setStyleSheet("background-color: #1e1e1e; color: white;")
        layout.addWidget(self.status_output)
        self.status_output.setVisible(False)

        self.setLayout(layout)

        self.print_connections()

    def toggle_log_visibility(self):
        is_visible = self.toggle_log_btn.isChecked()
        self.status_output.setVisible(is_visible)
        self.log_label.setVisible(is_visible)
        self.toggle_log_btn.setText("Log verbergen" if is_visible else "Log anzeigen")

        if self.toggle_log_btn.isChecked():
            self.setFixedSize(750, 625)
        else:
            self.setFixedSize(750, 450)

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

    def handle_ftp_upload(self):
        # Bilddateien auswählen
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Bilder für FTP-Upload auswählen",
            "",
            "Image files (*.webp)"
        )
        if not files:
            return

        # FTP-Zugangsdaten aus Einstellungen holen
        settings = QSettings("VISIQUE", "WebPConverter")
        host = settings.value("ftp_server", "")
        user = settings.value("ftp_user", "")
        password = settings.value("ftp_pass", "")
        dir = settings.value("ftp_dir", "")

        try:
            self.log("Verbindung zum FTP-Server wird aufgebaut ...")
            ftp = FTP(host)
            ftp.login(user, password)
            ftp.cwd(dir)

            self.log(f"Erfolgreich verbunden mit {host}.")
            for path in files:
                file_name = os.path.basename(path)
                with open(path, 'rb') as f:
                    ftp.storbinary(f"STOR {file_name}", f)
                    self.log(f"Bild hochgeladen: {file_name}")

            ftp.quit()
            self.log("FTP-Upload abgeschlossen.")
            QMessageBox.information(self, "Fertig", "Die Bilder wurden auf den FTP-Server hochgeladen.")

        except Exception as e:
            self.log(f"FTP-Upload fehlgeschlagen: {e}")
            QMessageBox.critical(self, "Fehler", f"Upload fehlgeschlagen:\n{e}")

    def upload_image_to_shopify(self, image_path):
        settings = QSettings("VISIQUE", "WebPConverter")
        domain = settings.value("shopify_domain")
        token = settings.value("shopify_token")
        graphql_url = f"https://{domain}/admin/api/2025-01/graphql.json"

        # Dialog zur Alt-Text-Abfrage
        dialog = AltTextDialog(image_path, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.log(f"Shopify Upload abgebrochen für {os.path.basename(image_path)}.")
            return

        alt_text = dialog.get_alt_text()
        if not alt_text:
            self.log("ALT-Text wurde nicht eingegeben. Upload übersprungen.")
            return

        try:
            self.log("Starte Shopify-Upload...")
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": token
            }

            filename = os.path.basename(image_path)
            mime_type = "image/webp"
            staged_payload = {
                "query": """
                    mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
                    stagedUploadsCreate(input: $input) {
                        stagedTargets {
                        url
                        resourceUrl
                        parameters {
                            name
                            value
                        }
                        }
                        userErrors {
                        field
                        message
                        }
                    }
                    }
                """,
                "variables": {
                    "input": [{
                        "filename": filename,
                        "mimeType": mime_type,
                        "resource": "FILE",
                        "httpMethod": "POST"
                    }]
                }
            }

            staged_response = requests.post(graphql_url, headers=headers, json=staged_payload)
            staged_data = staged_response.json()

            targets = staged_data.get("data", {}).get("stagedUploadsCreate", {}).get("stagedTargets", [])
            if not targets:
                raise Exception("Kein Upload-Ziel erhalten.")

            upload_url = targets[0]["url"]
            resource_url = targets[0]["resourceUrl"]
            parameters = {p["name"]: p["value"] for p in targets[0]["parameters"]}

            with open(image_path, "rb") as f:
                file_data = f.read()

            files = {'file': (filename, file_data, mime_type)}
            upload_response = requests.post(upload_url, data=parameters, files=files)
            if upload_response.status_code >= 300:
                raise Exception(f"Fehler beim Datei-Upload: {upload_response.text}")

            # Bild registrieren
            file_create_payload = {
                "query": """
                    mutation fileCreate($files: [FileCreateInput!]!) {
                    fileCreate(files: $files) {
                        files {
                        id
                        alt
                        createdAt
                        preview {
                            image {
                            url
                            }
                        }
                        }
                        userErrors {
                        field
                        message
                        }
                    }
                    }
                """,
                "variables": {
                    "files": [{
                        "alt": alt_text,
                        "contentType": "IMAGE",
                        "originalSource": resource_url
                    }]
                }
            }

            file_create_response = requests.post(graphql_url, headers=headers, json=file_create_payload)
            file_data = file_create_response.json()

            errors = file_data.get("errors", [])
            user_errors = file_data.get("data", {}).get("fileCreate", {}).get("userErrors", [])

            if errors or user_errors:
                raise Exception(errors[0]["message"] if errors else user_errors[0]["message"])

            self.log(f"Shopify Hochgeladen: {filename} mit ALT-Text: {alt_text}")

        except Exception as e:
            self.log(f"Fehler beim Shopify-Upload: {e}")

    def process_images(self, file_paths):
        output_folder = QFileDialog.getExistingDirectory(self, "Export Ordner wählen")
        if not output_folder:
            return

        # Prüfen, ob Shopify-Daten vorhanden sind
        settings = QSettings("VISIQUE", "WebPConverter")
        shopify_domain = settings.value("shopify_domain", "")
        shopify_token = settings.value("shopify_token", "")
        upload_to_shopify = False

        if shopify_domain and shopify_token:
            answer = QMessageBox.question(
                self,
                "Zu Shopify hochladen?",
                "Sollen die konvertierten Bilder direkt zu Shopify hochgeladen werden?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            upload_to_shopify = (answer == QMessageBox.StandardButton.Yes)

        for path in file_paths:
            self.log(f"Verarbeite {os.path.basename(path)} ...")
            msg = convert_image_to_webp(path, output_folder, max_size=2048, square=self.square_checkbox.isChecked())
            self.log(msg)

            if upload_to_shopify:
                try:
                    self.upload_image_to_shopify(os.path.join(output_folder, os.path.splitext(os.path.basename(path))[0] + ".webp"))
                except Exception as e:
                    self.log(f"Fehler beim Shopify-Upload: {e}")

        QMessageBox.information(self, "Fertig", "Die Konvertierung ist abgeschlossen!")
        webbrowser.open(f"file:///{output_folder}")


    def open_api_settings(self):
        dialog = ApiSettingsDialog(self)
        dialog.exec()

    def print_connections(self):
        settings = QSettings("VISIQUE", "WebPConverter")
        shopify_domain = settings.value("shopify_domain", "")
        ftp_server = settings.value("ftp_server", "")
        self.log(f"Gespeicherte Shopify Domain: {shopify_domain}")
        self.log(f"Gespeicherter FTP Server: {ftp_server}")

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

class AltTextDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ALT-Text eingeben")
        self.image_path = image_path

        layout = QVBoxLayout()

        # Bildvorschau
        pixmap = QPixmap(image_path).scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        # Textfeld
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("ALT-Text eingeben")
        layout.addWidget(self.text_input)

        # Buttons horizontal
        btn_layout = QHBoxLayout()

        # Generieren-Button – immer erstellen, aber ggf. ausblenden
        self.generate_btn = QPushButton("Mit KI generieren")
        self.generate_btn.clicked.connect(self.generate_alt_text)
        self.generate_btn.setStyleSheet("""
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

        # GPT-Token prüfen und Button ggf. verstecken
        settings = QSettings("VISIQUE", "WebPConverter")
        api_key = settings.value("chatgpt_token", "")
        if api_key:
            btn_layout.addWidget(self.generate_btn)
        else:
            self.generate_btn.hide()

        # Hochladen-Button
        btn_upload = QPushButton("Hochladen")
        btn_upload.clicked.connect(self.accept)
        btn_layout.addWidget(btn_upload)

        # Button-Style
        for btn in (self.generate_btn, btn_upload):
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

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_alt_text(self):
        return self.text_input.text().strip()

    def generate_alt_text(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.generate_btn.setEnabled(False)

        try:
            # Bild als base64
            with open(self.image_path, "rb") as f:
                b64_image = base64.b64encode(f.read()).decode("utf-8")

            image_url = f"data:image/webp;base64,{b64_image}"

            settings = QSettings("VISIQUE", "WebPConverter")
            api_key = settings.value("chatgpt_token", "")
            if not api_key:
                self.status.setText("Kein ChatGPT API-Token hinterlegt.")
                return

            client = OpenAI(api_key=api_key)

            gpt_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Erstelle einen prägnanten Alt-Text mit maximal 125 Zeichen für das angehängte Produktbild. "
                                    "Beschreibe objektiv, was auf dem Bild zu sehen ist, idealerweise mit Hinweisen auf Art, "
                                    "Einsatzbereich oder Zielgruppe. Hinterlege Markennamen und Modell wenn diese ersichtlich sind. "
                                    "Keine Erklärungen oder Meta-Kommentare wie zb 'Markenname nicht erkenntlich', nur der reine Alt-Text. "
                                    "Schreibe nicht zu hochgestochen, sondern so, dass es für eine breite Zielgruppe verständlich ist."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100
            )

            alt_text = gpt_response.choices[0].message.content
            self.text_input.setText(alt_text.strip())

        finally:
            self.generate_btn.setEnabled(True)
            QApplication.restoreOverrideCursor()

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