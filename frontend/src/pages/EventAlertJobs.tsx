import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Paper, Grid, Stack, Button, Divider, Select, MenuItem, TextField, ToggleButton, ToggleButtonGroup, List, ListItem, ListItemIcon, ListItemText, Alert, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, IconButton, Accordion, AccordionSummary, AccordionDetails,
  Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Switch, Checkbox, Radio
} from '@mui/material';
import { CheckCircle, Videocam, AccessTime, CalendarMonth, Save, ListAlt, Info, Warning, Delete, AssignmentTurnedIn, ExpandMore, Edit, Map as MapIcon, ToggleOn, Add, Check } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { dataService, CameraProfile, ROI, AlertJob } from '../services/dataService';

const timePresets = [
  { label: 'Full Day (24h)', start: '00:00', end: '23:59' },
  { label: 'Night Shift', start: '20:00', end: '06:00' },
];

const dayOptions = [
  { label: 'Mon', value: 'Monday' },
  { label: 'Tue', value: 'Tuesday' },
  { label: 'Wed', value: 'Wednesday' },
  { label: 'Thu', value: 'Thursday' },
  { label: 'Fri', value: 'Friday' },
  { label: 'Sat', value: 'Saturday' },
  { label: 'Sun', value: 'Sunday' },
];

const eventTypes = [
  { name: 'Fire Detection' },
  { name: 'Smoke Detection' },
  { name: 'Human Detection' },
  { name: 'Mobile Phone Detection' },
  { name: 'Bag Detection' },
  { name: 'Bench Detection' },
  { name: 'Fainting Detection' },
  { name: 'Fight Detection' },
  { name: 'Smoking Detection' },
];


const EventAlertJobs: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const queryParams = new URLSearchParams(location.search);
  const targetsStr = queryParams.get('targets');

  // Parse targets from URL: format "camId:roiId,camId2:roiId2"
  const targets = targetsStr ? targetsStr.split(',').map(t => {
    const [camId, roiId] = t.split(':');
    return { camId, roiId };
  }) : [];

  const [cameras, setCameras] = useState<CameraProfile[]>([]);
  const [alertJobs, setAlertJobs] = useState<AlertJob[]>([]);
  const [jobName, setJobName] = useState('');
  const [selectedEventTypes, setSelectedEventTypes] = useState<string[]>(['Fire Detection']);
  const [timeMode, setTimeMode] = useState<'preset' | 'manual'>('preset');
  const [selectedPreset, setSelectedPreset] = useState(0);
  const [manualTimes, setManualTimes] = useState({ start: '00:00', end: '23:59' });
  const [dayMode, setDayMode] = useState<'all' | 'custom'>('all');
  const [selectedDays, setSelectedDays] = useState<string[]>(dayOptions.map(d => d.value));

  // Confirmation Dialog State
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmData, setConfirmData] = useState<{ type: 'job' | 'cam', jobId: string, camId?: string, title: string, text: string } | null>(null);

  // Deploy Dialog State
  const [deployDialogOpen, setDeployDialogOpen] = useState(false);
  const [selectedDeployTargets, setSelectedDeployTargets] = useState<{ camId: string, roiId: string }[]>([]);

  // Rename Dialog State
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [renameJobId, setRenameJobId] = useState<string | null>(null);
  const [newJobName, setNewJobName] = useState('');

  const refreshData = useCallback(async () => {
    const fetchedCams = await dataService.fetchCameras();
    const fetchedJobs = await dataService.getAlertJobs();
    setCameras(fetchedCams || []);
    setAlertJobs(fetchedJobs || []);
  }, []);

  useEffect(() => {
    refreshData();
    if (targets.length > 0) {
      setJobName(`Alert Job - ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
    }
  }, [targetsStr, refreshData]);

  const toggleDay = (day: string) => {
    if (selectedDays.includes(day)) {
      setSelectedDays(selectedDays.filter(d => d !== day));
    } else {
      setSelectedDays([...selectedDays, day]);
    }
  };

  const handleApplyJobs = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    if (targets.length === 0) {
      alert("No target regions selected.");
      return;
    }

    const promptedName = window.prompt("Enter a name for this Event Configuration:", jobName);
    if (promptedName === null) return;
    const finalJobName = promptedName.trim() || jobName;

    const finalStartTime = timeMode === 'preset' ? timePresets[selectedPreset].start : manualTimes.start;
    const finalEndTime = timeMode === 'preset' ? timePresets[selectedPreset].end : manualTimes.end;
    const finalDays = dayMode === 'all' ? ['All Days'] : selectedDays;
    const finalEventTypesStr = selectedEventTypes.join(', ');

    const newJob: AlertJob = {
      id: `JOB-${Date.now()}`,
      name: finalJobName,
      eventType: finalEventTypesStr,
      startTime: finalStartTime,
      endTime: finalEndTime,
      days: finalDays,
      cameraIds: Array.from(new Set(targets.map(t => t.camId)))
    };

    // 1. Create the alert job first to get the backend-assigned UUID
    const savedJob = await dataService.addAlertJob(newJob);

    // 2. Map cameras using the correct savedJob.id
    const updatedCams = cameras.map(cam => {
      const camTargets = targets.filter(t => t.camId === cam.id);
      if (camTargets.length > 0) {
        const targetRoiIds = camTargets.map(t => t.roiId);
        const currentRois = cam.rois || [];

        const updatedRois = currentRois.map((roi) => {
          if (targetRoiIds.includes(roi.id)) {
            return {
              ...roi,
              events: [...(roi.events || []), {
                id: `E-${savedJob.id}-${cam.id}`,
                type: finalEventTypesStr,
                startTime: finalStartTime,
                endTime: finalEndTime,
                days: finalDays,
                roiName: roi.name
              } as any]
            };
          }
          return roi;
        });
        return { ...cam, rois: updatedRois };
      }
      return cam;
    });

    // 3. Save cameras with corrected event IDs
    await dataService.saveCameras(updatedCams);

    alert(`Event Configuration "${finalJobName}" deployed.`);
    navigate('/event-jobs', { replace: true });
    refreshData();
  };

  const openDeleteJobConfirm = (e: React.MouseEvent, job: AlertJob) => {
    e.stopPropagation();
    e.preventDefault();
    setConfirmData({
      type: 'job',
      jobId: job.id,
      title: 'Delete Entire Alert Job?',
      text: `Are you sure you want to delete the job group "${job.name}"? This action cannot be undone.`
    });
    setConfirmOpen(true);
  };

  const openRemoveCamConfirm = (e: React.MouseEvent, job: AlertJob, cam: CameraProfile) => {
    e.stopPropagation();
    e.preventDefault();
    setConfirmData({
      type: 'cam',
      jobId: job.id,
      camId: cam.id,
      title: 'Remove Camera from Job?',
      text: `Are you sure you want to remove "${cam.name}" from the job "${job.name}"?`
    });
    setConfirmOpen(true);
  };

  const processDeletion = async () => {
    if (!confirmData) return;

    if (confirmData.type === 'job') {
      const job = alertJobs.find(j => j.id === confirmData.jobId);
      if (job) {
        const currentCams = await dataService.fetchCameras();
        const updatedCams = currentCams.map(cam => {
          if (job.cameraIds.includes(cam.id)) {
            const updatedRois = (cam.rois || []).map(roi => ({
              ...roi,
              events: (roi.events || []).filter(ev => !ev.id.includes(confirmData.jobId))
            }));
            return { ...cam, rois: updatedRois };
          }
          return cam;
        });
        const currentJobs = await dataService.getAlertJobs();
        const updatedJobs = currentJobs.filter(j => j.id !== confirmData.jobId);
        
        await dataService.deleteAlertJob(confirmData.jobId);
        await dataService.saveCameras(updatedCams);
        await dataService.saveAlertJobs(updatedJobs);
        
        setCameras([...updatedCams]);
        setAlertJobs([...updatedJobs]);
      }
    } else {
      const camId = confirmData.camId!;
      const jobId = confirmData.jobId;
      const currentCams = await dataService.fetchCameras();
      const updatedCams = currentCams.map(c => {
        if (c.id === camId) {
          const updatedRois = (c.rois || []).map(roi => ({
            ...roi,
            events: (roi.events || []).filter(ev => !ev.id.includes(jobId))
          }));
          return { ...c, rois: updatedRois };
        }
        return c;
      });
      const currentJobs = await dataService.getAlertJobs();
      const updatedJobs = currentJobs.map(j => {
        if (j.id === jobId) {
          return { ...j, cameraIds: j.cameraIds.filter(id => id !== camId) };
        }
        return j;
      }).filter(j => j.cameraIds.length > 0);
      
      const jobRemoved = !updatedJobs.some(j => j.id === jobId);
      if (jobRemoved) {
        await dataService.deleteAlertJob(jobId);
      }
      
      await dataService.saveCameras(updatedCams);
      await dataService.saveAlertJobs(updatedJobs);
      
      setCameras([...updatedCams]);
      setAlertJobs([...updatedJobs]);
    }

    setConfirmOpen(false);
    setConfirmData(null);
  };

  const toggleJobStatus = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation();
    const updatedJobs = alertJobs.map(j => {
      if (j.id === jobId) return { ...j, isActive: j.isActive === false ? true : false };
      return j;
    });
    await dataService.saveAlertJobs(updatedJobs);
    setAlertJobs([...updatedJobs]);
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        {targets.length > 0 ? (
          <Stack direction="row" spacing={1.5}>
            <Button variant="outlined" onClick={() => navigate('/event-jobs')} size="small">Exit Deploy Mode</Button>
            <Button variant="contained" onClick={handleApplyJobs} startIcon={<CheckCircle />} sx={{ bgcolor: '#2C3E50' }}>Deploy Job</Button>
          </Stack>
        ) : (
          <Button variant="contained" onClick={() => setDeployDialogOpen(true)} startIcon={<Add />} sx={{ bgcolor: '#2C3E50' }}>Deploy New Job</Button>
        )}
      </Box>

      {targets.length > 0 ? (
        <Grid container spacing={3} sx={{ mb: 6 }}>
          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 4, borderRadius: 1, bgcolor: '#FFFFFF', border: '2px solid #3A6EA5' }}>
              <form id="job-form" onSubmit={handleApplyJobs}>
                <Typography variant="h3" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AssignmentTurnedIn color="primary" /> NEW EVENT CONFIGURATION
                </Typography>
                <Stack spacing={4}>
                  <Box>
                    <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 1 }}>1. EVENT TYPES</Typography>
                    <Select
                      multiple
                      fullWidth
                      size="small"
                      value={selectedEventTypes}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSelectedEventTypes(typeof val === 'string' ? val.split(',') : val);
                      }}
                      sx={{ maxWidth: 400 }}
                      displayEmpty
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.length === 0 && <Typography variant="body2" color="text.secondary">Select event types</Typography>}
                          {selected.map((value) => (
                            <Chip key={value} label={value} size="small" sx={{ height: 20, fontSize: '12px', bgcolor: '#e3f2fd', color: '#1976d2' }} />
                          ))}
                        </Box>
                      )}
                    >
                      {eventTypes.map((type) => (
                        <MenuItem key={type.name} value={type.name}>
                          <Checkbox checked={selectedEventTypes.indexOf(type.name) > -1} size="small" />
                          <ListItemText primary={type.name} />
                        </MenuItem>
                      ))}
                    </Select>
                  </Box>
                  <Divider />
                  <Box>
                    <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 1 }}>2. OPERATIONAL WINDOW</Typography>
                    <ToggleButtonGroup size="small" value={timeMode} exclusive onChange={(_, val) => val && setTimeMode(val)} sx={{ mb: 2 }}>
                      <ToggleButton value="preset" sx={{ px: 3 }}>PRESETS</ToggleButton>
                      <ToggleButton value="manual" sx={{ px: 3 }}>MANUAL</ToggleButton>
                    </ToggleButtonGroup>
                    {timeMode === 'preset' ? (
                      <Stack direction="row" spacing={2}>
                        {timePresets.map((preset, idx) => (
                          <Paper key={idx} onClick={() => setSelectedPreset(idx)} sx={{ p: 2, flex: 1, textAlign: 'center', cursor: 'pointer', border: selectedPreset === idx ? '1px solid #2C3E50' : '1px solid #DDD', bgcolor: selectedPreset === idx ? '#f0f4f8' : '#FFF' }}>
                            <Typography variant="body2" fontWeight="600">{preset.label}</Typography>
                            <Typography variant="caption">{preset.start} - {preset.end}</Typography>
                          </Paper>
                        ))}
                      </Stack>
                    ) : (
                      <Stack direction="row" spacing={2} sx={{ maxWidth: 400 }}>
                        <TextField type="time" fullWidth size="small" value={manualTimes.start} onChange={(e) => setManualTimes({ ...manualTimes, start: e.target.value })} />
                        <TextField type="time" fullWidth size="small" value={manualTimes.end} onChange={(e) => setManualTimes({ ...manualTimes, end: e.target.value })} />
                      </Stack>
                    )}
                  </Box>
                  <Divider />
                  <Box>
                    <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 1 }}>3. WEEKLY SCHEDULE</Typography>
                    <Stack direction="row" spacing={1}>
                      {dayOptions.map((day) => {
                        const isSelected = selectedDays.includes(day.value);
                        return (
                          <Paper
                            key={day.value}
                            onClick={() => toggleDay(day.value)}
                            elevation={0}
                            sx={{
                              flexGrow: 1,
                              py: 1,
                              textAlign: 'center',
                              cursor: 'pointer',
                              bgcolor: isSelected ? '#f4f9ff' : '#FFF',
                              color: isSelected ? '#1976d2' : '#666',
                              border: isSelected ? '2px solid #1976d2' : '1px solid #DDD',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: 0.5,
                              borderRadius: 1
                            }}
                          >
                            {isSelected && <Check sx={{ fontSize: 16 }} />}
                            <Typography variant="caption" fontWeight={isSelected ? "bold" : "medium"}>{day.label}</Typography>
                          </Paper>
                        );
                      })}
                    </Stack>
                  </Box>
                </Stack>
              </form>
            </Paper>
          </Grid>
          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 3, borderRadius: 1, bgcolor: '#FFFFFF', border: '1px solid #DDDDDD' }}>
              <Typography variant="h3" sx={{ mb: 2, fontSize: '16px !important' }}> Target ROIs ({targets.length})</Typography>
              <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                {targets.map((target, idx) => {
                  const cam = cameras.find(c => c.id === target.camId);
                  const roi = cam?.rois?.find(r => r.id === target.roiId);
                  if (!cam || !roi) return null;
                  return (
                    <ListItem key={idx} sx={{ px: 0, borderBottom: '1px solid #f0f0f0', display: 'block', pb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}><Videocam sx={{ fontSize: 18 }} /></ListItemIcon>
                        <ListItemText primary={cam.name} secondary={cam.id} primaryTypographyProps={{ fontSize: '14px', fontWeight: 600 }} />
                      </Box>
                      <Box sx={{ pl: 4, display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ minWidth: 80 }}>Target Region:</Typography>
                        <Chip label={roi.name} size="small" sx={{ height: 24, fontSize: '12px', fontWeight: 500, bgcolor: '#e3f2fd', color: '#1976d2' }} />
                      </Box>
                    </ListItem>
                  );
                })}
              </List>
            </Paper>
          </Grid>
        </Grid>
      ) : (
        <Box>
          <Box sx={{ mb: 3 }}><Typography variant="h3" sx={{ fontSize: '18px !important' }}>Active Alert Jobs Registry</Typography></Box>
          <Stack spacing={2}>
            {alertJobs.map((job) => (
              <Accordion key={job.id} defaultExpanded elevation={0} sx={{ border: '1px solid #DDDDDD', '&:before': { display: 'none' }, opacity: job.isActive === false ? 0.6 : 1 }}>
                <AccordionSummary expandIcon={<ExpandMore />} sx={{ bgcolor: job.isActive === false ? '#f5f5f5' : '#F8F9FA', '& .MuiAccordionSummary-content': { alignItems: 'center', justifyContent: 'space-between' } }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <ListAlt sx={{ fontSize: 20, color: job.isActive === false ? '#999' : '#3A6EA5' }} />
                    <Box>
                      <Typography variant="body2" fontWeight="bold" sx={{ color: job.isActive === false ? '#777' : '#2C3E50' }}>{job.name}</Typography>
                    </Box>
                    <Chip
                      label={job.isActive === false ? 'INACTIVE' : 'ACTIVE'}
                      size="small"
                      color={job.isActive === false ? 'default' : 'success'}
                      sx={{ fontSize: '9px', height: 18, fontWeight: 'bold' }}
                    />
                    <Chip label={`${job.cameraIds.length} PROFILES`} size="small" sx={{ fontSize: '9px', height: 18, bgcolor: '#e3f2fd', color: '#1976d2', fontWeight: 'bold' }} />
                    {job.eventType && (
                      <Chip label={job.eventType} size="small" sx={{ fontSize: '9px', height: 18, bgcolor: '#fff3e0', color: '#e65100', fontWeight: 'bold' }} />
                    )}
                  </Stack>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="caption" sx={{ fontWeight: 'bold', color: job.isActive === false ? '#999' : '#2C3E50' }}>{job.isActive === false ? 'OFF' : 'ON'}</Typography>
                    <Switch
                      size="small"
                      checked={job.isActive !== false}
                      onMouseDown={(e) => toggleJobStatus(e, job.id)}
                      color="success"
                    />
                    <Divider orientation="vertical" flexItem sx={{ mx: 1, height: 20, alignSelf: 'center' }} />
                    <Box
                      component="span"
                      onClick={(e) => {
                        e.stopPropagation();
                        setRenameJobId(job.id);
                        setNewJobName(job.name);
                        setRenameDialogOpen(true);
                      }}
                      sx={{
                        display: 'flex',
                        p: 1,
                        borderRadius: '50%',
                        cursor: 'pointer',
                        color: 'primary.main',
                        '&:hover': { bgcolor: 'rgba(25, 118, 210, 0.04)' }
                      }}
                      title="Rename Job"
                    >
                      <Edit sx={{ fontSize: 18 }} />
                    </Box>
                    <Box
                      component="span"
                      onClick={(e) => openDeleteJobConfirm(e, job)}
                      sx={{
                        mr: 1,
                        display: 'flex',
                        p: 1,
                        borderRadius: '50%',
                        cursor: 'pointer',
                        color: '#d32f2f',
                        '&:hover': { bgcolor: 'rgba(211, 47, 47, 0.04)' }
                      }}
                      title="Delete Job"
                    >
                      <Delete sx={{ fontSize: 18 }} />
                    </Box>
                  </Stack>
                </AccordionSummary>
                <AccordionDetails sx={{ p: 0, bgcolor: job.isActive === false ? '#fafafa' : '#fff' }}>
                  <Box sx={{ p: 0 }}>
                    <Table size="small">
                      <TableHead sx={{ bgcolor: '#fbfcfe' }}>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 'bold', fontSize: '11px', pl: 6 }}>ATTACHED CAMERA / PROFILE</TableCell>
                          <TableCell sx={{ fontWeight: 'bold', fontSize: '11px' }}>TARGET REGIONS</TableCell>
                          <TableCell sx={{ fontWeight: 'bold', fontSize: '11px' }} align="right">ACTIONS</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {job.cameraIds.map((camId) => {
                          const cam = cameras.find(c => c.id === camId);
                          const attachedRois = cam?.rois?.filter(roi => roi.events?.some(e => e.id.includes(job.id))) || [];

                          return (
                            <TableRow key={`${job.id}-${camId}`}>
                              <TableCell sx={{ pl: 6 }}>
                                <Stack direction="row" spacing={1} alignItems="center">
                                  <Videocam sx={{ fontSize: 16, color: 'text.secondary' }} />
                                  <Box><Typography variant="body2" fontWeight="600">{cam?.name || 'Unknown Profile'}</Typography><Typography variant="caption" color="text.secondary">{camId}</Typography></Box>
                                </Stack>
                              </TableCell>
                              <TableCell>
                                <Stack spacing={0.5} alignItems="flex-start">
                                  {attachedRois.map(roi => (
                                    <Chip 
                                      key={roi.id} 
                                      label={roi.name} 
                                      size="small" 
                                      variant="outlined" 
                                      color="primary" 
                                      onClick={() => navigate(`/roi?camId=${camId}&roiId=${roi.id}`)}
                                      sx={{ fontSize: '10px', height: 20, cursor: 'pointer', '&:hover': { bgcolor: '#f0f4f8' } }} 
                                    />
                                  ))}
                                  {attachedRois.length === 0 && <Typography variant="caption" color="error">No active region</Typography>}
                                </Stack>
                              </TableCell>
                              <TableCell align="right">
                                <Stack direction="row" spacing={1} justifyContent="flex-end">
                                  <IconButton size="small" color="primary" onClick={() => navigate(`/roi?camId=${camId}`)} title="Edit ROI"><MapIcon sx={{ fontSize: 16 }} /></IconButton>
                                  <IconButton
                                    size="small"
                                    color="error"
                                    onClick={(e) => cam && openRemoveCamConfirm(e, job, cam)}
                                    title="Delete from Job"
                                  >
                                    <Delete sx={{ fontSize: 16 }} />
                                  </IconButton>
                                </Stack>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
            {alertJobs.length === 0 && (
              <Paper sx={{ py: 10, textAlign: 'center', bgcolor: '#f8f9fa', border: '1px dashed #ccc' }}>
                <Box sx={{ opacity: 0.5 }}><AssignmentTurnedIn sx={{ fontSize: 48, mb: 1 }} /><Typography variant="body2">No active monitoring jobs found.</Typography><Typography variant="caption">Select profiles from the Camera Directory to deploy new jobs.</Typography></Box>
              </Paper>
            )}
          </Stack>
        </Box>
      )}

      {/* Persistence Confirmation Dialog */}
      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)} PaperProps={{ sx: { borderRadius: 1, minWidth: 400 } }}>
        <DialogTitle sx={{ fontWeight: 700, bgcolor: '#f8f9fa', borderBottom: '1px solid #ddd' }}>{confirmData?.title}</DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <DialogContentText sx={{ color: 'text.primary' }}>{confirmData?.text}</DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2, bgcolor: '#f8f9fa', borderTop: '1px solid #ddd' }}>
          <Button onClick={() => setConfirmOpen(false)} color="inherit" size="small">Cancel</Button>
          <Button onClick={processDeletion} variant="contained" color="error" size="small">Confirm Delete</Button>
        </DialogActions>
      </Dialog>

      {/* Deploy New Job Dialog */}
      <Dialog open={deployDialogOpen} onClose={() => setDeployDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, bgcolor: '#f8f9fa', borderBottom: '1px solid #ddd' }}>Select Regions for New Job</DialogTitle>
        <DialogContent sx={{ mt: 2, p: 0 }}>
          <Box sx={{ px: 3, py: 1 }}>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Expand cameras to select specific Regions of Interest (ROIs) for the new alert job.
            </Typography>
          </Box>
          <List sx={{ maxHeight: 400, overflow: 'auto', p: 0 }}>
            {cameras.map((cam) => (
              <React.Fragment key={cam.id}>
                <ListItem sx={{ bgcolor: '#f8f9fa', borderTop: '1px solid #eee', borderBottom: '1px solid #eee', py: 1 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}><Videocam sx={{ fontSize: 18 }} /></ListItemIcon>
                  <ListItemText
                    primary={cam.name}
                    secondary={cam.location || cam.id}
                    primaryTypographyProps={{ fontWeight: 600, fontSize: '14px' }}
                  />
                </ListItem>
                {cam.rois && cam.rois.length > 0 ? (
                  cam.rois.map(roi => {
                    const isSelected = selectedDeployTargets.some(t => t.camId === cam.id && t.roiId === roi.id);
                    return (
                      <ListItem
                        key={roi.id}
                        sx={{
                          pl: 6,
                          borderBottom: '1px solid #f9f9f9',
                          cursor: 'pointer',
                          bgcolor: isSelected ? '#f0f4f8' : 'transparent',
                          '&:hover': { bgcolor: '#f0f4f8' }
                        }}
                        onClick={() => {
                          if (isSelected) {
                            setSelectedDeployTargets(selectedDeployTargets.filter(t => !(t.camId === cam.id && t.roiId === roi.id)));
                          } else {
                            const otherCameraTargets = selectedDeployTargets.filter(t => t.camId !== cam.id);
                            setSelectedDeployTargets([...otherCameraTargets, { camId: cam.id, roiId: roi.id }]);
                          }
                        }}
                      >
                        <ListItemIcon sx={{ minWidth: 40 }}>
                          <Radio
                            edge="start"
                            checked={isSelected}
                            disableRipple
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={roi.name}
                          secondary={roi.type === 'polygon' ? 'Polygon' : 'Rectangle'}
                          primaryTypographyProps={{ fontSize: '13px', fontWeight: 500 }}
                        />
                      </ListItem>
                    );
                  })
                ) : (
                  <ListItem sx={{ pl: 6, borderBottom: '1px solid #f9f9f9' }}>
                    <ListItemText secondary="No regions defined for this camera." secondaryTypographyProps={{ fontStyle: 'italic', fontSize: '12px' }} />
                  </ListItem>
                )}
              </React.Fragment>
            ))}
          </List>
        </DialogContent>
        <DialogActions sx={{ p: 2, bgcolor: '#f8f9fa', borderTop: '1px solid #ddd' }}>
          <Button onClick={() => setDeployDialogOpen(false)} color="inherit" size="small">Cancel</Button>
          <Button
            onClick={() => {
              setDeployDialogOpen(false);
              const targetStr = selectedDeployTargets.map(t => `${t.camId}:${t.roiId}`).join(',');
              navigate(`/event-jobs?targets=${targetStr}`);
              setSelectedDeployTargets([]);
            }}
            variant="contained"
            sx={{ bgcolor: '#2C3E50' }}
            size="small"
            disabled={selectedDeployTargets.length === 0}
          >
            Continue to Configure
          </Button>
        </DialogActions>
      </Dialog>

      {/* Rename Job Dialog */}
      <Dialog open={renameDialogOpen} onClose={() => setRenameDialogOpen(false)} PaperProps={{ sx: { borderRadius: 1, minWidth: 400 } }}>
        <DialogTitle sx={{ fontWeight: 700, bgcolor: '#f8f9fa', borderBottom: '1px solid #ddd' }}>Rename Alert Job</DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ mb: 2 }}>Enter a new name for this event configuration:</Typography>
          <TextField
            autoFocus
            fullWidth
            size="small"
            value={newJobName}
            onChange={(e) => setNewJobName(e.target.value)}
            placeholder="e.g. Front Door Night Shift"
          />
        </DialogContent>
        <DialogActions sx={{ p: 2, bgcolor: '#f8f9fa', borderTop: '1px solid #ddd' }}>
          <Button onClick={() => setRenameDialogOpen(false)} color="inherit" size="small">Cancel</Button>
          <Button 
            onClick={async () => {
              if (!renameJobId || !newJobName.trim()) return;
              const updatedJobs = alertJobs.map(j => j.id === renameJobId ? { ...j, name: newJobName.trim() } : j);
              await dataService.saveAlertJobs(updatedJobs);
              setAlertJobs(updatedJobs);
              setRenameDialogOpen(false);
            }} 
            variant="contained" 
            sx={{ bgcolor: '#2C3E50' }} 
            size="small"
            disabled={!newJobName.trim()}
          >
            Save Name
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EventAlertJobs;
