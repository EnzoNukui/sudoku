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


def salvar_usuario(google_sub, nome, foto_url):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """MERGE INTO SUDOKU_USUARIOS destino
                   USING (SELECT :google_sub AS GOOGLE_SUB FROM DUAL) origem
                   ON (destino.GOOGLE_SUB = origem.GOOGLE_SUB)
                   WHEN MATCHED THEN UPDATE SET NOME = :nome, FOTO_URL = :foto_url
                   WHEN NOT MATCHED THEN INSERT (GOOGLE_SUB, NOME, FOTO_URL)
                   VALUES (:google_sub, :nome, :foto_url)""",
                google_sub=google_sub, nome=nome, foto_url=foto_url,
            )
        conexao.commit()


def iniciar_partida(partida_id, google_sub, tamanho, dificuldade):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """INSERT INTO SUDOKU_PARTIDAS
                   (ID, GOOGLE_SUB, TAMANHO, DIFICULDADE)
                   VALUES (:partida_id, :google_sub, :tamanho, :dificuldade)""",
                partida_id=partida_id, google_sub=google_sub,
                tamanho=tamanho, dificuldade=dificuldade,
            )
        conexao.commit()


def atualizar_partida(partida_id, erros, dicas, vidas_extras, resultado=None, tempo_ms=None):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """UPDATE SUDOKU_PARTIDAS
                   SET ERROS = :erros, DICAS_USADAS = :dicas,
                       VIDAS_EXTRAS = :vidas_extras,
                       RESULTADO = COALESCE(:resultado, RESULTADO),
                       FINALIZADA_EM = CASE WHEN :resultado IS NULL OR :resultado = 'EM_ANDAMENTO'
                           THEN NULL ELSE SYSTIMESTAMP END,
                       TEMPO_MS = :tempo_ms
                   WHERE ID = :partida_id""",
                partida_id=partida_id, erros=erros, dicas=dicas,
                vidas_extras=vidas_extras, resultado=resultado, tempo_ms=tempo_ms,
            )
        conexao.commit()


def listar_ranking(tamanho, dificuldade, limite=50):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """SELECT POSICAO, NOME, FOTO_URL, TEMPO_MS, ERROS, FINALIZADA_EM
                   FROM (
                       SELECT ROW_NUMBER() OVER (
                                  ORDER BY p.TEMPO_MS, p.FINALIZADA_EM
                              ) AS POSICAO,
                              u.NOME, u.FOTO_URL, p.TEMPO_MS, p.ERROS,
                              p.FINALIZADA_EM
                       FROM SUDOKU_PARTIDAS p
                       INNER JOIN SUDOKU_USUARIOS u
                           ON u.GOOGLE_SUB = p.GOOGLE_SUB
                       WHERE p.TAMANHO = :tamanho
                         AND p.DIFICULDADE = :dificuldade
                         AND p.RESULTADO = 'VITORIA'
                         AND p.DICAS_USADAS = 0
                         AND p.VIDAS_EXTRAS = 0
                   )
                   WHERE POSICAO <= :limite
                   ORDER BY POSICAO""",
                tamanho=tamanho, dificuldade=dificuldade, limite=limite,
            )
            return [
                {
                    "posicao": linha[0],
                    "nome": linha[1],
                    "foto_url": linha[2],
                    "tempo_ms": linha[3],
                    "erros": linha[4],
                    "finalizada_em": linha[5],
                }
                for linha in cursor.fetchall()
            ]


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
