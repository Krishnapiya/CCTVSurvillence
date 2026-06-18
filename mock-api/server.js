const express = require('express');
const cors = require('cors');
const app = express();
const port = 3001;

app.use(cors());
app.use(express.json());

// Mock Database
let cameras = [
  {
    id: 'CAM-001',
    name: 'Front Entrance (Server)',
    location: 'Main Gate',
    status: 'active',
    ip: '192.168.1.101',
    rois: []
  }
];

// API Endpoints
app.get('/api/cameras', (req, res) => {
  res.json(cameras);
});

app.get('/api/status', (req, res) => {
  res.json({ status: 'Online', system: 'Surveillance-AI', version: '1.0.0' });
});

app.post('/api/cameras', (req, res) => {
  const newCam = { ...req.body, id: `CAM-${Date.now()}` };
  cameras.push(newCam);
  res.status(201).json(newCam);
});

// Start Server
app.listen(port, '0.0.0.0', () => {
  console.log(`🚀 Mock API Server running at http://localhost:${port}`);
  console.log(`🌐 Accessible on LAN at http://192.168.10.189:${port}`);
});
