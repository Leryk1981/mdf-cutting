import React from 'react'
import { Box, AppBar, Toolbar, Typography, IconButton } from '@mui/material'
import { Menu as MenuIcon, Notifications, AccountCircle } from '@mui/icons-material'
import { useSelector, useDispatch } from 'react-redux'

import Sidebar from './Sidebar.jsx'
import { toggleSidebar } from '../../store/slices/uiSlice.js'

const AppLayout = ({ children }) => {
  const dispatch = useDispatch()
  const { sidebarOpen } = useSelector((state) => state.ui)

  const handleSidebarToggle = () => {
    dispatch(toggleSidebar())
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* App Bar */}
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: 'primary.main',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="toggle sidebar"
            onClick={handleSidebarToggle}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Раскрой MDF Накладок
          </Typography>
          
          <IconButton color="inherit">
            <Notifications />
          </IconButton>
          
          <IconButton color="inherit">
            <AccountCircle />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Sidebar open={sidebarOpen} />

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: 8, // Account for AppBar height
          backgroundColor: 'background.default',
          minHeight: '100vh',
        }}
      >
        {children}
      </Box>
    </Box>
  )
}

export default AppLayout 