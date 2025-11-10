from PySide6.QtWidgets import QMainWindow, QStackedWidget, QApplication
from PySide6.QtCore import QTimer
from gui.pages.login_page import LoginPage
from gui.pages.home_page import HomePage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartView")

        # Stack para gerenciar as páginas
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Instancia a LoginPage
        self.login_page = LoginPage(self.on_connected)
        self.home_page = None  # será criada após o login

        # Adiciona a página inicial (login)
        self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)

        # Define tamanho inicial para login
        self.resize(500, 850)
        self.setMinimumSize(500, 850)
        self.setMaximumSize(500, 850)

        # Centraliza após a renderização
        QTimer.singleShot(1, self.center_window)

    def center_window(self):
        """Centraliza a janela principal na tela."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def on_connected(self, server: str, database: str):
        """
        Chamado pela LoginPage após uma conexão bem-sucedida.
        Troca para a HomePage e ajusta a janela.
        """
        # Remove restrições de tamanho
        self.setMinimumSize(800, 600)
        self.setMaximumSize(16777215, 16777215)  # Remove limite máximo
        
        # Maximiza a janela
        self.showMaximized()

        # Cria HomePage se ainda não existir
        if not self.home_page:
            self.home_page = HomePage(server, database, main_window=self)
            self.stack.addWidget(self.home_page)

        # Alterna para a HomePage
        self.stack.setCurrentWidget(self.home_page)

    def back_to_login(self):
        """
        Volta para a tela de login e reseta o tamanho da janela.
        """
        # Volta para tamanho fixo de login
        self.setMinimumSize(500, 650)
        self.setMaximumSize(500, 650)
        self.resize(500, 650)
        self.center_window()
        
        # Remove a home_page antiga
        if self.home_page:
            self.stack.removeWidget(self.home_page)
            self.home_page.deleteLater()
            self.home_page = None
        
        # Recria a LoginPage para limpar dados
        self.stack.removeWidget(self.login_page)
        self.login_page.deleteLater()
        self.login_page = LoginPage(self.on_connected)
        self.stack.addWidget(self.login_page)
        
        # Alterna para a LoginPage
        self.stack.setCurrentWidget(self.login_page)