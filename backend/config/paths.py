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

# === Graphviz ===
GRAPHVIZ_DIR = ROOT_DIR / "graphviz"
GRAPHVIZ_BIN = GRAPHVIZ_DIR / "bin"

# Adiciona Graphviz ao PATH se existir
if GRAPHVIZ_BIN.exists():
    os.environ["PATH"] = f"{GRAPHVIZ_BIN}{os.pathsep}" + os.environ.get("PATH", "")
    print(f" Graphviz adicionado ao PATH: {GRAPHVIZ_BIN}")
else:
    print(f" Graphviz não encontrado em: {GRAPHVIZ_BIN}")
    print(f"   Os diagramas de relacionamento não serão gerados.")
    print(f"   Baixe em: https://graphviz.org/download/")

# === Arquivos principais ===
JSON_FILE = ROOT_DIR / "connection.json"
LOG_FILE = ROOT_DIR / "connection.log"

# === SchemaSpy ===
SCHEMASPY_JAR = SCHEMASPY_DIR / "schemaspy-app.jar"
DRIVER_JAR = SCHEMASPY_DIR / "mssql-jdbc-13.2.1.jre11.jar"
OUTPUT_DIR = SCHEMASPY_DIR / "output"

# === Garantir que pastas importantes existam ===
for path in [SCHEMASPY_DIR, OUTPUT_DIR, GRAPHVIZ_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# === Função utilitária para debug ===
def debug_paths():
    """Exibe todos os caminhos configurados para debug"""
    print("\n" + "="*60)
    print(" CAMINHOS CONFIGURADOS")
    print("="*60)
    print(f"ROOT_DIR:       {ROOT_DIR}")
    print(f"BACKEND_DIR:    {BACKEND_DIR}")
    print(f"CONFIG_DIR:     {CONFIG_DIR}")
    print(f"UTILS_DIR:      {UTILS_DIR}")
    print(f"GUI_DIR:        {GUI_DIR}")
    print(f"SCHEMASPY_DIR:  {SCHEMASPY_DIR}")
    print(f"GRAPHVIZ_DIR:   {GRAPHVIZ_DIR}")
    print(f"GRAPHVIZ_BIN:   {GRAPHVIZ_BIN}")
    print(f"JSON_FILE:      {JSON_FILE}")
    print(f"LOG_FILE:       {LOG_FILE}")
    print(f"SCHEMASPY_JAR:  {SCHEMASPY_JAR}")
    print(f"DRIVER_JAR:     {DRIVER_JAR}")
    print(f"OUTPUT_DIR:     {OUTPUT_DIR}")
    print("="*60 + "\n")
    
    # Verifica existência dos arquivos críticos
    print(" VERIFICAÇÃO DE ARQUIVOS:")
    checks = {
        "SCHEMASPY_JAR": SCHEMASPY_JAR.exists(),
        "DRIVER_JAR": DRIVER_JAR.exists(),
        "GRAPHVIZ_BIN": GRAPHVIZ_BIN.exists(),
        "JSON_FILE": JSON_FILE.exists(),
    }
    for name, exists in checks.items():
        status = "EXISTE" if exists else "NAO EXISTE"
        print(f"  {status} {name}")
    print("="*60 + "\n")