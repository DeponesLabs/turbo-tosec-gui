import os

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit, QLabel, QHeaderView, QAbstractItemView, QPushButton, QProgressBar, QFileDialog, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QIcon

from turbo_tosec import DatabaseManager
from turbo_skryer.ui.models import InfiniteTableModel
from turbo_skryer.ui.workers import IngestionWorker

class MainWindow(QMainWindow):
    
    def __init__(self):
        
        super().__init__()
        
        db_path = "TEST_DATS/tosec-2025-03-13.duckdb"
        
        self.setWindowTitle("Depones GUI - Turbo-TOSEC Viewer")
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
        self._setup_table_view()
        self._setup_status_bar()
        
        # 4. Debounce Timer (Critical for Search Performance)
        self.search_timer = QTimer()
        self.search_timer.setInterval(300) # Wait 300ms after last keystroke
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._apply_search)

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

    def _setup_table_view(self):
        """Configures the Grid."""
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        
        # Visual Tweaks for "Pro" Look
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows) # Select full row
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.verticalHeader().setVisible(False) # Hide index numbers (1,2,3...)
        self.table_view.setShowGrid(False) # Modern look (only rows)
        
        # Column Resizing Strategy
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True) # Description fills the rest
        # We can optimize column widths later based on content
        
        self.layout.addWidget(self.table_view)

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
        self.db.disconnect()
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

    def _reset_ui_state(self):
        self.btn_import.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.search_input.setEnabled(True)
        self.statusBar().showMessage("Ready")
        