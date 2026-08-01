import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import Engineers from './pages/Engineers'
import Projects from './pages/Projects'
import Chat from './pages/Chat'
import ExecutionStudio from './pages/ExecutionStudio'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="chat" element={<Chat />} />
          <Route path="execution-studio" element={<ExecutionStudio />} />
          <Route path="engineers" element={<Engineers />} />
          <Route path="projects" element={<Projects />} />
          <Route path="documents" element={<Documents />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
