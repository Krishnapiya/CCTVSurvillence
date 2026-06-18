export interface EventSchedule {
  id: string;
  type: string;
  startTime: string;
  endTime: string;
  roiName: string;
  days?: string[];
}

export interface ROI {
  id: string;
  name: string;
  color: string;
  type?: 'rect' | 'polygon';
  events: EventSchedule[];
  coords?: { left: number, top: number, width: number, height: number };
  points?: { x: number, y: number }[];
}

export interface CameraProfile {
  id: string;
  name: string;
  location: string;
  status: 'active' | 'inactive' | 'error';
  ip: string;
  rois: ROI[];
}

export interface AlertJob {
  id: string;
  name: string;
  eventType: string;
  startTime: string;
  endTime: string;
  days: string[];
  cameraIds: string[];
  isActive?: boolean;
}

const STORAGE_KEYS = {
  CAMERAS: 'surv_cameras',
  LOGS: 'surv_logs',
  JOBS: 'surv_alert_jobs',
};

// Dynamic API and Media URLs based on client access address
export const getHost = () => {
  return typeof window !== 'undefined' ? window.location.hostname : 'localhost';
};

export const getPort = () => {
  return localStorage.getItem('surv_backend_port') || '8005';
};

const API_BASE = `http://${getHost()}:${getPort()}/api/v1`;
const MEDIA_BASE = `http://${getHost()}:${getPort()}`;

export const dataService = {
  // Check if API is available
  checkApi: async () => {
    const host = getHost();
    const currentPort = getPort();
    try {
      const res = await fetch(`http://${host}:${currentPort}/api/v1/status`);
      if (res.ok && res.headers.get('content-type')?.includes('application/json')) {
        const data = await res.json();
        if (data && (data.status === 'healthy' || data.status === 'online')) {
          return true;
        }
      }
    } catch {}

    const candidatePorts = ['8005', '8000', '8001', '8010'];
    for (const port of candidatePorts) {
      if (port === currentPort) continue;
      try {
        const res = await fetch(`http://${host}:${port}/api/v1/status`);
        if (res.ok && res.headers.get('content-type')?.includes('application/json')) {
          const data = await res.json();
          if (data && (data.status === 'healthy' || data.status === 'online')) {
            localStorage.setItem('surv_backend_port', port);
            window.location.reload();
            return true;
          }
        }
      } catch {}
    }
    return false;
  },

  getCameras: (): CameraProfile[] => {
    const data = localStorage.getItem(STORAGE_KEYS.CAMERAS);
    if (!data) {
      const sample: CameraProfile = {
        id: 'CAM-001',
        name: 'Front Entrance (Sample)',
        location: 'Main Gate',
        status: 'active',
        ip: '192.168.1.101',
        rois: []
      };
      localStorage.setItem(STORAGE_KEYS.CAMERAS, JSON.stringify([sample]));
      return [sample];
    }
    return JSON.parse(data);
  },

  fetchCameras: async (): Promise<CameraProfile[]> => {
    const token = localStorage.getItem('surv_token');
    try {
      const response = await fetch(`${API_BASE}/cameras/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const backendCameras = await response.json();
        const mapped: CameraProfile[] = backendCameras.map((c: any) => ({
          id: c.id,
          name: c.name,
          location: 'Company Site',
          status: c.status === 'online' ? 'active' : 'inactive',
          ip: c.rtsp_url,
          rois: c.rois || []
        }));
        localStorage.setItem(STORAGE_KEYS.CAMERAS, JSON.stringify(mapped));
        return mapped;
      }
    } catch (err) {
      console.error('Error fetching cameras from backend:', err);
    }
    return dataService.getCameras();
  },

  updateCamera: async (camera: CameraProfile) => {
    const token = localStorage.getItem('surv_token');
    if (camera.id.length > 15) {
      try {
        await fetch(`${API_BASE}/cameras/${camera.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            name: camera.name,
            rtsp_url: camera.ip,
            rois: camera.rois
          })
        });
      } catch (err) {
        console.error('Failed to update camera in backend:', err);
      }
    }
    const cameras = dataService.getCameras();
    const updated = cameras.map(c => c.id === camera.id ? camera : c);
    localStorage.setItem(STORAGE_KEYS.CAMERAS, JSON.stringify(updated));
  },

  saveCameras: async (cameras: CameraProfile[]) => {
    localStorage.setItem(STORAGE_KEYS.CAMERAS, JSON.stringify(cameras));
    for (const cam of cameras) {
      await dataService.updateCamera(cam);
    }
  },

  addCamera: async (camera: CameraProfile) => {
    const token = localStorage.getItem('surv_token');
    try {
      const response = await fetch(`${API_BASE}/cameras/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: camera.name,
          rtsp_url: camera.ip
        })
      });
      if (response.ok) {
        const newCam = await response.json();
        camera.id = newCam.id;
      }
    } catch (err) {
      console.error('Failed to sync added camera to backend:', err);
    }

    const cameras = dataService.getCameras();
    if (!cameras.some(c => c.id === camera.id)) {
      cameras.push(camera);
    }
    localStorage.setItem(STORAGE_KEYS.CAMERAS, JSON.stringify(cameras));
  },

  deleteCamera: async (id: string) => {
    const token = localStorage.getItem('surv_token');
    if (id.length > 15) {
      try {
        await fetch(`${API_BASE}/cameras/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      } catch (err) {
        console.error('Failed to delete camera from backend:', err);
      }
    }
    const cameras = dataService.getCameras();
    const updated = cameras.filter(c => c.id !== id);
    localStorage.setItem(STORAGE_KEYS.CAMERAS, JSON.stringify(updated));
  },

  getAlertJobs: async (): Promise<AlertJob[]> => {
    const token = localStorage.getItem('surv_token');
    try {
      const response = await fetch(`${API_BASE}/alert-jobs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const backendJobs = await response.json();
        const mapped = backendJobs.map((j: any) => ({
          id: j.id,
          name: j.name,
          eventType: j.event_type,
          startTime: j.start_time,
          endTime: j.end_time,
          days: j.days,
          cameraIds: j.camera_ids
        }));
        localStorage.setItem(STORAGE_KEYS.JOBS, JSON.stringify(mapped));
        return mapped;
      }
    } catch (err) {
      console.error('Failed to fetch alert jobs:', err);
    }
    const data = localStorage.getItem(STORAGE_KEYS.JOBS);
    return data ? JSON.parse(data) : [];
  },

  saveAlertJobs: async (jobs: AlertJob[]) => {
    localStorage.setItem(STORAGE_KEYS.JOBS, JSON.stringify(jobs));
    const token = localStorage.getItem('surv_token');
    for (const job of jobs) {
      if (job.id.length > 15) {
        try {
          await fetch(`${API_BASE}/alert-jobs/${job.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              name: job.name,
              event_type: job.eventType,
              start_time: job.startTime,
              end_time: job.endTime,
              days: job.days,
              camera_ids: job.cameraIds,
              is_active: job.isActive !== false
            })
          });
        } catch (err) {
          console.error('Failed to sync alert job update to backend:', err);
        }
      }
    }
  },

  addAlertJob: async (job: AlertJob): Promise<AlertJob> => {
    const token = localStorage.getItem('surv_token');
    let returnedJob = job;
    try {
      const response = await fetch(`${API_BASE}/alert-jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: job.name,
          event_type: job.eventType,
          start_time: job.startTime,
          end_time: job.endTime,
          days: job.days,
          camera_ids: job.cameraIds
        })
      });
      if (response.ok) {
        const backendJob = await response.json();
        returnedJob = {
          id: backendJob.id,
          name: backendJob.name,
          eventType: backendJob.event_type,
          startTime: backendJob.start_time,
          endTime: backendJob.end_time,
          days: backendJob.days,
          cameraIds: backendJob.camera_ids
        };
      }
    } catch (err) {
      console.error('Failed to save alert job to backend:', err);
    }
    const jobs = await dataService.getAlertJobs();
    if (!jobs.some(j => j.id === returnedJob.id)) {
      jobs.push(returnedJob);
    }
    localStorage.setItem(STORAGE_KEYS.JOBS, JSON.stringify(jobs));
    return returnedJob;
  },

  deleteAlertJob: async (id: string) => {
    const token = localStorage.getItem('surv_token');
    if (id.length > 15) {
      try {
        await fetch(`${API_BASE}/alert-jobs/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      } catch (err) {
        console.error('Failed to delete alert job from backend:', err);
      }
    }
  },

  getLogs: async (): Promise<any[]> => {
    const token = localStorage.getItem('surv_token');
    try {
      const response = await fetch(`${API_BASE}/events`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const events = await response.json();
        
        let cameras = [];
        try {
          cameras = await dataService.fetchCameras();
        } catch (e) {
          cameras = dataService.getCameras();
        }
        
        const mapped = events.map((e: any) => {
          const camera = cameras.find(c => c.id === e.camera_id);
          const camName = camera ? camera.name : 'IP Camera';
          
          let severity = 'medium';
          const typeLower = e.type.toLowerCase();
          if (typeLower.includes('fire') || typeLower.includes('smoke') || typeLower.includes('fight') || typeLower.includes('suicide')) {
            severity = 'critical';
          } else if (typeLower.includes('faint') || typeLower.includes('phone') || typeLower.includes('smoking') || typeLower.includes('uniform')) {
            severity = 'high';
          }
          
          let thumbnail = 'https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=400&q=80';
          if (e.snapshot_path) {
            thumbnail = e.snapshot_path.startsWith('http') ? e.snapshot_path : `${MEDIA_BASE}/${e.snapshot_path}`;
          }
          
          return {
            id: e.id,
            event: e.type,
            camera: camName,
            timestamp: new Date(e.timestamp).toLocaleString(),
            severity: severity,
            confidence: `${(e.confidence * 100).toFixed(1)}%`,
            thumbnail: thumbnail,
            videoUrl: e.video_clip_path ? (e.video_clip_path.startsWith('http') ? e.video_clip_path : `${MEDIA_BASE}/${e.video_clip_path}`) : null
          };
        });
        localStorage.setItem(STORAGE_KEYS.LOGS, JSON.stringify(mapped));
        return mapped;
      }
    } catch (err) {
      console.error('Failed to fetch events from backend:', err);
    }
    
    const data = localStorage.getItem(STORAGE_KEYS.LOGS);
    return data ? JSON.parse(data) : [];
  },
  
  addLog: async (log: any) => {
    const logs = await dataService.getLogs();
    const newLog = { ...log, id: Date.now(), timestamp: new Date().toLocaleString() };
    logs.unshift(newLog);
    localStorage.setItem(STORAGE_KEYS.LOGS, JSON.stringify(logs.slice(0, 50)));
  }
};
