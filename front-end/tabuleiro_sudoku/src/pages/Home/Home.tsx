import { useCallback, useEffect, useRef, useState } from 'react'
import Content from '../../components/Content/Content'
import Tabuleiro from '../../components/Tabuleiro/Tabuleiro'
import {
  adicionarVida as registrarVidaExtra,
  criarNovoJogo,
  pedirDica,
  reiniciarDicas,
  verificarJogada,
  verificarTabuleiro,
  type Dificuldade,
  type Jogo,
  type TamanhoSudoku,
} from '../../services/sudokuApi'

export default function Home({ token }: { token: string | null }) {
  const [tamanho, setTamanho] = useState<TamanhoSudoku>(9)
  const [dificuldade, setDificuldade] = useState<Dificuldade>('facil')
  const [jogo, setJogo] = useState<Jogo | null>(null)
  const [tabuleiro, setTabuleiro] = useState<number[][]>([])
  const [celulasFixas, setCelulasFixas] = useState<boolean[][]>([])
  const [situacoes, setSituacoes] = useState<(boolean | null)[][]>([])
  const [celulaSelecionada, setCelulaSelecionada] = useState<[number, number] | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [mensagem, setMensagem] = useState('')
  const [erros, setErros] = useState(0)
  const [tempo, setTempo] = useState(0)
  const [finalizado, setFinalizado] = useState(false)
  const [perdeu, setPerdeu] = useState(false)
  const [limiteErros, setLimiteErros] = useState(3)
  const [dicasRestantes, setDicasRestantes] = useState(3)
  const verificando = useRef(false)
  const intervaloTempo = useRef<number | null>(null)
  const tempoAtual = useRef(0)
  const versaoPartida = useRef(0)
  const ultimaConfiguracao = useRef<string | null>(null)
  const classeSelecao =
    'rounded-jogo border border-borda bg-superficie px-3 py-2 text-texto outline-none transition-colors focus:border-borda-forte focus:ring-2 focus:ring-primaria-clara'
  const classeBotao =
    'min-h-12 rounded-jogo border border-borda bg-superficie px-4 py-3 font-medium text-texto transition-colors hover:bg-primaria-clara disabled:opacity-50'

  const carregarJogo = useCallback(async () => {
    const versao = ++versaoPartida.current
    try {
      const novoJogo = await criarNovoJogo(tamanho, dificuldade, token)
      if (versao !== versaoPartida.current) return
      setJogo(novoJogo)
      setTabuleiro(novoJogo.tabuleiro.map((linha) => [...linha]))
      setCelulasFixas(
        novoJogo.tabuleiro.map((linha) => linha.map((numero) => numero !== 0)),
      )
      setSituacoes(
        novoJogo.tabuleiro.map((linha) => linha.map(() => null)),
      )
      setErros(0)
      setTempo(0)
      tempoAtual.current = 0
      setFinalizado(false)
      setPerdeu(false)
      setLimiteErros(3)
      setDicasRestantes(novoJogo.dicas_restantes)
      verificando.current = false
    } catch {
      if (versao !== versaoPartida.current) return
      setJogo(null)
      setMensagem('Não foi possível carregar o jogo. Verifique se a API está ligada.')
    } finally {
      if (versao === versaoPartida.current) setCarregando(false)
    }
  }, [tamanho, dificuldade, token])

  useEffect(() => {
    const configuracao = `${tamanho}:${dificuldade}:${token ?? 'visitante'}`
    if (ultimaConfiguracao.current === configuracao) return
    ultimaConfiguracao.current = configuracao
    void carregarJogo()
  }, [carregarJogo, tamanho, dificuldade, token])

  useEffect(() => {
    if (!jogo || carregando || finalizado) return

    const intervalo = window.setInterval(() => {
      setTempo((atual) => {
        const proximoTempo = atual + 1
        tempoAtual.current = proximoTempo
        return proximoTempo
      })
    }, 1000)
    intervaloTempo.current = intervalo

    return () => {
      window.clearInterval(intervalo)
      if (intervaloTempo.current === intervalo) intervaloTempo.current = null
    }
  }, [jogo, carregando, finalizado])

  function pararTemporizador() {
    if (intervaloTempo.current !== null) {
      window.clearInterval(intervaloTempo.current)
      intervaloTempo.current = null
    }
  }

  function digitarNumero(linha: number, coluna: number, numero: number) {
    if (celulasFixas[linha]?.[coluna] || !jogo || finalizado || verificando.current) {
      return
    }

    const novoTabuleiro = tabuleiro.map((valores) => [...valores])
    novoTabuleiro[linha][coluna] = numero
    setTabuleiro(novoTabuleiro)
    setMensagem('')

    const novasSituacoes = situacoes.map((valores) => [...valores])
    novasSituacoes[linha][coluna] = null
    setSituacoes(novasSituacoes)

    if (numero !== 0) {
      const tabuleiroPreenchido = novoTabuleiro.every((valores) =>
        valores.every((valor) => valor !== 0),
      )
      const tempoFinal = tabuleiroPreenchido ? tempoAtual.current : null

      if (tabuleiroPreenchido) {
        pararTemporizador()
        setFinalizado(true)
      }

      void confirmarNumero(linha, coluna, numero, novoTabuleiro, tempoFinal)
    }
  }

  async function confirmarNumero(
    linha: number,
    coluna: number,
    numero: number,
    novoTabuleiro: number[][],
    tempoFinal: number | null,
  ) {
    if (!jogo || finalizado || verificando.current || celulasFixas[linha]?.[coluna]) return

    verificando.current = true
    const versao = versaoPartida.current

    try {
      const resultado = await verificarJogada(jogo.jogo_id, linha, coluna, numero, token)
      if (versao !== versaoPartida.current) return
      const { correta } = resultado

      const novasSituacoes = situacoes.map((valores) => [...valores])
      novasSituacoes[linha][coluna] = correta
      setSituacoes(novasSituacoes)

      if (!correta) {
        const totalErros = resultado.erros
        setErros(totalErros)
        if (totalErros >= limiteErros) {
          setFinalizado(true)
          setPerdeu(true)
          setMensagem(`Você atingiu o limite de ${limiteErros} erros.`)
        } else {
          if (tempoFinal !== null) setFinalizado(false)
          setMensagem('Número incorreto. Corrija a célula digitando outro número.')
        }
        return
      }

      setMensagem('Número correto!')
      const completo = novoTabuleiro.every((valores, indiceLinha) =>
        valores.every((valor, indiceColuna) =>
          valor !== 0 && (
            celulasFixas[indiceLinha][indiceColuna] ||
            novasSituacoes[indiceLinha][indiceColuna] === true
          ),
        ),
      )

      const verificacao = completo
        ? await verificarTabuleiro(
          jogo.jogo_id,
          novoTabuleiro,
          tempoFinal ?? tempoAtual.current,
          token,
        )
        : null
      if (verificacao?.completo) {
        if (versao !== versaoPartida.current) return
        setFinalizado(true)
        setMensagem(verificacao.ranking_elegivel
          ? 'Parabéns! Você completou o Sudoku. Tempo registrado para o ranking.'
          : 'Parabéns! Você completou o Sudoku.')
      } else if (tempoFinal !== null) {
        setFinalizado(false)
      }
    } catch {
      if (versao !== versaoPartida.current) return
      if (tempoFinal !== null) setFinalizado(false)
      setMensagem('Não foi possível verificar a jogada.')
    } finally {
      if (versao === versaoPartida.current) verificando.current = false
    }
  }

  function apagarSelecionada() {
    if (!celulaSelecionada) {
      setMensagem('Selecione uma célula para apagar.')
      return
    }

    const [linha, coluna] = celulaSelecionada

    if (celulasFixas[linha][coluna]) {
      setMensagem('Os números iniciais não podem ser apagados.')
      return
    }

    digitarNumero(linha, coluna, 0)
  }

  async function tentarDeNovo() {
    if (!jogo) return

    try {
      await reiniciarDicas(jogo.jogo_id, token)
    } catch {
      setMensagem('Não foi possível reiniciar a partida. Verifique se a API está ligada.')
      return
    }

    setTabuleiro(jogo.tabuleiro.map((linha) => [...linha]))
    setCelulasFixas(jogo.tabuleiro.map((linha) => linha.map((numero) => numero !== 0)))
    setSituacoes(jogo.tabuleiro.map((linha) => linha.map(() => null)))
    setCelulaSelecionada(null)
    setErros(0)
    setLimiteErros(3)
    setDicasRestantes(3)
    setTempo(0)
    tempoAtual.current = 0
    setFinalizado(false)
    setPerdeu(false)
    setMensagem('Boa sorte! Tente resolver o mesmo tabuleiro novamente.')
  }

  async function adicionarVida() {
    if (!jogo) return
    try {
      const novoLimite = await registrarVidaExtra(jogo.jogo_id, token)
      setLimiteErros(novoLimite)
      setFinalizado(false)
      setPerdeu(false)
      setMensagem('Você ganhou mais uma chance. Continue de onde parou!')
    } catch {
      setMensagem('Não foi possível adicionar uma vida.')
    }
  }

  async function usarDica() {
    if (!jogo || carregando || finalizado || dicasRestantes === 0 || verificando.current) return

    verificando.current = true
    const versao = versaoPartida.current
    let tempoFinal: number | null = null

    try {
      const dica = await pedirDica(jogo.jogo_id, tabuleiro, token)
      if (versao !== versaoPartida.current) return

      const novoTabuleiro = tabuleiro.map((linha) => [...linha])
      novoTabuleiro[dica.linha][dica.coluna] = dica.numero
      setTabuleiro(novoTabuleiro)

      const novasSituacoes = situacoes.map((linha) => [...linha])
      novasSituacoes[dica.linha][dica.coluna] = true
      setSituacoes(novasSituacoes)

      const novasCelulasFixas = celulasFixas.map((linha) => [...linha])
      novasCelulasFixas[dica.linha][dica.coluna] = true
      setCelulasFixas(novasCelulasFixas)
      setDicasRestantes(dica.dicas_restantes)
      setCelulaSelecionada([dica.linha, dica.coluna])
      setMensagem('Dica aplicada! O número revelado não pode ser alterado.')

      const completo = novoTabuleiro.every((valores, indiceLinha) =>
        valores.every((valor, indiceColuna) =>
          valor !== 0 && (
            novasCelulasFixas[indiceLinha][indiceColuna] ||
            novasSituacoes[indiceLinha][indiceColuna] === true
          ),
        ),
      )

      if (completo) {
        tempoFinal = tempoAtual.current
        pararTemporizador()
        setFinalizado(true)
      }

      const verificacao = completo
        ? await verificarTabuleiro(
          jogo.jogo_id,
          novoTabuleiro,
          tempoFinal ?? tempoAtual.current,
          token,
        )
        : null
      if (verificacao?.completo) {
        if (versao !== versaoPartida.current) return
        pararTemporizador()
        setFinalizado(true)
        setMensagem('Parabéns! Você completou o Sudoku.')
      }
    } catch {
      if (versao !== versaoPartida.current) return
      if (tempoFinal !== null) setFinalizado(false)
      setMensagem('Não foi possível obter a dica ou não há células disponíveis.')
    } finally {
      if (versao === versaoPartida.current) verificando.current = false
    }
  }

  return (
    <Content>
      <section
        className="mb-6 flex flex-col justify-center gap-3 sm:flex-row sm:gap-6"
        aria-label="Configurações do jogo"
      >
          <label className="flex items-center justify-between gap-2 font-bold sm:justify-start">
            Tamanho
            <select
              className={classeSelecao}
              value={tamanho}
              onChange={(evento) => {
                setCarregando(true)
                setMensagem('')
                setCelulaSelecionada(null)
                setTamanho(Number(evento.target.value) as TamanhoSudoku)
              }}
            >
              <option value={4}>4 × 4</option>
              <option value={6}>6 × 6</option>
              <option value={9}>9 × 9</option>
            </select>
          </label>

          <label className="flex items-center justify-between gap-2 font-bold sm:justify-start">
            Dificuldade
            <select
              className={classeSelecao}
              value={dificuldade}
              onChange={(evento) => {
                setCarregando(true)
                setMensagem('')
                setCelulaSelecionada(null)
                setDificuldade(evento.target.value as Dificuldade)
              }}
            >
              <option value="facil">Fácil</option>
              <option value="medio">Médio</option>
              <option value="dificil">Difícil</option>
            </select>
          </label>
      </section>

      <div className="mb-4 text-center">
        <p className="text-sm text-texto-suave">Digite um número para verificar a jogada.</p>
        {jogo && (
          <p className="mt-1 text-sm text-texto-suave">
            {jogo.ranking_habilitado
              ? 'Partida registrada. Dicas e vidas extras a deixam fora do ranking.'
              : 'Partida como visitante: entre com Google para registrar as próximas partidas.'}
          </p>
        )}
        <div className="mt-2 flex justify-center gap-6 font-semibold text-texto" aria-live="polite">
          <span>Tempo: {String(Math.floor(tempo / 60)).padStart(2, '0')}:{String(tempo % 60).padStart(2, '0')}</span>
          <span>Erros: {erros}/{limiteErros}</span>
        </div>
      </div>

      <section className="grid items-start gap-6 md:grid-cols-[minmax(0,1fr)_minmax(280px,620px)_minmax(0,1fr)]">
          <div className="min-w-0 md:col-start-2">
            {carregando && (
              <p className="py-8 text-center text-texto-suave">Carregando tabuleiro...</p>
            )}

            {!carregando && jogo && (
              <Tabuleiro
                valores={tabuleiro}
                celulasFixas={celulasFixas}
                situacoes={situacoes}
                bloqueado={finalizado}
                blocoLinhas={jogo.bloco_linhas}
                blocoColunas={jogo.bloco_colunas}
                celulaSelecionada={celulaSelecionada}
                aoSelecionar={(linha, coluna) => setCelulaSelecionada([linha, coluna])}
                aoDigitar={digitarNumero}
              />
            )}

            {mensagem && (
              <p className="mt-3 min-h-6 text-center font-semibold text-primaria-escura" role="status">
                {mensagem}
              </p>
            )}

            {perdeu && (
              <div className="mt-4 flex flex-wrap justify-center gap-3">
                <button className={classeBotao} type="button" onClick={() => void tentarDeNovo()}>
                  Tentar de novo
                </button>
                <button className={`${classeBotao} bg-primaria-clara`} type="button" onClick={() => void adicionarVida()}>
                  Adicionar uma vida
                </button>
              </div>
            )}
          </div>

          <aside
            className="grid grid-cols-3 gap-3 md:col-start-3 md:w-full md:max-w-[170px] md:grid-cols-1"
            aria-label="Controles do jogo"
          >
            <button
              className={`${classeBotao} bg-primaria-clara font-bold text-primaria-escura`}
              type="button"
              onClick={() => {
                setCarregando(true)
                setMensagem('')
                setCelulaSelecionada(null)
                void carregarJogo()
              }}
            >
              Novo jogo
            </button>
            <button className={classeBotao} type="button" onClick={apagarSelecionada} disabled={finalizado}>
              Apagar
            </button>
            <button
              className={classeBotao}
              type="button"
              disabled={carregando || finalizado || dicasRestantes === 0 || !jogo}
              onClick={() => void usarDica()}
            >
              Dica ({dicasRestantes})
            </button>
          </aside>
      </section>
    </Content>
  )
}
