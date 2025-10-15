import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
sys.path.append(str(ROOT_DIR))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow 

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
