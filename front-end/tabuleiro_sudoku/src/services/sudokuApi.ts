export type TamanhoSudoku = 4 | 6 | 9
export type Dificuldade = 'facil' | 'medio' | 'dificil'

export type Jogo = {
  jogo_id: string
  tamanho: TamanhoSudoku
  bloco_linhas: number
  bloco_colunas: number
  dificuldade: Dificuldade
  dicas_restantes: number
  ranking_habilitado: boolean
  tabuleiro: number[][]
}

export type Dica = {
  linha: number
  coluna: number
  numero: number
  dicas_restantes: number
}

export type PosicaoRanking = {
  posicao: number
  nome: string
  foto_url: string | null
  tempo_ms: number
  erros: number
  finalizada_em: string
}

const API_URL = import.meta.env.VITE_API_URL
  ?? (import.meta.env.PROD ? '/api' : 'http://127.0.0.1:8000/api')

function cabecalhos(token: string | null): HeadersInit {
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function tratarResposta<T>(resposta: Response): Promise<T> {
  if (!resposta.ok) {
    throw new Error('Não foi possível comunicar com a API do Sudoku.')
  }

  return resposta.json() as Promise<T>
}

export async function criarNovoJogo(
  tamanho: TamanhoSudoku,
  dificuldade: Dificuldade,
  token: string | null,
): Promise<Jogo> {
  const resposta = await fetch(`${API_URL}/novo-jogo`, {
    method: 'POST',
    headers: cabecalhos(token),
    body: JSON.stringify({ tamanho, dificuldade }),
  })

  return tratarResposta<Jogo>(resposta)
}

export async function verificarJogada(
  jogoId: string,
  linha: number,
  coluna: number,
  numero: number,
  token: string | null,
): Promise<{ correta: boolean; erros: number }> {
  const resposta = await fetch(`${API_URL}/verificar-jogada`, {
    method: 'POST',
    headers: cabecalhos(token),
    body: JSON.stringify({ jogo_id: jogoId, linha, coluna, numero }),
  })

  return tratarResposta<{ correta: boolean; erros: number }>(resposta)
}

export async function verificarTabuleiro(
  jogoId: string,
  tabuleiro: number[][],
  token: string | null,
): Promise<{ completo: boolean; ranking_elegivel: boolean }> {
  const resposta = await fetch(`${API_URL}/verificar-tabuleiro`, {
    method: 'POST',
    headers: cabecalhos(token),
    body: JSON.stringify({ jogo_id: jogoId, tabuleiro }),
  })

  return tratarResposta<{ completo: boolean; ranking_elegivel: boolean }>(resposta)
}

export async function pedirDica(
  jogoId: string,
  tabuleiro: number[][],
  token: string | null,
): Promise<Dica> {
  const resposta = await fetch(`${API_URL}/dica`, {
    method: 'POST',
    headers: cabecalhos(token),
    body: JSON.stringify({ jogo_id: jogoId, tabuleiro }),
  })

  return tratarResposta<Dica>(resposta)
}

export async function reiniciarDicas(jogoId: string, token: string | null): Promise<void> {
  const resposta = await fetch(`${API_URL}/reiniciar-dicas`, {
    method: 'POST',
    headers: cabecalhos(token),
    body: JSON.stringify({ jogo_id: jogoId }),
  })

  await tratarResposta<{ dicas_restantes: number }>(resposta)
}

export async function adicionarVida(jogoId: string, token: string | null): Promise<number> {
  const resposta = await fetch(`${API_URL}/adicionar-vida`, {
    method: 'POST',
    headers: cabecalhos(token),
    body: JSON.stringify({ jogo_id: jogoId }),
  })

  const resultado = await tratarResposta<{ limite_erros: number }>(resposta)
  return resultado.limite_erros
}

export async function entrarComGoogle(credential: string): Promise<{ token: string; nome: string; foto_url: string | null }> {
  const resposta = await fetch(`${API_URL}/auth/google`, {
    method: 'POST',
    headers: cabecalhos(null),
    body: JSON.stringify({ credential }),
  })

  return tratarResposta<{ token: string; nome: string; foto_url: string | null }>(resposta)
}

export async function buscarRanking(
  tamanho: TamanhoSudoku,
  dificuldade: Dificuldade,
): Promise<PosicaoRanking[]> {
  const parametros = new URLSearchParams({
    tamanho: String(tamanho),
    dificuldade,
  })
  const resposta = await fetch(`${API_URL}/ranking?${parametros}`)
  return tratarResposta<PosicaoRanking[]>(resposta)
}
