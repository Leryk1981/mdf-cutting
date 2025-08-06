import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'

import AppLayout from './components/layout/AppLayout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import CuttingOptimization from './pages/CuttingOptimization.jsx'
import Optimization from './pages/Optimization.jsx'
import MaterialsManagement from './pages/MaterialsManagement.jsx'
import Projects from './pages/Projects.jsx'
import Reports from './pages/Reports.jsx'
import AIOptimization from './pages/AIOptimization.jsx'

function App() {
  return (
    <Box sx={{ display: 'flex' }}>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cutting" element={<CuttingOptimization />} />
          <Route path="/optimization" element={<Optimization />} />
          <Route path="/materials" element={<MaterialsManagement />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/ai" element={<AIOptimization />} />
        </Routes>
      </AppLayout>
    </Box>
  )
}

export default App 