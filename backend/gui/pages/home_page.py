import json
import subprocess
import os
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt, QThread, Signal
from backend.config.paths import ROOT_DIR, JSON_FILE, LOG_FILE, BASE_DIR

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
    print("⚠️ Pasta graphviz/bin não encontrada — diagramas podem não ser gerados corretamente.")


def log(msg: str):
    """Registra mensagem no arquivo de log"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


class SchemaSpyThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        """Executa SchemaSpy em thread separada"""
        try:
            self.log_signal.emit("⚙️ Thread iniciada para gerar documentação.")

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
                self.log_signal.emit(f"❌ {msg}")
                log(msg)
                self.finished_signal.emit(False)
                return

            if not driver_jar.exists():
                msg = f"Driver JDBC não encontrado em {driver_jar}"
                self.log_signal.emit(f"❌ {msg}")
                log(msg)
                self.finished_signal.emit(False)
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
                    self.log_signal.emit(f"❌ {msg}")
                    log(msg)
                    self.finished_signal.emit(False)
                    return
                else:
                    java_version = java_check.stderr.split('\n')[0] if java_check.stderr else "Versão desconhecida"
                    self.log_signal.emit(f"☕ Java detectado: {java_version}")
            except Exception as e:
                msg = f"Erro ao verificar Java: {e}"
                self.log_signal.emit(f"❌ {msg}")
                log(msg)
                self.finished_signal.emit(False)
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
                "-debug"  # Adiciona debug para ver detalhes do erro
            ]

            # Autenticação
            if auth == "windows" or self.config.get("windows_auth", False):
                # Garante DLL no PATH (precisa ser x64 se java for x64)
                if dll_file.exists():
                    # Adiciona ao PATH
                    dll_dir = str(dll_file.parent)
                    os.environ["PATH"] = f"{dll_dir}{os.pathsep}" + os.environ.get("PATH", "")
                    
                    # Também define a propriedade do sistema Java
                    cmd[1] = f"-Djava.library.path={dll_dir}"
                    
                    self.log_signal.emit(f"🪟 mssql-jdbc_auth-13.2.1.x64.dll configurado:")
                    self.log_signal.emit(f"   📁 Pasta: {dll_dir}")
                    self.log_signal.emit(f"   📏 Tamanho: {dll_file.stat().st_size:,} bytes")
                else:
                    msg = f"❌ CRÍTICO: mssql-jdbc_auth-13.2.1.x64.dll não encontrado em {dll_file}"
                    self.log_signal.emit(msg)
                    self.log_signal.emit("   Baixe em: https://learn.microsoft.com/en-us/sql/connect/jdbc/download-microsoft-jdbc-driver-for-sql-server")
                    self.log_signal.emit("   Use a versão x64 para Java 64-bit")
                    log(msg)
                    self.finished_signal.emit(False)
                    return

                # Para Windows Auth, criar arquivo temporário de propriedades
                self.log_signal.emit("🔐 Configurando autenticação Windows...")
                
                conn_props_file = SCHEMASPY_DIR / "connection.properties"
                try:
                    with open(conn_props_file, "w", encoding="utf-8") as f:
                        f.write("integratedSecurity=true\n")
                        f.write("encrypt=true\n")
                        f.write("trustServerCertificate=true\n")
                    
                    # Verifica se o arquivo foi criado
                    if conn_props_file.exists():
                        with open(conn_props_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        self.log_signal.emit(f"   📝 Arquivo de propriedades criado: {conn_props_file}")
                        self.log_signal.emit(f"   📄 Conteúdo:\n{content}")
                    else:
                        self.log_signal.emit(f"   ⚠️ Arquivo não foi criado!")
                        
                except Exception as e:
                    self.log_signal.emit(f"⚠️ Erro ao criar arquivo de propriedades: {e}")
                
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
                    self.log_signal.emit(f"❌ {msg}")
                    log(msg)
                    self.finished_signal.emit(False)
                    return
                
                # Criar arquivo de propriedades para SSL mesmo em autenticação SQL
                conn_props_file = SCHEMASPY_DIR / "connection.properties"
                try:
                    with open(conn_props_file, "w", encoding="utf-8") as f:
                        f.write("encrypt=true\n")
                        f.write("trustServerCertificate=true\n")
                    self.log_signal.emit(f" Arquivo de propriedades SSL criado: {conn_props_file}")
                    cmd += ["-u", user, "-p", password, "-connprops", str(conn_props_file)]
                except Exception as e:
                    # Se falhar ao criar arquivo, tenta sem ele
                    self.log_signal.emit(f"⚠️ Erro ao criar arquivo de propriedades: {e}")
                    cmd += ["-u", user, "-p", password]

            self.log_signal.emit(f" Executando SchemaSpy...")
            self.log_signal.emit(f" Comando completo:")
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
            self.log_signal.emit(f"   {' '.join(cmd_display)}")

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Sempre logue os dois para depuração
            if proc.stdout:
                self.log_signal.emit(f" STDOUT:\n{proc.stdout.strip()}")
            if proc.stderr:
                self.log_signal.emit(f" STDERR:\n{proc.stderr.strip()}")

            if proc.returncode == 0:
                self.log_signal.emit(" Documentação gerada com sucesso!")
                log("SchemaSpy executado com sucesso.")
                self.finished_signal.emit(True)
            else:
                self.log_signal.emit(f"❌ SchemaSpy falhou (código {proc.returncode}). Veja STDOUT/STDERR acima.")
                log(f"Erro ao executar SchemaSpy (returncode={proc.returncode}): {proc.stderr.strip()}")
                self.finished_signal.emit(False)

        except subprocess.TimeoutExpired:
            msg = "⏱️ Timeout: SchemaSpy demorou mais de 5 minutos"
            self.log_signal.emit(msg)
            log(msg)
            self.finished_signal.emit(False)
        except Exception as e:
            msg = f"⚠️ Erro inesperado: {e}"
            self.log_signal.emit(msg)
            log(msg)
            self.finished_signal.emit(False)


class HomePage(QWidget):
    def __init__(self, server=None, database=None):
        super().__init__()

        # --- Carrega dados de conexão do JSON ---
        if not JSON_FILE.exists():
            raise FileNotFoundError(f"Arquivo de conexão não encontrado: {JSON_FILE}")

        with open(JSON_FILE, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Se vierem parâmetros, eles têm prioridade
        self.server = server or self.config.get("server", "localhost")
        self.database = database or self.config.get("database", "Desconhecido")

        print(f"[HomePage] Conectado em {self.server} - {self.database}")

        # --- Interface ---
        title = QLabel(f"📊 Banco: {self.database} | Servidor: {self.server}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")

        self.btn_generate = QPushButton("Gerar Documentação SchemaSpy")
        self.btn_generate.clicked.connect(self.generate_docs)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Logs da execução aparecerão aqui...")
        self.log_box.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")

        self.browser = QWebEngineView()
        self.browser.setHtml("<h3 style='text-align:center;margin-top:20px;'>Nenhum relatório carregado ainda.</h3>")

        # --- Layout ---
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.btn_generate)
        layout.addWidget(self.log_box, 2)
        layout.addWidget(self.browser, 5)
        self.setLayout(layout)

        # Variável para armazenar a thread
        self.thread = None

    def append_log(self, text: str):
        """Adiciona mensagens ao log visual e no arquivo"""
        self.log_box.append(text)
        log(text)

    def generate_docs(self):
        """Inicia a geração do SchemaSpy em thread separada"""
        self.append_log("Iniciando geração...")
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("Gerando...")

        self.thread = SchemaSpyThread(self.config)
        self.thread.log_signal.connect(self.append_log)
        self.thread.finished_signal.connect(self.on_generation_finished)
        self.thread.start()

    def on_generation_finished(self, success: bool):
        """Chamado quando a thread termina"""
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("Gerar Documentação SchemaSpy")
        
        if success:
            self.load_report()
            QMessageBox.information(self, "Sucesso", "Documentação gerada com sucesso!")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao gerar a documentação. Verifique os logs.")

    def load_report(self):
        """Carrega o relatório gerado no navegador embutido"""
        index_path = OUTPUT_DIR / "index.html"
        if index_path.exists():
            url = QUrl.fromLocalFile(str(index_path))
            self.browser.setUrl(url)
            self.append_log(" Relatório carregado no visualizador.")
        else:
            self.append_log(" Relatório não encontrado em 'schemaspy/output/index.html'.")