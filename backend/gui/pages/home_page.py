import json
import subprocess
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QDialog, QPlainTextEdit, QFrame
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt, QThread, Signal
from PySide6.QtGui import QIcon
from backend.config.paths import ROOT_DIR, JSON_FILE, LOG_FILE

# Caminhos principais
SCHEMASPY_DIR = ROOT_DIR / "schemaspy"
SCHEMASPY_JAR = SCHEMASPY_DIR / "schemaspy-app.jar"
DRIVER_JAR = SCHEMASPY_DIR / "mssql-jdbc-13.2.1.jre11.jar"
OUTPUT_DIR = SCHEMASPY_DIR / "output"

# Caminho para o Graphviz portátil
GRAPHVIZ_BIN = ROOT_DIR / "graphviz" / "bin"

if GRAPHVIZ_BIN.exists():
    os.environ["PATH"] = f"{GRAPHVIZ_BIN};" + os.environ["PATH"]
    print(f"✅ Graphviz adicionado ao PATH: {GRAPHVIZ_BIN}")
else:
    print("⚠️ Pasta graphviz/bin não encontrada — diagramas podem não ser gerados corretamente")


def log(msg: str):
    """Registra mensagem no arquivo de log"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


class SchemaSpyThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)  # sucesso, mensagem de erro

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.error_log = []

    def run(self):
        """Executa SchemaSpy em thread separada"""
        try:
            log("⚙️ Thread iniciada para gerar documentação.")

            host = self.config.get("server", "localhost")
            port = str(self.config.get("port", 1433))
            db = self.config.get("database", "")
            schema = self.config.get("schema", "dbo")
            auth = self.config.get("auth", "sql").lower()

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            # drivers dentro de schemaspy/drivers
            driver_jar = SCHEMASPY_DIR / "drivers" / "mssql-jdbc-13.2.1.jre11.jar"
            dll_file = SCHEMASPY_DIR / "mssql-jdbc_auth-13.2.1.x64.dll"

            # Validações
            if not SCHEMASPY_JAR.exists():
                msg = f"schemaspy-app.jar não encontrado em {SCHEMASPY_JAR}"
                log(f"❌ {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            if not driver_jar.exists():
                msg = f"Driver JDBC não encontrado em {driver_jar}"
                log(f"❌ {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            # Verifica se Java está disponível
            try:
                java_check = subprocess.run(
                    ["java", "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if java_check.returncode != 0:
                    msg = "Java não está instalado ou não está no PATH"
                    log(f"❌ {msg}")
                    self.error_log.append(msg)
                    self.finished_signal.emit(False, "\n".join(self.error_log))
                    return
                else:
                    java_version = java_check.stderr.split('\n')[0] if java_check.stderr else "Versão desconhecida"
                    log(f"☕ Java detectado: {java_version}")
            except Exception as e:
                msg = f"Erro ao verificar Java: {e}"
                log(f"❌ {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            # Use tipo compatível com SchemaSpy (ex.: mssql17 para 2017+)
            db_type = "mssql17"
            
            # Comando base
            cmd = [
                "java",
                f"-Djava.library.path={str(SCHEMASPY_DIR)}",
                "-jar", str(SCHEMASPY_JAR),
                "-t", db_type,
                "-db", db,
                "-s", schema,
                "-host", host,
                "-port", port,
                "-dp", str(driver_jar),
                "-o", str(OUTPUT_DIR),
                "-debug"
            ]

            # Autenticação
            if auth == "windows" or self.config.get("windows_auth", False):
                if dll_file.exists():
                    dll_dir = str(dll_file.parent)
                    os.environ["PATH"] = f"{dll_dir}{os.pathsep}" + os.environ.get("PATH", "")
                    cmd[1] = f"-Djava.library.path={dll_dir}"
                    
                    log(f"🪟 mssql-jdbc_auth-13.2.1.x64.dll configurado:")
                    log(f"   📁 Pasta: {dll_dir}")
                    log(f"   📏 Tamanho: {dll_file.stat().st_size:,} bytes")
                else:
                    msg = f"❌ CRÍTICO: mssql-jdbc_auth-13.2.1.x64.dll não encontrado em {dll_file}"
                    log(msg)
                    self.error_log.append(msg)
                    self.error_log.append("Baixe em: https://learn.microsoft.com/en-us/sql/connect/jdbc/download-microsoft-jdbc-driver-for-sql-server")
                    self.finished_signal.emit(False, "\n".join(self.error_log))
                    return

                log("🔐 Configurando autenticação Windows...")
                
                conn_props_file = SCHEMASPY_DIR / "connection.properties"
                try:
                    with open(conn_props_file, "w", encoding="utf-8") as f:
                        f.write("integratedSecurity=true\n")
                        f.write("encrypt=true\n")
                        f.write("trustServerCertificate=true\n")
                    
                    if conn_props_file.exists():
                        with open(conn_props_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        log(f"   📝 Arquivo de propriedades criado: {conn_props_file}")
                        log(f"   📄 Conteúdo:\n{content}")
                    else:
                        log(f"   ⚠️ Arquivo não foi criado!")
                        
                except Exception as e:
                    log(f"⚠️ Erro ao criar arquivo de propriedades: {e}")
                
                cmd += [
                    "-u", "ignored", 
                    "-p", "ignored",
                    "-connprops", str(conn_props_file)
                ]
            else:
                user = self.config.get("username", "")
                password = self.config.get("password", "")
                if not user:
                    msg = "Usuário SQL não configurado"
                    log(f"❌ {msg}")
                    self.error_log.append(msg)
                    self.finished_signal.emit(False, "\n".join(self.error_log))
                    return
                
                conn_props_file = SCHEMASPY_DIR / "connection.properties"
                try:
                    with open(conn_props_file, "w", encoding="utf-8") as f:
                        f.write("encrypt=true\n")
                        f.write("trustServerCertificate=true\n")
                    log(f"📝 Arquivo de propriedades SSL criado: {conn_props_file}")
                    cmd += ["-u", user, "-p", password, "-connprops", str(conn_props_file)]
                except Exception as e:
                    log(f"⚠️ Erro ao criar arquivo de propriedades: {e}")
                    cmd += ["-u", user, "-p", password]

            log(f"🚀 Executando SchemaSpy...")
            log(f"📋 Comando completo:")
            
            # Mostra comando completo mas mascara senha
            cmd_display = []
            hide_next = False
            for i, arg in enumerate(cmd):
                if hide_next:
                    cmd_display.append("****")
                    hide_next = False
                elif arg == "-p":
                    cmd_display.append(arg)
                    hide_next = True
                else:
                    cmd_display.append(arg)
            log(f"   {' '.join(cmd_display)}")

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Loga stdout e stderr
            if proc.stdout:
                log(f"📄 STDOUT:\n{proc.stdout.strip()}")
            if proc.stderr:
                log(f"⚠️ STDERR:\n{proc.stderr.strip()}")

            if proc.returncode == 0:
                log("✅ Documentação gerada com sucesso!")
                self.finished_signal.emit(True, "")
            else:
                msg = f"❌ SchemaSpy falhou (código {proc.returncode})"
                log(msg)
                self.error_log.append(msg)
                if proc.stdout:
                    self.error_log.append("\n--- STDOUT ---")
                    self.error_log.append(proc.stdout.strip())
                if proc.stderr:
                    self.error_log.append("\n--- STDERR ---")
                    self.error_log.append(proc.stderr.strip())
                self.finished_signal.emit(False, "\n".join(self.error_log))

        except subprocess.TimeoutExpired:
            msg = "⏱️ Timeout: SchemaSpy demorou mais de 5 minutos"
            log(msg)
            self.error_log.append(msg)
            self.finished_signal.emit(False, "\n".join(self.error_log))
        except Exception as e:
            msg = f"⚠️ Erro inesperado: {e}"
            log(msg)
            self.error_log.append(msg)
            self.finished_signal.emit(False, "\n".join(self.error_log))


class HomePage(QWidget):
    def __init__(self, server=None, database=None, main_window=None):
        super().__init__()
        
        self.main_window = main_window

        # --- Carrega dados de conexão do JSON ---
        if not JSON_FILE.exists():
            raise FileNotFoundError(f"Arquivo de conexão não encontrado: {JSON_FILE}")

        with open(JSON_FILE, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.server = server or self.config.get("server", "localhost")
        self.database = database or self.config.get("database", "Desconhecido")

        log(f"[HomePage] Conectado em {self.server} - {self.database}")

        # --- Layout Principal ---
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # --- Área de Conteúdo ---
        content = self.create_content()
        main_layout.addWidget(content, 1)
        
        self.setLayout(main_layout)
        self.thread = None

    def create_sidebar(self):
        """Cria sidebar minimalista"""
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2596be;
                border-right: 1px solid #1a7a9e;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        sidebar.setFixedWidth(200)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(5)
        
        # Logo/Título
        title = QLabel("SmartView")
        title.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            padding: 15px;
            margin-bottom: 20px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Botão Voltar
        btn_back = QPushButton("← Voltar ao Login")
        btn_back.clicked.connect(self.back_to_login)
        layout.addWidget(btn_back)
        
        # Botão Fechar
        btn_close = QPushButton("✕ Fechar")
        btn_close.clicked.connect(self.close_application)
        layout.addWidget(btn_close)
        
        layout.addStretch()
        sidebar.setLayout(layout)
        return sidebar

    def create_content(self):
        """Cria área de conteúdo principal"""
        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel(f"📊 Banco: {self.database} | Servidor: {self.server}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2596be;
            padding: 10px;
            background-color: #f0f8ff;
            border-radius: 5px;
        """)
        layout.addWidget(title)
        
        # Botão Gerar Documentação
        self.btn_generate = QPushButton("🚀 Gerar Documentação SchemaSpy")
        self.btn_generate.clicked.connect(self.generate_docs)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #2596be;
                color: white;
                font-size: 16px;
                font-weight: 600;
                padding: 15px;
                border: none;
                border-radius: 8px;
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
        layout.addWidget(self.btn_generate)
        
        # Navegador Web
        self.browser = QWebEngineView()
        self.browser.setHtml("""
            <div style='
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                font-family: Arial, sans-serif;
                color: #666;
            '>
                <div style='text-align: center;'>
                    <h2 style='color: #2596be; margin-bottom: 10px;'>📄 Nenhum relatório carregado</h2>
                    <p>Clique no botão acima para gerar a documentação</p>
                </div>
            </div>
        """)
        self.browser.setStyleSheet("border: 1px solid #ddd; border-radius: 5px;")
        layout.addWidget(self.browser, 1)
        
        content.setLayout(layout)
        return content

    def show_error_dialog(self, title: str, message: str):
        """Exibe diálogo de erro com log detalhado"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Detalhes do erro:")
        label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        
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

    def generate_docs(self):
        """Inicia a geração do SchemaSpy em thread separada"""
        log("🔹 Iniciando geração de documentação...")
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("⏳ Gerando documentação...")

        self.thread = SchemaSpyThread(self.config)
        self.thread.finished_signal.connect(self.on_generation_finished)
        self.thread.start()

    def on_generation_finished(self, success: bool, error_msg: str):
        """Chamado quando a thread termina"""
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("🚀 Gerar Documentação SchemaSpy")
        
        if success:
            self.load_report()
        else:
            self.show_error_dialog("❌ Erro ao Gerar Documentação", error_msg)

    def load_report(self):
        """Carrega o relatório gerado no navegador embutido"""
        index_path = OUTPUT_DIR / "index.html"
        if index_path.exists():
            url = QUrl.fromLocalFile(str(index_path))
            self.browser.setUrl(url)
            log("📂 Relatório carregado no visualizador.")
        else:
            log("⚠️ Relatório não encontrado em 'schemaspy/output/index.html'.")
            self.show_error_dialog(
                "Arquivo não encontrado",
                f"O arquivo index.html não foi encontrado em:\n{index_path}"
            )

    def back_to_login(self):
        """Volta para a tela de login"""
        if self.main_window:
            reply = QMessageBox.question(
                self,
                "Voltar ao Login",
                "Tem certeza que deseja voltar à tela de login?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.main_window.back_to_login()

    def close_application(self):
        """Fecha a aplicação"""
        reply = QMessageBox.question(
            self,
            "Fechar Aplicação",
            "Tem certeza que deseja fechar o SmartView?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            log("Aplicação fechada pelo usuário")
            self.main_window.close() if self.main_window else self.close()