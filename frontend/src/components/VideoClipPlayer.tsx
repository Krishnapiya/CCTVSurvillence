import { useEffect, useState } from 'react'
import { getBackendBaseUrl } from '../services/dataService'

interface VideoClipPlayerProps {
  eventId: string
  poster?: string
  autoPlay?: boolean
  className?: string
}

export default function VideoClipPlayer({
  eventId,
  poster,
  autoPlay = true,
  className = 'clip-player',
}: VideoClipPlayerProps) {
  const [src, setSrc] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!eventId) {
      setLoading(false)
      setError('No event selected')
      return
    }

    let objectUrl: string | null = null
    const controller = new AbortController()

    const loadClip = async () => {
      setLoading(true)
      setError(null)
      setSrc(null)

      try {
        const token = localStorage.getItem('surv_token')
        const response = await fetch(`${getBackendBaseUrl()}/api/v1/events/${eventId}/clip`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error('Clip unavailable')
        }

        const blob = await response.blob()
        if (!blob.size) {
          throw new Error('Empty video clip')
        }

        objectUrl = URL.createObjectURL(blob)
        setSrc(objectUrl)
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setError('This clip cannot be played in the browser. Use Download to open it in VLC.')
        }
      } finally {
        setLoading(false)
      }
    }

    loadClip()

    return () => {
      controller.abort()
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [eventId])

  if (loading) {
    return <div className="clip-placeholder">Loading video...</div>
  }

  if (error || !src) {
    return (
      <div className="clip-placeholder">
        <p>{error || 'Video not available'}</p>
        {poster && (
          <img
            src={poster}
            alt="Event snapshot"
            style={{ maxWidth: '100%', maxHeight: 240, marginTop: 12, opacity: 0.85 }}
          />
        )}
      </div>
    )
  }

  return (
    <video
      className={className}
      src={src}
      controls
      autoPlay={autoPlay}
      playsInline
      poster={poster}
      style={{ width: '100%', height: '100%', objectFit: 'contain', background: '#000' }}
    >
      Your browser does not support video playback.
    </video>
  )
}

export function getEventClipDownloadUrl(eventId: string) {
  return `${getBackendBaseUrl()}/api/v1/events/${eventId}/clip`
}
