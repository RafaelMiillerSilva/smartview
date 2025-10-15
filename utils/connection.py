import pyodbc
import json
from pathlib import Path
import logging

# -----------------------
# Diretórios e arquivos
# -----------------------
ROOT_DIR = Path(__file__).parent.resolve()
JSON_FILE = ROOT_DIR / "connection.json"
LOG_FILE = ROOT_DIR / "connection.log"

# -----------------------
# Configuração de log
# -----------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log(message: str):
    """Registra mensagem no log e imprime no console"""
    logging.info(message)
    print(f"[{message}]")

# -----------------------
# Funções de conexão
# -----------------------
def save_connection_json(server, database, username, password, windows_auth=False):
    """Salva dados de conexão no connection.json"""
    data = {
        "server": server,
        "database": database,
        "username": username,
        "password": password,
        "windows_auth": windows_auth,
    }
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)
    log(f"Arquivo {JSON_FILE.name} atualizado com sucesso.")

def load_connection_json():
    """Carrega dados de conexão do connection.json ou cria um modelo se não existir"""
    if not JSON_FILE.exists():
        # Cria arquivo com valores padrão
        default_data = {
            "server": "",
            "database": "",
            "username": "",
            "password": "",
            "windows_auth": True
        }
        with open(JSON_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        log(f"Arquivo {JSON_FILE.name} não existia e foi criado com valores padrão.")
        return default_data

    with open(JSON_FILE, "r") as f:
        data = json.load(f)
    log(f"Arquivo {JSON_FILE.name} carregado com sucesso.")
    return data

def list_databases(server, username, password, windows_auth=False):
    """Retorna lista de bancos disponíveis no servidor"""
    log(f"Listando bancos de dados no servidor '{server}'...")
    try:
        if windows_auth:
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE=master;"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE=master;"
                f"UID={username};"
                f"PWD={password};"
                f"Encrypt=no;"
                f"TrustServerCertificate=yes;"
            )

        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4")  # ignora system DBs
        databases = [row[0] for row in cursor.fetchall()]
        conn.close()
        log(f"Bancos encontrados: {databases}")
        return True, databases
    except Exception as e:
        log(f"Erro ao listar bancos: {e}")
        return False, str(e)

def connect_to_database(server, username, password, database, windows_auth=False):
    """Conecta ao SQL Server usando pyodbc"""
    log(f"Tentando conectar ao servidor '{server}' e banco '{database}'...")
    try:
        if windows_auth:
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"Encrypt=no;"
                f"TrustServerCertificate=yes;"
            )

        conn = pyodbc.connect(conn_str, timeout=5)
        conn.close()
        save_connection_json(server, database, username, password, windows_auth)
        log(f"Conectado ao banco '{database}' com sucesso!")
        return True, f"Conectado ao banco '{database}' com sucesso!"
    except pyodbc.InterfaceError as e:
        log(f"Erro de interface ODBC: {e}")
        return False, f"Erro de interface ODBC: {e}"
    except pyodbc.OperationalError as e:
        log(f"Erro operacional ODBC: {e}")
        return False, f"Erro operacional ODBC: {e}"
    except Exception as e:
        log(f"Erro inesperado: {e}")
        return False, str(e)
