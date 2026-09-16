import os
import re
from pathlib import Path

import oracledb


def conectar():
    usuario = os.getenv("ORACLE_USER")
    senha = os.getenv("ORACLE_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")

    if not usuario or not senha or not dsn:
        raise RuntimeError(
            "Defina ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN antes de conectar."
        )

    return oracledb.connect(user=usuario, password=senha, dsn=dsn)


def testar_conexao():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT 1 FROM DUAL")
            return cursor.fetchone()[0] == 1


def criar_tabelas():
    arquivo_sql = Path(__file__).with_name("schema.sql")
    comandos = arquivo_sql.read_text(encoding="utf-8").split(";")

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            for comando in comandos:
                comando = comando.strip()
                if not comando:
                    continue

                objeto = re.match(r"CREATE\s+(TABLE|INDEX)\s+(\w+)", comando, re.I)
                if objeto is None:
                    raise ValueError("O schema contém um comando inesperado.")

                tipo, nome = objeto.groups()
                cursor.execute(
                    "SELECT COUNT(*) FROM USER_OBJECTS "
                    "WHERE OBJECT_TYPE = :tipo AND OBJECT_NAME = :nome",
                    tipo=tipo.upper(),
                    nome=nome.upper(),
                )

                if cursor.fetchone()[0] == 0:
                    cursor.execute(comando)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2 or sys.argv[1] not in ("testar", "criar"):
        raise SystemExit("Uso: python sudoku_db.py testar | criar")

    if sys.argv[1] == "testar":
        testar_conexao()
        print("Conexão com o Oracle funcionando.")
    else:
        criar_tabelas()
        print("Tabelas e índices do Sudoku verificados no Oracle.")
