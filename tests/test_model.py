import os
import pytest
from unittest.mock import MagicMock

from PySide6.QtCore import Qt

from turbo_tosec import DatabaseManager
from turbo_skryer.ui.models import InfiniteTableModel

# Bu fonksiyon bir "Fixture"dır. Testlerden önce çalışır.
@pytest.fixture
def db_manager():
    path = "E:/HOME/Documents/Databases/turbo-tosec/duckdb/tosec-v2025-03-13.duckdb"
    db = DatabaseManager(path, read_only=True)
    db.connect()
    return db

@pytest.fixture
def model(db_manager):
    model = InfiniteTableModel(db_manager)
    return model
    
# Test turbo_tosec.DatabaseManager.fetch_page method
# def fetch_page(self, limit: int, offset: int, filters: Dict[str, str] = None, sort_col: str = None, sort_asc: bool = True) -> List[Tuple]:
# @pytest.mark.parametrize("platform, expected_folder", [
#     ("Commodore 64", "C64"),
#     ("Commodore Amiga", "Amiga"),
#     ("Atari ST", "Atari ST"),
#     ("Unknown System", None) # Fail-safe testi (örnek)
# ])
def foo(platform, expected_folder):
    pass

def test_on_table_row_selected(db_manager, model):

    columns = db_manager.columns
    row_idx = 0  # First line is enough for test purposes.
    row_data = {}
    
    for col_idx, col_name in enumerate(columns):
        # Access the cell using the model's index() method
        index = model.index(row_idx, col_idx)
        # Get data with data() (DisplayRole)
        value = model.data(index, Qt.DisplayRole)
        row_data[col_name] = value
        
    platform_name = row_data['platform']
    
    assert(platform_name, 'platform')

def get_row_as_dict(model, row_idx):
  
    row_data = {}
    col_count = model.columnCount()
    col_names = model.db.columns 
    
    for col_idx in range(col_count):
        col_name = col_names[col_idx]
        
        index = model.index(row_idx, col_idx)
        val = model.data(index, role=Qt.DisplayRole)
        row_data[col_name] = val
        
    return row_data


    
# Test with mock object
def test_model_with_mock_db():
    # 1. DÜBLÖRÜ YARAT (Mock Object)
    # Artık 'mock_db' adında, her şeye "he" diyen bir nesnemiz var.
    mock_db = MagicMock()

    # 2. SENARYOYU YAZ (Dublöre ne yapacağını öğret)
    
    # A) Sanki veritabanında bu sütunlar varmış gibi davran:
    mock_db.columns = ['game_name', 'platform']
    
    # B) Biri senden 'count_total_rows' isterse, hesaplama yapma, direkt 100 dön.
    mock_db.count_total_rows = 100
    
    # 3. TESTİ BAŞLAT (Modeli sahte db ile kandır)
    # Model, karşısındakini gerçek DatabaseManager sanıyor.
    model = InfiniteTableModel(mock_db)
    
    # 4. KONTROL ET (Assert)
    
    # Model sütunları dublörden alabildi mi?
    print(f"\nModelin Sütunları: {model.db.columns}")
    assert "platform" in model.db.columns
    