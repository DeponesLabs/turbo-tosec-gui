import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # 1. Setup Application
    app = QApplication(sys.argv)
    app.setApplicationName("Depones GUI")
    app.setOrganizationName("Depones Labs")
    
    # 2. Argument Parsing (Simple)
    # Usage: python main.py [path_to_db]
    db_path = "tosec.duckdb" # Default fallback
    
    if len(sys.argv) > 1:
        potential_path = sys.argv[1]
        if os.path.exists(potential_path):
            db_path = potential_path
            
    if not os.path.exists(db_path):
        print(f"Error: Database not found at '{db_path}'")
        print("Please generate it first using 'turbo-tosec' CLI.")
        print("Usage: python main.py <path_to_duckdb>")
        sys.exit(1)

    # 3. Launch Window
    window = MainWindow(db_path)
    window.show()
    
    # 4. Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()