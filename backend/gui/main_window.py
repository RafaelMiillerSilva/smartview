from PySide6.QtWidgets import QMainWindow, QStackedWidget
from .pages.login_page import LoginPage
from .pages.home_page import HomePage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartView")

        # Stack para páginas
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Instancia LoginPage
        self.login_page = LoginPage(self.on_connected)
        self.home_page = None  # criada apenas após login

        self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)

        # Tamanho fixo do login e centralizado
        self.login_page.setFixedSize(500, 400)
        self.center_window()

    def center_window(self):
        """Centraliza a MainWindow na tela."""
        frameGm = self.frameGeometry()
        screen = self.screen().availableGeometry().center()
        frameGm.moveCenter(screen)
        self.move(frameGm.topLeft())

    def on_connected(self, server, database):
        """Chamado pela LoginPage após login bem-sucedido"""
        # Remove tamanho fixo para permitir maximização da janela
        self.login_page.setFixedSize(self.login_page.sizeHint())  # libera tamanho do stack
        self.showMaximized()  # maximiza a janela

        # Cria HomePage se ainda não existir
        if not self.home_page:
            self.home_page = HomePage(server, database)
            self.stack.addWidget(self.home_page)

        # Exibe HomePage
        self.stack.setCurrentWidget(self.home_page)
