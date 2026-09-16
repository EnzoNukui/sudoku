from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sudoku_logica import (
    criar_jogo,
    obter_tamanho_bloco,
    verificar_jogada,
    verificar_tabuleiro_completo,
)


app = FastAPI(title="API do Sudoku")

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
    tabuleiro: list[list[int]]
    linha: int
    coluna: int
    numero: int


class Tabuleiro(BaseModel):
    tabuleiro: list[list[int]]


def validar_formato_tabuleiro(tabuleiro):
    tamanho = len(tabuleiro)

    if tamanho not in (4, 6, 9):
        raise HTTPException(status_code=400, detail="O tabuleiro deve ser 4x4, 6x6 ou 9x9.")

    for linha in tabuleiro:
        if len(linha) != tamanho:
            raise HTTPException(status_code=400, detail="O tabuleiro deve ser quadrado.")

    return tamanho


@app.get("/")
def verificar_api():
    return {"mensagem": "API do Sudoku funcionando"}


@app.post("/novo-jogo")
def novo_jogo(dados: NovoJogo):
    tabuleiro = criar_jogo(dados.tamanho, dados.dificuldade)
    bloco_linhas, bloco_colunas = obter_tamanho_bloco(dados.tamanho)

    return {
        "tamanho": dados.tamanho,
        "bloco_linhas": bloco_linhas,
        "bloco_colunas": bloco_colunas,
        "dificuldade": dados.dificuldade,
        "tabuleiro": tabuleiro,
    }


@app.post("/verificar-jogada")
def validar_jogada(dados: Jogada):
    tamanho = validar_formato_tabuleiro(dados.tabuleiro)

    if not (0 <= dados.linha < tamanho and 0 <= dados.coluna < tamanho):
        raise HTTPException(status_code=400, detail="Linha ou coluna fora do tabuleiro.")

    tabuleiro = [linha.copy() for linha in dados.tabuleiro]
    tabuleiro[dados.linha][dados.coluna] = 0
    tamanho_bloco = obter_tamanho_bloco(tamanho)

    valida = verificar_jogada(
        tabuleiro,
        dados.linha,
        dados.coluna,
        dados.numero,
        tamanho_bloco,
    )

    return {"valida": valida}


@app.post("/verificar-tabuleiro")
def validar_tabuleiro(dados: Tabuleiro):
    tamanho = validar_formato_tabuleiro(dados.tabuleiro)
    tamanho_bloco = obter_tamanho_bloco(tamanho)
    tabuleiro = [linha.copy() for linha in dados.tabuleiro]

    completo = verificar_tabuleiro_completo(tabuleiro, tamanho_bloco)

    return {"completo": completo}
