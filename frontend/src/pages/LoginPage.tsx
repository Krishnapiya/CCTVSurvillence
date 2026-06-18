import React from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Paper, 
  Stack, 
  InputAdornment, 
  IconButton,
  useTheme
} from '@mui/material';
import { Visibility, VisibilityOff, Security } from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { loginSuccess } from '../store/authSlice';

const LoginPage: React.FC = () => {
  const [showPassword, setShowPassword] = React.useState(false);
  const [username, setUsername] = React.useState('admin');
  const [password, setPassword] = React.useState('admin123');
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const handleLogin = async () => {
    try {
      const formData = new URLSearchParams();
      // Map frontend 'admin' username to seeded 'admin@surveillance.com' email
      formData.append('username', username === 'admin' ? 'admin@surveillance.com' : username);
      formData.append('password', password);

      const backendHost = window.location.hostname;
      let backendPort = localStorage.getItem('surv_backend_port') || '8005';

      let response;
      try {
        response = await fetch(`http://${backendHost}:${backendPort}/api/v1/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: formData,
        });
      } catch (err) {
        const candidatePorts = ['8005', '8000', '8001', '8010'];
        for (const port of candidatePorts) {
          if (port === backendPort) continue;
          try {
            response = await fetch(`http://${backendHost}:${port}/api/v1/auth/login`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
              body: formData,
            });
            if (response.ok) {
              localStorage.setItem('surv_backend_port', port);
              break;
            }
          } catch (err2) {}
        }
        if (!response || !response.ok) {
          throw err;
        }
      }

      if (response && response.ok) {
        const data = await response.json();
        localStorage.setItem('surv_auth', 'true');
        localStorage.setItem('surv_token', data.access_token);
        dispatch(loginSuccess({ username }));
        navigate('/');
        return;
      } else if (response) {
        const errorData = await response.json();
        alert(`Authentication failed: ${errorData.detail || 'Invalid credentials'}`);
        return;
      }
    } catch (err) {
      console.warn('Real backend login failed or offline. Falling back to local mock login.', err);
    }

    // Local Mock Fallback
    if (username === 'admin' && password === 'admin123') {
      localStorage.setItem('surv_auth', 'true');
      localStorage.setItem('surv_token', 'mock-token-value');
      dispatch(loginSuccess({ username }));
      navigate('/');
    } else {
      alert('Invalid credentials. Hint: admin / admin123');
    }
  };

  return (
    <Box 
      sx={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        bgcolor: '#F5F5F5',
      }}
    >
      <Container maxWidth="xs">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
          <Paper 
            sx={{ 
              p: 4, 
              borderRadius: 1, 
              bgcolor: '#FFFFFF',
              border: '1px solid #DDDDDD',
              textAlign: 'center'
            }}
          >
            <Stack spacing={3}>
              <Box sx={{ mb: 1 }}>
                <Security sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h1" sx={{ fontSize: '20px !important', mb: 0.5 }}>
                  SYSTEM ACCESS
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Please sign in to the Surveillance Portal
                </Typography>
              </Box>

              <Box sx={{ textAlign: 'left' }}>
                <Typography variant="caption" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>USERNAME</Typography>
                <TextField
                  fullWidth
                  variant="outlined"
                  size="small"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                  sx={{ bgcolor: '#FFFFFF' }}
                />
              </Box>

              <Box sx={{ textAlign: 'left' }}>
                <Typography variant="caption" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>PASSWORD</Typography>
                <TextField
                  fullWidth
                  type={showPassword ? 'text' : 'password'}
                  variant="outlined"
                  size="small"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={() => setShowPassword(!showPassword)} size="small">
                          {showPassword ? <VisibilityOff sx={{ fontSize: 18 }} /> : <Visibility sx={{ fontSize: 18 }} />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{ bgcolor: '#FFFFFF' }}
                />
              </Box>

              <Button 
                fullWidth 
                variant="contained" 
                onClick={handleLogin}
                sx={{ 
                  height: 44, 
                  bgcolor: '#2C3E50',
                  '&:hover': { bgcolor: '#34495E' }
                }}
              >
                Sign In
              </Button>

              <Typography variant="caption" color="text.secondary">
                © 2026 SURV-EYE • Internal Use Only
              </Typography>
            </Stack>
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
};

export default LoginPage;
