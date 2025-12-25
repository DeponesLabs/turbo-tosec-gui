from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit, QLabel, QHeaderView, QAbstractItemView
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QIcon

from core.database import DatabaseManager
from ui.models import InfiniteTableModel

class MainWindow(QMainWindow):
    
    def __init__(self):
        
        super().__init__()
        
        db_path = "../../../TEST_DATS/tosec-2025-03-13.duckdb"
        
        self.setWindowTitle("Depones GUI - Turbo-TOSEC Viewer")
        self.resize(1200, 800)
        
        # 1. Backend Setup
        self.db = DatabaseManager(db_path)
        self.db.connect()
        
        # 2. Model Setup
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
        lbl = QLabel("Filter (Title):")
        lbl.setStyleSheet("font-weight: bold;")
        
        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search... (e.g. 'Mario', 'Zelda')")
        self.search_input.setClearButtonEnabled(True)
        
        # Connect Input -> Timer (Not directly to Model!)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        
        bar_layout.addWidget(lbl)
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