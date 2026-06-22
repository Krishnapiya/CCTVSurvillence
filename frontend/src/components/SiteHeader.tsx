import { branding, getPageSubtitle } from '../config/branding'

interface SiteHeaderProps {
  username?: string
  onLogout?: () => void
}

export default function SiteHeader({ username, onLogout }: SiteHeaderProps) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <div className="site-header-logos">
          <a href="https://keralaprisons.gov.in/index.html" target="_blank" rel="noreferrer">
            <img
              src="/assets/images/logo-2.png"
              alt="Kerala Prisons & Correctional Services"
              className="logo-prisons"
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
            />
          </a>
          <img
            src="/assets/images/gvt.png"
            alt="Government of Kerala"
            className="logo-govt"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        </div>
        <div className="site-header-title">
          <h1>{branding.organization}</h1>
          <p>{getPageSubtitle()}</p>
          <div className="station-badge">
            <span className="station-badge-code">{branding.stationCode}</span>
            <span className="station-badge-name">{branding.stationName}</span>
            <span className="station-badge-install mono">{branding.installationId}</span>
          </div>
        </div>
        {username && (
          <div className="site-header-user">
            <span>{username}</span>
            {onLogout && (
              <button type="button" className="header-logout-btn" onClick={onLogout}>
                Logout
              </button>
            )}
          </div>
        )}
      </div>
      <div className="site-header-bar" />
    </header>
  )
}
