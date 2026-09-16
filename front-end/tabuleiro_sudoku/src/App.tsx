import Footer from './components/Footer/Footer'
import Menu from './components/Menu/Menu'
import Home from './pages/Home/Home'

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Menu />
      <Home />
      <Footer />
    </div>
  )
}
