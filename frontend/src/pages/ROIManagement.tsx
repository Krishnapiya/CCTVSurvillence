import React, { useState, useEffect } from 'react';
import { 
  Grid, Paper, Typography, Box, Stack, List, ListItem, ListItemText, Button, Divider, IconButton, TextField, Chip, ListItemIcon
} from '@mui/material';
import { Add, Delete, CheckCircle, Edit, Map as MapIcon, Layers } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import VideoCanvas from '../components/VideoCanvas/VideoCanvas';
import { dataService, CameraProfile, ROI } from '../services/dataService';

const ROIManagement: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const queryParams = new URLSearchParams(location.search);
  const camId = queryParams.get('camId');
  const queryRoiId = queryParams.get('roiId');

  const [camera, setCamera] = useState<CameraProfile | null>(null);
  const [canvasMode, setCanvasMode] = useState<'view' | 'add' | 'edit'>('view');
  const [drawingData, setDrawingData] = useState<any>(null);
  const [roiName, setRoiName] = useState('');
  const [activeRoiId, setActiveRoiId] = useState<string | null>(null);

  useEffect(() => {
    const loadCam = async () => {
      if (!camId) { navigate('/rois'); return; }
      const allCams = await dataService.fetchCameras();
      const cam = allCams.find(c => c.id === camId);
      if (cam) {
        setCamera(cam);
        if (queryRoiId) {
          const targetRoi = cam.rois?.find(r => r.id === queryRoiId);
          if (targetRoi) {
            setCanvasMode('edit');
            setActiveRoiId(targetRoi.id);
            setDrawingData({ type: targetRoi.type, coords: targetRoi.coords, points: targetRoi.points, color: targetRoi.color });
            setRoiName(targetRoi.name);
          } else {
            if (cam.rois && cam.rois.length > 0) {
              setCanvasMode('view');
            } else {
              setCanvasMode('add');
              setRoiName(`${cam.name}_Region_${(cam.rois?.length || 0) + 1}`);
            }
          }
        } else {
          if (cam.rois && cam.rois.length > 0) {
            setCanvasMode('view');
          } else {
            setCanvasMode('add');
            setRoiName(`${cam.name}_Region_${(cam.rois?.length || 0) + 1}`);
          }
        }
      } else {
        navigate('/rois');
      }
    };
    loadCam();
  }, [camId, queryRoiId, navigate]);

  const handleCanvasChange = (roiData: any) => {
    setDrawingData(roiData);
  };

  const handleAddNewROI = () => {
    setCanvasMode('add');
    setActiveRoiId(null);
    setDrawingData(null);
    setRoiName(`${camera?.name}_Region_${(camera?.rois?.length || 0) + 1}`);
  };

  const handleSelectROI = (roi: ROI) => {
    setCanvasMode('edit');
    setActiveRoiId(roi.id);
    setDrawingData({ type: roi.type, coords: roi.coords, points: roi.points, color: roi.color });
    setRoiName(roi.name);
  };

  const handleSaveROI = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!camera) return;
    
    if (canvasMode === 'add' && !drawingData) {
      alert('Please draw a region on the canvas first.');
      return;
    }

    const currentRois = camera.rois || [];
    let updatedRois = [...currentRois];

    if (canvasMode === 'add') {
      const newRoi: ROI = {
        id: `ROI-${Date.now()}`,
        name: roiName || 'New Region',
        color: drawingData?.color || '#2C3E50',
        coords: drawingData?.coords,
        type: drawingData?.type,
        points: drawingData?.points,
        events: [] 
      };
      updatedRois.push(newRoi);
    } else if (canvasMode === 'edit' && activeRoiId) {
      updatedRois = updatedRois.map(r => {
        if (r.id === activeRoiId) {
          return {
            ...r,
            name: roiName || r.name,
            coords: drawingData?.coords || r.coords,
            type: drawingData?.type || r.type,
            points: drawingData?.points || r.points,
          };
        }
        return r;
      });
    }

    const updatedCamera = { ...camera, rois: updatedRois };
    await dataService.updateCamera(updatedCamera);
    setCamera(updatedCamera);
    setCanvasMode('view');
    setActiveRoiId(null);
    alert(`Region saved for ${camera.name}.`);
  };

  const handleDeleteROI = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!camera) return;
    if (window.confirm('Are you sure you want to delete this region?')) {
      const updatedRois = camera.rois.filter(r => r.id !== id);
      const updatedCamera = { ...camera, rois: updatedRois };
      await dataService.updateCamera(updatedCamera);
      setCamera(updatedCamera);
      if (activeRoiId === id) {
        setCanvasMode('view');
        setActiveRoiId(null);
      }
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h1">Region of Interest Configuration</Typography>
          <Typography variant="body2" color="text.secondary">
            Managing zones for: <strong>{camera?.name || 'Loading...'}</strong>
          </Typography>
        </Box>
        <Stack direction="row" spacing={1.5}>
          <Button variant="outlined" onClick={() => navigate('/rois')} size="small">Back to List</Button>
          {(canvasMode === 'add' || canvasMode === 'edit') && (
            <Button 
              variant="contained" 
              onClick={handleSaveROI}
              sx={{ bgcolor: '#2C3E50' }}
              startIcon={<CheckCircle />}
            >
              Save Region
            </Button>
          )}
        </Stack>
      </Box>

      <Grid container spacing={2}>
        <Grid item xs={12} lg={8.5}>
          <Paper sx={{ p: 1, borderRadius: 1, bgcolor: '#FFFFFF', border: '1px solid #DDDDDD' }}>
            <Box sx={{ mb: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 1 }}>
              <Typography variant="caption" fontWeight="bold" color="text.secondary">
                {canvasMode === 'view' ? 'ALL ZONES OVERVIEW' : (canvasMode === 'edit' ? 'EDITING ZONE' : 'DRAWING NEW ZONE')}
              </Typography>
              {canvasMode === 'view' && (
                <Button 
                  size="small" 
                  variant="text" 
                  startIcon={<Add />} 
                  onClick={handleAddNewROI}
                  sx={{ fontSize: '11px' }}
                >
                  Draw New Zone
                </Button>
              )}
            </Box>
            <VideoCanvas 
              cameraId={camera?.id}
              onChange={handleCanvasChange}
              initialRois={camera?.rois || []} 
              focusedRoiId={activeRoiId}
              mode={canvasMode} 
            />
          </Paper>
        </Grid>
        
        <Grid item xs={12} lg={3.5}>
          <Paper sx={{ p: 3, borderRadius: 1, bgcolor: '#FFFFFF', height: '100%', border: '1px solid #DDDDDD', display: 'flex', flexDirection: 'column' }}>
            {(canvasMode === 'add' || canvasMode === 'edit') && (
              <Box sx={{ p: 2, mb: 3, bgcolor: '#f8f9fa', borderRadius: 1, border: '1px solid #ddd' }}>
                <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 1 }}>
                  {canvasMode === 'add' ? 'NEW ZONE DETAILS' : 'EDIT ZONE DETAILS'}
                </Typography>
                <TextField 
                  fullWidth 
                  size="small" 
                  label="Zone Name"
                  value={roiName} 
                  onChange={(e) => setRoiName(e.target.value)} 
                  sx={{ bgcolor: 'white' }}
                />
              </Box>
            )}

            <Typography variant="h3" sx={{ mb: 2, fontSize: '16px !important', display: 'flex', alignItems: 'center', gap: 1 }}>
              <Layers color="primary" sx={{ fontSize: 20 }} /> Active Regions
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <List sx={{ flexGrow: 1, overflowY: 'auto', mb: 2 }}>
              {camera?.rois?.length === 0 ? (
                <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
                  No regions configured yet.
                </Typography>
              ) : (
                camera?.rois?.map(roi => (
                  <ListItem 
                    key={roi.id} 
                    button 
                    selected={activeRoiId === roi.id}
                    onClick={() => handleSelectROI(roi)}
                    sx={{ 
                      borderRadius: 1, 
                      mb: 1, 
                      border: '1px solid #eee',
                      bgcolor: activeRoiId === roi.id ? '#f0f4f8' : 'transparent',
                      '&.Mui-selected': { bgcolor: '#e3f2fd' }
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <Box sx={{ width: 16, height: 16, borderRadius: '50%', bgcolor: roi.color }} />
                    </ListItemIcon>
                    <ListItemText 
                      primary={roi.name} 
                      secondary={roi.type === 'polygon' ? 'Polygon' : 'Rectangle'}
                      primaryTypographyProps={{ fontWeight: 600, fontSize: '13px' }}
                    />
                    <IconButton size="small" onClick={(e) => handleDeleteROI(roi.id, e)} color="error">
                      <Delete sx={{ fontSize: 16 }} />
                    </IconButton>
                  </ListItem>
                ))
              )}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ROIManagement;
