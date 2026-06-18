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
      main: '#2C3E50', // Dark Blue/Grey Government Style
    },
    secondary: {
      main: '#3A6EA5',
    },
    background: {
      default: '#F5F5F5', // Soft light background
      paper: '#FFFFFF',
    },
    text: {
      primary: '#222222',
      secondary: '#555555',
    },
    divider: '#DDDDDD',
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontSize: '22px', fontWeight: 600 },
    h2: { fontSize: '18px', fontWeight: 600 },
    h3: { fontSize: '16px', fontWeight: 600 },
    body1: { fontSize: '14px' },
    body2: { fontSize: '14px' },
    button: { textTransform: 'none', fontWeight: 500 },
  },
  shape: {
    borderRadius: 4, // 4px radius as per guidelines
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          border: '1px solid #DDDDDD',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          borderBottom: '1px solid #DDDDDD',
          backgroundColor: '#FFFFFF',
          color: '#222222',
        },
      },
    },
  },
});

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
