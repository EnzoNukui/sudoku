import os
import re
import json
import random
import time
import threading
from pathlib import Path

import oracledb


_pool = None
_pool_lock = threading.Lock()


def obter_pool():
    global _pool
    if _pool is not None:
        return _pool

    with _pool_lock:
        if _pool is None:
            usuario = os.getenv("ORACLE_USER")
            senha = os.getenv("ORACLE_PASSWORD")
            dsn = os.getenv("ORACLE_DSN")

            if not usuario or not senha or not dsn:
                raise RuntimeError(
                    "Defina ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN antes de conectar."
                )

            _pool = oracledb.create_pool(
                user=usuario,
                password=senha,
                dsn=dsn,
                min=0,
                max=1,
                increment=1,
                timeout=30,
                wait_timeout=15000,
                ping_interval=30,
                getmode=oracledb.POOL_GETMODE_WAIT,
            )

    return _pool


def conectar():
    for tentativa in range(6):
        try:
            return obter_pool().acquire()
        except oracledb.DatabaseError as erro:
            codigo = getattr(erro.args[0], "code", None)
            if codigo != 2391 or tentativa == 5:
                raise
            time.sleep(0.2 * (tentativa + 1) + random.uniform(0, 0.1))


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


def criar_jogo(jogo):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """INSERT INTO SUDOKU_JOGOS
                   (ID, GOOGLE_SUB, PARTIDA_ID, TABULEIRO_INICIAL, SOLUCAO,
                    DICAS_USADAS, TAMANHO, DIFICULDADE, INICIADA_EM, ERROS,
                    VIDAS_EXTRAS, LIMITE_ERROS, RESULTADO)
                   VALUES
                   (:id, :google_sub, :partida_id, :tabuleiro_inicial, :solucao,
                    :dicas_usadas, :tamanho, :dificuldade, :iniciada_em, :erros,
                    :vidas_extras, :limite_erros, :resultado)""",
                id=jogo["jogo_id"], google_sub=jogo["google_sub"],
                partida_id=jogo["partida_id"],
                tabuleiro_inicial=json.dumps(jogo["tabuleiro_inicial"]),
                solucao=json.dumps(jogo["solucao"]), dicas_usadas="[]",
                tamanho=jogo["tamanho"], dificuldade=jogo["dificuldade"],
                iniciada_em=jogo["iniciada_em"], erros=jogo["erros"],
                vidas_extras=jogo["vidas_extras"], limite_erros=jogo["limite_erros"],
                resultado=jogo["resultado"],
            )
        conexao.commit()


def buscar_jogo(jogo_id):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """SELECT GOOGLE_SUB, PARTIDA_ID, TABULEIRO_INICIAL, SOLUCAO,
                          DICAS_USADAS, TAMANHO, DIFICULDADE, INICIADA_EM, ERROS,
                          VIDAS_EXTRAS, LIMITE_ERROS, RESULTADO
                   FROM SUDOKU_JOGOS WHERE ID = :jogo_id""",
                jogo_id=jogo_id,
            )
            linha = cursor.fetchone()

    if linha is None:
        return None

    return {
        "jogo_id": jogo_id,
        "google_sub": linha[0],
        "partida_id": linha[1],
        "tabuleiro_inicial": json.loads(linha[2]),
        "solucao": json.loads(linha[3]),
        "dicas_usadas": {tuple(posicao) for posicao in json.loads(linha[4])},
        "tamanho": linha[5],
        "dificuldade": linha[6],
        "iniciada_em": linha[7],
        "erros": linha[8],
        "vidas_extras": linha[9],
        "limite_erros": linha[10],
        "resultado": linha[11],
    }


def atualizar_jogo(jogo):
    dicas = json.dumps([list(posicao) for posicao in sorted(jogo["dicas_usadas"])])
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """UPDATE SUDOKU_JOGOS
                   SET PARTIDA_ID = :partida_id, DICAS_USADAS = :dicas_usadas,
                       INICIADA_EM = :iniciada_em, ERROS = :erros,
                       VIDAS_EXTRAS = :vidas_extras, LIMITE_ERROS = :limite_erros,
                       RESULTADO = :resultado
                   WHERE ID = :jogo_id""",
                jogo_id=jogo["jogo_id"], partida_id=jogo["partida_id"],
                dicas_usadas=dicas, iniciada_em=jogo["iniciada_em"],
                erros=jogo["erros"], vidas_extras=jogo["vidas_extras"],
                limite_erros=jogo["limite_erros"], resultado=jogo["resultado"],
            )
        conexao.commit()


def salvar_progresso(jogo, resultado=None, tempo_ms=None):
    dicas = json.dumps([list(posicao) for posicao in sorted(jogo["dicas_usadas"])])
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """UPDATE SUDOKU_JOGOS
                   SET PARTIDA_ID = :partida_id, DICAS_USADAS = :dicas_usadas,
                       INICIADA_EM = :iniciada_em, ERROS = :erros,
                       VIDAS_EXTRAS = :vidas_extras, LIMITE_ERROS = :limite_erros,
                       RESULTADO = :resultado_jogo
                   WHERE ID = :jogo_id""",
                jogo_id=jogo["jogo_id"], partida_id=jogo["partida_id"],
                dicas_usadas=dicas, iniciada_em=jogo["iniciada_em"],
                erros=jogo["erros"], vidas_extras=jogo["vidas_extras"],
                limite_erros=jogo["limite_erros"], resultado_jogo=jogo["resultado"],
            )

            if jogo["google_sub"]:
                cursor.execute(
                    """UPDATE SUDOKU_PARTIDAS
                       SET ERROS = :erros, DICAS_USADAS = :dicas,
                           VIDAS_EXTRAS = :vidas_extras,
                           RESULTADO = COALESCE(:resultado_partida, RESULTADO),
                           FINALIZADA_EM = CASE
                               WHEN :resultado_partida IS NULL
                                 OR :resultado_partida = 'EM_ANDAMENTO'
                               THEN NULL ELSE SYSTIMESTAMP END,
                           TEMPO_MS = :tempo_ms
                       WHERE ID = :partida_id""",
                    partida_id=jogo["partida_id"], erros=jogo["erros"],
                    dicas=len(jogo["dicas_usadas"]), vidas_extras=jogo["vidas_extras"],
                    resultado_partida=resultado, tempo_ms=tempo_ms,
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
