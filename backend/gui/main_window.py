from PySide6.QtWidgets import QMainWindow, QStackedWidget, QApplication, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QRect
from PySide6.QtGui import QPalette, QColor, QIcon
from gui.pages.login_page import LoginPage
from gui.pages.home_page import HomePage

try:
    from backend.config.paths import ROOT_DIR
except ImportError:
    from pathlib import Path
    ROOT_DIR = Path(__file__).parent.parent


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartView")
        
        # Define o icone da janela
        icon_path = ROOT_DIR / "assets" / "smartview_logov2.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Stack para gerenciar as paginas
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Instancia a LoginPage
        self.login_page = LoginPage(self.on_connected)
        self.home_page = None  # sera criada apos o login

        # Adiciona a pagina inicial (login)
        self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)

        # Define tamanho inicial para login
        self.resize(500, 750)
        self.setMinimumSize(500, 750)
        self.setMaximumSize(500, 750)

        # Centraliza apos a renderizacao
        QTimer.singleShot(1, self.center_window)

    def center_window(self):
        """Centraliza a janela principal na tela."""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def on_connected(self, server: str, database: str):
        """
        Chamado pela LoginPage apos uma conexao bem-sucedida.
        Troca para a HomePage com animacao suave.
        """
        # Cria HomePage se ainda nao existir
        if not self.home_page:
            self.home_page = HomePage(server, database, main_window=self)
            self.stack.addWidget(self.home_page)
        
        # Inicia a transicao animada
        self.animate_transition_to_home()

    def animate_transition_to_home(self):
        """Anima a transicao da tela de login para home"""
        # 1. Fade out da tela de login
        self.fade_out_widget(self.login_page, duration=300)
        
        # 2. Apos fade out, redimensiona e maximiza
        QTimer.singleShot(300, self.resize_and_show_home)

    def resize_and_show_home(self):
        """Redimensiona a janela e mostra a home com fade in"""
        # Remove restricoes de tamanho
        self.setMinimumSize(800, 600)
        self.setMaximumSize(16777215, 16777215)
        
        # Animacao de redimensionamento suave
        self.animate_window_resize()
        
        # Apos redimensionar, troca para home com fade in
        QTimer.singleShot(400, self.show_home_with_fade)

    def animate_window_resize(self):
        """Anima o redimensionamento da janela"""
        # Pega geometria atual e da tela
        screen = QApplication.primaryScreen().availableGeometry()
        
        # Cria animacao de geometria
        self.resize_animation = QPropertyAnimation(self, b"geometry")
        self.resize_animation.setDuration(400)
        self.resize_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        # Define geometria inicial (atual) e final (maximizada)
        current_geometry = self.geometry()
        self.resize_animation.setStartValue(current_geometry)
        self.resize_animation.setEndValue(screen)
        
        self.resize_animation.start()

    def show_home_with_fade(self):
        """Mostra a home page com fade in"""
        # Troca para a home page
        self.stack.setCurrentWidget(self.home_page)
        
        # Fade in da home page
        self.fade_in_widget(self.home_page, duration=400)

    def fade_out_widget(self, widget, duration=300):
        """Aplica efeito de fade out em um widget"""
        # Cria efeito de opacidade se nao existir
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        else:
            effect = widget.graphicsEffect()
        
        # Animacao de fade out
        self.fade_animation = QPropertyAnimation(effect, b"opacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()

    def fade_in_widget(self, widget, duration=300):
        """Aplica efeito de fade in em um widget"""
        # Cria efeito de opacidade se nao existir
        if not widget.graphicsEffect():
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        else:
            effect = widget.graphicsEffect()
        
        # Define opacidade inicial como 0
        effect.setOpacity(0.0)
        
        # Animacao de fade in
        self.fade_animation = QPropertyAnimation(effect, b"opacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()

    def back_to_login(self):
        """
        Volta para a tela de login com animacao suave.
        """
        # Fade out da home page
        self.fade_out_widget(self.home_page, duration=300)
        
        # Apos fade out, redimensiona e volta para login
        QTimer.singleShot(300, self.resize_and_show_login)

    def resize_and_show_login(self):
        """Redimensiona para tamanho de login e mostra com fade in"""
        # Animacao de redimensionamento
        self.resize_animation = QPropertyAnimation(self, b"geometry")
        self.resize_animation.setDuration(400)
        self.resize_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        # Geometria atual e final (centralizada com tamanho de login)
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - 500) // 2
        y = (screen.height() - 750) // 2
        
        target_geometry = QRect(x, y, 500, 750)
        
        self.resize_animation.setStartValue(self.geometry())
        self.resize_animation.setEndValue(target_geometry)
        self.resize_animation.start()
        
        # Apos redimensionar, troca para login
        QTimer.singleShot(400, self.show_login_with_fade)

    def show_login_with_fade(self):
        """Mostra a tela de login com fade in"""
        # Volta para tamanho fixo
        self.setMinimumSize(500, 750)
        self.setMaximumSize(500, 750)
        self.resize(500, 750)
        
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
        
        # Alterna para a LoginPage com fade in
        self.stack.setCurrentWidget(self.login_page)
        self.fade_in_widget(self.login_page, duration=400)