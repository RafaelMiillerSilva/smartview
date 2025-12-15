 SmartView
Gerador automático de documentação de banco de dados com interface gráfica em Python + PySide6 + SchemaSpy

O SmartView é uma aplicação desktop desenvolvida em Python 3.12 com PySide6, projetada para gerar documentação completa de bancos de dados SQL Server usando o SchemaSpy.
Ele permite que qualquer usuário visualize estruturas, relacionamentos, informações de tabelas e diagramas gerados automaticamente.

A aplicação foi estruturada para ser totalmente portátil e funcionar via release executável (.exe), ideal para equipes de TI, DBAs, devs e analistas.

 Recursos principais

✔ Interface amigável feita com PySide6
✔ Geração automática de documentação HTML via SchemaSpy
✔ Suporte a Autenticação Windows (integratedSecurity)
✔ Suporte a autenticação SQL tradicional
✔ Inclusão automática do sqljdbc_auth.dll no PATH
✔ Inclusão automática do Graphviz portable
✔ Suporte a drivers customizados do SQL Server (JDBC)
✔ Criação de arquivo config.json automática
✔ Logs detalhados na interface
✔ Execução do SchemaSpy em thread separada (UI não trava)
✔ Timeout configurável para geração
✔ Preview do progresso em tempo real

 Tecnologias utilizadas
Backend (Python)

Python 3.12

PySide6 (GUI)

threading (execução assíncrona)

subprocess (executar SchemaSpy)

json / pathlib (configuração)

venv (ambiente virtual)

SchemaSpy (motor de documentação)

Ferramentas externas

SchemaSpy 7.0.2

Graphviz Portable

Driver JDBC MSSQL (mssql-jdbc-13.2.1.jre11.jar)

sqljdbc_auth.dll — necessário para Autenticação Windows
