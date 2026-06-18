import React, { useState } from 'react';
import { getPort } from '../services/dataService';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Tabs,
  Tab,
  Grid,
  CircularProgress,
  Divider,
  Chip,
  Paper,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  CloudUpload,
  Image as ImageIcon,
  Movie as MovieIcon,
  CheckCircle,
  Warning as WarningIcon,
  Timeline,
  LocalFireDepartment,
  SmokingRooms,
  SportsKabaddi,
  AccessibilityNew,
  PhoneAndroid
} from '@mui/icons-material';

interface Detection {
  type: string;
  confidence: number;
  details: any;
}

const YoloTesting: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  
  const [loading, setLoading] = useState(false);
  
  // Results
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  
  const [resultVideoUrl, setResultVideoUrl] = useState<string | null>(null);
  const [detectedTypes, setDetectedTypes] = useState<string[]>([]);
  const [processedFrames, setProcessedFrames] = useState<number>(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    resetState();
  };

  const resetState = () => {
    setImageFile(null);
    setImagePreview(null);
    setVideoFile(null);
    setVideoPreview(null);
    setResultImage(null);
    setDetections([]);
    setResultVideoUrl(null);
    setDetectedTypes([]);
    setProcessedFrames(0);
    setLoading(false);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
      setResultImage(null);
      setDetections([]);
    }
  };

  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setVideoFile(file);
      setVideoPreview(URL.createObjectURL(file));
      setResultVideoUrl(null);
      setDetectedTypes([]);
      setProcessedFrames(0);
    }
  };

  const analyzeImage = async () => {
    if (!imageFile) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', imageFile);

    try {
      const host = window.location.hostname;
      const port = getPort();
      const response = await fetch(`http://${host}:${port}/api/v1/test-yolo/image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to analyze image');
      const data = await response.json();
      setResultImage(data.image);
      setDetections(data.detections);
    } catch (err) {
      console.error(err);
      alert('Error analyzing image. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const analyzeVideo = async () => {
    if (!videoFile) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', videoFile);

    try {
      const host = window.location.hostname;
      const port = getPort();
      const response = await fetch(`http://${host}:${port}/api/v1/test-yolo/video`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to analyze video');
      const data = await response.json();
      setResultVideoUrl(`http://${host}:${port}${data.video_url}`);
      setDetectedTypes(data.detected_types);
      setProcessedFrames(data.processed_frames);
    } catch (err) {
      console.error(err);
      alert('Error analyzing video. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('fire') || t.includes('smoke')) return <LocalFireDepartment sx={{ color: '#E74C3C' }} />;
    if (t.includes('smoking')) return <SmokingRooms sx={{ color: '#9B59B6' }} />;
    if (t.includes('fight')) return <SportsKabaddi sx={{ color: '#E67E22' }} />;
    if (t.includes('faint') || t.includes('suicide')) return <AccessibilityNew sx={{ color: '#3498DB' }} />;
    if (t.includes('phone') || t.includes('mobile')) return <PhoneAndroid sx={{ color: '#2ECC71' }} />;
    return <CheckCircle sx={{ color: '#1ABC9C' }} />;
  };

  const getBadgeColor = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('fire') || t.includes('smoke') || t.includes('intrusion')) return 'error';
    if (t.includes('fight') || t.includes('suicide')) return 'warning';
    if (t.includes('phone') || t.includes('smoking')) return 'secondary';
    return 'success';
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 1 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: '#2C3E50' }}>
          AI Model Lab
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Upload images or video clips to test real-time YOLOv11 detectors, pose estimators, and polygon intrusion engine.
        </Typography>
      </Box>

      <Card sx={{ borderRadius: 2, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: '#F8F9FA' }}>
          <Tabs value={tabValue} onChange={handleTabChange} textColor="primary" indicatorColor="primary">
            <Tab icon={<ImageIcon />} iconPosition="start" label="Image Analyzer" sx={{ fontWeight: 600, py: 2 }} />
            <Tab icon={<MovieIcon />} iconPosition="start" label="Video Stream Test" sx={{ fontWeight: 600, py: 2 }} />
          </Tabs>
        </Box>

        <CardContent sx={{ p: 4 }}>
          {tabValue === 0 ? (
            // IMAGE TAB
            <Grid container spacing={4}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  1. Upload Source Image
                </Typography>
                
                <Box
                  sx={{
                    border: '2px dashed #BDC3C7',
                    borderRadius: 2,
                    p: 4,
                    textAlign: 'center',
                    cursor: 'pointer',
                    bgcolor: '#FAFBFB',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: '#F0F4F8'
                    }
                  }}
                  component="label"
                >
                  <input type="file" accept="image/*" hidden onChange={handleImageChange} />
                  <CloudUpload sx={{ fontSize: 48, color: '#95A5A6', mb: 1.5 }} />
                  <Typography variant="subtitle1" fontWeight="600">
                    Click to upload or drag & drop
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Supports PNG, JPG, JPEG
                  </Typography>
                </Box>

                {imagePreview && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Original Frame:
                    </Typography>
                    <Box
                      component="img"
                      src={imagePreview}
                      alt="Source Preview"
                      sx={{
                        width: '100%',
                        maxHeight: 320,
                        objectFit: 'contain',
                        borderRadius: 1.5,
                        border: '1px solid #E2E8F0',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                      }}
                    />
                    <Button
                      variant="contained"
                      fullWidth
                      size="large"
                      onClick={analyzeImage}
                      disabled={loading}
                      sx={{ mt: 2, py: 1.5, fontWeight: 600 }}
                    >
                      {loading ? <CircularProgress size={24} color="inherit" /> : 'Run Detections'}
                    </Button>
                  </Box>
                )}
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  2. Analysis Output
                </Typography>

                {!resultImage && !loading && (
                  <Box
                    sx={{
                      height: '100%',
                      minHeight: 300,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '1px solid #E2E8F0',
                      borderRadius: 2,
                      bgcolor: '#F8F9FA'
                    }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      Run detections to view annotated frame output
                    </Typography>
                  </Box>
                )}

                {loading && (
                  <Box
                    sx={{
                      height: '100%',
                      minHeight: 300,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '1px solid #E2E8F0',
                      borderRadius: 2,
                      bgcolor: '#F8F9FA',
                      gap: 2
                    }}
                  >
                    <CircularProgress />
                    <Typography variant="body2" color="text.secondary">
                      Running YOLO model inference...
                    </Typography>
                  </Box>
                )}

                {resultImage && !loading && (
                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Annotated Detections (YOLO + Skeleton Overlay):
                    </Typography>
                    <Box
                      component="img"
                      src={resultImage}
                      alt="Result Output"
                      sx={{
                        width: '100%',
                        maxHeight: 320,
                        objectFit: 'contain',
                        borderRadius: 1.5,
                        border: '1px solid #E2E8F0',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                      }}
                    />

                    <Typography variant="subtitle2" sx={{ mt: 3, mb: 1, fontWeight: 600 }}>
                      Detected Objects & Events ({detections.length})
                    </Typography>
                    <Divider sx={{ mb: 1.5 }} />

                    {detections.length === 0 ? (
                      <Paper sx={{ p: 2, bgcolor: '#FAFBFB', border: '1px solid #E2E8F0', borderRadius: 1.5 }}>
                        <Typography variant="body2" color="text.secondary" align="center">
                          No safety violations or target objects detected.
                        </Typography>
                      </Paper>
                    ) : (
                      <List sx={{ p: 0 }}>
                        {detections.map((det, index) => (
                          <ListItem
                            key={index}
                            sx={{
                              p: 1.5,
                              mb: 1,
                              border: '1px solid #E2E8F0',
                              borderRadius: 1.5,
                              bgcolor: '#FFFFFF',
                              '&:hover': { bgcolor: '#F8F9FA' }
                            }}
                          >
                            <ListItemIcon sx={{ minWidth: 40 }}>
                              {getEventIcon(det.type)}
                            </ListItemIcon>
                            <ListItemText
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                    {det.type.replace('_', ' ').toUpperCase()}
                                  </Typography>
                                  <Chip
                                    label={det.type}
                                    size="small"
                                    color={getBadgeColor(det.type) as any}
                                    sx={{ height: 20, fontSize: 10, fontWeight: 600 }}
                                  />
                                </Box>
                              }
                              secondary={
                                <Box sx={{ mt: 0.5 }}>
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                    Confidence: {(det.confidence * 100).toFixed(1)}%
                                  </Typography>
                                  <LinearProgress
                                    variant="determinate"
                                    value={det.confidence * 100}
                                    color={getBadgeColor(det.type) as any}
                                    sx={{ height: 4, borderRadius: 1, mt: 0.5 }}
                                  />
                                </Box>
                              }
                            />
                          </ListItem>
                        ))}
                      </List>
                    )}
                  </Box>
                )}
              </Grid>
            </Grid>
          ) : (
            // VIDEO TAB
            <Grid container spacing={4}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  1. Select CCTV / Video Clip
                </Typography>
                
                <Box
                  sx={{
                    border: '2px dashed #BDC3C7',
                    borderRadius: 2,
                    p: 4,
                    textAlign: 'center',
                    cursor: 'pointer',
                    bgcolor: '#FAFBFB',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: '#F0F4F8'
                    }
                  }}
                  component="label"
                >
                  <input type="file" accept="video/*" hidden onChange={handleVideoChange} />
                  <CloudUpload sx={{ fontSize: 48, color: '#95A5A6', mb: 1.5 }} />
                  <Typography variant="subtitle1" fontWeight="600">
                    Click to upload video file
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Supports MP4, AVI, MOV (Max size: 50MB)
                  </Typography>
                </Box>

                <Paper sx={{ mt: 2, p: 1.5, bgcolor: '#FFF9E6', border: '1px solid #FFE499', borderRadius: 1.5 }}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <WarningIcon color="warning" sx={{ fontSize: 20 }} />
                    <Typography variant="caption" color="warning.dark" sx={{ fontWeight: 500 }}>
                      Notice: To ensure fast processing times, the analysis pipeline is configured to evaluate only the first 150 frames (approx. 5-10 seconds of action).
                    </Typography>
                  </Box>
                </Paper>

                {videoPreview && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Video Source:
                    </Typography>
                    <Box
                      component="video"
                      src={videoPreview}
                      controls
                      sx={{
                        width: '100%',
                        maxHeight: 280,
                        borderRadius: 1.5,
                        border: '1px solid #E2E8F0'
                      }}
                    />
                    <Button
                      variant="contained"
                      fullWidth
                      size="large"
                      onClick={analyzeVideo}
                      disabled={loading}
                      sx={{ mt: 2, py: 1.5, fontWeight: 600 }}
                    >
                      {loading ? <CircularProgress size={24} color="inherit" /> : 'Process Video Stream'}
                    </Button>
                  </Box>
                )}
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  2. Live Stream Inference Results
                </Typography>

                {!resultVideoUrl && !loading && (
                  <Box
                    sx={{
                      height: '100%',
                      minHeight: 300,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '1px solid #E2E8F0',
                      borderRadius: 2,
                      bgcolor: '#F8F9FA'
                    }}
                  >
                    <Typography variant="body2" color="text.secondary">
                      Submit video to begin frame-by-frame analysis
                    </Typography>
                  </Box>
                )}

                {loading && (
                  <Box
                    sx={{
                      height: '100%',
                      minHeight: 300,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '1px solid #E2E8F0',
                      borderRadius: 2,
                      bgcolor: '#F8F9FA',
                      gap: 2,
                      p: 3
                    }}
                  >
                    <CircularProgress />
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      Processing video file...
                    </Typography>
                    <Typography variant="caption" color="text.secondary" align="center">
                      Splitting frames, running YOLO inference, drawing annotations, and encoding to Web MP4 container.
                    </Typography>
                  </Box>
                )}

                {resultVideoUrl && !loading && (
                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Processed Stream output (Annotated & Transcoded):
                    </Typography>
                    <Box
                      component="video"
                      src={resultVideoUrl}
                      controls
                      autoPlay
                      loop
                      sx={{
                        width: '100%',
                        maxHeight: 280,
                        borderRadius: 1.5,
                        border: '1px solid #E2E8F0',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                      }}
                    />

                    <Typography variant="subtitle2" sx={{ mt: 3, mb: 1, fontWeight: 600 }}>
                      Video Log summary ({processedFrames} frames evaluated)
                    </Typography>
                    <Divider sx={{ mb: 1.5 }} />

                    {detectedTypes.length === 0 ? (
                      <Paper sx={{ p: 2, bgcolor: '#FAFBFB', border: '1px solid #E2E8F0', borderRadius: 1.5 }}>
                        <Typography variant="body2" color="text.secondary" align="center">
                          No alerts generated during this stream.
                        </Typography>
                      </Paper>
                    ) : (
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          The following safety events were triggered during video processing:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {detectedTypes.map((type) => (
                            <Chip
                              key={type}
                              icon={getEventIcon(type)}
                              label={type.replace('_', ' ').toUpperCase()}
                              color={getBadgeColor(type) as any}
                              variant="outlined"
                              sx={{ fontWeight: 600, py: 1.8 }}
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Box>
                )}
              </Grid>
            </Grid>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default YoloTesting;
