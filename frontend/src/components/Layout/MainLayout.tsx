import React, { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Camera,
  Map,
  ClipboardList,
  History,
  Settings,
  RefreshCw,
  LogOut,
  Bell,
  AlertTriangle,
} from 'lucide-react'
import SiteHeader from '../SiteHeader'
import { dataService } from '../../services/dataService'
import { branding } from '../../config/branding'

const NAV_ITEMS = [
  { text: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { text: 'Camera Management', icon: Camera, path: '/cameras' },
  { text: 'Region of Interest', icon: Map, path: '/rois' },
  { text: 'Event Alert Jobs', icon: ClipboardList, path: '/event-jobs' },
  { text: 'Event Logs', icon: History, path: '/logs' },
  { text: 'Settings', icon: Settings, path: '/settings' },
]

const PAGE_DESCRIPTIONS: Record<string, string> = {
  '/': `Live monitoring for ${branding.stationName} — cameras, alerts, and AI detections`,
  '/cameras': 'Configure and monitor CCTV cameras at this station',
  '/rois': 'Define regions of interest for event detection',
  '/roi': 'Draw and edit ROI zones on camera feeds',
  '/event-jobs': 'Schedule automated alert rules by camera and event type',
  '/logs': 'Review detected events and alert history',
  '/settings': 'Station profile and notification preferences',
}

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [logs, setLogs] = useState<any[]>([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const username = localStorage.getItem('surv_username') || 'Admin'

  const currentNav = NAV_ITEMS.find(
    (item) => item.path === location.pathname || (item.path === '/' && location.pathname === '/dashboard')
  )
  const pageTitle = currentNav?.text || 'Surveillance System'
  const pageDescription = PAGE_DESCRIPTIONS[location.pathname] || branding.masterDashboardHint

  useEffect(() => {
    const fetchLogs = async () => {
      const fetched = await dataService.getLogs()
      setLogs(fetched || [])
    }
    fetchLogs()
    const interval = setInterval(fetchLogs, 3000)
    return () => clearInterval(interval)
  }, [refreshKey])

  const handleLogout = () => {
    localStorage.removeItem('surv_auth')
    localStorage.removeItem('surv_token')
    localStorage.removeItem('surv_username')
    navigate('/login')
  }

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/' || location.pathname === '/dashboard'
    return location.pathname === path || location.pathname.startsWith(`${path}/`)
  }

  return (
    <div className="app-shell">
      <SiteHeader username={username} onLogout={handleLogout} />

      <div className="app-layout">
        <aside className="sidebar">
          <nav className="sidebar-nav">
            {NAV_ITEMS.map(({ text, icon: Icon, path }) => (
              <button
                key={path}
                type="button"
                className={`nav-item ${isActive(path) ? 'active' : ''}`}
                onClick={() => navigate(path)}
              >
                <Icon size={18} />
                {text}
              </button>
            ))}
          </nav>
          <div className="sync-status">
            <span className="dot" />
            Connected to backend · auto-refresh
          </div>
        </aside>

        <main className="main-content">
          <div className="toolbar">
            <div className="toolbar-notifications">
              <button
                type="button"
                className="refresh-btn notification-btn"
                onClick={() => setShowNotifications((v) => !v)}
              >
                <Bell size={16} />
                Alerts
                {logs.length > 0 && <span className="notification-count">{logs.length}</span>}
              </button>
              {showNotifications && (
                <div className="notifications-panel">
                  <div className="notifications-panel-header">Recent Alerts</div>
                  {logs.length === 0 ? (
                    <div className="notifications-empty">No new notifications</div>
                  ) : (
                    logs.slice(0, 5).map((log, i) => (
                      <button
                        key={i}
                        type="button"
                        className="notification-item"
                        onClick={() => {
                          setShowNotifications(false)
                          navigate('/logs')
                        }}
                      >
                        <AlertTriangle size={16} className="notification-icon" />
                        <div>
                          <div className="notification-title">{log.event}</div>
                          <div className="notification-time">{log.timestamp}</div>
                        </div>
                      </button>
                    ))
                  )}
                  <button
                    type="button"
                    className="notifications-view-all"
                    onClick={() => {
                      setShowNotifications(false)
                      navigate('/logs')
                    }}
                  >
                    View all logs
                  </button>
                </div>
              )}
            </div>
            <button type="button" className="refresh-btn" onClick={() => setRefreshKey((k) => k + 1)}>
              <RefreshCw size={16} />
              Refresh
            </button>
            <button type="button" className="logout-btn" onClick={handleLogout}>
              <LogOut size={16} />
              Logout
            </button>
          </div>

          <div className="page-header">
            <h2>{pageTitle}</h2>
            <p>{pageDescription}</p>
          </div>

          <Outlet key={refreshKey} />
        </main>
      </div>
    </div>
  )
}

export default MainLayout
