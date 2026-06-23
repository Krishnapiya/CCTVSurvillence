import { EVENT_TYPE_LABELS } from '../constants/eventTypes';

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
  cameraCode?: string;
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

// Backend URL: set VITE_BACKEND_HOST / VITE_BACKEND_PORT in .env.local for remote API
export const getHost = () => {
  const envHost = import.meta.env.VITE_BACKEND_HOST;
  if (envHost) return envHost;
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('surv_backend_host');
    if (stored) return stored;
    return window.location.hostname;
  }
  return 'localhost';
};

export const getPort = () => {
  const envPort = import.meta.env.VITE_BACKEND_PORT;
  if (envPort) return envPort;
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('surv_backend_port');
    if (stored) return stored;
  }
  return '8005';
};

export const getBackendBaseUrl = () => `http://${getHost()}:${getPort()}`;

export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith('http')) return path;

  let normalized = path.trim();
  if (normalized.startsWith('./')) {
    normalized = normalized.slice(2);
  }
  normalized = normalized.replace(/^\/+/, '');
  if (!normalized.startsWith('media/')) {
    normalized = `media/${normalized}`;
  }
  return `${getBackendBaseUrl()}/${normalized}`;
}

const API_BASE = `${getBackendBaseUrl()}/api/v1`;
const MEDIA_BASE = getBackendBaseUrl();

let cachedCameras: CameraProfile[] = [];
let cachedJobs: AlertJob[] = [];

export const dataService = {
  // Check if API is available
  checkApi: async () => {
    const host = getHost();
    const currentPort = getPort();
    const configured = Boolean(import.meta.env.VITE_BACKEND_HOST);
    try {
      const res = await fetch(`${getBackendBaseUrl()}/api/v1/status`);
      if (res.ok && res.headers.get('content-type')?.includes('application/json')) {
        const data = await res.json();
        if (data && (data.status === 'healthy' || data.status === 'online')) {
          return true;
        }
      }
    } catch {}

    if (configured) return false;

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
    return cachedCameras;
  },

  fetchCameras: async (): Promise<CameraProfile[]> => {
    const token = localStorage.getItem('surv_token');
    try {
      const response = await fetch(`${API_BASE}/cameras`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const backendCameras = await response.json();
        const mapped: CameraProfile[] = backendCameras
          .filter((c: any) => !c.name.includes('Sample'))
          .map((c: any) => ({
            id: c.id,
            cameraCode: c.camera_code,
            name: c.name,
            location: c.location || 'Company Site',
            status: c.status === 'online' ? 'active' : 'inactive',
            ip: c.rtsp_url,
            rois: c.rois || []
          }));
        cachedCameras = mapped;
        return mapped;
      }
    } catch (err) {
      console.error('Error fetching cameras from backend:', err);
    }
    return cachedCameras;
  },

  updateCamera: async (camera: CameraProfile) => {
    const token = localStorage.getItem('surv_token');
    if (camera.id) {
      try {
        const response = await fetch(`${API_BASE}/cameras/${camera.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            name: camera.name,
            rtsp_url: camera.ip,
            rois: camera.rois,
            location: camera.location,
            ...(camera.cameraCode ? { camera_code: camera.cameraCode } : {}),
          })
        });
        if (!response.ok) {
          if (response.status === 401) {
            throw new Error("Unauthorized: Please log in again.");
          }
          const errText = await response.text();
          throw new Error(`Server returned ${response.status}: ${errText}`);
        }
      } catch (err) {
        console.error('Failed to update camera in backend:', err);
        throw err;
      }
    }
    cachedCameras = cachedCameras.map(c => c.id === camera.id ? camera : c);
  },

  saveCameras: async (cameras: CameraProfile[]) => {
    for (const cam of cameras) {
      await dataService.updateCamera(cam);
    }
  },

  addCamera: async (camera: CameraProfile) => {
    const token = localStorage.getItem('surv_token');
    try {
      const response = await fetch(`${API_BASE}/cameras`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: camera.name,
          rtsp_url: camera.ip,
          location: camera.location,
          ...(camera.cameraCode ? { camera_code: camera.cameraCode } : {}),
        })
      });
      if (response.ok) {
        const newCam = await response.json();
        camera.id = newCam.id;
        camera.cameraCode = newCam.camera_code;
        camera.location = newCam.location || camera.location;
        
        // If there are ROIs, update them as well
        if (camera.rois && camera.rois.length > 0) {
          await dataService.updateCamera(camera);
        }
      }
    } catch (err) {
      console.error('Failed to sync added camera to backend:', err);
    }

    if (!cachedCameras.some(c => c.id === camera.id)) {
      cachedCameras.push(camera);
    }
  },

  deleteCamera: async (id: string) => {
    const token = localStorage.getItem('surv_token');
    if (id) {
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
    cachedCameras = cachedCameras.filter(c => c.id !== id);
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
          cameraIds: j.camera_ids,
          isActive: j.is_active
        }));
        cachedJobs = mapped;
        return mapped;
      }
    } catch (err) {
      console.error('Failed to fetch alert jobs:', err);
    }
    return cachedJobs;
  },

  saveAlertJobs: async (jobs: AlertJob[]) => {
    const token = localStorage.getItem('surv_token');
    for (const job of jobs) {
      if (job.id) {
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
    cachedJobs = jobs;
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
          cameraIds: backendJob.camera_ids,
          isActive: backendJob.is_active
        };
      } else {
        if (response.status === 401) {
          throw new Error("Unauthorized: Please log in again.");
        }
        const errText = await response.text();
        throw new Error(`Server returned ${response.status}: ${errText}`);
      }
    } catch (err) {
      console.error('Failed to save alert job to backend:', err);
      throw err;
    }
    if (!cachedJobs.some(j => j.id === returnedJob.id)) {
      cachedJobs.push(returnedJob);
    }
    return returnedJob;
  },

  deleteAlertJob: async (id: string) => {
    const token = localStorage.getItem('surv_token');
    if (id) {
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
    cachedJobs = cachedJobs.filter((j: any) => j.id !== id);
  },

  getLogs: async (): Promise<any[]> => {
    const token = localStorage.getItem('surv_token');
    try {
      const response = await fetch(`${API_BASE}/events?min_confidence=0.55`, {
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
          cameras = cachedCameras;
        }
        
        const mapped = events
          .filter((e: any) => e.confidence >= 0.55)
          .map((e: any) => {
            const camera = cameras.find(c => c.id === e.camera_id);
            const camName = camera ? camera.name : 'IP Camera';
            
            let severity = 'medium';
            const typeLower = (e.type || '').toLowerCase();
            if (typeLower.includes('fire') || typeLower.includes('smoke') || typeLower.includes('fight') || typeLower.includes('suicide')) {
              severity = 'critical';
            } else if (typeLower.includes('faint') || typeLower.includes('phone') || typeLower.includes('smoking') || typeLower.includes('uniform')) {
              severity = 'high';
            }
            
            let thumbnail = 'https://images.unsplash.com/photo-1557597774-9d273605dfa9?auto=format&fit=crop&w=400&q=80';
            if (e.snapshot_path) {
              thumbnail = resolveMediaUrl(e.snapshot_path) || thumbnail;
            }
            
            const videoUrl = resolveMediaUrl(e.video_clip_path);
            const clipStreamUrl = e.id ? `${getBackendBaseUrl()}/api/v1/events/${e.id}/clip` : null;
            
            return {
              id: e.id,
              eventType: e.type,
              event: EVENT_TYPE_LABELS[e.type] || e.type,
              camera: camName,
              cameraId: e.camera_id,
              timestamp: new Date(e.timestamp).toLocaleString(),
              timestampRaw: e.timestamp,
              severity: severity,
              confidence: `${(e.confidence * 100).toFixed(1)}%`,
              thumbnail: thumbnail,
              videoUrl: videoUrl,
              clipStreamUrl: clipStreamUrl,
            };
          });
        return mapped;
      }
    } catch (err) {
      console.error('Failed to fetch events from backend:', err);
    }
    return [];
  },
  
  addLog: async (log: any) => {
    // Backend API handles logs automatically; local addLog is deprecated
  }
};
