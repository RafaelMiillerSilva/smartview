import json
import subprocess
import os
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QDialog, QPlainTextEdit, QFrame
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from backend.config.paths import (
    ROOT_DIR, JSON_FILE, LOG_FILE, SCHEMASPY_DIR,
    SCHEMASPY_JAR, OUTPUT_DIR, GRAPHVIZ_BIN
)
import sys

# Driver JAR
DRIVER_JAR = SCHEMASPY_DIR / "drivers" / "mssql-jdbc-13.2.1.jre11.jar"


class Logger:
    def __init__(self, logfile):
        self.logfile = logfile

    def write(self, message):
        with open(self.logfile, "a", encoding="utf-8") as f:
            f.write(message)

    def flush(self):
        pass  # necessário para compatibilidade com stdout


# Ativar redirecionamento
sys.stdout = Logger(LOG_FILE)
sys.stderr = Logger(LOG_FILE)


def log(msg: str):
    """Registra mensagem no arquivo de log com timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    print(linha)


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
            log("Thread iniciada para gerar documentacao.")

            host = self.config.get("host", self.config.get("server", "localhost"))
            port = str(self.config.get("port", 1433))
            db = self.config.get("database", "")
            schema = self.config.get("schema", "dbo")
            auth = self.config.get("auth", "sql").lower()

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            driver_jar = DRIVER_JAR
            dll_file = SCHEMASPY_DIR / "mssql-jdbc_auth-13.2.1.x64.dll"

            # Logs de diagnóstico de parâmetros e paths
            log("========== PARAMETROS DE CONEXAO / AMBIENTE ==========")
            log(f"host   = {host}")
            log(f"port   = {port}")
            log(f"db     = {db}")
            log(f"schema = {schema}")
            log(f"auth   = {auth}")
            log(f"SCHEMASPY_JAR = {SCHEMASPY_JAR}")
            log(f"DRIVER_JAR    = {driver_jar}")
            log(f"SCHEMASPY_DIR = {SCHEMASPY_DIR}")
            log(f"OUTPUT_DIR    = {OUTPUT_DIR}")
            log(f"dll_file      = {dll_file}")
            log("======================================================")

            # Validações
            if not SCHEMASPY_JAR.exists():
                msg = f"schemaspy-app.jar nao encontrado em {SCHEMASPY_JAR}"
                log(f"ERRO: {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            if not driver_jar.exists():
                msg = f"Driver JDBC nao encontrado em {driver_jar}"
                log(f"ERRO: {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            if not OUTPUT_DIR.exists():
                msg = f"Diretorio de saida nao existe ou nao pode ser criado: {OUTPUT_DIR}"
                log(f"ERRO: {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            # Verifica Java
            try:
                log("Verificando instalacao do Java...")
                java_check = subprocess.run(
                    ["java", "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                log(f"Resultado java -version | returncode={java_check.returncode}")
                log(f"STDOUT java -version:\n{java_check.stdout}")
                log(f"STDERR java -version:\n{java_check.stderr}")

                if java_check.returncode != 0:
                    msg = "Java nao esta instalado ou nao esta no PATH"
                    log(f"ERRO: {msg}")
                    self.error_log.append(msg)
                    self.finished_signal.emit(False, "\n".join(self.error_log))
                    return
                else:
                    java_version = java_check.stderr.split('\n')[0] if java_check.stderr else "Versao desconhecida"
                    log(f"Java detectado: {java_version}")
            except Exception as e:
                msg = f"Erro ao verificar Java: {e}"
                log(f"ERRO: {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            # Verifica Graphviz
            try:
                graphviz_check = subprocess.run(
                    ["dot", "-V"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if graphviz_check.returncode == 0:
                    version_output = graphviz_check.stderr.strip() if graphviz_check.stderr else graphviz_check.stdout.strip()
                    log(f"Graphviz detectado: {version_output}")
                else:
                    log("Graphviz nao encontrado - diagramas de relacionamento nao serao gerados")
                    log("Instale em: https://graphviz.org/download/")
            except FileNotFoundError:
                log("Graphviz nao encontrado no PATH")
                log("Diagramas de relacionamento nao serao gerados")
                log("Baixe em: https://graphviz.org/download/")
                log(f"Ou coloque o Graphviz em: {GRAPHVIZ_BIN.parent}")
            except Exception as e:
                log(f"Erro ao verificar Graphviz: {e}")

            # Detecta se é instância nomeada
            is_named_instance = "\\" in host
            if is_named_instance:
                parts = host.split("\\")
                server_name = parts[0]
                instance_name = parts[1] if len(parts) > 1 else ""
                log(f"Detectada instancia nomeada: {server_name}\\{instance_name}")
            else:
                server_name = host
                instance_name = ""
                log(f"Servidor padrao: {server_name}")

            # Obter credenciais
            user = self.config.get("user", self.config.get("username", ""))
            password = self.config.get("password", "")
            windows_auth = auth == "windows" or self.config.get("windows_auth", False)

            # Criar connection string JDBC completa
            if is_named_instance:
                if windows_auth:
                    jdbc_url = (
                        f"jdbc:sqlserver://{server_name};"
                        f"instanceName={instance_name};"
                        f"databaseName={db};"
                        f"integratedSecurity=true;"
                        f"encrypt=true;"
                        f"trustServerCertificate=true"
                    )
                else:
                    jdbc_url = (
                        f"jdbc:sqlserver://{server_name};"
                        f"instanceName={instance_name};"
                        f"databaseName={db};"
                        f"user={user};"
                        f"password={password};"
                        f"encrypt=true;"
                        f"trustServerCertificate=true"
                    )
                jdbc_url_masked = jdbc_url.replace(password, "****") if password else jdbc_url
                log(f"URL JDBC (instancia nomeada): {jdbc_url_masked}")
            else:
                if windows_auth:
                    jdbc_url = (
                        f"jdbc:sqlserver://{server_name}:{port};"
                        f"databaseName={db};"
                        f"integratedSecurity=true;"
                        f"encrypt=true;"
                        f"trustServerCertificate=true"
                    )
                else:
                    jdbc_url = (
                        f"jdbc:sqlserver://{server_name}:{port};"
                        f"databaseName={db};"
                        f"user={user};"
                        f"password={password};"
                        f"encrypt=true;"
                        f"trustServerCertificate=true"
                    )
                jdbc_url_masked = jdbc_url.replace(password, "****") if password else jdbc_url
                log(f"URL JDBC (servidor padrao): {jdbc_url_masked}")

            # Configurar DLL para Windows Auth se necessário
            if windows_auth:
                if dll_file.exists():
                    dll_dir = str(dll_file.parent)
                    os.environ["PATH"] = f"{dll_dir}{os.pathsep}" + os.environ.get("PATH", "")
                    log("Windows Auth: mssql-jdbc_auth-13.2.1.x64.dll configurado:")
                    log(f"Pasta: {dll_dir}")
                    log(f"Tamanho: {dll_file.stat().st_size:,} bytes")
                else:
                    msg = f"CRITICO: mssql-jdbc_auth-13.2.1.x64.dll nao encontrado em {dll_file}"
                    log(msg)
                    self.error_log.append(msg)
                    self.error_log.append(
                        "Baixe em: https://learn.microsoft.com/en-us/sql/connect/jdbc/download-microsoft-jdbc-driver-for-sql-server"
                    )
                    self.finished_signal.emit(False, "\n".join(self.error_log))
                    return

            # Criar tipo de banco customizado para usar URL completa
            custom_db_type = SCHEMASPY_DIR / "mssql-custom.properties"
            try:
                with open(custom_db_type, "w", encoding="utf-8") as f:
                    f.write("# Custom SQL Server type for named instances\n")
                    f.write("description=Microsoft SQL Server with custom connection\n")
                    f.write("driver=com.microsoft.sqlserver.jdbc.SQLServerDriver\n")
                    f.write(f"connectionSpec={jdbc_url}\n")
                    f.write("extends=mssql05\n")
                log(f"Tipo de banco customizado criado: {custom_db_type}")
            except Exception as e:
                msg = f"Erro ao criar tipo customizado: {e}"
                log(f"ERRO: {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            # Criar arquivo de propriedades de conexão adicional (para encrypt/trust)
            conn_props_file = SCHEMASPY_DIR / "connection.properties"
            try:
                with open(conn_props_file, "w", encoding="utf-8") as f:
                    f.write("# Additional connection properties\n")
                log(f"Arquivo de propriedades criado: {conn_props_file}")
            except Exception as e:
                msg = f"Erro ao criar arquivo de propriedades: {e}"
                log(f"ERRO: {msg}")
                self.error_log.append(msg)
                self.finished_signal.emit(False, "\n".join(self.error_log))
                return

            # Comando SchemaSpy usando tipo customizado
            cmd = [
                "java",
                f"-Djava.library.path={str(SCHEMASPY_DIR)}",
                "-jar", str(SCHEMASPY_JAR),
                "-t", str(custom_db_type),
                "-s", schema,
                "-dp", str(driver_jar),
                "-o", str(OUTPUT_DIR),
                "-debug",
                # -no-xml não existe de verdade na 7.0.2; será ignorado, então removi
            ]

            # SchemaSpy requer -u e -p
            if windows_auth:
                cmd += ["-u", "ignored", "-p", "ignored"]
            else:
                if not user:
                    msg = "Usuario SQL nao configurado"
                    log(f"ERRO: {msg}")
                    self.error_log.append(msg)
                    self.finished_signal.emit(False, "\n".join(self.error_log))
                    return
                cmd += ["-u", user, "-p", password]

            log("Executando SchemaSpy...")
            log("Comando completo:")

            # Mostrar comando completo mascarando a senha
            cmd_display = []
            hide_next = False
            for arg in cmd:
                if hide_next:
                    cmd_display.append("****")
                    hide_next = False
                elif arg == "-p":
                    cmd_display.append(arg)
                    hide_next = True
                else:
                    cmd_display.append(arg)
            log(" ".join(cmd_display))

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            log(f"SchemaSpy finalizado com returncode={proc.returncode}")
            log("===== STDOUT SchemaSpy =====")
            log(proc.stdout.strip() if proc.stdout else "<vazio>")
            log("===== STDERR SchemaSpy =====")
            log(proc.stderr.strip() if proc.stderr else "<vazio>")
            log("======================================")

            stderr = proc.stderr or ""

            if proc.returncode == 0:
                log("Documentacao gerada com sucesso!")
                self.finished_signal.emit(True, "")
            else:
                # Tratamento especial: bug de XML (NPE em XmlProducerUsingDOM)
                if "XmlProducerUsingDOM.generate" in stderr and "NullPointerException" in stderr:
                    warn_msg = (
                        "SchemaSpy gerou HTML com sucesso, mas falhou ao gerar XML "
                        "(NullPointerException em XmlProducerUsingDOM - bug conhecido da versao 7.0.2)."
                    )
                    log(warn_msg)
                    self.error_log.append(warn_msg)
                    # Considera como sucesso para nao quebrar a UX
                    self.finished_signal.emit(True, "\n".join(self.error_log))
                    return

                # Demais erros: tratar como falha real
                msg = f"SchemaSpy falhou (codigo {proc.returncode})"
                log(f"ERRO: {msg}")
                self.error_log.append(msg)
                if proc.stdout:
                    self.error_log.append("\n--- STDOUT ---")
                    self.error_log.append(proc.stdout.strip())
                if stderr:
                    self.error_log.append("\n--- STDERR ---")
                    self.error_log.append(stderr.strip())
                self.finished_signal.emit(False, "\n".join(self.error_log))

        except subprocess.TimeoutExpired:
            msg = "Timeout: SchemaSpy demorou mais de 5 minutos"
            log(f"ERRO: {msg}")
            self.error_log.append(msg)
            self.finished_signal.emit(False, "\n".join(self.error_log))
        except Exception as e:
            msg = f"Erro inesperado: {e}"
            log(f"ERRO: {msg}")
            self.error_log.append(msg)
            self.finished_signal.emit(False, "\n".join(self.error_log))


class HomePage(QWidget):
    def __init__(self, server=None, database=None, main_window=None):
        super().__init__()
        
        self.main_window = main_window

        # --- Carrega dados de conexao do JSON ---
        if not JSON_FILE.exists():
            raise FileNotFoundError(f"Arquivo de conexao nao encontrado: {JSON_FILE}")

        with open(JSON_FILE, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.server = server or self.config.get("host", self.config.get("server", "localhost"))
        self.database = database or self.config.get("database", "Desconhecido")

        log(f"[HomePage] Conectado em {self.server} - {self.database}")

        # --- Layout Principal ---
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # --- Area de Conteudo (apenas relatorio) ---
        content = self.create_content()
        main_layout.addWidget(content, 1)
        
        self.setLayout(main_layout)
        self.thread = None

    def create_sidebar(self):
        """Cria sidebar com logo, info do banco e controles"""
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #192c3e;
                border-right: 1px solid #0f1f2e;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 12px;
                text-align: left;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:disabled {
                background-color: rgba(100, 100, 100, 0.3);
                color: #999999;
            }
            QLabel {
                color: white;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        sidebar.setFixedWidth(280)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(10)
        
        # Logo/Imagem
        logo = QLabel()
        logo_path = ROOT_DIR / "assets" / "smartview_logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaled(250, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(scaled_pixmap)
        else:
            logo.setText("SmartView")
            logo.setStyleSheet("""
                color: white;
                font-size: 20px;
                font-weight: bold;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
            """)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(logo.styleSheet() + "padding: 10px; margin-bottom: 20px;")
        layout.addWidget(logo)
        
        # Separador
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); max-height: 1px;")
        layout.addWidget(separator1)
        
        # Informacoes do Banco
        info_label = QLabel("CONEXAO ATIVA")
        info_label.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #7ed4ff;
            padding: 10px 5px 5px 5px;
        """)
        layout.addWidget(info_label)
        
        server_label = QLabel(f"Servidor:\n{self.server}")
        server_label.setWordWrap(True)
        server_label.setStyleSheet("""
            font-size: 12px;
            padding: 5px;
            color: #e0e0e0;
        """)
        layout.addWidget(server_label)
        
        db_label = QLabel(f"Banco:\n{self.database}")
        db_label.setWordWrap(True)
        db_label.setStyleSheet("""
            font-size: 12px;
            padding: 5px;
            color: #e0e0e0;
        """)
        layout.addWidget(db_label)
        
        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); max-height: 1px;")
        layout.addWidget(separator2)
        
        # Botao Gerar Documentacao
        self.btn_generate = QPushButton("Gerar Documentacao")
        self.btn_generate.clicked.connect(self.generate_docs)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #2a5a7a;
                color: white;
                border: none;
                padding: 15px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Typold', 'Inter', 'Segoe UI', sans-serif;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #3a7a9a;
            }
            QPushButton:pressed {
                background-color: #1a4a6a;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
        """)
        layout.addWidget(self.btn_generate)
        
        # Espaco flexivel
        layout.addStretch()
        
        # Separador
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); max-height: 1px;")
        layout.addWidget(separator3)
        
        # Botao Voltar
        btn_back = QPushButton("Voltar ao Login")
        btn_back.clicked.connect(self.back_to_login)
        layout.addWidget(btn_back)
        
        # Botao Fechar
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close_application)
        layout.addWidget(btn_close)
        
        sidebar.setLayout(layout)
        return sidebar

    def create_content(self):
        """Cria area de conteudo apenas com o navegador"""
        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Navegador Web (ocupa toda a area)
        self.browser = QWebEngineView()
        self.browser.setHtml("""
            <div style='
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                font-family: "Typold", "Inter", "Segoe UI", sans-serif;
                color: #666;
                background-color: #f9f9f9;
            '>
                <div style='text-align: center;'>
                    <h2 style='color: #192c3e; margin-bottom: 10px;'>Nenhum relatorio carregado</h2>
                    <p>Clique em "Gerar Documentacao" na barra lateral</p>
                </div>
            </div>
        """)
        self.browser.setStyleSheet("border: none;")
        layout.addWidget(self.browser)
        
        content.setLayout(layout)
        return content

    def show_error_dialog(self, title: str, message: str):
        """Exibe dialogo de erro com log detalhado"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Detalhes do erro:")
        label.setStyleSheet("""
            font-weight: bold;
            margin-bottom: 10px;
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

    def generate_docs(self):
        """Inicia a geracao do SchemaSpy em thread separada"""
        log("Iniciando geracao de documentacao...")
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("Gerando...")

        self.thread = SchemaSpyThread(self.config)
        self.thread.finished_signal.connect(self.on_generation_finished)
        self.thread.start()

    def on_generation_finished(self, success: bool, error_msg: str):
        """Chamado quando a thread termina"""
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("Gerar Documentacao")
        
        if success:
            self.load_report()
        else:
            self.show_error_dialog("Erro ao Gerar Documentacao", error_msg)

    def load_report(self):
        """Carrega o relatorio gerado no navegador embutido"""
        index_path = OUTPUT_DIR / "index.html"
        if index_path.exists():
            url = QUrl.fromLocalFile(str(index_path))
            self.browser.setUrl(url)
            log("Relatorio carregado no visualizador.")
        else:
            log("Relatorio nao encontrado em 'schemaspy/output/index.html'.")
            self.show_error_dialog(
                "Arquivo nao encontrado",
                f"O arquivo index.html nao foi encontrado em:\n{index_path}"
            )

    def back_to_login(self):
        """Volta para a tela de login"""
        if self.main_window:
            reply = QMessageBox.question(
                self,
                "Voltar ao Login",
                "Tem certeza que deseja voltar a tela de login?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.main_window.back_to_login()

    def close_application(self):
        """Fecha a aplicacao"""
        reply = QMessageBox.question(
            self,
            "Fechar Aplicacao",
            "Tem certeza que deseja fechar o SmartView?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            log("Aplicacao fechada pelo usuario")
            if self.main_window:
                self.main_window.close()
            else:
                self.close()