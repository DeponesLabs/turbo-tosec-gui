from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QTextBrowser, QGroupBox, QFrame, QPushButton, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from turbo_skryer.utils import util

class DetailPanel(QWidget):
    """
    Displays detailed information about the selected ROM.
    Acts as the 'Right Pane' in the Master-Detail view.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        # Header (Title and Icon Area)
        self._setup_header()
        # 2. Metadata (Platform, Year, Category etc.)
        self._setup_metadata_section()
        # 3. Technical Details (Hashs, Size, Filename)
        self._setup_technical_section()
        self._setup_description_section()
        # 5. Action Buttons (Launcher, Folder etc.) (Phase 4)
        self._setup_action_bar()
        
        self.layout.addStretch()

    def _setup_header(self):
        # Box Art will be coming here in Phase 4
        # For now, put a gray placeholder box.
        self.image_placeholder = QLabel("No Image Available")
        self.image_placeholder.setAlignment(Qt.AlignCenter)
        self.image_placeholder.setStyleSheet("background-color: #2d2d2d; color: #888; border-radius: 5px;")
        self.image_placeholder.setMinimumHeight(200)
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
        self.launch_button.setEnabled(False) # Faz 4'te aktifleşecek
        
        self.folder_button = QPushButton("Open Folder")
        self.folder_button.setEnabled(False)
        
        hbox.addWidget(self.launch_button)
        hbox.addWidget(self.folder_button)
        self.layout.addLayout(hbox)

    def update_data(self, data: dict):
        """
        Populates the UI with data from the selected row.
        Expecting a dictionary mapping column names to values.
        """
        if not data:
            self.clear()
            return

        self.title_label.setText(data.get("title", "Unknown Title"))
        self.platform_label.setText(data.get("system", "-"))
        self.year_label.setText(str(data.get("release_year", "-")))
        
        self.filename_label.setText(data.get("rom_name", "-"))
        self.size_label.setText(util.human_readable_size(data.get("size", 0)))
        
        self.crc_label.setText(data.get("crc", "-"))
        self.md5_label.setText(data.get("md5", "-"))
        
        desc = data.get("description", "")
        self.description_textbrowser.setText(desc if desc else "No description.")

    def clear(self):
        
        self.title_label.setText("Select a Game")
        self.platform_label.setText("-")
        self.year_label.setText("-")
        self.filename_label.setText("-")
        self.size_label.setText("-")
        self.crc_label.setText("-")
        self.md5_label.setText("-")
        self.description_textbrowser.clear()

    
