import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, Typography, Button, Paper, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Dialog, DialogTitle, 
  DialogContent, DialogActions, FormControl, InputLabel, Select, 
  MenuItem, Stack, Chip, IconButton, TextField, InputAdornment
} from '@mui/material';
import { Add, Map as MapIcon, Delete, Edit, Videocam, Search } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { dataService, CameraProfile, ROI } from '../services/dataService';

interface ROIWithCamera extends ROI {
  camId: string;
  camName: string;
}

const ROIListPage: React.FC = () => {
  const navigate = useNavigate();
  const [cameras, setCameras] = useState<CameraProfile[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedCamId, setSelectedCamId] = useState<string>('');
  const [search, setSearch] = useState('');
  const [cameraFilter, setCameraFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const loadData = async () => {
    const allCams = await dataService.fetchCameras();
    setCameras(allCams);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddNew = () => {
    setIsDialogOpen(true);
  };

  const handleDialogClose = () => {
    setIsDialogOpen(false);
    setSelectedCamId('');
  };

  const handleContinueDraw = () => {
    if (selectedCamId) {
      navigate(`/roi?camId=${selectedCamId}`);
    }
  };

  const handleDeleteROI = (roiId: string, camId: string) => {
    if (window.confirm('Are you sure you want to delete this ROI?')) {
      const cam = cameras.find(c => c.id === camId);
      if (cam) {
        const updatedCam = {
          ...cam,
          rois: cam.rois.filter(r => r.id !== roiId)
        };
        dataService.updateCamera(updatedCam);
        loadData();
      }
    }
  };

  const filteredCameras = useMemo(() => {
    return cameras
      .filter((c) => c.rois && c.rois.length > 0)
      .filter((c) => !cameraFilter || c.id === cameraFilter)
      .map((cam) => ({
        ...cam,
        rois: cam.rois.filter((roi) => {
          if (typeFilter && roi.type !== typeFilter) return false;
          if (search) {
            const q = search.toLowerCase();
            const matchesRoi = roi.name.toLowerCase().includes(q);
            const matchesCam = cam.name.toLowerCase().includes(q);
            if (!matchesRoi && !matchesCam) return false;
          }
          return true;
        }),
      }))
      .filter((cam) => cam.rois.length > 0);
  }, [cameras, search, cameraFilter, typeFilter]);

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box />
        <Button 
          variant="contained" 
          startIcon={<Add />} 
          onClick={handleAddNew}
          sx={{ bgcolor: '#2C3E50' }}
        >
          Add New ROI
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 3, borderRadius: 1, border: '1px solid #DDDDDD' }} elevation={0}>
        <Stack spacing={2}>
          <TextField
            placeholder="Search ROI name or camera..."
            size="small"
            fullWidth
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start"><Search sx={{ fontSize: 20 }} /></InputAdornment>
              ),
            }}
          />
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <FormControl size="small" fullWidth>
              <InputLabel>Camera</InputLabel>
              <Select
                label="Camera"
                value={cameraFilter}
                onChange={(e) => setCameraFilter(e.target.value)}
              >
                <MenuItem value="">All cameras</MenuItem>
                {cameras.filter((c) => c.rois?.length).map((cam) => (
                  <MenuItem key={cam.id} value={cam.id}>{cam.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" fullWidth>
              <InputLabel>ROI Type</InputLabel>
              <Select
                label="ROI Type"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <MenuItem value="">All types</MenuItem>
                <MenuItem value="rect">Rectangle</MenuItem>
                <MenuItem value="polygon">Polygon</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </Stack>
      </Paper>

      <Paper sx={{ width: '100%', mb: 2, border: '1px solid #DDDDDD', borderRadius: 1 }}>
        <TableContainer>
          <Table sx={{ minWidth: 650 }}>
            <TableHead sx={{ bgcolor: '#F9F9F9' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold', pl: 6 }}>ROI Name</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Type</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredCameras.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                    <Typography color="text.secondary">
                      {cameras.filter(c => c.rois && c.rois.length > 0).length === 0
                        ? 'No Regions of Interest defined.'
                        : 'No ROIs match your search filters.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredCameras.map((cam) => (
                  <React.Fragment key={cam.id}>
                    <TableRow sx={{ bgcolor: '#f4f6f8' }}>
                      <TableCell colSpan={3} sx={{ py: 1, pl: 3 }}>
                        <Stack direction="row" alignItems="center" spacing={1}>
                          <Videocam sx={{ fontSize: 18, color: 'primary.main' }} />
                          <Typography variant="body2" fontWeight="bold" color="primary.main">{cam.name}</Typography>
                          <Typography variant="caption" color="text.secondary">({cam.rois.length} Regions)</Typography>
                        </Stack>
                      </TableCell>
                    </TableRow>
                    {cam.rois.map((roi) => (
                      <TableRow key={roi.id} hover>
                        <TableCell sx={{ pl: 6 }}>
                          <Stack direction="row" alignItems="center" spacing={1.5}>
                            <Box sx={{ width: 14, height: 14, borderRadius: '50%', bgcolor: roi.color }} />
                            <Typography variant="body2" fontWeight="500">{roi.name}</Typography>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={roi.type === 'rect' ? 'Rectangle' : roi.type === 'polygon' ? 'Polygon' : 'Zone'} 
                            size="small" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton size="small" onClick={() => navigate(`/roi?camId=${cam.id}&roiId=${roi.id}`)}>
                            <Edit fontSize="small" color="primary" />
                          </IconButton>
                          <IconButton size="small" onClick={() => handleDeleteROI(roi.id, cam.id)}>
                            <Delete fontSize="small" color="error" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </React.Fragment>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Add New ROI Dialog */}
      <Dialog open={isDialogOpen} onClose={handleDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Region of Interest</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Select a camera to draw a new detection zone.
          </Typography>
          <FormControl fullWidth size="small">
            <InputLabel id="camera-select-label">Select Camera</InputLabel>
            <Select
              labelId="camera-select-label"
              value={selectedCamId}
              label="Select Camera"
              onChange={(e) => setSelectedCamId(e.target.value)}
            >
              {cameras.map((cam) => (
                <MenuItem key={cam.id} value={cam.id}>
                  {cam.name} ({cam.location})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleDialogClose} variant="outlined" size="small">Cancel</Button>
          <Button 
            onClick={handleContinueDraw} 
            variant="contained" 
            disabled={!selectedCamId}
            sx={{ bgcolor: '#2C3E50' }}
            size="small"
          >
            Continue to Draw
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ROIListPage;
