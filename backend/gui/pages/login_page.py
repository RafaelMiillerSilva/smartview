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
        
        # Define fundo da página
        self.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        self.setLayout(layout)

        # -------------------
        # BLOCO: Conexão Servidor
        # -------------------
        server_frame = QFrame()
        server_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        server_layout = QVBoxLayout(server_frame)

        lbl_server = QLabel("Servidor:")
        lbl_server.setStyleSheet("font-weight: bold; margin-top: 5px; color: #333;")
        self.input_server = QLineEdit()
        self.input_server.setPlaceholderText("Ex: localhost, DESKTOP\\SQLEXPRESS")
        self.input_server.setStyleSheet("""
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 13px;
            background-color: white;
        """)
        server_layout.addWidget(lbl_server)
        server_layout.addWidget(self.input_server)

        self.checkbox_windows_auth = QCheckBox("Usar autenticação do Windows")
        self.checkbox_windows_auth.setChecked(True)
        self.checkbox_windows_auth.stateChanged.connect(self.toggle_auth_mode)
        self.checkbox_windows_auth.setStyleSheet("""
            color: #333;
            font-size: 13px;
        """)
        server_layout.addWidget(self.checkbox_windows_auth)

        lbl_user = QLabel("Usuário:")
        lbl_user.setStyleSheet("font-weight: bold; margin-top: 10px; color: #333;")
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuário (SQL Authentication)")
        self.input_user.setStyleSheet("""
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 13px;
            background-color: white;
        """)
        server_layout.addWidget(lbl_user)
        server_layout.addWidget(self.input_user)

        lbl_pass = QLabel("Senha:")
        lbl_pass.setStyleSheet("font-weight: bold; margin-top: 10px; color: #333;")
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Senha")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setStyleSheet("""
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 13px;
            background-color: white;
        """)
        server_layout.addWidget(lbl_pass)
        server_layout.addWidget(self.input_password)

        self.button_connect_server = QPushButton("Conectar ao Servidor")
        self.button_connect_server.clicked.connect(self.try_connect_server)
        self.button_connect_server.setStyleSheet("""
            QPushButton {
                background-color: #2596be;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1a7a9e;
            }
            QPushButton:pressed {
                background-color: #156380;
            }
        """)
        server_layout.addWidget(self.button_connect_server)

        section_title1 = QLabel("🔌 Conexão com Servidor")
        section_title1.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2596be;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(section_title1)
        layout.addWidget(server_frame)

        # -------------------
        # BLOCO: Conexão Banco
        # -------------------
        db_frame = QFrame()
        db_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        db_layout = QVBoxLayout(db_frame)

        lbl_db = QLabel("Banco de Dados:")
        lbl_db.setStyleSheet("font-weight: bold; margin-top: 5px; color: #333;")
        self.combo_database = QComboBox()
        self.combo_database.setEditable(True)
        self.combo_database.setEnabled(False)
        self.combo_database.setStyleSheet("""
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 13px;
            background-color: white;
        """)
        db_layout.addWidget(lbl_db)
        db_layout.addWidget(self.combo_database)

        self.button_continue = QPushButton("Conectar ao Banco")
        self.button_continue.setEnabled(False)
        self.button_continue.clicked.connect(self.try_connect_database)
        self.button_continue.setStyleSheet("""
            QPushButton {
                background-color: #2596be;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1a7a9e;
            }
            QPushButton:pressed {
                background-color: #156380;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        db_layout.addWidget(self.button_continue)

        section_title2 = QLabel("📂 Conexão com Banco de Dados")
        section_title2.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2596be;
            margin-top: 15px;
            margin-bottom: 5px;
        """)
        layout.addWidget(section_title2)
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
            border-radius: 5px;
        """)
        layout.addWidget(self.label_error)

        # -------------------
        # Pré-carrega última conexão
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
    # MÉTODOS
    # -------------------
    def toggle_auth_mode(self):
        """Habilita/desabilita campos de usuário/senha conforme o modo"""
        is_windows_auth = self.checkbox_windows_auth.isChecked()
        self.input_user.setDisabled(is_windows_auth)
        self.input_password.setDisabled(is_windows_auth)

    def animate_button(self, button, success: bool):
        """Anima visualmente o botão"""
        original_style = button.styleSheet()
        if success:
            button.setStyleSheet("""
                background-color: #28a745;
                color: white;
                font-weight: bold;
            """)
        else:
            button.setStyleSheet("""
                background-color: #dc3545;
                color: white;
                font-weight: bold;
            """)
        QTimer.singleShot(600, lambda: button.setStyleSheet(original_style))

    def show_error_dialog(self, title: str, message: str):
        """Exibe diálogo de erro com texto detalhado"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)
        
        label = QLabel("Detalhes do erro:")
        label.setStyleSheet("font-weight: bold; margin-bottom: 10px; color: #333;")
        
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
            border-radius: 5px;
        """)

        btn_close = QPushButton("Fechar")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #2596be;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1a7a9e;
            }
        """)
        btn_close.clicked.connect(dialog.close)

        layout.addWidget(label)
        layout.addWidget(text_box)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

        dialog.exec()

    # -------------------
    # CONEXÃO COM SERVIDOR
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
            self.label_error.setText("✅ Servidor conectado! Selecione o banco.")
            self.label_error.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                border-radius: 5px;
                background-color: #d4edda;
                color: #155724;
            """)
            self.animate_button(self.button_connect_server, True)

            # Salva conexão parcial
            save_connection_json(server, "", user, password, windows_auth)

        else:
            self.combo_database.setEnabled(False)
            self.button_continue.setEnabled(False)
            self.label_error.setText("❌ Erro ao conectar ao servidor")
            self.label_error.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                border-radius: 5px;
                background-color: #f8d7da;
                color: #721c24;
            """)
            self.animate_button(self.button_connect_server, False)
            self.show_error_dialog("Erro ao conectar ao servidor", str(result))

    # -------------------
    # CONEXÃO COM BANCO
    # -------------------
    def try_connect_database(self):
        server = self.input_server.text().strip()
        database = self.combo_database.currentText().strip()
        windows_auth = self.checkbox_windows_auth.isChecked()

        user = self.input_user.text().strip() if not windows_auth else ""
        password = self.input_password.text().strip() if not windows_auth else ""

        ok, message = connect_to_database(server, user, password, database, windows_auth)
        if ok:
            self.label_error.setText("✅ " + message)
            self.label_error.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                border-radius: 5px;
                background-color: #d4edda;
                color: #155724;
            """)
            self.animate_button(self.button_continue, True)

            # salva no connection.json
            save_connection_json(server, database, user, password, windows_auth)
            log(f"Conexão salva: {server} / {database}")

            # Passa servidor e banco para o callback (MainWindow)
            self.on_connect(server, database)
        else:
            self.label_error.setText("❌ Erro ao conectar ao banco")
            self.label_error.setStyleSheet("""
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
                border-radius: 5px;
                background-color: #f8d7da;
                color: #721c24;
            """)
            self.animate_button(self.button_continue, False)
            self.show_error_dialog("Erro ao conectar ao banco", message)