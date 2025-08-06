import React from 'react'
import { 
  Drawer, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText,
  Divider,
  Box,
  Typography,
} from '@mui/material'
import {
  Dashboard,
  ScatterPlot,
  Inventory,
  Folder,
  Assessment,
  Psychology,
  Settings,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'

import { setCurrentPage } from '../../store/slices/uiSlice.js'

const drawerWidth = 240

const menuItems = [
  {
    text: 'Главная',
    icon: <Dashboard />,
    path: '/',
    page: 'dashboard',
  },
  {
    text: 'Оптимизация раскроя',
    icon: <ScatterPlot />,
    path: '/cutting',
    page: 'cutting',
  },
  {
    text: 'Управление материалами',
    icon: <Inventory />,
    path: '/materials',
    page: 'materials',
  },
  {
    text: 'Проекты',
    icon: <Folder />,
    path: '/projects',
    page: 'projects',
  },
  {
    text: 'Отчеты',
    icon: <Assessment />,
    path: '/reports',
    page: 'reports',
  },
  {
    text: 'AI Оптимизация',
    icon: <Psychology />,
    path: '/ai',
    page: 'ai',
  },
]

const Sidebar = ({ open }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  const { currentPage } = useSelector((state) => state.ui)

  const handleNavigation = (path, page) => {
    navigate(path)
    dispatch(setCurrentPage(page))
  }

  const drawer = (
    <Box>
      {/* Logo/Brand */}
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="h6" color="primary.main" fontWeight="bold">
          MDF Cutting
        </Typography>
      </Box>
      
      <Divider />
      
      {/* Navigation Menu */}
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path, item.page)}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.light',
                  color: 'primary.contrastText',
                  '&:hover': {
                    backgroundColor: 'primary.main',
                  },
                },
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: location.pathname === item.path ? 'inherit' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      <Divider />
      
      {/* Settings */}
      <List>
        <ListItem disablePadding>
          <ListItemButton>
            <ListItemIcon>
              <Settings />
            </ListItemIcon>
            <ListItemText primary="Настройки" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  )

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: 'background.paper',
          borderRight: '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      {drawer}
    </Drawer>
  )
}

export default Sidebar 