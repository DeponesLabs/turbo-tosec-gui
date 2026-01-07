from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, QCheckBox, QDialogButtonBox, QFormLayout,
                             QGroupBox, QLabel, QPushButton, QLineEdit, QHBoxLayout, QFileDialog, QMessageBox,
                             QScrollArea)
from PySide6.QtCore import QSettings, Qt

class SettingsDialog(QDialog):
    
    EMULATORS = [
        ("Commodore 64", "emulators/c64"),
        ("Commodore Amiga", "emulators/amiga"),
        ("Amstrad CPC", "emulators/amstrad"),       # WinCPC
        ("Atari ST", "emulators/atari_st"),         # Steem SSE
        ("Atari 8bit", "emulators/atari_8bit"),     # Altirra
        ("Sinclair ZX Spectrum", "emulators/spectrum"),
        ("DOS", "emulators/dos"),
        ("ScummVM", "emulators/scummvm")
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.resize(600, 500)
        
        self.settings = QSettings("Depones Labs", "Skryer")
        
        # Store dynamically generated inputs here. 
        # Example: { "emulators/c64": <QLineEdit Object> }
        self.emu_widgets = {}
        
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tab_general = QWidget()
        self.tab_paths = QWidget()
        self.tab_emulators = QWidget()
        
        self.tabs.addTab(self.tab_general, "General")
        self.tabs.addTab(self.tab_paths, "Vault & Paths")
        self.tabs.addTab(self.tab_emulators, "Emulators")
        layout.addWidget(self.tabs)
        
        self._setup_general_tab()
        self._setup_paths_tab()
        self._setup_emulators_tab()
        
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
        
        self.lock_panel_checkbox = QCheckBox("Lock Detail Panel Width")
        self.lock_panel_checkbox.setToolTip("If checked, the right panel will maintain a fixed width.")
        
        self.restore_layout_checkbox = QCheckBox("Restore Layout on Startup")
        self.restore_layout_checkbox.setToolTip("Remember window size and splitter position.")
        
        form.addRow(self.lock_panel_checkbox)
        form.addRow(self.restore_layout_checkbox)
        
        group_ui.setLayout(form)
        layout.addWidget(group_ui)
        layout.addStretch()

    def _setup_paths_tab(self):
        
        layout = QVBoxLayout(self.tab_paths)
        
        group = QGroupBox("Vault Location")
        form = QFormLayout()
        
        # *** Vault Root ***
        self.vault_path_lineedit = QLineEdit()
        self.vault_path_lineedit.setPlaceholderText("e.g. E:/RetroVault")
        
        browse_button = QPushButton("...")
        browse_button.setFixedWidth(30)
        browse_button.clicked.connect(self._browse_vault_path)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.vault_path_lineedit)
        hbox.addWidget(browse_button)
        
        form.addRow("Root Directory:", hbox)
        
        info_label = QLabel("Select the root folder containing 'Games', 'Collections' etc.")
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        form.addRow("", info_label)
        
        self.fix_structure_button = QPushButton("Initialize / Fix Directory Structure")
        self.fix_structure_button.clicked.connect(self._on_fix_structure)
        form.addRow("", self.fix_structure_button)
        
        group.setLayout(form)
        layout.addWidget(group)
        layout.addStretch()

    def _browse_vault_path(self):
        
        directory = QFileDialog.getExistingDirectory(self, "Select RetroVault Root")
        if directory:
            self.vault_path_lineedit.setText(directory)
            
    def _on_fix_structure(self):
        """When the user presses the button, it repairs the folder tree."""
        path = self.vault_path_lineedit.text()
        if not path: 
            return
        
        try:
            # Temporary import to avoid cyclic dependency
            from turbo_skryer.core.vault import VaultManager
            vm = VaultManager(path)
            created = vm.ensure_structure()
            
            if created:
                QMessageBox.information(self, "Success", f"Created {len(created)} folders:\n" + "\n".join(created[:5]) + "...")
            else:
                QMessageBox.information(self, "Info", "Structure is already correct.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _setup_emulators_tab(self):
        """Dynamically generates emulator selectors."""
        layout = QVBoxLayout(self.tab_emulators)
        
        # Add a scroll area so the list fits if it gets longer.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content_widget = QWidget()
        form = QFormLayout(content_widget)
        form.setLabelAlignment(Qt.AlignLeft)
        
        info_label = QLabel("Select the executable (.exe) for each platform emulator:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        form.addRow(info_label)
        
        # Create the interface by iterating through the list
        for platform_name, settings_key in self.EMULATORS:
            
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Path to emulator for {platform_name}...")
            
            browse_button = QPushButton("...")
            browse_button.setFixedWidth(30)
            
            # We use Lambda to specify which key is being browsed. 
            # # We pass line_edit=line_edit to avoid closure issues.
            browse_button.clicked.connect(lambda _, le=line_edit: self._browse_emulator_exe(le))
            
            hbox = QHBoxLayout()
            hbox.addWidget(line_edit)
            hbox.addWidget(browse_button)
            
            form.addRow(f"{platform_name}:", hbox)
            
            # Save the widget to the dictionary (for Load/Save)
            self.emu_widgets[settings_key] = line_edit
            
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def _browse_emulator_exe(self, line_edit_widget):
        """General file selector."""
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Emulator Executable", "", "Executables (*.exe);;All Files (*)")
        if filepath:
            line_edit_widget.setText(filepath)

    def load_settings(self):
        # General
        self.lock_panel_checkbox.setChecked(self.settings.value("ui/lock_panel", False, type=bool))
        self.restore_layout_checkbox.setChecked(self.settings.value("ui/restore_layout", True, type=bool))
        
        # Paths
        self.vault_path_lineedit.setText(self.settings.value("paths/vault_root", "", type=str))
        
        # Emulators (Auto-loop)
        for key, widget in self.emu_widgets.items():
            widget.setText(self.settings.value(key, "", type=str))

    def save_settings(self):
        # General
        self.settings.setValue("ui/lock_panel", self.lock_panel_checkbox.isChecked())
        self.settings.setValue("ui/restore_layout", self.restore_layout_checkbox.isChecked())
        
        # Paths
        self.settings.setValue("paths/vault_root", self.vault_path_lineedit.text())
        
        # Emulators (Otomatik Döngü)
        for key, widget in self.emu_widgets.items():
            path = widget.text().strip()
            self.settings.setValue(key, path)
        
    def accept(self):
        """It works when the OK button is pressed."""
        self.save_settings()
        super().accept()
