import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Stack, Button, Dialog, DialogTitle, DialogContent, Grid, Divider
} from '@mui/material';
import { Download, AccessTime, PlayCircleFilled } from '@mui/icons-material';
import { dataService } from '../services/dataService';
import VideoClipPlayer, { getEventClipDownloadUrl } from '../components/VideoClipPlayer';
import EventLogFilters from '../components/EventLogFilters';
import { applyLogFilters, DEFAULT_LOG_FILTERS } from '../utils/logFilters';

const EventLogs: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [selectedLog, setSelectedLog] = useState<any | null>(null);
  const [filters, setFilters] = useState(DEFAULT_LOG_FILTERS);

  useEffect(() => {
    const fetchLogs = async () => {
      const fetched = await dataService.getLogs();
      setLogs(fetched);
    };
    fetchLogs();

    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  const cameraOptions = useMemo(
    () => Array.from(new Set(logs.map((l) => l.camera).filter(Boolean))).sort(),
    [logs],
  );

  const filteredLogs = useMemo(() => applyLogFilters(logs, filters), [logs, filters]);

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
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <Button 
          variant="outlined" 
          startIcon={<Download sx={{ fontSize: 18 }} />} 
          size="small"
          sx={{ fontSize: '13px' }}
        >
          Export CSV
        </Button>
      </Box>

      <EventLogFilters filters={filters} onChange={setFilters} cameras={cameraOptions} />

      <TableContainer component={Paper} sx={{ borderRadius: 1 }}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead sx={{ bgcolor: '#F8F9FA' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', py: 1.5 }}>VISUAL</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>TIMESTAMP</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>CAMERA</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>VIOLATION TYPE</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>STATUS</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }} align="right">RECORD</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredLogs.map((log) => (
              <TableRow key={log.id} className="gov-table-row">
                <TableCell>
                  <Box 
                    sx={{ 
                      width: 60, 
                      height: 34, 
                      borderRadius: 0.5, 
                      overflow: 'hidden', 
                      position: 'relative', 
                      border: '1px solid #DDD', 
                      cursor: 'pointer',
                      bgcolor: '#000'
                    }} 
                    onClick={() => setSelectedLog(log)}
                  >
                    <img src={log.thumbnail} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.8 }} />
                    <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <PlayCircleFilled sx={{ fontSize: 16, color: 'white' }} />
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <AccessTime sx={{ fontSize: 14, color: 'text.secondary' }} />
                    <Typography variant="body2" sx={{ fontSize: '13px' }}>{log.timestamp}</Typography>
                  </Stack>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontSize: '13px', fontWeight: 500 }}>{log.camera}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontSize: '13px' }}>{log.event}</Typography>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={log.severity?.toUpperCase() || 'INFO'} 
                    size="small" 
                    sx={{ 
                      fontSize: '9px', 
                      height: 18, 
                      fontWeight: 'bold',
                      bgcolor: getSeverityColor(log.severity) + '11',
                      color: getSeverityColor(log.severity),
                      border: `1px solid ${getSeverityColor(log.severity)}44`
                    }} 
                  />
                </TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => setSelectedLog(log)} sx={{ fontSize: '12px' }}>Details</Button>
                </TableCell>
              </TableRow>
            ))}
            {filteredLogs.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 10 }}>
                  <Typography variant="body2" color="text.secondary">
                    {logs.length === 0 ? 'No event history found.' : 'No events match your search filters.'}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={!!selectedLog} onClose={() => setSelectedLog(null)} maxWidth="md" fullWidth PaperProps={{ sx: { borderRadius: 1 } }}>
        <DialogTitle sx={{ fontWeight: 700, bgcolor: '#f8f9fa', borderBottom: '1px solid #ddd' }}>
          Event Evidence: {selectedLog?.event}
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          <Grid container>
            <Grid item xs={12} md={8}>
              <Box sx={{ p: 2 }}>
                <Box sx={{ width: '100%', aspectRatio: '16/9', bgcolor: '#000', borderRadius: 0.5, overflow: 'hidden', position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  {selectedLog?.id ? (
                    <VideoClipPlayer
                      eventId={selectedLog.id}
                      poster={selectedLog.thumbnail}
                      autoPlay
                    />
                  ) : (
                    <>
                      <img src={selectedLog?.thumbnail} alt="Evidence" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
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
                    <Typography variant="body2" fontWeight="600">{selectedLog?.camera}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>EVENT TIME</Typography>
                    <Typography variant="body2" fontWeight="600">{selectedLog?.timestamp}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>AI CONFIDENCE</Typography>
                    <Typography variant="body2" fontWeight="600" color="success.main">{selectedLog?.confidence || '98.4%'}</Typography>
                  </Box>
                  <Divider />
                  <Button 
                    variant="contained" 
                    fullWidth 
                    disabled={!selectedLog?.id}
                    onClick={async () => {
                      if (!selectedLog?.id) return;
                      try {
                        const token = localStorage.getItem('surv_token');
                        const response = await fetch(getEventClipDownloadUrl(selectedLog.id), {
                          headers: token ? { Authorization: `Bearer ${token}` } : {},
                        });
                        if (!response.ok) throw new Error('Download failed');
                        const blob = await response.blob();
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `Evidence-${selectedLog.id}.mp4`;
                        link.click();
                        URL.revokeObjectURL(url);
                      } catch {
                        if (selectedLog?.videoUrl) {
                          window.open(selectedLog.videoUrl, '_blank');
                        }
                      }
                    }}
                    sx={{ bgcolor: '#2C3E50' }}
                  >
                    {selectedLog?.id ? 'Download Evidence Clip' : 'No Clip Available'}
                  </Button>
                </Stack>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default EventLogs;
