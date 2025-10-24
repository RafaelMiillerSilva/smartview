from PySide6.QtWidgets import QMainWindow, QStackedWidget, QApplication
from PySide6.QtCore import QTimer
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
        self.home_page = None  # será criada após o login

        self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)

        # Define tamanho fixo da janela (não do widget interno)
        self.setFixedSize(500, 400)

        # Centraliza após a janela estar visível
        QTimer.singleShot(1, self.center_window)

    def center_window(self):
        """Centraliza a janela principal na tela."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def on_connected(self, server, database):
        """Chamado pela LoginPage após login bem-sucedido"""
        # Libera o tamanho e maximiza
        self.setMinimumSize(800, 600)
        self.showMaximized()

        # Cria HomePage se ainda não existir
        if not self.home_page:
            self.home_page = HomePage(server, database)
            self.stack.addWidget(self.home_page)

        # Exibe HomePage
        self.stack.setCurrentWidget(self.home_page)
