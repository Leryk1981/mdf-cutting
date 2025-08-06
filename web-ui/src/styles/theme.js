import { createTheme } from '@mui/material/styles'

// Цветовая схема из ui_shablon/css/app.css
export const theme = createTheme({
  palette: {
    primary: {
      main: '#607D8B', // Основной синий (btn-clo)
      light: '#90A4AE',
      dark: '#455A64',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#90A4AE', // Вторичный серый
      light: '#B0BEC5',
      dark: '#546E7A',
      contrastText: '#ffffff',
    },
    success: {
      main: '#2e7d32', // Зеленый (button-success)
      light: '#4CAF50',
      dark: '#1B5E20',
      contrastText: '#ffffff',
    },
    error: {
      main: '#c62828', // Красный (button-danger)
      light: '#EF5350',
      dark: '#B71C1C',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#8C7601', // Золотой (gold-cell)
      light: '#FF9800',
      dark: '#E65100',
      contrastText: '#ffffff',
    },
    info: {
      main: '#607D8B',
      light: '#90A4AE',
      dark: '#455A64',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f5f5f5', // Светло-серый фон
      paper: '#ffffff',
    },
    text: {
      primary: '#263238', // Основной текст
      secondary: '#546E7A',
    },
    divider: '#CFD8DC', // Серая граница
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 300,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 300,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 400,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 400,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 400,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 2px 4px rgba(0,0,0,0.1)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
  },
}) 