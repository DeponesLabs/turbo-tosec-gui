import duckdb
from typing import List, Tuple, Optional, Any, Dict

class DatabaseManager:
    """
    A read-optimized DuckDB wrapper designed for GUI applications.
    It handles pagination, dynamic filtering, and sorting to support
    virtualized (infinite scroll) views.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._column_names = []

    def connect(self):
        """Establishes a read-only connection to the DuckDB database."""
        # read_only=True is crucial for GUI safety and performance
        self.conn = duckdb.connect(self.db_path, read_only=True)
        self._load_column_names()

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _load_column_names(self):
        """Cache column names for the model."""
        if self.conn:
            # We assume 'roms' is the main table, as defined in turbo-tosec
            try:
                # Limit 0 query is the fastest way to get schema without reading data
                self.conn.execute("SELECT * FROM roms LIMIT 0")
                self._column_names = [desc[0] for desc in self.conn.description]
            except duckdb.Error as e:
                print(f"DB Error loading schema: {e}")
                self._column_names = []

    @property
    def columns(self) -> List[str]:
        return self._column_names

    def get_total_count(self, filters: Dict[str, str] = None) -> int:
        """
        Returns the total number of rows matching the filters.
        Used by the GUI to calculate scrollbar size.
        """
        query = "SELECT COUNT(*) FROM roms"
        params = []
        
        if filters:
            where_clause, params = self._build_where_clause(filters)
            query += f" WHERE {where_clause}"

        try:
            return self.conn.execute(query, params).fetchone()[0]
        except Exception as e:
            print(f"DB Count Error: {e}")
            return 0

    def fetch_data(self, 
                   limit: int, 
                   offset: int, 
                   filters: Dict[str, str] = None, 
                   sort_col: str = None, 
                   sort_asc: bool = True) -> List[Tuple]:
        """
        Fetches a specific slice of data (The 'View' Port).
        This is the engine of the infinite scroll.
        """
        query = "SELECT * FROM roms"
        params = []

        # 1. Apply Filters
        if filters:
            where_clause, filter_params = self._build_where_clause(filters)
            query += f" WHERE {where_clause}"
            params.extend(filter_params)

        # 2. Apply Sorting
        if sort_col and sort_col in self._column_names:
            direction = "ASC" if sort_asc else "DESC"
            query += f" ORDER BY {sort_col} {direction}"
        
        # 3. Apply Pagination (The Virtualization Magic)
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            return self.conn.execute(query, params).fetchall()
        except Exception as e:
            print(f"DB Fetch Error: {e}")
            return []

    def _build_where_clause(self, filters: Dict[str, str]) -> Tuple[str, List[Any]]:
        """
        Constructs a safe SQL WHERE clause dynamically.
        filters: {'game_name': 'mario', 'platform': 'amiga'}
        """
        conditions = []
        params = []
        
        for col, val in filters.items():
            if not val:
                continue
            # Use ILIKE for case-insensitive flexible search
            # We assume string search for now. Can be enhanced for numbers later.
            conditions.append(f"{col} ILIKE ?")
            params.append(f"%{val}%")
            
        return " AND ".join(conditions), params

    def get_distinct_values(self, column: str) -> List[str]:
        """
        Useful for creating 'Combo Box' filters (e.g., select Platform).
        """
        if column not in self._column_names:
            return []
        
        try:
            query = f"SELECT DISTINCT {column} FROM roms ORDER BY {column}"
            result = self.conn.execute(query).fetchall()
            return [row[0] for row in result if row[0] is not None]
        except:
            return []
