import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import NavBar from './components/NavBar'
import PlayList from './pages/PlayList'
import PlayDetail from './pages/PlayDetail'
import SolveList from './pages/SolveList'
import SolveDetail from './pages/SolveDetail'
import Contribute from './pages/Contribute'

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <main style={{ padding: '24px', maxWidth: 960, margin: '0 auto' }}>
        <Routes>
          <Route path="/"              element={<Navigate to="/play" replace />} />
          <Route path="/play"          element={<PlayList />} />
          <Route path="/play/:id"      element={<PlayDetail />} />
          <Route path="/solve"         element={<SolveList />} />
          <Route path="/solve/:id"     element={<SolveDetail />} />
          <Route path="/contribute"    element={<Contribute />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
