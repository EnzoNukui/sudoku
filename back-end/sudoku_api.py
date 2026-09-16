import random
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sudoku_logica import (
    criar_jogo_com_solucao,
    obter_tamanho_bloco,
)


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


@app.post("/novo-jogo")
def novo_jogo(dados: NovoJogo):
    tabuleiro, solucao = criar_jogo_com_solucao(dados.tamanho, dados.dificuldade)
    bloco_linhas, bloco_colunas = obter_tamanho_bloco(dados.tamanho)
    jogo_id = str(uuid4())

    jogos[jogo_id] = {
        "tabuleiro_inicial": [linha.copy() for linha in tabuleiro],
        "solucao": solucao,
        "dicas_usadas": set(),
    }

    return {
        "jogo_id": jogo_id,
        "tamanho": dados.tamanho,
        "bloco_linhas": bloco_linhas,
        "bloco_colunas": bloco_colunas,
        "dificuldade": dados.dificuldade,
        "dicas_restantes": 3,
        "tabuleiro": tabuleiro,
    }


@app.post("/dica")
def dar_dica(dados: Tabuleiro):
    jogo = buscar_jogo(dados.jogo_id)
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

    return {
        "linha": linha,
        "coluna": coluna,
        "numero": solucao[linha][coluna],
        "dicas_restantes": 3 - len(jogo["dicas_usadas"]),
    }


@app.post("/reiniciar-dicas")
def reiniciar_dicas(dados: Partida):
    jogo = buscar_jogo(dados.jogo_id)
    jogo["dicas_usadas"].clear()
    return {"dicas_restantes": 3}


@app.post("/verificar-jogada")
def validar_jogada(dados: Jogada):
    jogo = buscar_jogo(dados.jogo_id)
    solucao = jogo["solucao"]
    tamanho = len(solucao)

    if not (0 <= dados.linha < tamanho and 0 <= dados.coluna < tamanho):
        raise HTTPException(status_code=400, detail="Linha ou coluna fora do tabuleiro.")

    if jogo["tabuleiro_inicial"][dados.linha][dados.coluna] != 0:
        raise HTTPException(status_code=400, detail="Essa célula é fixa.")

    correta = solucao[dados.linha][dados.coluna] == dados.numero

    return {"correta": correta}


@app.post("/verificar-tabuleiro")
def validar_tabuleiro(dados: Tabuleiro):
    jogo = buscar_jogo(dados.jogo_id)
    validar_formato_tabuleiro(dados.tabuleiro)

    completo = dados.tabuleiro == jogo["solucao"]

    return {"completo": completo}
