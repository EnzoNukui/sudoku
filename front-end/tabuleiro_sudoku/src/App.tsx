import { useCallback, useEffect, useRef, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import Footer from './components/Footer/Footer'
import Menu from './components/Menu/Menu'
import Home from './pages/Home/Home'
import Ranking from './pages/Ranking/Ranking'
import {
  carregarSessao,
  EVENTO_SESSAO_EXPIRADA,
  removerSessao,
  renovarSessao,
  salvarSessao,
  type Sessao,
} from './services/sudokuApi'

export default function App() {
  const [sessao, setSessao] = useState<Sessao | null>(carregarSessao)
  const [avisoSessao, setAvisoSessao] = useState('')
  const sessaoAtual = useRef(sessao)
  const sessaoAtiva = sessao !== null
  const token = sessao?.token ?? null
  const usuario = sessao?.usuario ?? null

  useEffect(() => {
    sessaoAtual.current = sessao
  }, [sessao])

  useEffect(() => {
    const encerrarSessaoExpirada = () => {
      setSessao(null)
      setAvisoSessao('Sua sessão expirou. Entre novamente com o Google para registrar a partida no ranking.')
    }
    window.addEventListener(EVENTO_SESSAO_EXPIRADA, encerrarSessaoExpirada)
    return () => window.removeEventListener(EVENTO_SESSAO_EXPIRADA, encerrarSessaoExpirada)
  }, [])

  useEffect(() => {
    if (!sessaoAtual.current) return

    let ativo = true
    const renovar = async () => {
      const atual = sessaoAtual.current
      if (!atual) return

      try {
        const novoToken = await renovarSessao(atual.token)
        if (!ativo) return
        const novaSessao = { ...atual, token: novoToken }
        sessaoAtual.current = novaSessao
        salvarSessao(novaSessao)
        setSessao(novaSessao)
      } catch {
        // O evento de 401 já encerra a sessão e exibe o aviso ao usuário.
      }
    }

    void renovar()
    const intervalo = window.setInterval(() => void renovar(), 12 * 60 * 60 * 1000)
    return () => {
      ativo = false
      window.clearInterval(intervalo)
    }
  }, [sessaoAtiva])

  const aoEntrar = useCallback((novoToken: string, nome: string) => {
    const novaSessao = { token: novoToken, usuario: nome }
    salvarSessao(novaSessao)
    setAvisoSessao('')
    setSessao(novaSessao)
  }, [])
  const aoSair = useCallback(() => {
    removerSessao()
    setSessao(null)
  }, [])

  return (
    <div className="flex min-h-screen flex-col">
      <Menu
        usuario={usuario}
        avisoSessao={avisoSessao}
        aoEntrar={aoEntrar}
        aoSair={aoSair}
      />
      <Routes>
        <Route path="/" element={<Home key={token ?? 'visitante'} token={token} />} />
        <Route path="/ranking" element={<Ranking />} />
      </Routes>
      <Footer />
    </div>
  )
}
