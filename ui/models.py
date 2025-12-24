from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal
from typing import Any, Dict

# core/database.py içindeki sınıfı import ediyoruz
# (Gerçek projede import yolu proje yapısına göre ayarlanmalı)
from core.database import DatabaseManager

class InfiniteTableModel(QAbstractTableModel):
    """
    A high-performance, virtualized table model for massive datasets.
    Implements a 'Sliding Window' cache strategy to minimize memory usage
    while maintaining 60 FPS scrolling.
    """
    
    # Constants for tuning performance
    PAGE_SIZE = 2000  # How many rows to fetch in one DB Query (The 'Chunk')
    CACHE_TOLERANCE = 500 # Pre-fetch margin (Not strictly used here but good for logic)

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        
        # State
        self._total_rows = 0
        self._filters: Dict[str, str] = {}
        self._sort_col_name: str = None
        self._sort_asc: bool = True
        
        # The Cache (Sliding Window)
        self._cache_data = []      # List of tuples/rows
        self._cache_offset = -1    # Where does the current cache start?
        self._cache_valid = False  # Is the cache dirty?
        
        # Initial Setup
        self.refresh()

    def refresh(self):
        """Re-calculates total count and invalidates cache."""
        self.beginResetModel()
        self._total_rows = self.db.get_total_count(self._filters)
        self._cache_valid = False
        self._cache_data = []
        self._cache_offset = -1
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Returns the TOTAL number of rows in the DB.
        The View thinks we have all data loaded, but we don't.
        """
        return self._total_rows

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.db.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        # Optimization: We only care about DisplayRole (Text)
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            
            # --- CACHE LOGIC START ---
            
            # Check if the requested row is inside our current memory window
            if not self._is_row_in_cache(row):
                self._fetch_page_containing(row)
            
            # Calculate local index within the cache list
            local_index = row - self._cache_offset
            
            try:
                # Return the data from RAM
                # Note: DuckDB returns tuples, so we access by index
                val = self._cache_data[local_index][col]
                
                # Format specific types if needed (e.g., Size bytes -> MB)
                # For raw speed, we return string representation for now
                return str(val) if val is not None else ""
                
            except IndexError:
                # Fallback for race conditions or edge cases
                return None
            
            # --- CACHE LOGIC END ---

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """Displays Column Names from DB Schema."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            try:
                col_name = self.db.columns[section]
                # Beautify headers: "release_year" -> "Release Year"
                return col_name.replace("_", " ").title()
            except IndexError:
                return ""
        return None

    def sort(self, column: int, order: Qt.SortOrder) -> None:
        """Called when user clicks a header."""
        self._sort_col_name = self.db.columns[column]
        self._sort_asc = (order == Qt.AscendingOrder)
        self.refresh()

    def set_filter(self, column: str, value: str):
        """Applies a filter and refreshes the view."""
        if not value:
            if column in self._filters:
                del self._filters[column]
        else:
            self._filters[column] = value
            
        self.refresh()
        
    def clear_filters(self):
        self._filters.clear()
        self.refresh()

    # --- Internal Helpers ---

    def _is_row_in_cache(self, row_index: int) -> bool:
        """Returns True if the requested row is currently in memory."""
        if not self._cache_valid or not self._cache_data:
            return False
            
        start = self._cache_offset
        end = start + len(self._cache_data)
        
        return start <= row_index < end

    def _fetch_page_containing(self, row_index: int):
        """
        The heavy lifting. Fetches a chunk of data from DB centered around the requested row.
        """
        # Strategy: Align to PAGE_SIZE boundaries (0, 2000, 4000...)
        # This prevents "cache thrashing" if user scrolls up/down by 1 pixel.
        page_start = (row_index // self.PAGE_SIZE) * self.PAGE_SIZE
        
        # Fetch from DB
        new_data = self.db.fetch_data(
            limit=self.PAGE_SIZE,
            offset=page_start,
            filters=self._filters,
            sort_col=self._sort_col_name,
            sort_asc=self._sort_asc
        )
        
        # Update Cache
        self._cache_data = new_data
        self._cache_offset = page_start
        self._cache_valid = True
        
        # Debug Log (Optional: To see when DB hits happen)
        # print(f"Cache Miss! Fetched rows {page_start} to {page_start + len(new_data)}")
