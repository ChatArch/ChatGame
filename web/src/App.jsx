import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import NavBar from './components/NavBar'
import Solver from './pages/Solver'
import Library from './pages/Library'
import LibraryDetail from './pages/LibraryDetail'
import Contribute from './pages/Contribute'

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <main style={{ padding: '24px', maxWidth: 960, margin: '0 auto' }}>
        <Routes>
          <Route path="/"              element={<Navigate to="/solver" replace />} />
          <Route path="/solver"        element={<Solver />} />
          <Route path="/library"       element={<Library />} />
          <Route path="/library/:id"   element={<LibraryDetail />} />
          <Route path="/contribute"    element={<Contribute />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
