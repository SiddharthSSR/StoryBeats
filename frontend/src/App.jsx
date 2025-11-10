import { useState } from 'react'
import PhotoUpload from './components/PhotoUpload'
import SongResults from './components/SongResults'
import './App.css'

// API URL configuration for production deployment
// In production, VITE_API_URL should be set to your backend URL
// In development, it uses the Vite proxy (empty string)
const API_URL = import.meta.env.VITE_API_URL || ''

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState(null)
  const [offset, setOffset] = useState(5)
  const [sessionId, setSessionId] = useState(null)
  const [feedback, setFeedback] = useState({}) // Track user feedback for each song

  const handlePhotoUpload = async (file) => {
    setLoading(true)
    setError(null)
    setResults(null)
    setOffset(5) // Reset offset
    setSessionId(null) // Reset session
    setFeedback({}) // Reset feedback

    const formData = new FormData()
    formData.append('photo', file)

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        setResults(data)
        setSessionId(data.session_id) // Track session ID
      } else {
        setError(data.error || 'Failed to analyze photo')
      }
    } catch (err) {
      setError('Network error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGetMoreSongs = async () => {
    if (!results || !results.analysis) return

    // Track load more click (implicit signal)
    trackImplicitFeedback('load_more', null, 0.5)

    setLoadingMore(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/more-songs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis: results.analysis,
          offset: offset,
          session_id: sessionId, // Send session ID to track duplicates
        }),
      })

      const data = await response.json()

      if (data.success) {
        // Replace the current songs with new recommendations
        setResults({
          ...results,
          songs: data.songs,
        })
        // Increment offset for next request
        setOffset(offset + 5)
      } else {
        setError(data.error || 'Failed to get more songs')
      }
    } catch (err) {
      setError('Network error: ' + err.message)
    } finally {
      setLoadingMore(false)
    }
  }

  const handleFeedback = async (song, feedbackValue) => {
    if (!sessionId) {
      console.error('No session ID available')
      return
    }

    try {
      const response = await fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          song_id: song.id,
          song_name: song.name,
          artist_name: song.artist,
          feedback: feedbackValue, // 1 for like, -1 for dislike
        }),
      })

      const data = await response.json()

      if (data.success) {
        // Update local feedback state
        setFeedback((prev) => ({
          ...prev,
          [song.id]: feedbackValue,
        }))
      } else {
        console.error('Failed to submit feedback:', data.error)
      }
    } catch (err) {
      console.error('Network error submitting feedback:', err)
    }
  }

  // Track implicit feedback signals (Phase 2: Implicit Feedback)
  const trackImplicitFeedback = async (signalType, song = null, weight = 1.0) => {
    if (!sessionId) return

    try {
      await fetch(`${API_URL}/api/feedback/implicit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          song_id: song?.id || '',
          song_name: song?.name || '',
          artist_name: song?.artist || '',
          signal_type: signalType,
          weight: weight,
        }),
      })
      // Fire and forget - don't wait for response
    } catch (err) {
      // Silently fail - implicit signals are not critical
      console.debug('Implicit feedback tracking:', err)
    }
  }

  const handleReset = () => {
    setResults(null)
    setError(null)
    setOffset(5)
    setSessionId(null)
    setFeedback({})
  }

  return (
    <div className="app">
      <header className="header">
        <h1>StoryBeats</h1>
        <p className="tagline">Find the perfect song for your Instagram story</p>
      </header>

      <main className="main">
        {!results && !loading && (
          <PhotoUpload onUpload={handlePhotoUpload} error={error} />
        )}

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Analyzing your photo...</p>
          </div>
        )}

        {results && (
          <SongResults
            analysis={results.analysis}
            songs={results.songs}
            onReset={handleReset}
            onGetMore={handleGetMoreSongs}
            loadingMore={loadingMore}
            onFeedback={handleFeedback}
            feedback={feedback}
            onImplicitFeedback={trackImplicitFeedback}
          />
        )}
      </main>

      <footer className="footer">
        <p>Powered by Spotify and AI</p>
      </footer>
    </div>
  )
}

export default App
