import './SongResults.css'

function SongResults({ analysis, songs, onReset, onGetMore, loadingMore }) {
  const safeAnalysis = analysis || {}
  const safeSongs = Array.isArray(songs) ? songs : []

  const mood = safeAnalysis.mood || 'Unknown'
  const description = safeAnalysis.description || 'No description available.'
  const themes = Array.isArray(safeAnalysis.themes) && safeAnalysis.themes.length > 0
    ? safeAnalysis.themes.join(', ')
    : 'Not specified'

  const clampPercent = (value) => {
    if (typeof value !== 'number' || Number.isNaN(value)) return 0
    return Math.min(100, Math.max(0, Math.round(value * 100)))
  }

  return (
    <div className="song-results">
      <div className="analysis-section">
        <h2>Photo Analysis</h2>
        <div className="analysis-details">
          <div className="analysis-item">
            <span className="label">Mood:</span>
            <span className="value">{mood}</span>
          </div>
          <div className="analysis-item">
            <span className="label">Description:</span>
            <span className="value">{description}</span>
          </div>
          <div className="analysis-item">
            <span className="label">Themes:</span>
            <span className="value">{themes}</span>
          </div>
          <div className="analysis-metrics">
            <div className="metric">
              <span className="metric-label">Energy</span>
              <div className="metric-bar">
                <div
                  className="metric-fill"
                  style={{ width: `${clampPercent(safeAnalysis.energy)}%` }}
                ></div>
              </div>
            </div>
            <div className="metric">
              <span className="metric-label">Positivity</span>
              <div className="metric-bar">
                <div
                  className="metric-fill"
                  style={{ width: `${clampPercent(safeAnalysis.valence)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="songs-section">
        <h2>Recommended Songs</h2>
        {safeSongs.length > 0 ? (
          <div className="songs-list">
            {safeSongs.map((song, index) => (
              <div key={song.id || index} className="song-card">
                <div className="song-number">{index + 1}</div>
                {song.album_cover && (
                  <img
                    src={song.album_cover}
                    alt={song.album}
                    className="album-cover"
                  />
                )}
                <div className="song-info">
                  <h3 className="song-name">{song.name || 'Untitled Track'}</h3>
                  <p className="song-artist">{song.artist || 'Unknown Artist'}</p>
                  <p className="song-album">{song.album || 'Unknown Album'}</p>
                </div>
                {song.preview_url && (
                  <audio controls className="song-preview">
                    <source src={song.preview_url} type="audio/mpeg" />
                    Your browser does not support the audio element.
                  </audio>
                )}
                {song.spotify_url && (
                  <a
                    href={song.spotify_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="spotify-link"
                  >
                    Open in Spotify
                  </a>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="no-songs">
            <p>We couldn&apos;t load song recommendations. Try refreshing or upload the photo again.</p>
          </div>
        )}
      </div>

      <div className="action-buttons">
        <button
          className="more-songs-button"
          onClick={onGetMore}
          disabled={loadingMore}
        >
          {loadingMore ? (
            <>
              <div className="button-spinner"></div>
              Loading More Songs...
            </>
          ) : (
            <>
              <svg className="refresh-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Get 5 More Songs
            </>
          )}
        </button>

        <button className="reset-button" onClick={onReset}>
          Upload Another Photo
        </button>
      </div>
    </div>
  )
}

export default SongResults
