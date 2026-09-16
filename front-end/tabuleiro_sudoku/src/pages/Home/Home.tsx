import { useCallback, useEffect, useState } from 'react'
import Content from '../../components/Content/Content'
import Footer from '../../components/Footer/Footer'
import Header from '../../components/Header/Header'
import Tabuleiro from '../../components/Tabuleiro/Tabuleiro'
import {
  criarNovoJogo,
  verificarJogada,
  verificarTabuleiro,
  type Dificuldade,
  type Jogo,
  type TamanhoSudoku,
} from '../../services/sudokuApi'

function Home() {
  const [tamanho, setTamanho] = useState<TamanhoSudoku>(9)
  const [dificuldade, setDificuldade] = useState<Dificuldade>('facil')
  const [jogo, setJogo] = useState<Jogo | null>(null)
  const [tabuleiro, setTabuleiro] = useState<number[][]>([])
  const [celulasFixas, setCelulasFixas] = useState<boolean[][]>([])
  const [celulaSelecionada, setCelulaSelecionada] = useState<[number, number] | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [mensagem, setMensagem] = useState('')

  const carregarJogo = useCallback(async () => {
    try {
      const novoJogo = await criarNovoJogo(tamanho, dificuldade)
      setJogo(novoJogo)
      setTabuleiro(novoJogo.tabuleiro.map((linha) => [...linha]))
      setCelulasFixas(
        novoJogo.tabuleiro.map((linha) => linha.map((numero) => numero !== 0)),
      )
    } catch {
      setJogo(null)
      setMensagem('Não foi possível carregar o jogo. Verifique se a API está ligada.')
    } finally {
      setCarregando(false)
    }
  }, [tamanho, dificuldade])

  useEffect(() => {
    void carregarJogo()
  }, [carregarJogo])

  async function digitarNumero(linha: number, coluna: number, numero: number) {
    if (celulasFixas[linha]?.[coluna]) {
      return
    }

    if (numero !== 0) {
      try {
        const valida = await verificarJogada(tabuleiro, linha, coluna, numero)

        if (!valida) {
          setMensagem('Esse número não pode ser colocado nessa posição.')
          return
        }
      } catch {
        setMensagem('Não foi possível verificar a jogada.')
        return
      }
    }

    const novoTabuleiro = tabuleiro.map((valores) => [...valores])
    novoTabuleiro[linha][coluna] = numero
    setTabuleiro(novoTabuleiro)
    setMensagem('')

    if (novoTabuleiro.every((valores) => valores.every((valor) => valor !== 0))) {
      const completo = await verificarTabuleiro(novoTabuleiro)
      setMensagem(completo ? 'Parabéns! Você completou o Sudoku.' : 'Ainda existem erros no tabuleiro.')
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

    void digitarNumero(linha, coluna, 0)
  }

  return (
    <div className="aplicacao">
      <Header />

      <Content>
        <section className="configuracoes" aria-label="Configurações do jogo">
          <label>
            Tamanho
            <select
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

          <label>
            Dificuldade
            <select
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

        <section className="area-jogo">
          <div className="area-tabuleiro">
            {carregando && <p>Carregando tabuleiro...</p>}

            {!carregando && jogo && (
              <Tabuleiro
                valores={tabuleiro}
                celulasFixas={celulasFixas}
                blocoLinhas={jogo.bloco_linhas}
                blocoColunas={jogo.bloco_colunas}
                celulaSelecionada={celulaSelecionada}
                aoSelecionar={(linha, coluna) => setCelulaSelecionada([linha, coluna])}
                aoDigitar={(linha, coluna, numero) => void digitarNumero(linha, coluna, numero)}
              />
            )}

            {mensagem && <p className="mensagem" role="status">{mensagem}</p>}
          </div>

          <aside className="controles" aria-label="Controles do jogo">
            <button
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
            <button type="button" onClick={apagarSelecionada}>
              Apagar
            </button>
            <button type="button" disabled title="A dica será implementada na próxima etapa">
              Dica
            </button>
          </aside>
        </section>
      </Content>

      <Footer />
    </div>
  )
}

export default Home
