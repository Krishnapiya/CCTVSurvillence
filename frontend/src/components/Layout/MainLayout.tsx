import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Drawer, 
  AppBar, 
  Toolbar, 
  List, 
  Typography, 
  Divider, 
  IconButton, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText,
  Avatar,
  Badge,
  useTheme,
  Chip,
  Menu,
  MenuItem,
  ListItemAvatar,
  Stack
} from '@mui/material';
import { 
  Dashboard as DashboardIcon, 
  Videocam, 
  History, 
  Settings, 
  Notifications, 
  Menu as MenuIcon,
  Map as MapIcon,
  Logout,
  Circle,
  Warning,
  Email,
  AssignmentTurnedIn,
  Science
} from '@mui/icons-material';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { dataService } from '../../services/dataService';

const drawerWidth = 240;

const MainLayout: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    const fetchLogs = async () => {
      const fetched = await dataService.getLogs();
      setLogs(fetched);
    };
    fetchLogs();

    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('surv_auth');
    navigate('/login');
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Camera Management', icon: <Videocam />, path: '/cameras' },
    { text: 'Region of Interest', icon: <MapIcon />, path: '/rois' },
    { text: 'Event Alert Jobs', icon: <AssignmentTurnedIn />, path: '/event-jobs' },
    { text: 'Event Logs', icon: <History />, path: '/logs' },
    { text: 'Settings', icon: <Settings />, path: '/settings' },
  ];

  return (
    <Box sx={{ display: 'flex', bgcolor: '#F5F5F5', minHeight: '100vh' }}>
      <AppBar 
        position="fixed" 
        sx={{ 
          width: `calc(100% - ${drawerWidth}px)`, 
          ml: `${drawerWidth}px`,
          bgcolor: '#FFFFFF',
          borderBottom: '1px solid #DDDDDD',
          color: '#222222'
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between', height: 64 }}>
          <Typography variant="h2" color="primary" sx={{ fontSize: '18px !important' }}>
            {menuItems.find(item => item.path === location.pathname)?.text || 'Surveillance System'}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} size="small">
              <Badge badgeContent={logs.length} color="error">
                <Notifications sx={{ fontSize: 20 }} />
              </Badge>
            </IconButton>
            <Divider orientation="vertical" flexItem sx={{ mx: 1, height: 24, my: 'auto' }} />
            <Stack direction="row" alignItems="center" spacing={1}>
              <Typography variant="body2" fontWeight="500">Admin</Typography>
              <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32, fontSize: 14 }}>AD</Avatar>
            </Stack>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Notifications Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
        PaperProps={{
          sx: {
            width: 320,
            maxHeight: 400,
            borderRadius: 1,
            mt: 1,
            border: '1px solid #DDDDDD'
          }
        }}
      >
        <Box sx={{ p: 1.5, bgcolor: '#f9f9f9' }}>
          <Typography variant="h3" sx={{ fontSize: '14px !important' }}>Recent Alerts</Typography>
        </Box>
        <Divider />
        {logs.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">No new notifications</Typography>
          </Box>
        ) : (
          logs.slice(0, 5).map((log, i) => (
            <MenuItem key={i} sx={{ py: 1, px: 2, borderBottom: '1px solid #f0f0f0' }}>
              <Box sx={{ mr: 2 }}>
                <Warning sx={{ fontSize: 18, color: 'error.main' }} />
              </Box>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{log.event}</Typography>
                <Typography variant="caption" color="text.secondary">{log.timestamp}</Typography>
              </Box>
            </MenuItem>
          ))
        )}
        <MenuItem onClick={() => { setAnchorEl(null); navigate('/logs'); }} sx={{ justifyContent: 'center', py: 1 }}>
          <Typography variant="caption" fontWeight="bold" color="primary">VIEW ALL</Typography>
        </MenuItem>
      </Menu>
      
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            bgcolor: '#FFFFFF',
            borderRight: '1px solid #DDDDDD',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1.5, bgcolor: '#2C3E50', color: 'white' }}>
          <Videocam sx={{ fontSize: 24 }} />
          <Typography variant="h1" sx={{ fontSize: '18px !important', color: 'white' }}>
            SURV-EYE
          </Typography>
        </Box>
        
        <List sx={{ p: 1, mt: 1 }}>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton 
                onClick={() => navigate(item.path)}
                selected={location.pathname === item.path}
                sx={{ 
                  borderRadius: 1,
                  py: 1,
                  '&.Mui-selected': {
                    bgcolor: '#f0f4f8',
                    color: 'primary.main',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.main',
                    }
                  }
                }}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {React.cloneElement(item.icon as React.ReactElement, { sx: { fontSize: 20 } })}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text} 
                  primaryTypographyProps={{ fontSize: '14px', fontWeight: location.pathname === item.path ? 600 : 400 }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        
        <Box sx={{ mt: 'auto', p: 1, borderTop: '1px solid #EEEEEE' }}>
          <ListItemButton onClick={handleLogout} sx={{ borderRadius: 1 }}>
            <ListItemIcon sx={{ minWidth: 36 }}>
              <Logout sx={{ fontSize: 20 }} />
            </ListItemIcon>
            <ListItemText primary="Sign Out" primaryTypographyProps={{ fontSize: '14px' }} />
          </ListItemButton>
        </Box>
      </Drawer>
      
      <Box component="main" sx={{ flexGrow: 1, p: 3, pt: 11 }}>
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;
