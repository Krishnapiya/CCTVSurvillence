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
    const data = localStorage.getItem(STORAGE_KEYS.CAMERAS);
    if (!data) {
      localStorage.setItem(STORAGE_KEYS.CAMERAS, JSON.stringify([]));
      return [];
    }
    try {
      const parsed = JSON.parse(data);
      return parsed.filter((c: any) => c.id !== 'CAM-001' && !c.name?.includes('Sample'));
    } catch {
      return [];
    }
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
        const localCameras = dataService.getCameras();
        const isRealToken = token && token !== 'mock-token-value';
        
        const mapped: CameraProfile[] = [];
        for (const c of backendCameras) {
          if (c.name.includes('Sample')) {
            continue;
          }
          const localCam = localCameras.find(lc => lc.id === c.id);
          let rois = c.rois || [];
          
          if (isRealToken && localCam && localCam.rois && localCam.rois.length > rois.length) {
            console.log(`Syncing local ROIs for camera ${c.name} to backend...`);
            try {
              await fetch(`${API_BASE}/cameras/${c.id}`, {
                method: 'PUT',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                  name: c.name,
                  rtsp_url: c.rtsp_url,
                  rois: localCam.rois,
                  location: localCam.location
                })
              });
              rois = localCam.rois;
            } catch (err) {
              console.error('Failed to sync local ROIs to backend:', err);
            }
          }
          
          mapped.push({
            id: c.id,
            cameraCode: c.camera_code,
            name: c.name,
            location: c.location || 'Company Site',
            status: c.status === 'online' ? 'active' : 'inactive',
            ip: c.rtsp_url,
            rois: rois
          });
        }

        // Sync local-only cameras to the backend (skipping sample ones)
        if (isRealToken) {
          for (const localCam of localCameras) {
            if (localCam.id === 'CAM-001' || localCam.name.includes('Sample')) {
              continue;
            }
            if (localCam.id.startsWith('CAM-')) {
              console.log(`Syncing local-only camera "${localCam.name}" to backend...`);
              try {
                const addRes = await fetch(`${API_BASE}/cameras`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                  },
                  body: JSON.stringify({
                    name: localCam.name,
                    rtsp_url: localCam.ip,
                    location: localCam.location
                  })
                });
                if (addRes.ok) {
                  const saved = await addRes.json();
                  let rois = localCam.rois || [];
                  if (rois.length > 0) {
                    try {
                      await fetch(`${API_BASE}/cameras/${saved.id}`, {
                        method: 'PUT',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                          name: saved.name,
                          rtsp_url: saved.rtsp_url,
                          rois: rois,
                          location: localCam.location
                        })
                      });
                    } catch (err) {
                      console.error('Failed to sync local ROIs for newly added camera:', err);
                    }
                  }
                  
                  mapped.push({
                    id: saved.id,
                    name: saved.name,
                    location: saved.location || 'Company Site',
                    status: saved.status === 'online' ? 'active' : 'inactive',
                    ip: saved.rtsp_url,
                    rois: rois
                  });
                }
              } catch (err) {
                console.error('Failed to sync local camera to backend:', err);
              }
            }
          }
        }
        
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
    if (camera.id && !camera.id.startsWith('CAM-')) {
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
    if (id && !id.startsWith('CAM-')) {
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
        const localJobs = localStorage.getItem(STORAGE_KEYS.JOBS) ? JSON.parse(localStorage.getItem(STORAGE_KEYS.JOBS)!) : [];
        const isRealToken = token && token !== 'mock-token-value';
        
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
        
        if (isRealToken) {
          for (const localJob of localJobs) {
            const backendMatch = mapped.find((mj: any) => mj.id === localJob.id);
            if (localJob.id.startsWith('JOB-')) {
              console.log(`Syncing local-only job "${localJob.name}" to backend...`);
              try {
                const addRes = await fetch(`${API_BASE}/alert-jobs`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                  },
                  body: JSON.stringify({
                    name: localJob.name,
                    event_type: localJob.eventType,
                    start_time: localJob.startTime,
                    end_time: localJob.endTime,
                    days: localJob.days,
                    camera_ids: localJob.cameraIds
                  })
                });
                if (addRes.ok) {
                  const saved = await addRes.json();
                  mapped.push({
                    id: saved.id,
                    name: saved.name,
                    eventType: saved.event_type,
                    startTime: saved.start_time,
                    endTime: saved.end_time,
                    days: saved.days,
                    cameraIds: saved.camera_ids,
                    isActive: saved.is_active
                  });
                  
                  const oldId = localJob.id;
                  const newId = saved.id;
                  const currentCameras = dataService.getCameras();
                  let camerasUpdated = false;
                  const updatedCams = currentCameras.map(cam => {
                    let camChanged = false;
                    const updatedRois = (cam.rois || []).map(roi => {
                      let roiChanged = false;
                      const updatedEvents = (roi.events || []).map((ev: any) => {
                        if (ev.id.includes(oldId)) {
                          roiChanged = true;
                          return {
                            ...ev,
                            id: ev.id.replace(oldId, newId)
                          };
                        }
                        return ev;
                      });
                      if (roiChanged) {
                        camChanged = true;
                        return { ...roi, events: updatedEvents };
                      }
                      return roi;
                    });
                    if (camChanged) {
                      camerasUpdated = true;
                      return { ...cam, rois: updatedRois };
                    }
                    return cam;
                  });

                  if (camerasUpdated) {
                    console.log(`Syncing updated camera event IDs from old job ${oldId} to new UUID ${newId}...`);
                    dataService.saveCameras(updatedCams);
                  }
                }
              } catch (err) {
                console.error('Failed to sync local job to backend:', err);
              }
            } else {
              const needsUpdate =
                localJob.name !== backendMatch.name ||
                localJob.eventType !== backendMatch.eventType ||
                localJob.startTime !== backendMatch.startTime ||
                localJob.endTime !== backendMatch.endTime ||
                JSON.stringify(localJob.days) !== JSON.stringify(backendMatch.days) ||
                JSON.stringify(localJob.cameraIds) !== JSON.stringify(backendMatch.cameraIds) ||
                localJob.isActive !== backendMatch.isActive;

              if (needsUpdate) {
                console.log(`Syncing local updates for job "${localJob.name}" to backend...`);
                try {
                  await fetch(`${API_BASE}/alert-jobs/${localJob.id}`, {
                    method: 'PUT',
                    headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                      name: localJob.name,
                      event_type: localJob.eventType,
                      start_time: localJob.startTime,
                      end_time: localJob.endTime,
                      days: localJob.days,
                      camera_ids: localJob.cameraIds,
                      is_active: localJob.isActive !== false
                    })
                  });
                  backendMatch.name = localJob.name;
                  backendMatch.eventType = localJob.eventType;
                  backendMatch.startTime = localJob.startTime;
                  backendMatch.endTime = localJob.endTime;
                  backendMatch.days = localJob.days;
                  backendMatch.cameraIds = localJob.cameraIds;
                  backendMatch.isActive = localJob.isActive;
                } catch (err) {
                  console.error('Failed to sync local job updates to backend:', err);
                }
              }
            }
          }
        }
        localStorage.setItem(STORAGE_KEYS.JOBS, JSON.stringify(mapped));
        return mapped;
      }
    } catch (err) {
      console.error('Failed to fetch alert jobs:', err);
    }
    const data = localStorage.getItem(STORAGE_KEYS.JOBS);
    if (data) {
      try {
        const parsed = JSON.parse(data);
        return parsed.filter((j: any) => !j.id?.startsWith('JOB-') && !j.cameraIds?.some((id: string) => id.startsWith('CAM-')));
      } catch {
        return [];
      }
    }
    return [];
  },

  saveAlertJobs: async (jobs: AlertJob[]) => {
    localStorage.setItem(STORAGE_KEYS.JOBS, JSON.stringify(jobs));
    const token = localStorage.getItem('surv_token');
    for (const job of jobs) {
      if (job.id && !job.id.startsWith('JOB-')) {
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
    const jobs = await dataService.getAlertJobs();
    if (!jobs.some(j => j.id === returnedJob.id)) {
      jobs.push(returnedJob);
    }
    localStorage.setItem(STORAGE_KEYS.JOBS, JSON.stringify(jobs));
    return returnedJob;
  },

  deleteAlertJob: async (id: string) => {
    const token = localStorage.getItem('surv_token');
    if (id && !id.startsWith('JOB-')) {
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
    const localJobs = localStorage.getItem(STORAGE_KEYS.JOBS) ? JSON.parse(localStorage.getItem(STORAGE_KEYS.JOBS)!) : [];
    const updated = localJobs.filter((j: any) => j.id !== id);
    localStorage.setItem(STORAGE_KEYS.JOBS, JSON.stringify(updated));
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
        localStorage.setItem(STORAGE_KEYS.LOGS, JSON.stringify(mapped));
        return mapped;
      }
    } catch (err) {
      console.error('Failed to fetch events from backend:', err);
    }
    
    const data = localStorage.getItem(STORAGE_KEYS.LOGS);
    if (data) {
      try {
        const parsed = JSON.parse(data);
        return parsed.filter((l: any) => !l.camera?.includes('Sample') && !l.event?.includes('Sample'));
      } catch {
        return [];
      }
    }
    return [];
  },
  
  addLog: async (log: any) => {
    const logs = await dataService.getLogs();
    const newLog = { ...log, id: Date.now(), timestamp: new Date().toLocaleString() };
    logs.unshift(newLog);
    localStorage.setItem(STORAGE_KEYS.LOGS, JSON.stringify(logs.slice(0, 50)));
  }
};
