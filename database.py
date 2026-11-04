import sqlite3 
from pathlib import Path
from datetime import datetime

#==========================================#
# Pasta onde os dados serão armazenados #
PASTA_DADOS = Path(__file__).parent / 'data' 
# Path(__file__) -> pega o arquivo atual
# .parent -> pega a pasta onde o arquivo está localizado
#==========================================#

PASTA_DADOS.mkdir(exist_ok=True) 
# Cria a pasta caso não exista#

CAMINHO_BANCO = PASTA_DADOS / 'sepatrack.db'
# Cria o caminho do banco de dados#

# Conectar ao banco

def conectar():
    return sqlite3.connect(CAMINHO_BANCO)

# Criar tabela de histórico
def inicializar_banco():
    with conectar() as conexao:
        cursor = conexao.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_separacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                odf TEXT NOT NULL,
                data_consulta TEXT NOT NULL,
                total_itens INTEGER NOT NULL,
                itens_seprados INTEGER NOT NULL,
                percentual_separado REAL NOT NULL
            )
        """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_historico_odf 
        ON historico_separacao (odf, data_consulta)
    """)
    # "crie um índice novo, mas se ele já existir, não faça nada" #
    # idx_historico_odf -> nome do índice # 
    # ON historico_separacao -> indica qual tabela vai receber esse índice #
    # (odf, data_consulta) -> são as colunas que formam o índice. # 
    # Esse trecho garante que, à medida que o SepaTrack crescer e acumular milhares ou milhões de registros de separações, as consultas por ODF continuarão a ser executadas de forma extremamente rápida e eficiente #

#==========================================#
    def salvar_historico(odf, total_itens, itens_separados):
        if total_itens <= 0:
            return  # Evita salvar registros com total de itens inválido

        percentual = (itens_separados / total_itens) * 100

        data_consulta = datetime.now().astimezone().isoformat(timespec="seconds")  # Armazena a data e hora com fuso horário

        with conectar() as conexao:
            conexao.execute("""
                INSERT INTO historico_separacao(
                odf,
                data_consulta,
                total_itens,
                itens_separados,
                percentual_separado
                )
                VALUES (?, ?, ?, ?, ?)
                """, (str(odf), data_consulta, total_itens, itens_separados, percentual)
            )

# Armazena o histórico de separação no banco de dados, incluindo a data e hora com fuso horário, garantindo que os registros sejam precisos e consistentes.
#==========================================#

#==========================================#
def buscar_historico(odf):
    with conectar() as conexao:
        conexao.row_factory = sqlite3.Row

        resultado = conexao.execute("""
            SELECT * FROM historico_separacao
            WHERE odf = ?
            ORDER BY data_consulta ASC
            """, (str(odf),)).fetchall()

    return [dict(row) for row in resultado]

# a função buscar_historico(odf) permite recuperar todos os registros de separação associados a um ODF específico, ordenados pela data de consulta em ordem crescente. Isso facilita a análise do histórico de separações ao longo do tempo para cada ODF.

#==========================================#