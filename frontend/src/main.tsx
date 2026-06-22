import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material'
import { Provider } from 'react-redux'
import { store } from './store'
import { BrowserRouter } from 'react-router-dom'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0b2d5c',
    },
    secondary: {
      main: '#1a4f8b',
    },
    background: {
      default: '#f0f4f8',
      paper: '#ffffff',
    },
    text: {
      primary: '#1e293b',
      secondary: '#475569',
    },
    divider: '#d8e2ec',
    success: { main: '#16a34a' },
    warning: { main: '#d97706' },
    error: { main: '#dc2626' },
    info: { main: '#0284c7' },
  },
  typography: {
    fontFamily: "'Inter', system-ui, sans-serif",
    h1: { fontSize: '1.5rem', fontWeight: 700, color: '#0b2d5c' },
    h2: { fontSize: '1.1rem', fontWeight: 600, color: '#0b2d5c' },
    h3: { fontSize: '0.95rem', fontWeight: 600 },
    body1: { fontSize: '0.875rem' },
    body2: { fontSize: '0.8125rem' },
    button: { textTransform: 'none', fontWeight: 500 },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          '&:hover': { boxShadow: 'none' },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 12px rgba(11, 45, 92, 0.08)',
          border: '1px solid #d8e2ec',
        },
      },
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  </React.StrictMode>,
)
