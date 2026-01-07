import sys
import os
from PySide6.QtWidgets import QApplication

from turbo_skryer.ui.MainWindow import MainWindow

def main():
    
    app = QApplication(sys.argv)
    app.setOrganizationName("Depones Labs")
    app.setApplicationName("Skryer")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    
    main()