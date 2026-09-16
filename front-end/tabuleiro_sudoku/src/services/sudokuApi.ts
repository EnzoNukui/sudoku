export type TamanhoSudoku = 4 | 6 | 9
export type Dificuldade = 'facil' | 'medio' | 'dificil'

export type Jogo = {
  jogo_id: string
  tamanho: TamanhoSudoku
  bloco_linhas: number
  bloco_colunas: number
  dificuldade: Dificuldade
  dicas_restantes: number
  tabuleiro: number[][]
}

export type Dica = {
  linha: number
  coluna: number
  numero: number
  dicas_restantes: number
}

const API_URL = 'http://127.0.0.1:8000'

async function tratarResposta<T>(resposta: Response): Promise<T> {
  if (!resposta.ok) {
    throw new Error('Não foi possível comunicar com a API do Sudoku.')
  }

  return resposta.json() as Promise<T>
}

export async function criarNovoJogo(
  tamanho: TamanhoSudoku,
  dificuldade: Dificuldade,
): Promise<Jogo> {
  const resposta = await fetch(`${API_URL}/novo-jogo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tamanho, dificuldade }),
  })

  return tratarResposta<Jogo>(resposta)
}

export async function verificarJogada(
  jogoId: string,
  linha: number,
  coluna: number,
  numero: number,
): Promise<boolean> {
  const resposta = await fetch(`${API_URL}/verificar-jogada`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jogo_id: jogoId, linha, coluna, numero }),
  })

  const resultado = await tratarResposta<{ correta: boolean }>(resposta)
  return resultado.correta
}

export async function verificarTabuleiro(
  jogoId: string,
  tabuleiro: number[][],
): Promise<boolean> {
  const resposta = await fetch(`${API_URL}/verificar-tabuleiro`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jogo_id: jogoId, tabuleiro }),
  })

  const resultado = await tratarResposta<{ completo: boolean }>(resposta)
  return resultado.completo
}

export async function pedirDica(
  jogoId: string,
  tabuleiro: number[][],
): Promise<Dica> {
  const resposta = await fetch(`${API_URL}/dica`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jogo_id: jogoId, tabuleiro }),
  })

  return tratarResposta<Dica>(resposta)
}

export async function reiniciarDicas(jogoId: string): Promise<void> {
  const resposta = await fetch(`${API_URL}/reiniciar-dicas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jogo_id: jogoId }),
  })

  await tratarResposta<{ dicas_restantes: number }>(resposta)
}
