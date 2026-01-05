import os

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit, QLabel, QHeaderView, \
                              QAbstractItemView, QPushButton, QProgressBar, QFileDialog, QMessageBox, QSplitter
from PySide6.QtCore import QTimer, Qt, QSettings
from PySide6.QtGui import QAction, QIcon

from turbo_tosec import DatabaseManager

from turbo_skryer.ui.DetailsPanel import DetailPanel
from turbo_skryer.ui.SettingsDialog import SettingsDialog
from turbo_skryer.ui.models import InfiniteTableModel
from turbo_skryer.ui.workers import IngestionWorker

class MainWindow(QMainWindow):
    
    def __init__(self):
        
        super().__init__()
        
        db_path = "TEST_DATS/tosec-2025-03-13.duckdb"
        self.setWindowTitle("Depones GUI - Turbo-Skryer")
        self.resize(1200, 800)
        
        # Backend Setup
        self.db = DatabaseManager(db_path, read_only=True)
        if os.path.exists(db_path):
            self.db.connect()
        
        # Model Setup
        self.model = InfiniteTableModel(self.db)
        
        # 3. UI Setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self._setup_top_bar()
        self._setup_content_area()
        self._setup_status_bar()
        
        # 4. Debounce Timer (Critical for Search Performance)
        self.search_timer = QTimer()
        self.search_timer.setInterval(300) # Wait 300ms after last keystroke
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._apply_search)
        
        self.settings = QSettings("Depones", "TurboSkryer")
        self._setup_menu_bar()
        self._load_ui_settings() # Pencere açılırken son konumu hatırla

    def _setup_menu_bar(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menu_bar.addMenu("&Edit")
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,") # VS Code tarzı kısayol
        settings_action.triggered.connect(self.open_settings)
        edit_menu.addAction(settings_action)

    def _setup_top_bar(self):
        """Search bar and controls."""
        bar_layout = QHBoxLayout()
        
        # Label
        filter_label = QLabel("Filter (Title):")
        filter_label.setStyleSheet("font-weight: bold;")
        
        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search... (e.g. 'Mario', 'Zelda')")
        self.search_input.setClearButtonEnabled(True)
        # Connect Input -> Timer (Not directly to Model!)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        
        self.import_button = QPushButton("Import Files")
        self.import_button.clicked.connect(self.start_import_process)
        
        # Progress Bar (Hide at start-up)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False) 
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedWidth(200) 
        
        bar_layout.addWidget(filter_label)
        bar_layout.addWidget(self.search_input)
        bar_layout.addStretch()
        bar_layout.addWidget(self.progress_bar)
        bar_layout.addWidget(self.import_button)
        bar_layout.addWidget(filter_label)
        bar_layout.addWidget(self.search_input)
        
        self.layout.addLayout(bar_layout)

    def _setup_content_area(self):
        """Creates the Master-Detail view using QSplitter."""
        
        # Create horizontal splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left Side: Create the Table
        self.table_view = self._create_table_view()
        
        # Right Side: Detail Panel
        self.detail_panel = DetailPanel()
        
        # Add to Splitter
        self.splitter.addWidget(self.table_view)
        self.splitter.addWidget(self.detail_panel)
        
        # Adjust the percentages (Table 70%, Detail 30%)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        
        # Add to Main Layout
        self.layout.addWidget(self.splitter)
        
        # 7. Signal Connection (Click Event)
        # Execute _on_row_selected when a row changes in the table
        selection_model = self.table_view.selectionModel()
        selection_model.currentRowChanged.connect(self._on_row_selected)
        
    def _create_table_view(self) -> QTableView:
        """Helper to configure the table view instance."""
        table = QTableView()
        table.setModel(self.model)
        
        # Appearance Settings
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        
        # Column Widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        # Sorting
        table.setSortingEnabled(True)
        header.sortIndicatorChanged.connect(self.model.sort)
        
        return table

    def _setup_status_bar(self):
        """Shows row count."""
        self.status_label = QLabel(f"Rows: {self.model.rowCount():,}")
        self.statusBar().addWidget(self.status_label)

    def _on_search_text_changed(self):
        """Restarts the timer on every keystroke."""
        self.search_timer.start()

    def _apply_search(self):
        """Executed only when timer times out."""
        text = self.search_input.text().strip()
        
        # Currently searching on 'title' or 'game_name'. 
        # Since we cleaned data, 'title' is better.
        self.model.set_filter("title", text)
        
        # Update Status Bar
        self.status_label.setText(f"Rows: {self.model.rowCount():,}")
        
        # Scroll to top
        self.table_view.scrollToTop()

    def closeEvent(self, event):
        """Cleanup resources properly."""
        self.settings.setValue("ui/window_geometry", self.saveGeometry())
        self.settings.setValue("ui/splitter_state", self.splitter.saveState())
        
        # 2. DB Kapat
        if self.db:
            self.db.close()
            
        event.accept()
        
    def start_import_process(self):
        """Opens file dialog and starts the worker."""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilters(["Data Files (*.dat *.xml *.parquet)", "All Files (*)"])
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            if not files:
                return
            
        # 2. Disconnect the GUI Connection (Very Important!)
        # DuckDB may freeze if the read connection remains open while performing a write operation.
        if self.db.conn:
            self.db.close()
                
        # Prepare UI
        self.import_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.search_input.setEnabled(False)
        
        # Bind signals to slots and start worker
        self.worker = IngestionWorker(self.db_path, files, mode='staged')
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.status_changed.connect(lambda message: self.statusBar().showMessage(message))
        self.worker.finished.connect(self.on_import_finished)
        self.worker.error_occurred.connect(self.on_import_error)
        
        self.worker.start()
        
    def on_import_finished(self, stats):

        QMessageBox.information(self, "Success", "Process completed!\n\n", 
                                f"Processed: {stats.get('processed_files', 0)}\n",
                                f"ROMs Added: {stats.get('total_roms', 0)}")
        
        self._reset_ui_state()
        
        self.db.connect()
        self.model.refresh()
        self.status_label.setText(f"Rows: {self.model.rowCount():,}")
        
    def on_import_error(self, error_msg):
        
        QMessageBox.critical(self, "Error", f"Import Failed:\n{error_msg}")
        self._reset_ui_state()
        
        # Even if there's an error, restore the old connection.
        self.db.connect()

    def _on_row_selected(self, current, previous):
        """Handles row selection and updates the detail panel."""
        if not current.isValid():
            self.detail_panel.clear()
            return
        
        row_idx = current.row()
        
        columns = self.db.columns
        if not columns:
            return
        
        row_data = {}
        # Request data from model for all columns
        for col_idx, col_name in enumerate(columns):
            # Access the cell using the model's index() method
            index = self.model.index(row_idx, col_idx)
            # Get data with data() (DisplayRole)
            value = self.model.data(index, Qt.DisplayRole)
            row_data[col_name] = value
            
            # Send dict to Detail Panel
            self.detail_panel.update_data(row_data)

    def _reset_ui_state(self):
        self.btn_import.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.search_input.setEnabled(True)
        self.statusBar().showMessage("Ready")
        
    def open_settings(self):
        """Opens the Settings dialog."""
        settingsDialog = SettingsDialog(self)
        if settingsDialog.exec():
            # Settings saved, now apply in runtime
            self._apply_runtime_settings()
            
    def _apply_runtime_settings(self):
        """The settings are reflected on the interface in real time."""
        lock_panel = self.settings.value("ui/lock_panel", False, type=bool)
        
        if lock_panel:
            # Freeze panel width to its current state
            current_width = self.detail_panel.width()
            self.detail_panel.setFixedWidth(current_width)
        else:
            # Unlock (Release Minimum and Maximum)
            self.detail_panel.setMinimumWidth(0)
            self.detail_panel.setMaximumWidth(16777215) # QWIDGETSIZE_MAX
            
            # Make the splitter flexible again. 
            # (Prioritize the left side, let the right side adapt to the content)
            self.splitter.setStretchFactor(0, 1)
            self.splitter.setStretchFactor(1, 0)

    def _load_ui_settings(self):
        """Restores window size and splitter position."""
        restore = self.settings.value("ui/restore_layout", True, type=bool)
        if not restore:
            return
        
        geometry = self.settings.value("ui/window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        splitter_state = self.settings.value("ui/splitter_state")
        if splitter_state:
            self.splitter.restoreState(splitter_state)

        self._apply_runtime_settings()
