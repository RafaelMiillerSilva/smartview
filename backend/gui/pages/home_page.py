from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class HomePage(QWidget):
    def __init__(self, server, database):
        super().__init__()
        layout = QVBoxLayout()

        msg = f"✅ Conectado a {server} — Banco: {database}\nBem-vindo ao SmartView 🚀"
        label = QLabel(msg)
        layout.addWidget(label)

        self.setLayout(layout)
