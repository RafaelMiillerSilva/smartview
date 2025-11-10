import os
from pathlib import Path

# === Diretório raiz do projeto ===
ROOT_DIR = Path(__file__).resolve().parents[2]  # sobe até a raiz do projeto (smartview)

# === Pastas principais ===
BACKEND_DIR = ROOT_DIR / "backend"
CONFIG_DIR = BACKEND_DIR / "config"
UTILS_DIR = BACKEND_DIR / "utils"
GUI_DIR = ROOT_DIR / "gui"  
SCHEMASPY_DIR = ROOT_DIR / "schemaspy"
BASE_DIR = Path(__file__).resolve().parent
GRAPHVIZ_BIN = BASE_DIR / "graphviz" / "bin"
os.environ["PATH"] = f"{GRAPHVIZ_BIN};" + os.environ["PATH"]

# === Arquivos principais ===
JSON_FILE = ROOT_DIR / "connection.json"
LOG_FILE = ROOT_DIR / "connection.log"

# === SchemaSpy ===
SCHEMASPY_JAR = SCHEMASPY_DIR / "schemaspy-app.jar"
DRIVER_JAR = SCHEMASPY_DIR / "mssql-jdbc-13.2.1.jre11.jar"
OUTPUT_DIR = SCHEMASPY_DIR / "output"

# === Garantir que pastas importantes existam ===
for path in [SCHEMASPY_DIR, OUTPUT_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# === Função utilitária para debug ===
def debug_paths():
    print("🔍 Caminhos configurados:")
    print(f"ROOT_DIR:       {ROOT_DIR}")
    print(f"BACKEND_DIR:    {BACKEND_DIR}")
    print(f"CONFIG_DIR:     {CONFIG_DIR}")
    print(f"UTILS_DIR:      {UTILS_DIR}")
    print(f"GUI_DIR:        {GUI_DIR}")
    print(f"SCHEMASPY_DIR:  {SCHEMASPY_DIR}")
    print(f"JSON_FILE:      {JSON_FILE}")
    print(f"LOG_FILE:       {LOG_FILE}")
    print(f"SCHEMASPY_JAR:  {SCHEMASPY_JAR}")
    print(f"DRIVER_JAR:     {DRIVER_JAR}")
    print(f"OUTPUT_DIR:     {OUTPUT_DIR}")
