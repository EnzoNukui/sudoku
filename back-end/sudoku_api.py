import random
import os
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel
from requests.exceptions import RequestException
from dotenv import load_dotenv

import sudoku_db
from sudoku_logica import (
    criar_jogo_com_solucao,
    obter_tamanho_bloco,
)


load_dotenv(Path(__file__).with_name(".env"))


app = FastAPI(title="API do Sudoku")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://ende-sudoku.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NovoJogo(BaseModel):
    tamanho: Literal[4, 6, 9]
    dificuldade: Literal["facil", "medio", "dificil"]


class Jogada(BaseModel):
    jogo_id: str
    linha: int
    coluna: int
    numero: int


class Tabuleiro(BaseModel):
    jogo_id: str
    tabuleiro: list[list[int]]
    tempo_segundos: int | None = None


class Partida(BaseModel):
    jogo_id: str


class CredencialGoogle(BaseModel):
    credential: str


def verificar_credencial_google(credential):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Login Google não configurado na API.")

    try:
        dados = id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
    except (ValueError, RequestException, GoogleAuthError):
        raise HTTPException(status_code=401, detail="Login Google inválido ou expirado.")

    if not dados.get("sub"):
        raise HTTPException(status_code=401, detail="Conta Google inválida.")
    return dados


def codificar_base64(valor):
    return base64.urlsafe_b64encode(valor).rstrip(b"=").decode("ascii")


def decodificar_base64(valor):
    return base64.urlsafe_b64decode(valor + "=" * (-len(valor) % 4))


def criar_token_sessao(usuario):
    segredo = os.getenv("SESSION_SECRET")
    if not segredo:
        raise HTTPException(status_code=503, detail="Sessão não configurada na API.")

    conteudo = json.dumps(
        {
            "sub": usuario["sub"],
            "name": usuario.get("name") or "Jogador",
            "picture": usuario.get("picture"),
            "exp": int(time.time()) + 7 * 24 * 60 * 60,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assinatura = hmac.new(segredo.encode("utf-8"), conteudo, hashlib.sha256).digest()
    return f"{codificar_base64(conteudo)}.{codificar_base64(assinatura)}"


def usuario_sessao(authorization):
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Autenticação inválida.")

    segredo = os.getenv("SESSION_SECRET")
    if not segredo:
        raise HTTPException(status_code=503, detail="Sessão não configurada na API.")

    try:
        conteudo_codificado, assinatura_codificada = authorization[7:].split(".", 1)
        conteudo = decodificar_base64(conteudo_codificado)
        assinatura = decodificar_base64(assinatura_codificada)
        assinatura_esperada = hmac.new(
            segredo.encode("utf-8"), conteudo, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(assinatura, assinatura_esperada):
            raise ValueError
        usuario = json.loads(conteudo)
        if not usuario.get("sub") or usuario.get("exp", 0) <= int(time.time()):
            raise ValueError
        return usuario
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")


def acessar_jogo(jogo_id, authorization):
    jogo = buscar_jogo(jogo_id)
    usuario = usuario_sessao(authorization)
    if jogo["google_sub"] != (usuario["sub"] if usuario else None):
        raise HTTPException(status_code=403, detail="Esta partida pertence a outro usuário.")
    return jogo


def tempo_partida_ms(jogo):
    inicio = jogo["iniciada_em"]
    if inicio.tzinfo is None:
        inicio = inicio.replace(tzinfo=timezone.utc)
    return max(1, int((datetime.now(timezone.utc) - inicio).total_seconds() * 1000))


def salvar_progresso(jogo, resultado=None, tempo_ms=None):
    if tempo_ms is None and resultado and resultado != "EM_ANDAMENTO":
        tempo_ms = tempo_partida_ms(jogo)
    sudoku_db.salvar_progresso(
        jogo,
        resultado,
        tempo_ms,
    )


def validar_formato_tabuleiro(tabuleiro):
    tamanho = len(tabuleiro)

    if tamanho not in (4, 6, 9):
        raise HTTPException(status_code=400, detail="O tabuleiro deve ser 4x4, 6x6 ou 9x9.")

    for linha in tabuleiro:
        if len(linha) != tamanho:
            raise HTTPException(status_code=400, detail="O tabuleiro deve ser quadrado.")

    return tamanho


def buscar_jogo(jogo_id):
    jogo = sudoku_db.buscar_jogo(jogo_id)

    if jogo is None:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    return jogo


@app.get("/api")
def verificar_api():
    return {"mensagem": "API do Sudoku funcionando"}


@app.post("/api/auth/google")
def login_google(dados: CredencialGoogle):
    usuario = verificar_credencial_google(dados.credential)
    nome = usuario.get("name") or "Jogador"
    foto = usuario.get("picture")
    sudoku_db.salvar_usuario(usuario["sub"], nome, foto)
    return {"token": criar_token_sessao(usuario), "nome": nome, "foto_url": foto}


@app.get("/api/ranking")
def consultar_ranking(
    tamanho: int = Query(default=9),
    dificuldade: str = Query(default="facil"),
):
    if tamanho not in (4, 6, 9) or dificuldade not in ("facil", "medio", "dificil"):
        raise HTTPException(status_code=400, detail="Tamanho ou dificuldade inválidos.")
    return sudoku_db.listar_ranking(tamanho, dificuldade)


@app.post("/api/novo-jogo")
def novo_jogo(dados: NovoJogo, authorization: str | None = Header(default=None)):
    usuario = usuario_sessao(authorization)
    tabuleiro, solucao = criar_jogo_com_solucao(dados.tamanho, dados.dificuldade)
    bloco_linhas, bloco_colunas = obter_tamanho_bloco(dados.tamanho)
    jogo_id = str(uuid4())
    partida_id = str(uuid4()) if usuario else None

    if usuario:
        sudoku_db.salvar_usuario(
            usuario["sub"], usuario.get("name") or "Jogador", usuario.get("picture")
        )
        sudoku_db.iniciar_partida(partida_id, usuario["sub"], dados.tamanho, dados.dificuldade)

    jogo = {
        "jogo_id": jogo_id,
        "tabuleiro_inicial": [linha.copy() for linha in tabuleiro],
        "solucao": solucao,
        "dicas_usadas": set(),
        "google_sub": usuario["sub"] if usuario else None,
        "partida_id": partida_id,
        "tamanho": dados.tamanho,
        "dificuldade": dados.dificuldade,
        "iniciada_em": datetime.now(timezone.utc),
        "erros": 0,
        "vidas_extras": 0,
        "limite_erros": 3,
        "resultado": "EM_ANDAMENTO",
    }
    sudoku_db.criar_jogo(jogo)

    return {
        "jogo_id": jogo_id,
        "tamanho": dados.tamanho,
        "bloco_linhas": bloco_linhas,
        "bloco_colunas": bloco_colunas,
        "dificuldade": dados.dificuldade,
        "dicas_restantes": 3,
        "ranking_habilitado": bool(usuario),
        "tabuleiro": tabuleiro,
    }


@app.post("/api/dica")
def dar_dica(dados: Tabuleiro, authorization: str | None = Header(default=None)):
    jogo = acessar_jogo(dados.jogo_id, authorization)
    if jogo["resultado"] != "EM_ANDAMENTO":
        raise HTTPException(status_code=409, detail="Partida encerrada.")
    solucao = jogo["solucao"]
    tamanho = validar_formato_tabuleiro(dados.tabuleiro)

    if tamanho != len(solucao):
        raise HTTPException(status_code=400, detail="Tamanho do tabuleiro incorreto.")

    if len(jogo["dicas_usadas"]) >= 3:
        raise HTTPException(status_code=409, detail="Limite de dicas atingido.")

    candidatas = [
        (linha, coluna)
        for linha in range(tamanho)
        for coluna in range(tamanho)
        if jogo["tabuleiro_inicial"][linha][coluna] == 0
        and (linha, coluna) not in jogo["dicas_usadas"]
        and dados.tabuleiro[linha][coluna] != solucao[linha][coluna]
    ]

    if not candidatas:
        raise HTTPException(status_code=409, detail="Não há células para receber dica.")

    linha, coluna = random.choice(candidatas)
    jogo["dicas_usadas"].add((linha, coluna))
    salvar_progresso(jogo)

    return {
        "linha": linha,
        "coluna": coluna,
        "numero": solucao[linha][coluna],
        "dicas_restantes": 3 - len(jogo["dicas_usadas"]),
    }


@app.post("/api/reiniciar-dicas")
def reiniciar_dicas(dados: Partida, authorization: str | None = Header(default=None)):
    jogo = acessar_jogo(dados.jogo_id, authorization)
    if jogo["resultado"] == "EM_ANDAMENTO":
        raise HTTPException(status_code=409, detail="A partida ainda está em andamento.")
    nova_partida_id = str(uuid4()) if jogo["google_sub"] else None
    if nova_partida_id:
        sudoku_db.iniciar_partida(
            nova_partida_id, jogo["google_sub"], jogo["tamanho"], jogo["dificuldade"]
        )
    jogo["partida_id"] = nova_partida_id
    jogo["dicas_usadas"].clear()
    jogo["iniciada_em"] = datetime.now(timezone.utc)
    jogo["erros"] = 0
    jogo["vidas_extras"] = 0
    jogo["limite_erros"] = 3
    jogo["resultado"] = "EM_ANDAMENTO"
    salvar_progresso(jogo, "EM_ANDAMENTO")
    return {"dicas_restantes": 3}


@app.post("/api/adicionar-vida")
def adicionar_vida(dados: Partida, authorization: str | None = Header(default=None)):
    jogo = acessar_jogo(dados.jogo_id, authorization)
    if jogo["resultado"] != "DERROTA":
        raise HTTPException(status_code=409, detail="A partida não está em derrota.")
    jogo["vidas_extras"] += 1
    jogo["limite_erros"] += 1
    jogo["resultado"] = "EM_ANDAMENTO"
    salvar_progresso(jogo, "EM_ANDAMENTO")
    return {"limite_erros": jogo["limite_erros"]}


@app.post("/api/verificar-jogada")
def validar_jogada(dados: Jogada, authorization: str | None = Header(default=None)):
    jogo = acessar_jogo(dados.jogo_id, authorization)
    if jogo["resultado"] != "EM_ANDAMENTO":
        raise HTTPException(status_code=409, detail="Partida encerrada.")
    solucao = jogo["solucao"]
    tamanho = len(solucao)

    if not (0 <= dados.linha < tamanho and 0 <= dados.coluna < tamanho):
        raise HTTPException(status_code=400, detail="Linha ou coluna fora do tabuleiro.")

    if jogo["tabuleiro_inicial"][dados.linha][dados.coluna] != 0:
        raise HTTPException(status_code=400, detail="Essa célula é fixa.")

    correta = solucao[dados.linha][dados.coluna] == dados.numero
    if not correta:
        jogo["erros"] += 1
        if jogo["erros"] >= jogo["limite_erros"]:
            jogo["resultado"] = "DERROTA"
            salvar_progresso(jogo, "DERROTA")
        else:
            salvar_progresso(jogo)

    return {"correta": correta, "erros": jogo["erros"]}


@app.post("/api/verificar-tabuleiro")
def validar_tabuleiro(dados: Tabuleiro, authorization: str | None = Header(default=None)):
    jogo = acessar_jogo(dados.jogo_id, authorization)
    if jogo["resultado"] != "EM_ANDAMENTO":
        raise HTTPException(status_code=409, detail="Partida encerrada.")
    validar_formato_tabuleiro(dados.tabuleiro)

    completo = dados.tabuleiro == jogo["solucao"]
    if completo:
        if dados.tempo_segundos is not None and dados.tempo_segundos < 0:
            raise HTTPException(status_code=400, detail="Tempo inválido.")
        jogo["resultado"] = "VITORIA"
        tempo_ms = dados.tempo_segundos * 1000 if dados.tempo_segundos is not None else None
        salvar_progresso(jogo, "VITORIA", tempo_ms)

    return {
        "completo": completo,
        "ranking_elegivel": completo and bool(jogo["google_sub"])
        and not jogo["dicas_usadas"] and jogo["vidas_extras"] == 0,
    }
