import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QComboBox, QFrame, QDialog, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer
from utils.connection import (
    connect_to_database,
    list_databases,
    load_connection_json,
    save_connection_json,
    log
)


class LoginPage(QWidget):
    def __init__(self, on_connect):
        super().__init__()
        self.on_connect = on_connect
        
        # Define fundo da pagina
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        self.setLayout(layout)

        # -------------------
        # BLOCO: Conexao Servidor
        # -------------------
        server_frame = QFrame()
        server_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0px;
                padding: 15px;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        server_layout = QVBoxLayout(server_frame)

        lbl_server = QLabel("Servidor:")
        lbl_server.setStyleSheet("""
            font-weight: bold;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            font-size: 17px;                                 
        """)
        self.input_server = QLineEdit()
        self.input_server.setPlaceholderText("Ex: localhost, DESKTOP\\SQLEXPRESS")
        self.input_server.setStyleSheet("""
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 0px;
            font-size: 13px;
            background-color: white;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
        """)
        server_layout.addWidget(lbl_server)
        server_layout.addWidget(self.input_server)

        self.checkbox_windows_auth = QCheckBox("Usar autenticacao do Windows")
        self.checkbox_windows_auth.setChecked(True)
        self.checkbox_windows_auth.stateChanged.connect(self.toggle_auth_mode)
        self.checkbox_windows_auth.setStyleSheet("""
            color: #192c3e;
            font-size: 13px;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
        """)
        server_layout.addWidget(self.checkbox_windows_auth)

        lbl_user = QLabel("Usuario:")
        lbl_user.setStyleSheet("""
            font-weight: bold;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            font-size: 17px;
        """)
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuario (SQL Authentication)")
        self.input_user.setStyleSheet("""
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 0px;
            font-size: 13px;
            background-color: white;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
        """)
        server_layout.addWidget(lbl_user)
        server_layout.addWidget(self.input_user)

        lbl_pass = QLabel("Senha:")
        lbl_pass.setStyleSheet("""
            font-weight: bold;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            font-size: 17px;                   
        """)
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Senha")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setStyleSheet("""
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 0px;
            font-size: 13px;
            background-color: white;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
        """)
        server_layout.addWidget(lbl_pass)
        server_layout.addWidget(self.input_password)

        self.button_connect_server = QPushButton("Conectar ao Servidor")
        self.button_connect_server.clicked.connect(self.try_connect_server)
        self.button_connect_server.setStyleSheet("""
            QPushButton {
                background-color: #192c3e;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 0px;
                font-size: 14px;
                font-weight: 600;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #243d54;
            }
            QPushButton:pressed {
                background-color: #0f1f2e;
            }
        """)
        server_layout.addWidget(self.button_connect_server)

       
        layout.addWidget(server_frame)

        # -------------------
        # BLOCO: Conexao Banco
        # -------------------
        db_frame = QFrame()
        db_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0px;
                padding: 15px;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        db_layout = QVBoxLayout(db_frame)

        lbl_db = QLabel("Banco de Dados:")
        lbl_db.setStyleSheet("""
            font-weight: bold;
            margin-top: 5px;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            font-size: 20px;                 
        """)
        self.combo_database = QComboBox()
        self.combo_database.setEditable(True)
        self.combo_database.setEnabled(False)
        self.combo_database.setStyleSheet("""
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 0px;
            font-size: 13px;
            background-color: white;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
        """)
        db_layout.addWidget(lbl_db)
        db_layout.addWidget(self.combo_database)

        self.button_continue = QPushButton("Conectar ao Banco")
        self.button_continue.setEnabled(False)
        self.button_continue.clicked.connect(self.try_connect_database)
        self.button_continue.setStyleSheet("""
            QPushButton {
                background-color: #192c3e;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 0px;
                font-size: 14px;
                font-weight: 600;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #243d54;
            }
            QPushButton:pressed {
                background-color: #0f1f2e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        db_layout.addWidget(self.button_continue)

        layout.addWidget(db_frame)

        # -------------------
        # Mensagem de erro/sucesso
        # -------------------
        self.label_error = QLabel("")
        self.label_error.setAlignment(Qt.AlignCenter)
        self.label_error.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            padding: 10px;
            border-radius: 0px;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
        """)
        layout.addWidget(self.label_error)

        # -------------------
        # Pre-carrega ultima conexao
        # -------------------
        last_conn = load_connection_json()
        if last_conn:
            self.input_server.setText(last_conn.get("server", ""))
            self.checkbox_windows_auth.setChecked(last_conn.get("windows_auth", True))
            if not last_conn.get("windows_auth", True):
                self.input_user.setText(last_conn.get("username", ""))
                self.input_password.setText(last_conn.get("password", ""))
            if "database" in last_conn and last_conn["database"]:
                self.combo_database.addItem(last_conn["database"])
                self.combo_database.setEnabled(True)
                self.button_continue.setEnabled(True)

        self.toggle_auth_mode()

    # -------------------
    # METODOS
    # -------------------
    def toggle_auth_mode(self):
        """Habilita/desabilita campos de usuario/senha conforme o modo"""
        is_windows_auth = self.checkbox_windows_auth.isChecked()
        self.input_user.setDisabled(is_windows_auth)
        self.input_password.setDisabled(is_windows_auth)

    def show_error_dialog(self, title: str, message: str):
        """Exibe dialogo de erro com texto detalhado"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)
        
        label = QLabel("Detalhes do erro:")
        label.setStyleSheet("""
            font-weight: bold;
            margin-bottom: 10px;
            color: #192c3e;
            font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
        """)
        
        text_box = QPlainTextEdit()
        text_box.setPlainText(message)
        text_box.setReadOnly(True)
        text_box.setStyleSheet("""
            background-color: #2b2b2b;
            color: #f0f0f0;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11pt;
            padding: 10px;
            border: 1px solid #444;
            border-radius: 0px;
        """)

        btn_close = QPushButton("Fechar")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #192c3e;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 0px;
                font-weight: 600;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #243d54;
            }
        """)
        btn_close.clicked.connect(dialog.close)

        layout.addWidget(label)
        layout.addWidget(text_box)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

        dialog.exec()

    # -------------------
    # CONEXAO COM SERVIDOR
    # -------------------
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
            self.label_error.setText("Servidor conectado! Selecione o banco.")
            self.label_error.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                border-radius: 0px;
                background-color: #d4edda;
                color: #155724;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            """)

            # Salva conexao parcial
            save_connection_json(server, "", user, password, windows_auth)

        else:
            self.combo_database.setEnabled(False)
            self.button_continue.setEnabled(False)
            self.label_error.setText("Erro ao conectar ao servidor")
            self.label_error.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                border-radius: 0px;
                background-color: #f8d7da;
                color: #721c24;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            """)
            self.show_error_dialog("Erro ao conectar ao servidor", str(result))

    # -------------------
    # CONEXAO COM BANCO
    # -------------------
    def try_connect_database(self):
        server = self.input_server.text().strip()
        database = self.combo_database.currentText().strip()
        windows_auth = self.checkbox_windows_auth.isChecked()

        user = self.input_user.text().strip() if not windows_auth else ""
        password = self.input_password.text().strip() if not windows_auth else ""

        ok, message = connect_to_database(server, user, password, database, windows_auth)
        if ok:
            self.label_error.setText(message)
            self.label_error.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                border-radius: 0px;
                background-color: #d4edda;
                color: #155724;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            """)

            # salva no connection.json
            save_connection_json(server, database, user, password, windows_auth)
            log(f"Conexao salva: {server} / {database}")

            # Passa servidor e banco para o callback (MainWindow)
            self.on_connect(server, database)
        else:
            self.label_error.setText("Erro ao conectar ao banco")
            self.label_error.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                border-radius: 0px;
                background-color: #f8d7da;
                color: #721c24;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            """)
            self.show_error_dialog("Erro ao conectar ao banco", message)