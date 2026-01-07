import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QTextBrowser, QGroupBox, QFrame, QPushButton, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QPixmap

from turbo_skryer.utils import util
from turbo_skryer.core.vault import VaultManager
from turbo_skryer.core.launcher import Launcher

class DetailPanel(QWidget):
    """
    Displays detailed information about the selected ROM.
    Acts as the 'Right Pane' in the Master-Detail view.
    """
    # Platform Name in DB -> Settings Key Match
    # Must match the EMULATORS list in SettingsDialog.py.
    PLATFORM_TO_SETTINGS_KEY = {
        "Commodore 64": "emulators/c64",
        "Commodore Amiga": "emulators/amiga",
        "Amstrad CPC": "emulators/amstrad",
        "Atari ST": "emulators/atari_st",
        "Atari 8bit": "emulators/atari_8bit",
        "Sinclair ZX Spectrum": "emulators/spectrum",
        "DOS": "emulators/dos",
        "ScummVM": "emulators/scummvm"
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.vault_manager = None
        self.current_playable_path = None
        self.settings = QSettings("Depones Labs", "Skryer")
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        self._setup_header()
        self._setup_metadata_section()
        self._setup_technical_section()
        self._setup_description_section()
        self._setup_action_bar()
        
        self.layout.addStretch()

    def _setup_header(self):
        # Box Art will be coming here in Phase 4
        # For now, put a gray placeholder box.
        self.image_placeholder = QLabel("No Image Available")
        self.image_placeholder.setAlignment(Qt.AlignCenter)
        self.image_placeholder.setStyleSheet("background-color: #2d2d2d; color: #888; border-radius: 5px;")
        self.image_placeholder.setMinimumSize(350, 400)
        self.layout.addWidget(self.image_placeholder)

        # Game Title
        self.title_label = QLabel("Select a Game")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

    def _setup_metadata_section(self):
        
        group = QGroupBox("Game Info")
        form = QFormLayout()
        
        self.platform_label = QLabel("-")
        self.year_label = QLabel("-")
        self.publisher_label = QLabel("-") # It doesn't currently exist as a column in the DB, but it can be parsed from DAT in the future.
        
        form.addRow("Platform:", self.platform_label)
        form.addRow("Release Year:", self.year_label)
        
        group.setLayout(form)
        self.layout.addWidget(group)

    def _setup_technical_section(self):
        """
        This is the most important part for data holders. Hashes must be copyable.
        """
        group = QGroupBox("Technical Data")
        form = QFormLayout()
        
        self.filename_label = QLabel("-")
        self.filename_label.setTextInteractionFlags(Qt.TextSelectableByMouse) # Make it copyable
        
        self.size_label = QLabel("-")
        
        self.crc_label = QLabel("-")
        self.crc_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.md5_label = QLabel("-")
        self.md5_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.sha1_label = QLabel("-")
        self.sha1_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        form.addRow("ROM Name:", self.filename_label)
        form.addRow("Size:", self.size_label)
        form.addRow("CRC32:", self.crc_label)
        form.addRow("MD5:", self.md5_label)
        # SHA1 is too long, add it if needed.
        
        group.setLayout(form)
        self.layout.addWidget(group)

    def _setup_description_section(self):
        
        self.description_textbrowser = QTextBrowser() # Read-only text area
        self.description_textbrowser.setPlaceholderText("No description available.")
        self.description_textbrowser.setMaximumHeight(100)
        self.layout.addWidget(self.description_textbrowser)

    def _setup_action_bar(self):
        
        hbox = QHBoxLayout()
        
        self.launch_button = QPushButton("Play")
        self.launch_button.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold; padding: 5px;")
        self.launch_button.setEnabled(False)
        self.launch_button.clicked.connect(self._on_play_clicked)
        
        self.folder_button = QPushButton("Open Folder")
        self.folder_button.setEnabled(False)
        
        hbox.addWidget(self.launch_button)
        hbox.addWidget(self.folder_button)
        self.layout.addLayout(hbox)

    def _on_play_clicked(self):
        
        # 1. Gerekli verileri topla
        # Şu anki veriyi (data dict) update_data'dan saklamadık, ama UI'dan okuyabiliriz 
        # veya self.current_game_data diye bir değişkende tutabilirdik.
        # En temizi self.last_loaded_data tutmaktır. 
        # Ama şimdilik basitçe self.platform_label ve self.current_playable_path kullanalım.
        
        game_path = self.current_playable_path
        platform = self.platform_label.text() # UI'dan okuyoruz (örn: Commodore 64)
        
        if not game_path:
            return # Dosya yoksa zaten buton pasif olmalı ama güvenlik için.

        # 2. Ayarlardan Emülatör yolunu bul
        settings_key = self.PLATFORM_TO_SETTINGS_KEY.get(platform)
        if not settings_key:
            # Bilinmeyen platform
            print(f"Unknown platform key for: {platform}")
            return

        emulator_exe = self.settings.value(settings_key, "", type=str)
        
        # 3. Emülatör ayarlı mı?
        if not emulator_exe:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Emulator Not Configured", 
                                f"Please configure the emulator for '{platform}' in Settings > Emulators.")
            return

        # Launch
        success = Launcher.launch(emulator_exe, game_path, platform)
        
        if not success:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Launch Failed", 
                                 f"Could not launch the emulator.\nCheck the console logs for details.\n\nExe: {emulator_exe}\nFile: {game_path}")
    
            
    def set_vault_path(self, path):
        """Called by Main Window."""
        if path:
            self.vault_manager = VaultManager(path)
        else:
            self.vault_manager = None
    
    def _load_cover(self, data):
        """
        Searches for covers using VaultManager.
        """
        self._set_placeholder_image() # Clear
        
        if not self.vault_manager or not self.vault_manager.is_valid():
            return

        # Get the game name (Title takes prior, otherwise rom_name)
        title = data.get("title", "")
        if not title and data.get("rom_name"):
             title = os.path.splitext(data.get("rom_name"))[0]

        # Ask Vault for assets
        assets = self.vault_manager.find_game_assets(title)
        
        if assets.get("covers"):
            image_path = assets["covers"][0]
            
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                # En-boy oranını koruyarak kutuya sığdır
                # Not: Genişliği panelin o anki genişliğine göre dinamik yapmak daha şık olabilir
                # ama şimdilik sabit 400px genişlik veya 300px yükseklik sınırı koyuyoruz.
                scaled = pixmap.scaled(350, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_placeholder.setPixmap(scaled)
                self.image_placeholder.setText("")
        else:
            if assets.get("root"):
                self.image_placeholder.setText("No Images\n(Folder Found)")

    def _set_placeholder_image(self):
        
        self.image_placeholder.setText("No Image Available")
        self.image_placeholder.setStyleSheet("background-color: #2d2d2d; color: #888; border-radius: 5px;")
        self.image_placeholder.clear()
        self.image_placeholder.setText("No Image Available")
    
    def update_data(self, data: dict):
        """
        Populates the UI with data from the selected row.
        Expecting a dictionary mapping column names to values.
        """
        if not data:
            self.clear()
            return

        platform_name = data.get("platform", data.get("system", "-"))

        self.title_label.setText(data.get("title", "Unknown Title"))
        self.platform_label.setText(data.get("platform", "-"))
        self.year_label.setText(str(data.get("release_year", "-")))
        
        self.filename_label.setText(data.get("rom_name", "-"))
        self.size_label.setText(util.human_readable_size(data.get("size", 0)))
        
        self.crc_label.setText(data.get("crc", "-"))
        self.md5_label.setText(data.get("md5", "-"))
        
        desc = data.get("description", "")
        self.description_textbrowser.setText(desc if desc else "No description.")
        
        self._load_cover(data)
        self._check_playable_media(data)

    def _check_playable_media(self, data):
        """
        It asks VaultManager: Does this game have a playable file? 
        If so, it activates the Play button.
        """
        self.launch_button.setEnabled(False)
        self.launch_button.setToolTip("Game file not found in RetroVault")
        self.current_playable_path = None

        if not self.vault_manager or not self.vault_manager.is_valid():
            return

        title = data.get("title", "")
        if not title and data.get("rom_name"):
             title = os.path.splitext(data.get("rom_name"))[0]
        
        platform_name = data.get("platform", data.get("system", ""))

        # Dosyayı Ara
        media_path = self.vault_manager.find_playable_media(title, platform_name)
        
        if media_path:
            self.current_playable_path = media_path
            self.launch_button.setEnabled(True)
            self.launch_button.setToolTip(f"Ready to launch: {os.path.basename(media_path)}")
            
            # Klasör butonunu da açabiliriz
            self.folder_button.setEnabled(True) 
        else:
            self.folder_button.setEnabled(False)

    def clear(self):
        
        self.title_label.setText("Select a Game")
        self.platform_label.setText("-")
        self.year_label.setText("-")
        self.filename_label.setText("-")
        self.size_label.setText("-")
        self.crc_label.setText("-")
        self.md5_label.setText("-")
        self.description_textbrowser.clear()

        self._set_placeholder_image()
        
        # Reset buttons
        self.launch_button.setEnabled(False)
        self.folder_button.setEnabled(False)
        self.current_playable_path = None
