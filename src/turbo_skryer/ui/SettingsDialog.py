from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QCheckBox, QDialogButtonBox, QFormLayout, QGroupBox, QLabel
from PySide6.QtCore import QSettings

class SettingsDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.resize(400, 300)
        
        # QSettings Setup (Organization and Application Name)
        self.settings = QSettings("Depones Labs", "Skryer")
        
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tab_general = QWidget()
        
        self.tabs.addTab(self.tab_general, "General")
        layout.addWidget(self.tabs)
        
        self._setup_general_tab()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.load_settings()

    def _setup_general_tab(self):
        
        layout = QVBoxLayout(self.tab_general)
        
        # --- UI Behavior Grubu ---
        group_ui = QGroupBox("User Interface")
        form = QFormLayout()
        
        # AYAR 1: Panel Resize Modu
        # Checkbox işaretliyse: Panel boyutu kilitlenir (sabit kalır).
        # İşaretli değilse: Kullanıcı elle değiştirebilir (default splitter davranışı).
        self.lock_panel_checkbox = QCheckBox("Lock Detail Panel Width")
        self.lock_panel_checkbox.setToolTip("If checked, the right panel will maintain a fixed width.")
        
        # AYAR 2: Otomatik Yükleme
        self.restore_layout_checkbox = QCheckBox("Restore Layout on Startup")
        self.restore_layout_checkbox.setToolTip("Remember window size and splitter position.")
        
        form.addRow(self.lock_panel_checkbox)
        form.addRow(self.restore_layout_checkbox)
        
        group_ui.setLayout(form)
        layout.addWidget(group_ui)
        layout.addStretch()

    def load_settings(self):
        # False: Default value
        self.lock_panel_checkbox.setChecked(self.settings.value("ui/lock_panel", False, type=bool))
        self.restore_layout_checkbox.setChecked(self.settings.value("ui/restore_layout", True, type=bool))

    def save_settings(self):
        
        self.settings.setValue("ui/lock_panel", self.lock_panel_checkbox.isChecked())
        self.settings.setValue("ui/restore_layout", self.restore_layout_checkbox.isChecked())
        
    def accept(self):
        """It works when the OK button is pressed."""
        self.save_settings()
        super().accept()