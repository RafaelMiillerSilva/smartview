from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Bem-vindo ao SmartView! Conexão estabelecida com sucesso 🚀")
        layout.addWidget(label)
        self.setLayout(layout)
    
    def go_to_home(server, database):
        home = HomePage(server, database)
        home.showMaximized()  # 🔹 abre tela cheia
        login.close()

