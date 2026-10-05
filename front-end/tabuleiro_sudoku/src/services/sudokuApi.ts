export type TamanhoSudoku = 4 | 6 | 9
export type Dificuldade = 'facil' | 'medio' | 'dificil'

export type Sessao = {
  token: string
  usuario: string
}

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
const CHAVE_SESSAO = 'sudoku_sessao'
export const EVENTO_SESSAO_EXPIRADA = 'sudoku-sessao-expirada'

function tokenExpirado(token: string) {
  try {
    const [conteudo] = token.split('.')
    if (!conteudo) return true

    const base64 = conteudo.replace(/-/g, '+').replace(/_/g, '/')
    const base64Completo = base64.padEnd(base64.length + (-base64.length % 4), '=')
    const dados = JSON.parse(atob(base64Completo)) as { exp?: number }
    return typeof dados.exp !== 'number' || dados.exp <= Date.now() / 1000
  } catch {
    return true
  }
}

export function carregarSessao(): Sessao | null {
  try {
    const sessao = localStorage.getItem(CHAVE_SESSAO)
    if (!sessao) return null

    const dados = JSON.parse(sessao) as Partial<Sessao>
    if (
      typeof dados.token !== 'string'
      || typeof dados.usuario !== 'string'
      || tokenExpirado(dados.token)
    ) {
      localStorage.removeItem(CHAVE_SESSAO)
      return null
    }

    return { token: dados.token, usuario: dados.usuario }
  } catch {
    localStorage.removeItem(CHAVE_SESSAO)
    return null
  }
}

export function salvarSessao(sessao: Sessao) {
  localStorage.setItem(CHAVE_SESSAO, JSON.stringify(sessao))
}

export function removerSessao(notificar = false) {
  localStorage.removeItem(CHAVE_SESSAO)
  if (notificar) window.dispatchEvent(new Event(EVENTO_SESSAO_EXPIRADA))
}

function cabecalhos(token: string | null): HeadersInit {
  const tokenValido = token && !tokenExpirado(token) ? token : null
  if (token && !tokenValido) removerSessao(true)

  return {
    'Content-Type': 'application/json',
    ...(tokenValido ? { Authorization: `Bearer ${tokenValido}` } : {}),
  }
}

async function tratarResposta<T>(resposta: Response): Promise<T> {
  if (!resposta.ok) {
    if (resposta.status === 401) removerSessao(true)
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
  tempoSegundos: number,
  token: string | null,
): Promise<{ completo: boolean; ranking_elegivel: boolean }> {
  const resposta = await fetch(`${API_URL}/verificar-tabuleiro`, {
    method: 'POST',
    headers: cabecalhos(token),
    body: JSON.stringify({ jogo_id: jogoId, tabuleiro, tempo_segundos: tempoSegundos }),
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
