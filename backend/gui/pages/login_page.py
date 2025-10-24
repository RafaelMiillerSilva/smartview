import sys
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QFrame, QDialog, QPlainTextEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from utils.connection import connect_to_database, list_databases, load_connection_json, log

class LoginPage(QWidget):
    def __init__(self, on_connect):
        super().__init__()
        self.on_connect = on_connect
        layout = QVBoxLayout()
        self.setLayout(layout)

        # -------------------
        # BLOCO: Conexão Servidor
        # -------------------
        server_frame = QFrame()
        server_layout = QVBoxLayout(server_frame)

        lbl_server = QLabel("Servidor:")
        self.input_server = QLineEdit()
        self.input_server.setPlaceholderText("Ex: localhost, DESKTOP\\SQLEXPRESS")
        server_layout.addWidget(lbl_server)
        server_layout.addWidget(self.input_server)

        self.checkbox_windows_auth = QCheckBox("Usar autenticação do Windows")
        self.checkbox_windows_auth.setChecked(True)
        self.checkbox_windows_auth.stateChanged.connect(self.toggle_auth_mode)
        server_layout.addWidget(self.checkbox_windows_auth)

        lbl_user = QLabel("Usuário:")
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuário (SQL Authentication)")
        server_layout.addWidget(lbl_user)
        server_layout.addWidget(self.input_user)

        lbl_pass = QLabel("Senha:")
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Senha")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        server_layout.addWidget(lbl_pass)
        server_layout.addWidget(self.input_password)

        self.button_connect_server = QPushButton("Conectar")
        self.button_connect_server.clicked.connect(self.try_connect_server)
        server_layout.addWidget(self.button_connect_server)

        layout.addWidget(QLabel("🔌 Conexão com Servidor"))
        layout.addWidget(server_frame)

        # -------------------
        # BLOCO: Conexão Banco
        # -------------------
        db_frame = QFrame()
        db_layout = QVBoxLayout(db_frame)

        lbl_db = QLabel("Banco de Dados:")
        self.combo_database = QComboBox()
        self.combo_database.setEditable(True)
        self.combo_database.setEnabled(False)
        db_layout.addWidget(lbl_db)
        db_layout.addWidget(self.combo_database)

        self.button_continue = QPushButton("Continuar")
        self.button_continue.setEnabled(False)
        self.button_continue.clicked.connect(self.try_connect_database)
        db_layout.addWidget(self.button_continue)

        layout.addWidget(QLabel("📂 Conexão com Banco de Dados"))
        layout.addWidget(db_frame)

        # -------------------
        # Mensagem de erro/sucesso
        # -------------------
        self.label_error = QLabel("")
        layout.addWidget(self.label_error)

        # Pré-carrega último servidor salvo
        last_conn = load_connection_json()
        if last_conn:
            if "server" in last_conn:
                self.input_server.setText(last_conn["server"])
            if last_conn.get("windows_auth", False):
                self.checkbox_windows_auth.setChecked(True)
            if "database" in last_conn:
                self.combo_database.addItem(last_conn["database"])

        self.toggle_auth_mode()
        self.setFixedSize(500, 400)
    

    # -------------------
    # MÉTODOS
    # -------------------
    
    def toggle_auth_mode(self):
        is_windows_auth = self.checkbox_windows_auth.isChecked()
        self.input_user.setDisabled(is_windows_auth)
        self.input_password.setDisabled(is_windows_auth)

    def animate_button(self, button, color):
        original_style = button.styleSheet()
        button.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold;")
        QTimer.singleShot(600, lambda: button.setStyleSheet(original_style))


    def show_error_dialog(self, title: str, message: str):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)
        label = QLabel("Detalhes do erro:")
        text_box = QPlainTextEdit()
        text_box.setPlainText(message)
        text_box.setReadOnly(True)
        text_box.setStyleSheet("background-color: #222; color: #ddd; font-family: Consolas; font-size: 11pt;")

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.close)

        layout.addWidget(label)
        layout.addWidget(text_box)
        layout.addWidget(btn_close)

        dialog.exec()

    def try_connect_server(self):
        server = self.input_server.text().strip()
        user = self.input_user.text().strip()
        password = self.input_password.text().strip()
        windows_auth = self.checkbox_windows_auth.isChecked()

        ok, result = list_databases(server, user, password, windows_auth)
        if ok:
            self.combo_database.clear()
            self.combo_database.addItems(result)
            self.combo_database.setEnabled(True)
            self.button_continue.setEnabled(True)
            self.label_error.setText("✅ Servidor conectado! Selecione o banco.")
            self.animate_button(self.button_connect_server, "green")
        else:
            self.combo_database.setEnabled(False)
            self.button_continue.setEnabled(False)
            self.label_error.setText("❌ Erro servidor")
            self.animate_button(self.button_connect_server, "red")
            self.show_error_dialog("Erro ao conectar ao servidor", str(result))


    def try_connect_database(self):
        server = self.input_server.text().strip()
        database = self.combo_database.currentText().strip()
        windows_auth = self.checkbox_windows_auth.isChecked()

        if windows_auth:
            user = ""
            password = ""
        else:
            user = self.input_user.text().strip()
            password = self.input_password.text().strip()

        ok, message = connect_to_database(server, user, password, database, windows_auth)
        if ok:
            self.label_error.setText("✅ " + message)

            #Passa servidor e banco para o callback
            self.on_connect(server, database)

        else:
            self.label_error.setText("❌ Erro ao conectar ao banco")
            self.show_error_dialog("Erro ao conectar ao banco", message)
