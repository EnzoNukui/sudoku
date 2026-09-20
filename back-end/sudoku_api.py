import random
import os
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
jogos = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


class Partida(BaseModel):
    jogo_id: str


class CredencialGoogle(BaseModel):
    credential: str


def usuario_google(authorization):
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Autenticação inválida.")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Login Google não configurado na API.")

    try:
        dados = id_token.verify_oauth2_token(
            authorization[7:], google_requests.Request(), client_id
        )
    except (ValueError, RequestException, GoogleAuthError):
        raise HTTPException(status_code=401, detail="Login Google inválido ou expirado.")

    if not dados.get("sub"):
        raise HTTPException(status_code=401, detail="Conta Google inválida.")
    return dados


def acessar_jogo(jogo_id, authorization):
    jogo = buscar_jogo(jogo_id)
    usuario = usuario_google(authorization)
    if jogo["google_sub"] != (usuario["sub"] if usuario else None):
        raise HTTPException(status_code=403, detail="Esta partida pertence a outro usuário.")
    return jogo


def tempo_partida_ms(jogo):
    return max(1, int((datetime.now(timezone.utc) - jogo["iniciada_em"]).total_seconds() * 1000))


def salvar_progresso(jogo, resultado=None):
    if jogo["google_sub"]:
        sudoku_db.atualizar_partida(
            jogo["partida_id"], jogo["erros"], len(jogo["dicas_usadas"]),
            jogo["vidas_extras"], resultado,
            tempo_partida_ms(jogo) if resultado and resultado != "EM_ANDAMENTO" else None,
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
    jogo = jogos.get(jogo_id)

    if jogo is None:
        raise HTTPException(status_code=404, detail="Partida não encontrada.")

    return jogo


@app.get("/")
def verificar_api():
    return {"mensagem": "API do Sudoku funcionando"}


@app.post("/auth/google")
def login_google(dados: CredencialGoogle):
    usuario = usuario_google(f"Bearer {dados.credential}")
    nome = usuario.get("name") or "Jogador"
    foto = usuario.get("picture")
    sudoku_db.salvar_usuario(usuario["sub"], nome, foto)
    return {"nome": nome, "foto_url": foto}


@app.get("/ranking")
def consultar_ranking(
    tamanho: int = Query(default=9),
    dificuldade: str = Query(default="facil"),
):
    if tamanho not in (4, 6, 9) or dificuldade not in ("facil", "medio", "dificil"):
        raise HTTPException(status_code=400, detail="Tamanho ou dificuldade inválidos.")
    return sudoku_db.listar_ranking(tamanho, dificuldade)


@app.post("/novo-jogo")
def novo_jogo(dados: NovoJogo, authorization: str | None = Header(default=None)):
    usuario = usuario_google(authorization)
    tabuleiro, solucao = criar_jogo_com_solucao(dados.tamanho, dados.dificuldade)
    bloco_linhas, bloco_colunas = obter_tamanho_bloco(dados.tamanho)
    jogo_id = str(uuid4())
    partida_id = str(uuid4()) if usuario else None

    if usuario:
        sudoku_db.salvar_usuario(
            usuario["sub"], usuario.get("name") or "Jogador", usuario.get("picture")
        )
        sudoku_db.iniciar_partida(partida_id, usuario["sub"], dados.tamanho, dados.dificuldade)

    jogos[jogo_id] = {
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


@app.post("/dica")
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


@app.post("/reiniciar-dicas")
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
    return {"dicas_restantes": 3}


@app.post("/adicionar-vida")
def adicionar_vida(dados: Partida, authorization: str | None = Header(default=None)):
    jogo = acessar_jogo(dados.jogo_id, authorization)
    if jogo["resultado"] != "DERROTA":
        raise HTTPException(status_code=409, detail="A partida não está em derrota.")
    jogo["vidas_extras"] += 1
    jogo["limite_erros"] += 1
    jogo["resultado"] = "EM_ANDAMENTO"
    salvar_progresso(jogo, "EM_ANDAMENTO")
    return {"limite_erros": jogo["limite_erros"]}


@app.post("/verificar-jogada")
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


@app.post("/verificar-tabuleiro")
def validar_tabuleiro(dados: Tabuleiro, authorization: str | None = Header(default=None)):
    jogo = acessar_jogo(dados.jogo_id, authorization)
    if jogo["resultado"] != "EM_ANDAMENTO":
        raise HTTPException(status_code=409, detail="Partida encerrada.")
    validar_formato_tabuleiro(dados.tabuleiro)

    completo = dados.tabuleiro == jogo["solucao"]
    if completo:
        jogo["resultado"] = "VITORIA"
        salvar_progresso(jogo, "VITORIA")

    return {
        "completo": completo,
        "ranking_elegivel": completo and bool(jogo["google_sub"])
        and not jogo["dicas_usadas"] and jogo["vidas_extras"] == 0,
    }
