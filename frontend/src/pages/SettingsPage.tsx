import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Stack, Switch, FormControlLabel, Divider, Button, TextField, Avatar, Grid, Dialog, DialogTitle, DialogContent, DialogActions, Alert, Snackbar
} from '@mui/material';
import { 
  Notifications, 
  Security, 
  Language, 
  Palette, 
  Storage,
  Save,
  LockOpen
} from '@mui/icons-material';
import { motion } from 'framer-motion';

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState({
    audioAlerts: true,
    emailNotifications: false,
    darkMode: false,
    autoSave: true
  });

  const [pwdDialogOpen, setPwdDialogOpen] = useState(false);
  const [pwdData, setPwdData] = useState({ current: '', new: '', confirm: '' });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Load settings on mount
  useEffect(() => {
    const saved = localStorage.getItem('surv_settings');
    if (saved) {
      setSettings(JSON.parse(saved));
    }
  }, []);

  const handleSaveSettings = () => {
    localStorage.setItem('surv_settings', JSON.stringify(settings));
    setSnackbar({ open: true, message: 'Settings updated successfully.', severity: 'success' });
  };

  const handlePwdChange = () => {
    if (pwdData.new !== pwdData.confirm) {
      setSnackbar({ open: true, message: 'Passwords do not match.', severity: 'error' });
      return;
    }
    if (pwdData.current !== 'admin123') {
      setSnackbar({ open: true, message: 'Current password incorrect.', severity: 'error' });
      return;
    }
    setSnackbar({ open: true, message: 'Password changed successfully.', severity: 'success' });
    setPwdDialogOpen(false);
    setPwdData({ current: '', new: '', confirm: '' });
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h1">Account & System Settings</Typography>
        <Typography variant="body2" color="text.secondary">Configure your user profile and system notification preferences</Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, borderRadius: 1, bgcolor: '#FFFFFF', textAlign: 'center' }}>
            <Avatar sx={{ width: 80, height: 80, mx: 'auto', mb: 2, bgcolor: 'primary.main', fontSize: '1.5rem' }}>AD</Avatar>
            <Typography variant="h2" sx={{ fontSize: '18px !important' }}>Admin User</Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 3 }}>SYSTEM ADMINISTRATOR</Typography>
            <Divider sx={{ mb: 3 }} />
            <Button 
              variant="outlined" 
              fullWidth 
              size="small" 
              startIcon={<LockOpen sx={{ fontSize: 16 }} />}
              onClick={() => setPwdDialogOpen(true)}
              sx={{ fontSize: '12px' }}
            >
              Update Password
            </Button>
          </Paper>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, borderRadius: 1, bgcolor: '#FFFFFF' }}>
            <Stack spacing={4}>
              <Box>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                  <Notifications color="primary" sx={{ fontSize: 20 }} />
                  <Typography variant="h3" sx={{ fontSize: '16px !important' }}>Alerts & Notifications</Typography>
                </Stack>
                <Divider sx={{ mb: 2 }} />
                <Stack spacing={1}>
                  <FormControlLabel 
                    control={<Switch size="small" checked={settings.audioAlerts} onChange={(e) => setSettings({...settings, audioAlerts: e.target.checked})} />} 
                    label={<Typography variant="body2">Audible Alert on Violation</Typography>} 
                  />
                  <FormControlLabel 
                    control={<Switch size="small" checked={settings.emailNotifications} onChange={(e) => setSettings({...settings, emailNotifications: e.target.checked})} />} 
                    label={<Typography variant="body2">Send Email Reports</Typography>} 
                  />
                </Stack>
              </Box>

              <Box>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                  <Palette color="primary" sx={{ fontSize: 20 }} />
                  <Typography variant="h3" sx={{ fontSize: '16px !important' }}>System Preferences</Typography>
                </Stack>
                <Divider sx={{ mb: 2 }} />
                <Stack spacing={1}>
                  <FormControlLabel 
                    control={<Switch size="small" checked={settings.darkMode} onChange={(e) => setSettings({...settings, darkMode: e.target.checked})} />} 
                    label={<Typography variant="body2">Enable Dark Mode (Legacy)</Typography>} 
                  />
                  <FormControlLabel 
                    control={<Switch size="small" checked={settings.autoSave} onChange={(e) => setSettings({...settings, autoSave: e.target.checked})} />} 
                    label={<Typography variant="body2">Auto-save Modifications</Typography>} 
                  />
                </Stack>
              </Box>

              <Box sx={{ pt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button 
                  variant="contained" 
                  startIcon={<Save />} 
                  onClick={handleSaveSettings}
                  sx={{ bgcolor: '#2C3E50' }}
                >
                  Save All Changes
                </Button>
              </Box>
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      <Dialog open={pwdDialogOpen} onClose={() => setPwdDialogOpen(false)} PaperProps={{ sx: { borderRadius: 1, minWidth: 350 } }}>
        <DialogTitle sx={{ fontWeight: 700, bgcolor: '#f8f9fa', borderBottom: '1px solid #ddd' }}>Change Access Password</DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Stack spacing={2.5}>
            <Box>
              <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 0.5 }}>CURRENT PASSWORD</Typography>
              <TextField type="password" fullWidth size="small" value={pwdData.current} onChange={(e) => setPwdData({...pwdData, current: e.target.value})} />
            </Box>
            <Divider />
            <Box>
              <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 0.5 }}>NEW PASSWORD</Typography>
              <TextField type="password" fullWidth size="small" value={pwdData.new} onChange={(e) => setPwdData({...pwdData, new: e.target.value})} />
            </Box>
            <Box>
              <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 0.5 }}>CONFIRM NEW PASSWORD</Typography>
              <TextField type="password" fullWidth size="small" value={pwdData.confirm} onChange={(e) => setPwdData({...pwdData, confirm: e.target.value})} />
            </Box>
          </Stack>
        </DialogContent>
        <Divider />
        <DialogActions sx={{ p: 2, bgcolor: '#f8f9fa' }}>
          <Button onClick={() => setPwdDialogOpen(false)} color="inherit" size="small">Cancel</Button>
          <Button onClick={handlePwdChange} variant="contained" size="small" sx={{ bgcolor: '#2C3E50' }}>Update Security</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={() => setSnackbar({...snackbar, open: false})}>
        <Alert severity={snackbar.severity} variant="filled" sx={{ width: '100%', borderRadius: 1 }}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
};

export default SettingsPage;
