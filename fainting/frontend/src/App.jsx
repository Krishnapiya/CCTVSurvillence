import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Database, 
  Eye, 
  FileText, 
  Maximize2, 
  Play, 
  RefreshCw, 
  ShieldAlert, 
  Video, 
  Volume2, 
  X 
} from 'lucide-react';

// Automatically detect host URL
const BACKEND_URL = window.location.origin.includes('3000') 
  ? 'http://localhost:8000' 
  : window.location.origin;

function App() {
  const [events, setEvents] = useState([]);
  const [latestEvent, setLatestEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [activeAlert, setActiveAlert] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [modalType, setModalType] = useState('screenshot'); // 'screenshot' | 'video'

  const fetchEvents = async () => {
    try {
      // 1. Health check
      const healthRes = await fetch(`${BACKEND_URL}/health`);
      if (healthRes.ok) {
        setApiConnected(true);
      } else {
        setApiConnected(false);
      }

      // 2. Fetch all events
      const eventsRes = await fetch(`${BACKEND_URL}/events`);
      if (eventsRes.ok) {
        const eventsData = await eventsRes.json();
        setEvents(eventsData);
        
        // 3. Fetch latest event
        const latestRes = await fetch(`${BACKEND_URL}/latest-event`);
        if (latestRes.ok) {
          const latestData = await latestRes.json();
          if (latestData && Object.keys(latestData).length > 0) {
            // Check if this is a brand new alert we haven't seen yet
            if (latestEvent && latestData.event_id !== latestEvent.event_id) {
              // Sound a local browser notification beep
              playNotificationSound();
              // Trigger active alert panel
              setActiveAlert(latestData);
            } else if (!latestEvent) {
              // Initial load, if it occurred in the last 30 seconds, show it as active
              const eventTime = new Date(latestData.timestamp);
              const now = new Date();
              if (now - eventTime < 30000) {
                setActiveAlert(latestData);
              }
            }
            setLatestEvent(latestData);
          }
        }
      }
      setLoading(false);
    } catch (error) {
      console.error("Error connecting to CCTV backend API:", error);
      setApiConnected(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    
    // Set up polling interval
    const interval = setInterval(fetchEvents, 3000);
    return () => clearInterval(interval);
  }, [latestEvent]);

  const playNotificationSound = () => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.type = 'sine';
      // Alarm frequency sequence: High pitch warning beep
      oscillator.frequency.setValueAtTime(880, audioContext.currentTime); // A5 note
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      
      oscillator.start();
      oscillator.stop(audioContext.currentTime + 0.15);
      
      // Secondary beep
      setTimeout(() => {
        const osc2 = audioContext.createOscillator();
        const gain2 = audioContext.createGain();
        osc2.connect(gain2);
        gain2.connect(audioContext.destination);
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(880, audioContext.currentTime);
        gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
        osc2.start();
        osc2.stop(audioContext.currentTime + 0.25);
      }, 200);
    } catch (e) {
      console.warn("Audio Context playback not allowed by browser permissions.", e);
    }
  };

  const handleMediaOpen = (event, type) => {
    setSelectedEvent(event);
    setModalType(type);
  };

  const handleCloseModal = () => {
    setSelectedEvent(null);
  };

  const dismissActiveAlert = () => {
    setActiveAlert(null);
  };

  const formatRelativeTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    
    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="dashboard-container">
      {/* Dashboard Header */}
      <header className="dashboard-header glass-panel">
        <div className="brand-section">
          <div className="brand-logo">
            <ShieldAlert size={28} />
          </div>
          <div className="brand-title">
            <h1>SentryPose AI</h1>
            <p>CCTV Fall & Fainting Detection Gateway</p>
          </div>
        </div>

        <div className="status-section">
          <div className="status-indicator">
            <div className={`status-dot ${apiConnected ? 'active' : ''}`}></div>
            <span>{apiConnected ? 'API Connected' : 'Connecting to API...'}</span>
          </div>
          
          <div className="alert-counter">
            <span>{events.length} Incident{events.length !== 1 ? 's' : ''} Logged</span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Live Feed */}
        <section className="feed-panel glass-panel">
          <div className="feed-header">
            <div className="feed-title">
              <Activity size={18} className="live-badge" style={{ animation: 'none' }} />
              <span>Live Surveillance Feed</span>
              <span className="live-badge">Live</span>
            </div>
            <div style={{ color: var => var('--text-secondary'), fontSize: '0.8rem' }}>
              Source: {BACKEND_URL}/video_feed
            </div>
          </div>
          <div className="feed-viewports">
            {apiConnected ? (
              <img 
                src={`${BACKEND_URL}/video_feed`} 
                alt="Live Camera Feed Stream" 
                className="video-element"
                onError={(e) => {
                  e.target.style.display = 'none';
                  console.error("Video stream closed or unreachable.");
                }}
              />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', color: 'var(--text-secondary)' }}>
                <RefreshCw size={36} style={{ animation: 'spin 2s linear infinite' }} />
                <span>Awaiting connection to CCTV backend stream...</span>
              </div>
            )}
            <div className="feed-overlay-info">
              YOLOv11 Pose + ByteTrack Tracker ACTIVE
            </div>
          </div>
        </section>

        {/* Right Column: Active Alerts / Latest Event */}
        <section className="incident-panel glass-panel">
          <div className="panel-title">
            <AlertTriangle size={18} color="var(--accent-red)" />
            <span>Active Incident Monitor</span>
          </div>
          
          <div className="incident-content">
            {activeAlert ? (
              <div className="alert-active-state">
                <div className="alert-banner-top">
                  <div className="alert-banner-icon">
                    <ShieldAlert size={28} />
                  </div>
                  <div className="alert-banner-text">
                    <h3>FALL DETECTED</h3>
                    <p>Tracked Subject #{activeAlert.person_id} • {formatRelativeTime(activeAlert.timestamp)}</p>
                  </div>
                  <button 
                    onClick={dismissActiveAlert} 
                    style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                  >
                    <X size={16} />
                  </button>
                </div>
                
                {activeAlert.screenshot_path && (
                  <div 
                    className="alert-screenshot-preview"
                    onClick={() => handleMediaOpen(activeAlert, 'screenshot')}
                  >
                    <img src={`${BACKEND_URL}${activeAlert.screenshot_path}`} alt="Incident Screenshot" />
                    <span className="preview-badge"><Maximize2 size={12} /> View Frame</span>
                  </div>
                )}
                
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-label">Confidence</div>
                    <div className="stat-value high-confidence">{(activeAlert.confidence_score * 100).toFixed(0)}%</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-label">Fall Velocity</div>
                    <div className="stat-value">
                      {activeAlert.details?.peak_velocity ? `${activeAlert.details.peak_velocity.toFixed(0)} px/s` : 'N/A'}
                    </div>
                  </div>
                </div>
                
                {activeAlert.video_path && (
                  <button 
                    className="btn-primary"
                    onClick={() => handleMediaOpen(activeAlert, 'video')}
                  >
                    <Play size={16} fill="#fff" />
                    Replay Recorded Clip
                  </button>
                )}
              </div>
            ) : latestEvent ? (
              <div className="alert-active-state" style={{ opacity: 0.85 }}>
                <div className="alert-banner-top" style={{ background: 'rgba(255, 149, 0, 0.05)', border: '1px solid rgba(255, 149, 0, 0.15)' }}>
                  <div className="alert-banner-icon" style={{ color: 'var(--accent-orange)' }}>
                    <ShieldAlert size={28} />
                  </div>
                  <div className="alert-banner-text">
                    <h3 style={{ color: 'var(--accent-orange)' }}>Recent Event</h3>
                    <p>Tracked Subject #{latestEvent.person_id} • {new Date(latestEvent.timestamp).toLocaleTimeString()}</p>
                  </div>
                </div>
                
                {latestEvent.screenshot_path && (
                  <div 
                    className="alert-screenshot-preview"
                    onClick={() => handleMediaOpen(latestEvent, 'screenshot')}
                  >
                    <img src={`${BACKEND_URL}${latestEvent.screenshot_path}`} alt="Incident Screenshot" />
                    <span className="preview-badge"><Maximize2 size={12} /> View Frame</span>
                  </div>
                )}
                
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-label">Confidence</div>
                    <div className="stat-value" style={{ color: 'var(--accent-orange)' }}>{(latestEvent.confidence_score * 100).toFixed(0)}%</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-label">Verification</div>
                    <div className="stat-value" style={{ color: 'var(--accent-green)', fontSize: '0.9rem' }}>Motionless Passed</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="no-alerts-state">
                <CheckCircle size={48} className="no-alerts-icon" />
                <h3>No Incidents Registered</h3>
                <p style={{ fontSize: '0.85rem' }}>No fall or fainting activities detected in the viewport.</p>
              </div>
            )}
          </div>
        </section>
      </div>

      {/* History Log Section */}
      <section className="history-section">
        <div className="history-panel glass-panel">
          <div className="history-title">
            <h2>
              <Database size={20} color="var(--accent-blue)" />
              <span>Historical Fall Incident Logs</span>
            </h2>
            <button className="btn-icon" onClick={fetchEvents} title="Refresh Logs">
              <RefreshCw size={16} />
            </button>
          </div>
          
          <div className="table-wrapper">
            <table className="events-table">
              <thead>
                <tr>
                  <th>Event ID</th>
                  <th>Person ID</th>
                  <th>Timestamp</th>
                  <th>Confidence</th>
                  <th>Key Metrics</th>
                  <th>Screenshots</th>
                  <th>Video Clip</th>
                </tr>
              </thead>
              <tbody>
                {events.length > 0 ? (
                  events.map((event) => (
                    <tr key={event.event_id}>
                      <td style={{ fontWeight: '600' }}>#{event.event_id}</td>
                      <td>Subject #{event.person_id}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={14} color="var(--text-secondary)" />
                          <span>{new Date(event.timestamp).toLocaleString()}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`confidence-badge ${event.confidence_score >= 0.8 ? 'high' : 'medium'}`}>
                          {(event.confidence_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          V: {event.details?.peak_velocity ? `${event.details.peak_velocity.toFixed(0)} px/s` : 'N/A'} | 
                          Still: {event.details?.horizontal_duration ? `${event.details.horizontal_duration.toFixed(0)}s` : '5s'}
                        </div>
                      </td>
                      <td>
                        {event.screenshot_path ? (
                          <button 
                            className="btn-table-action"
                            onClick={() => handleMediaOpen(event, 'screenshot')}
                          >
                            <Eye size={12} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                            View
                          </button>
                        ) : 'N/A'}
                      </td>
                      <td>
                        {event.video_path ? (
                          <button 
                            className="btn-table-action"
                            style={{ background: 'rgba(52, 199, 89, 0.1)', borderColor: 'rgba(52, 199, 89, 0.2)', color: 'var(--accent-green)' }}
                            onClick={() => handleMediaOpen(event, 'video')}
                          >
                            <Video size={12} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                            Replay
                          </button>
                        ) : 'N/A'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="empty-table-state">
                      {loading ? 'Fetching historical database events...' : 'No fall/fainting events found in log database.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Modal Viewers */}
      {selectedEvent && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content glass-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {modalType === 'screenshot' ? 'Incident Screenshot' : 'Incident Video Clip'} 
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 'normal', marginLeft: '12px' }}>
                  Event #{selectedEvent.event_id} (Subject #{selectedEvent.person_id})
                </span>
              </h3>
              <button className="modal-close" onClick={handleCloseModal}>
                <X size={20} />
              </button>
            </div>
            
            <div className="modal-body">
              <div className="modal-media-viewer">
                {modalType === 'screenshot' ? (
                  <img src={`${BACKEND_URL}${selectedEvent.screenshot_path}`} alt="Annotated Fall Frame" />
                ) : (
                  <video 
                    src={`${BACKEND_URL}${selectedEvent.video_path}`} 
                    controls 
                    autoPlay
                    loop
                    className="video-element"
                  >
                    Your browser does not support HTML5 video playback.
                  </video>
                )}
              </div>
              
              <div className="modal-meta-grid">
                <div className="stat-item">
                  <div className="stat-label">Date & Time</div>
                  <div className="stat-value" style={{ fontSize: '0.95rem' }}>{new Date(selectedEvent.timestamp).toLocaleString()}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Confidence</div>
                  <div className="stat-value" style={{ color: selectedEvent.confidence_score >= 0.8 ? 'var(--accent-red)' : 'var(--accent-orange)' }}>
                    {(selectedEvent.confidence_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Velocity / Motion</div>
                  <div className="stat-value" style={{ fontSize: '0.95rem' }}>
                    {selectedEvent.details?.peak_velocity ? `${selectedEvent.details.peak_velocity.toFixed(0)} px/s` : 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
