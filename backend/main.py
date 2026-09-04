import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication


# === Define os diretórios no sys.path ===
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for path in [ROOT_DIR, BACKEND_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from backend.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
