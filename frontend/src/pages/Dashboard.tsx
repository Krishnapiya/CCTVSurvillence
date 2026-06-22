import React, { useState, useEffect, useMemo } from 'react';
import { 
  Grid, Paper, Typography, Box, Stack, useTheme, Chip, Divider, Switch, Menu, MenuItem, Dialog, DialogTitle, DialogContent, Button
} from '@mui/material';
import { Videocam, Warning, TrendingUp, Map as MapIcon, Circle, ListAlt, ArrowDropDown, PlayCircleFilled, AccessTime } from '@mui/icons-material';
import { dataService, CameraProfile, AlertJob } from '../services/dataService';
import VideoClipPlayer, { getEventClipDownloadUrl } from '../components/VideoClipPlayer';
import EventLogFilters from '../components/EventLogFilters';
import { applyLogFilters, DEFAULT_LOG_FILTERS } from '../utils/logFilters';

const StatCard: React.FC<{ 
  title: string, 
  value: string, 
  icon: React.ReactNode, 
  color: string, 
  trend?: string, 
  trendNode?: React.ReactNode,
  active?: boolean,
  onClick?: (event: React.MouseEvent<HTMLElement>) => void,
  isDropdown?: boolean
}> = ({ title, value, icon, color, trend, trendNode, active, onClick, isDropdown }) => {
  return (
    <Paper 
      onClick={onClick}
      sx={{ 
        p: 2, 
        borderRadius: 1, 
        bgcolor: '#FFFFFF', 
        border: '1px solid #DDDDDD',
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? { borderColor: '#3A6EA5', bgcolor: '#fbfcfe' } : {},
        position: 'relative'
      }}
    >
      <Stack direction="row" spacing={2} alignItems="center">
        <Box sx={{ p: 1, borderRadius: 1, bgcolor: active ? '#e8f5e9' : '#F8F9FA', color: active ? '#2e7d32' : color, border: '1px solid #EEEEEE', display: 'flex', alignItems: 'center' }}>{icon}</Box>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="caption" color="text.secondary" fontWeight="500">{title.toUpperCase()}</Typography>
          <Typography variant="h2" sx={{ fontSize: '20px !important', mt: 0.5, color: active ? '#2e7d32' : 'inherit' }}>{value}</Typography>
        </Box>
        {isDropdown && <ArrowDropDown sx={{ color: 'text.secondary', opacity: 0.5 }} />}
      </Stack>
      <Box sx={{ mt: 2, pt: 1, borderTop: '1px solid #F0F0F0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {trendNode ? trendNode : <Typography variant="caption" color="text.secondary">{trend}</Typography>}
        <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: active ? 'success.main' : (trend && trend.includes('+')) ? 'success.main' : 'primary.main' }} />
      </Box>
    </Paper>
  );
};

// Video Alert Card Component
const VideoAlertCard: React.FC<{ log: any; onView: () => void }> = ({ log, onView }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#d32f2f';
      case 'high': return '#ed6c02';
      case 'medium': return '#0288d1';
      case 'low': return '#2e7d32';
      default: return '#757575';
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 1,
        overflow: 'hidden',
        border: '1px solid #DDDDDD',
        bgcolor: '#FFFFFF',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 6px 12px rgba(0,0,0,0.08)',
          '& .play-overlay': { opacity: 1 },
          borderColor: '#3A6EA5'
        }
      }}
    >
      <Box sx={{ position: 'relative', aspectRatio: '16/9', bgcolor: '#000', overflow: 'hidden' }}>
        <img
          src={log.thumbnail}
          alt={log.event}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
        
        {/* Flashing Alert Indicator */}
        <Box
          sx={{
            position: 'absolute',
            top: 10,
            left: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            bgcolor: 'rgba(0,0,0,0.6)',
            px: 1,
            py: 0.5,
            borderRadius: 0.5,
            border: '1px solid rgba(255,255,255,0.2)'
          }}
        >
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: '#d32f2f',
              animation: 'pulse 1.5s infinite',
              '@keyframes pulse': {
                '0%': { transform: 'scale(0.8)', opacity: 0.5 },
                '50%': { transform: 'scale(1.2)', opacity: 1 },
                '100%': { transform: 'scale(0.8)', opacity: 0.5 }
              }
            }}
          />
          <Typography variant="caption" sx={{ color: '#fff', fontSize: '9px', fontWeight: 'bold', letterSpacing: '0.5px' }}>
            ALERT
          </Typography>
        </Box>

        {/* Confidence Badge */}
        <Box
          sx={{
            position: 'absolute',
            top: 10,
            right: 10,
            bgcolor: 'rgba(0,0,0,0.6)',
            px: 1,
            py: 0.5,
            borderRadius: 0.5,
            border: '1px solid rgba(255,255,255,0.2)'
          }}
        >
          <Typography variant="caption" sx={{ color: '#2ecc71', fontSize: '9px', fontWeight: 'bold' }}>
            {log.confidence || '98.4%'} CONF
          </Typography>
        </Box>

        {/* Play Overlay */}
        <Box
          className="play-overlay"
          onClick={onView}
          sx={{
            position: 'absolute',
            inset: 0,
            bgcolor: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0,
            transition: 'opacity 0.2s ease',
            cursor: 'pointer'
          }}
        >
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              bgcolor: 'rgba(255,255,255,0.9)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 10px rgba(0,0,0,0.3)'
            }}
          >
            <PlayCircleFilled sx={{ fontSize: 36, color: '#2C3E50' }} />
          </Box>
        </Box>
      </Box>

      {/* Details */}
      <Box sx={{ p: 1.5 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
          <Typography variant="body2" noWrap sx={{ fontWeight: 600, color: '#2C3E50', textOverflow: 'ellipsis', overflow: 'hidden', maxWidth: '170px' }}>
            {log.event}
          </Typography>
          <Chip
            label={log.severity?.toUpperCase() || 'INFO'}
            size="small"
            sx={{
              fontSize: '8px',
              height: 16,
              fontWeight: 'bold',
              bgcolor: getSeverityColor(log.severity) + '11',
              color: getSeverityColor(log.severity),
              border: `1px solid ${getSeverityColor(log.severity)}33`
            }}
          />
        </Stack>
        
        <Stack spacing={0.5}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Videocam sx={{ fontSize: 14, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary" noWrap sx={{ textOverflow: 'ellipsis', overflow: 'hidden' }}>
              {log.camera}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <AccessTime sx={{ fontSize: 14, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {log.timestamp}
            </Typography>
          </Box>
        </Stack>
      </Box>
    </Paper>
  );
};

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const [cameras, setCameras] = useState<CameraProfile[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [alertJobs, setAlertJobs] = useState<AlertJob[]>([]);
  const [selectedDetailLog, setSelectedDetailLog] = useState<any | null>(null);
  const [filters, setFilters] = useState(DEFAULT_LOG_FILTERS);

  // Menu State
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  useEffect(() => {
    const load = async () => {
      const cams = await dataService.fetchCameras();
      setCameras(cams);
      const fetchedLogs = await dataService.getLogs();
      setLogs(fetchedLogs || []);
      const fetchedJobs = await dataService.getAlertJobs();
      setAlertJobs(fetchedJobs || []);
    };
    load();

    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const toggleJobStatus = (jobId: string) => {
    const updatedJobs = alertJobs.map(j => {
      if (j.id === jobId) return { ...j, isActive: j.isActive === false ? true : false };
      return j;
    });
    dataService.saveAlertJobs(updatedJobs);
    setAlertJobs([...updatedJobs]);
  };

  const getTodaysDetectionsCount = () => {
    const todayStr = new Date().toDateString();
    return logs.filter(log => {
      try {
        return new Date(log.timestamp).toDateString() === todayStr;
      } catch {
        return false;
      }
    }).length;
  };

  const activeJobs = alertJobs.filter(j => j.isActive !== false);
  const activeProfilesCount = activeJobs.reduce((acc, job) => acc + job.cameraIds.length, 0);

  const cameraOptions = useMemo(
    () => Array.from(new Set(logs.map((l) => l.camera).filter(Boolean))).sort(),
    [logs],
  );

  const filteredLogs = useMemo(() => applyLogFilters(logs, filters), [logs, filters]);

  return (
    <Box>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Cameras Configured" 
            value={`${cameras.length}`} 
            icon={<Videocam sx={{ fontSize: 20 }} />} 
            color={theme.palette.primary.main} 
            trend={`${cameras.filter(c => c.status === 'active').length} Active Now`} 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total ROIs" 
            value={cameras.reduce((acc, cam) => acc + (cam.rois?.length || 0), 0).toString()} 
            icon={<MapIcon sx={{ fontSize: 20 }} />} 
            color="#27ae60" 
            trend="Configured Region boundaries" 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Alerts Detected" 
            value={logs.length.toString()} 
            icon={<Warning sx={{ fontSize: 20 }} />} 
            color="#e74c3c" 
            trendNode={
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Typography variant="caption" color="text.secondary">
                  Total: <strong>{logs.length}</strong>
                </Typography>
                <Divider orientation="vertical" flexItem sx={{ height: 12, my: 'auto' }} />
                <Typography variant="caption" color="text.secondary">
                  Today: <strong>{getTodaysDetectionsCount()}</strong>
                </Typography>
              </Stack>
            } 
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Active Alert Jobs" 
            value={activeJobs.length.toString()} 
            icon={<TrendingUp sx={{ fontSize: 20 }} />} 
            color="#2ecc71" 
            trend={`${activeProfilesCount} Active Profiles`} 
            active={activeJobs.length > 0}
            onClick={handleMenuClick}
            isDropdown
          />
          <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={handleMenuClose}
            PaperProps={{
              sx: { 
                minWidth: 280, 
                maxHeight: 400, 
                borderRadius: 1, 
                boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                border: '1px solid #eee',
                mt: 1
              }
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <Box sx={{ p: 1.5, bgcolor: '#f8f9fa', borderBottom: '1px solid #eee' }}>
              <Typography variant="caption" fontWeight="700" color="text.secondary">MANAGE EVENT CONFIGURATIONS</Typography>
            </Box>
            {alertJobs.length === 0 ? (
              <MenuItem disabled sx={{ py: 2 }}>
                <Typography variant="caption">No configurations found</Typography>
              </MenuItem>
            ) : (
              alertJobs.map((job) => (
                <MenuItem 
                  key={job.id} 
                  sx={{ 
                    py: 1, 
                    px: 2, 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    '&:hover': { bgcolor: '#f0f4f8' }
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <ListAlt sx={{ fontSize: 18, color: job.isActive === false ? '#999' : '#3A6EA5' }} />
                    <Box>
                      <Typography variant="body2" fontWeight="600" sx={{ color: job.isActive === false ? '#777' : '#2C3E50' }}>{job.name}</Typography>
                      <Typography variant="caption" color="text.secondary">{job.cameraIds.length} Profiles</Typography>
                    </Box>
                  </Stack>
                  <Switch 
                    size="small" 
                    checked={job.isActive !== false} 
                    onChange={() => toggleJobStatus(job.id)}
                    color="success" 
                  />
                </MenuItem>
              ))
            )}
          </Menu>
        </Grid>
      </Grid>

      <EventLogFilters filters={filters} onChange={setFilters} cameras={cameraOptions} />

      <Grid container spacing={2}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, borderRadius: 1, bgcolor: '#FFFFFF', display: 'flex', flexDirection: 'column', minHeight: 480 }}>
            <Typography variant="h3" sx={{ mb: 2, fontSize: '16px !important' }}>Latest Video Alerts</Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2} sx={{ flexGrow: 1 }}>
              {filteredLogs.slice(0, 4).map((log) => (
                <Grid item xs={12} sm={6} key={log.id}>
                  <VideoAlertCard log={log} onView={() => setSelectedDetailLog(log)} />
                </Grid>
              ))}
              {filteredLogs.length === 0 && (
                <Box sx={{ display: 'flex', flexGrow: 1, alignItems: 'center', justifyContent: 'center', p: 4, width: '100%' }}>
                  <Typography variant="body2" color="text.secondary">
                    {logs.length === 0 ? 'No video alerts detected yet.' : 'No alerts match your search filters.'}
                  </Typography>
                </Box>
              )}
            </Grid>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, borderRadius: 1, bgcolor: '#FFFFFF', height: '100%', minHeight: 480 }}>
            <Typography variant="h3" sx={{ mb: 2, fontSize: '16px !important' }}>Alert Cameras Sublisting</Typography>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
              Latest 3 detection events in active alert configurations
            </Typography>
            <Stack spacing={2}>
              {filteredLogs.length === 0 ? (
                <Typography variant="body2" sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
                  {logs.length === 0 ? 'No alert cameras listed.' : 'No alerts match your search filters.'}
                </Typography>
              ) : (
                filteredLogs.slice(0, 3).map((log) => (
                  <Box 
                    key={log.id} 
                    sx={{ 
                      p: 2, 
                      borderRadius: 1, 
                      bgcolor: '#F8F9FA', 
                      border: '1px solid #EEEEEE',
                      transition: 'border-color 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        borderColor: '#3A6EA5',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                      }
                    }}
                  >
                    <Stack spacing={1}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Circle 
                            sx={{ 
                              fontSize: 8, 
                              color: log.severity === 'critical' ? 'error.main' : 'warning.main',
                              animation: 'pulse 1.5s infinite',
                              '@keyframes pulse': {
                                '0%': { transform: 'scale(0.8)', opacity: 0.5 },
                                '50%': { transform: 'scale(1.2)', opacity: 1 },
                                '100%': { transform: 'scale(0.8)', opacity: 0.5 }
                              }
                            }} 
                          />
                          <Typography variant="body2" fontWeight="600" sx={{ color: '#2C3E50' }}>
                            {log.camera}
                          </Typography>
                        </Stack>
                        <Chip
                          label={log.severity?.toUpperCase() || 'INFO'}
                          size="small"
                          sx={{
                            fontSize: '8px',
                            height: 16,
                            fontWeight: 'bold',
                            bgcolor: log.severity === 'critical' ? '#ffebee' : '#fff3e0',
                            color: log.severity === 'critical' ? '#c62828' : '#ef6c00'
                          }}
                        />
                      </Stack>
                      <Divider sx={{ opacity: 0.5 }} />
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="caption" color="text.secondary">
                          Detection: <strong>{log.event}</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '10px' }}>
                          {log.timestamp.split(',')[1] || log.timestamp}
                        </Typography>
                      </Stack>
                    </Stack>
                  </Box>
                ))
              )}
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      {/* Detail Dialog */}
      <Dialog 
        open={!!selectedDetailLog} 
        onClose={() => setSelectedDetailLog(null)} 
        maxWidth="md" 
        fullWidth 
        PaperProps={{ sx: { borderRadius: 1 } }}
      >
        <DialogTitle sx={{ fontWeight: 700, bgcolor: '#f8f9fa', borderBottom: '1px solid #ddd', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" fontWeight="bold">Video Alert Evidence: {selectedDetailLog?.event}</Typography>
          <Chip 
            label={selectedDetailLog?.severity?.toUpperCase() || 'INFO'} 
            color="error" 
            size="small" 
            sx={{ fontWeight: 'bold' }}
          />
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          <Grid container>
            <Grid item xs={12} md={8}>
              <Box sx={{ p: 2 }}>
                <Box sx={{ width: '100%', aspectRatio: '16/9', bgcolor: '#000', borderRadius: 0.5, overflow: 'hidden', position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  {selectedDetailLog?.id ? (
                    <VideoClipPlayer
                      eventId={selectedDetailLog.id}
                      poster={selectedDetailLog.thumbnail}
                      autoPlay
                    />
                  ) : (
                    <>
                      <img src={selectedDetailLog?.thumbnail} alt="Evidence" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                      <PlayCircleFilled sx={{ position: 'absolute', inset: 'calc(50% - 24px)', fontSize: 48, color: 'white', opacity: 0.8 }} />
                    </>
                  )}
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={4} sx={{ borderLeft: '1px solid #ddd' }}>
              <Box sx={{ p: 2.5 }}>
                <Stack spacing={2.5}>
                  <Box>
                    <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>CAMERA SOURCE</Typography>
                    <Typography variant="body2" fontWeight="600">{selectedDetailLog?.camera}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>EVENT TIME</Typography>
                    <Typography variant="body2" fontWeight="600">{selectedDetailLog?.timestamp}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>AI CONFIDENCE</Typography>
                    <Typography variant="body2" fontWeight="600" color="success.main">{selectedDetailLog?.confidence || '98.4%'}</Typography>
                  </Box>
                  <Divider />
                  <Stack direction="row" spacing={1} sx={{ width: '100%' }}>
                    <Button 
                      variant="contained" 
                      fullWidth 
                      disabled={!selectedDetailLog?.id}
                      onClick={async () => {
                        if (!selectedDetailLog?.id) return;
                        try {
                          const token = localStorage.getItem('surv_token');
                          const response = await fetch(getEventClipDownloadUrl(selectedDetailLog.id), {
                            headers: token ? { Authorization: `Bearer ${token}` } : {},
                          });
                          if (!response.ok) throw new Error('Download failed');
                          const blob = await response.blob();
                          const url = URL.createObjectURL(blob);
                          const link = document.createElement('a');
                          link.href = url;
                          link.download = `Evidence-${selectedDetailLog.id}.mp4`;
                          link.click();
                          URL.revokeObjectURL(url);
                        } catch {
                          if (selectedDetailLog?.videoUrl) {
                            window.open(selectedDetailLog.videoUrl, '_blank');
                          }
                        }
                      }}
                      sx={{ bgcolor: '#2e7d32', '&:hover': { bgcolor: '#1b5e20' } }}
                    >
                      Download
                    </Button>
                    <Button variant="outlined" fullWidth onClick={() => setSelectedDetailLog(null)}>
                      Close
                    </Button>
                  </Stack>
                </Stack>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
