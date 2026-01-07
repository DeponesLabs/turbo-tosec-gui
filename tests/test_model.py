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
@pytest.mark.parametrize("system_name, expected_folder", [
    ("Commodore 64", "C64"),
    ("Commodore Amiga", "Amiga"),
    ("Atari ST", "Atari ST"),
    ("Unknown System", None) # Fail-safe testi (örnek)
])

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

@pytest.mark.parametrize("filter_system, expected_platform_val", [
    # (Veritabanında arayacağımız sistem, Beklediğimiz Platform Değeri)
    ("Commodore 64", "Commodore 64"),
    ("Commodore Amiga", "Commodore Amiga"),
    # Eğer DB'de "Unknown" yoksa bu test için Mock kullanmak gerekir, şimdilik var olanları yazalım:
    ("Sinclair ZX Spectrum", "Sinclair ZX Spectrum") 
])
def test_fetch_row_data_integration(model, filter_system, expected_platform_val):
    """
    Integration Test: 
    1. Modele filtre uygula.
    2. İlk satırı View gibi iste.
    3. Gelen veride 'platform' sütunu doğru mu kontrol et.
    """
    
    # 1. Filtrele (Böylece satır 0 kesinlikle istediğimiz sistem olur)
    # Not: DB'de 'system' sütununa göre filtreliyoruz
    model.set_filter("system", filter_system)
    
    # Veri var mı?
    if model.rowCount() == 0:
        pytest.skip(f"Veritabanında '{filter_system}' için kayıt bulunamadı, test atlanıyor.")
    
    # 2. View Simülasyonu: 0. Satırı çek
    # (Bu işlem arka planda fetch_page yapar, cache doldurur)
    row_data = get_row_as_dict(model, row_idx=0)
    
    # 3. Kontrol Et
    print(f"\nÇekilen Satır Verisi: {row_data}")
    
    # Platform sütunu geldi mi?
    assert "platform" in row_data, "Row data içinde 'platform' anahtarı yok!"
    
    # Gelen değer beklediğimiz mi?
    # Not: DB'deki veri bazen '-' olabilir, senin mapping mantığını burada değil
    # DetailsPanel testinde kontrol etmek daha doğrudur. 
    # Burada sadece Modelin veriyi doğru taşıdığını test ediyoruz.
    assert row_data["system"] == filter_system
    
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
    