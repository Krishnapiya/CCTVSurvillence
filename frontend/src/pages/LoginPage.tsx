import React, { useState } from 'react'
import { LogIn } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { loginSuccess } from '../store/authSlice'
import { getBackendBaseUrl, getHost, getPort } from '../services/dataService'
import { branding, getPageSubtitle } from '../config/branding'

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const dispatch = useDispatch()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const formData = new URLSearchParams()
      formData.append('username', username === 'admin' ? 'admin@surveillance.com' : username)
      formData.append('password', password)

      const backendHost = getHost()
      let backendPort = getPort()
      let response: Response | undefined

      try {
        response = await fetch(`${getBackendBaseUrl()}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData,
        })
      } catch (err) {
        if (import.meta.env.VITE_BACKEND_HOST) throw err
        const candidatePorts = ['8005', '8000', '8001', '8010']
        for (const port of candidatePorts) {
          if (port === backendPort) continue
          try {
            response = await fetch(`http://${backendHost}:${port}/api/v1/auth/login`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              body: formData,
            })
            if (response.ok) {
              localStorage.setItem('surv_backend_port', port)
              break
            }
          } catch {
            /* try next port */
          }
        }
        if (!response?.ok) throw err
      }

      if (response?.ok) {
        const data = await response.json()
        localStorage.setItem('surv_auth', 'true')
        localStorage.setItem('surv_token', data.access_token)
        localStorage.setItem('surv_username', username)
        dispatch(loginSuccess({ username }))
        navigate('/')
        return
      }

      const errorData = await response?.json().catch(() => ({}))
      setError(errorData.detail || 'Invalid credentials')
    } catch {
      setError('Could not connect to the station backend. Verify the server is running.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <img
            src="/assets/images/logo-2.png"
            alt="Kerala Prisons"
            className="login-logo"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
          <h1>{branding.organization}</h1>
          <p>{getPageSubtitle()}</p>
          <div className="station-badge login-station-badge">
            <span className="station-badge-code">{branding.stationCode}</span>
            <span className="station-badge-name">{branding.stationName}</span>
          </div>
        </div>

        <form className="login-form" onSubmit={handleLogin}>
          <h2>Sign In</h2>
          {error && <div className="login-error">{error}</div>}

          <label>
            Username
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              autoComplete="username"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              autoComplete="current-password"
              required
            />
          </label>

          <button type="submit" className="login-btn" disabled={submitting}>
            <LogIn size={18} />
            {submitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="login-footer">
          <img
            src="/assets/images/gvt.png"
            alt="Government of Kerala"
            className="login-govt"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default LoginPage
