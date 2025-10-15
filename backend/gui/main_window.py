from PySide6.QtWidgets import QMainWindow, QStackedWidget
from .pages.login_page import LoginPage
from .pages.home_page import HomePage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartView")
        self.showMaximized()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = LoginPage(self.on_connected)
        self.home_page = HomePage()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.home_page)

        self.stack.setCurrentWidget(self.login_page)

    def on_connected(self):
        self.stack.setCurrentWidget(self.home_page)
