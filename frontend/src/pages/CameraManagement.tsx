import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Stack, 
  Paper,
  Chip, 
  IconButton,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { Add, Search, Delete, Edit, Videocam, PlayCircleFilled, Map as MapIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { dataService, CameraProfile, getBackendBaseUrl } from '../services/dataService';

const CameraManagement: React.FC = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [cameras, setCameras] = useState<CameraProfile[]>([]);
  const [formData, setFormData] = useState({ id: '', name: '', location: '', ip: '' });
  const [isEditing, setIsEditing] = useState(false);
  const [search, setSearch] = useState('');
  const [liveCamera, setLiveCamera] = useState<CameraProfile | null>(null);

  const loadCameras = async () => {
    try {
      const cams = await dataService.fetchCameras();
      setCameras(cams);
    } catch (err) {
      console.error('Failed to load cameras:', err);
    }
  };

  useEffect(() => {
    loadCameras();
    // Poll camera statuses periodically
    const interval = setInterval(loadCameras, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenAdd = () => {
    setIsEditing(false);
    setFormData({ id: '', name: '', location: '', ip: '' });
    setOpen(true);
  };

  const handleOpenEdit = (cam: CameraProfile) => {
    setIsEditing(true);
    setFormData({ id: cam.id, name: cam.name, location: cam.location, ip: cam.ip });
    setOpen(true);
  };

  const handleSaveCamera = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!formData.name) return;

    try {
      if (isEditing) {
        const existingCam = cameras.find(c => c.id === formData.id);
        if (existingCam) {
          await dataService.updateCamera({
            ...existingCam,
            name: formData.name,
            location: formData.location,
            ip: formData.ip
          });
        }
      } else {
        await dataService.addCamera({
          id: `CAM-${Date.now()}`,
          name: formData.name,
          location: formData.location,
          ip: formData.ip,
          status: 'active',
          rois: []
        });
      }
      await loadCameras();
      setOpen(false);
    } catch (err) {
      console.error('Error saving camera:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this camera profile?")) return;
    try {
      await dataService.deleteCamera(id);
      await loadCameras();
    } catch (err) {
      console.error('Error deleting camera:', err);
    }
  };

  const filteredCameras = cameras.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) || 
    c.location.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <Button 
          variant="contained" 
          startIcon={<Add />} 
          onClick={handleOpenAdd}
          sx={{ bgcolor: '#2C3E50', fontWeight: 600 }}
        >
          Add Profile
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 3, borderRadius: 1, border: '1px solid #DDDDDD' }} elevation={0}>
        <TextField
          fullWidth
          size="small"
          placeholder="Filter by profile name, location or ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start"><Search sx={{ fontSize: 20 }} /></InputAdornment>
            ),
          }}
        />
      </Paper>

      <TableContainer component={Paper} sx={{ borderRadius: 1, border: '1px solid #DDDDDD' }} elevation={0}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead sx={{ bgcolor: '#F8F9FA' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', py: 1.5, pl: 3 }}>PROFILE NAME</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>LOCATION</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>IP/RTSP</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>STATUS</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }} align="right">ACTIONS</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCameras.map((cam) => (
              <TableRow 
                key={cam.id} 
                className="gov-table-row"
              >
                <TableCell sx={{ pl: 3 }}>
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Box sx={{ p: 1, bgcolor: '#f0f4f8', borderRadius: 1 }}>
                      <Videocam sx={{ fontSize: 18, color: 'primary.main' }} />
                    </Box>
                    <Box>
                      <Typography variant="body2" fontWeight="600">{cam.name}</Typography>
                      <Typography variant="caption" color="text.secondary">{cam.id}</Typography>
                    </Box>
                  </Stack>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{cam.location}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '12px' }}>{cam.ip}</Typography>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={cam.status === 'active' ? 'ONLINE' : 'OFFLINE'} 
                    size="small" 
                    sx={{ 
                      fontSize: '9px', 
                      height: 18,
                      fontWeight: 'bold',
                      bgcolor: cam.status === 'active' ? '#e8f5e9' : '#ffebee',
                      color: cam.status === 'active' ? '#2e7d32' : '#c62828',
                      border: '1px solid currentColor'
                    }} 
                  />
                </TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button 
                      size="small" 
                      variant="contained" 
                      startIcon={<PlayCircleFilled sx={{ fontSize: 16 }} />}
                      onClick={(e) => { e.stopPropagation(); setLiveCamera(cam); }}
                      sx={{ 
                        fontSize: '11px', 
                        height: 26, 
                        borderRadius: 0.5, 
                        bgcolor: '#2e7d32', 
                        fontWeight: 600,
                        '&:hover': { bgcolor: '#1b5e20' } 
                      }}
                    >
                      Live
                    </Button>
                    <Button 
                      size="small" 
                      variant="outlined" 
                      startIcon={<MapIcon sx={{ fontSize: 16 }} />}
                      onClick={(e) => { e.stopPropagation(); navigate(`/roi?camId=${cam.id}`); }}
                      sx={{ fontSize: '11px', height: 26, borderRadius: 0.5, fontWeight: 600 }}
                    >
                      ROI
                    </Button>
                    <IconButton size="small" color="primary" onClick={() => handleOpenEdit(cam)} title="Edit Profile">
                      <Edit sx={{ fontSize: 18 }} />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(cam.id)} color="error" title="Delete Profile">
                      <Delete sx={{ fontSize: 18 }} />
                    </IconButton>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {filteredCameras.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                  <Typography variant="body2" color="text.secondary">No camera profiles found.</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)} PaperProps={{ sx: { borderRadius: 1, minWidth: 400 } }}>
        <form onSubmit={handleSaveCamera}>
          <DialogTitle sx={{ fontWeight: 700, bgcolor: '#f8f9fa', borderBottom: '1px solid #ddd' }}>
            {isEditing ? 'Edit Camera Profile' : 'Register New Profile'}
          </DialogTitle>
          <DialogContent sx={{ mt: 2 }}>
            <Stack spacing={2.5}>
              <Box>
                <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 0.5 }}>PROFILE NAME</Typography>
                <TextField 
                  fullWidth 
                  size="small" 
                  autoFocus
                  value={formData.name} 
                  onChange={(e) => setFormData({...formData, name: e.target.value})} 
                  placeholder="e.g. Area 51 Entrance" 
                />
              </Box>
              <Box>
                <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 0.5 }}>LOCATION</Typography>
                <TextField 
                  fullWidth 
                  size="small" 
                  value={formData.location} 
                  onChange={(e) => setFormData({...formData, location: e.target.value})} 
                  placeholder="e.g. Block-B, Floor 2" 
                />
              </Box>
              <Box>
                <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 0.5 }}>IP ADDRESS / RTSP URL</Typography>
                <TextField 
                  fullWidth 
                  size="small" 
                  value={formData.ip} 
                  onChange={(e) => setFormData({...formData, ip: e.target.value})} 
                  placeholder="rtsp://admin:pwd@192.168..." 
                />
              </Box>
            </Stack>
          </DialogContent>
          <Divider />
          <DialogActions sx={{ p: 2, bgcolor: '#f8f9fa' }}>
            <Button onClick={() => setOpen(false)} color="inherit" size="small">Cancel</Button>
            <Button type="submit" variant="contained" size="small" sx={{ bgcolor: '#2C3E50' }}>Save Profile</Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Live Stream Dialog */}
      <Dialog 
        open={!!liveCamera} 
        onClose={() => setLiveCamera(null)} 
        PaperProps={{ sx: { borderRadius: 1.5, minWidth: 640, overflow: 'hidden' } }}
      >
        <DialogTitle sx={{ fontWeight: 700, bgcolor: '#2C3E50', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1.5 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ fontSize: '16px' }}>Live Feed: {liveCamera?.name}</Typography>
          <Chip 
            label="LIVE" 
            color="success" 
            size="small" 
            sx={{ 
              fontWeight: 'bold', 
              fontSize: '10px',
              height: 20,
              animation: 'pulse 1.5s infinite',
              '@keyframes pulse': {
                '0%': { transform: 'scale(0.95)', opacity: 0.8 },
                '50%': { transform: 'scale(1.05)', opacity: 1 },
                '100%': { transform: 'scale(0.95)', opacity: 0.8 }
              }
            }}
          />
        </DialogTitle>
        <DialogContent sx={{ p: 0, bgcolor: '#000', display: 'flex', justifyContent: 'center', alignItems: 'center', aspectRatio: '16/9' }}>
          {liveCamera && (
            <Box
              component="img"
              src={`${getBackendBaseUrl()}/api/v1/cameras/${liveCamera.id}/stream`}
              alt="Live Camera Stream"
              sx={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          )}
        </DialogContent>
        <DialogActions sx={{ p: 1.5, bgcolor: '#f8f9fa' }}>
          <Button onClick={() => setLiveCamera(null)} variant="contained" size="small" sx={{ bgcolor: '#2C3E50', fontWeight: 600 }}>
            Close Feed
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CameraManagement;
