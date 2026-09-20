import { useCallback, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import Footer from './components/Footer/Footer'
import Menu from './components/Menu/Menu'
import Home from './pages/Home/Home'
import Ranking from './pages/Ranking/Ranking'

export default function App() {
  const [token, setToken] = useState<string | null>(null)
  const [usuario, setUsuario] = useState<string | null>(null)
  const aoEntrar = useCallback((novoToken: string, nome: string) => {
    setToken(novoToken)
    setUsuario(nome)
  }, [])
  const aoSair = useCallback(() => {
    setToken(null)
    setUsuario(null)
  }, [])

  return (
    <div className="flex min-h-screen flex-col">
      <Menu usuario={usuario} aoEntrar={aoEntrar} aoSair={aoSair} />
      <Routes>
        <Route path="/" element={<Home key={token ?? 'visitante'} token={token} />} />
        <Route path="/ranking" element={<Ranking />} />
      </Routes>
      <Footer />
    </div>
  )
}
