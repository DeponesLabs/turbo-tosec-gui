import sys
import os
from PySide6.QtWidgets import QApplication
from ui.MainWindow import MainWindow

def main():
    
    # 1. Setup Application
    app = QApplication(sys.argv)
    app.setApplicationName("Depones GUI")
    app.setOrganizationName("Depones Labs")

    # 3. Launch Window
    window = MainWindow()
    window.show()
    
    # 4. Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()