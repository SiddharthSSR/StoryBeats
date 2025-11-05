import { useState } from 'react'
import PhotoUpload from './components/PhotoUpload'
import SongResults from './components/SongResults'
import logo from './assets/storybeats-logo.png'
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

  const handlePhotoUpload = async (file) => {
    setLoading(true)
    setError(null)
    setResults(null)
    setOffset(5) // Reset offset
    setSessionId(null) // Reset session

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

  const handleReset = () => {
    setResults(null)
    setError(null)
    setOffset(5)
    setSessionId(null)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <img src={logo} alt="StoryBeats Logo" className="logo" />
          <div className="header-text">
            <h1>StoryBeats</h1>
            <p className="tagline">Find the perfect song for your Instagram story</p>
          </div>
        </div>
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
