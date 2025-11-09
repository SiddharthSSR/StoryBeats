# StoryBeats Backend API

Flask-based REST API for analyzing Instagram story photos and recommending Spotify songs.

## Features

- Photo upload and analysis using LLM (Claude/GPT-4)
- Mood and theme detection from images
- Spotify song recommendations based on image analysis
- Support for multiple LLM providers (Anthropic, OpenAI, Gemini)
- **User feedback system** - Track likes/dislikes to improve recommendations
- **Background LLM reranking** - Verify and rerank songs for better matches
- **Instant "Load More"** - Pre-cached songs for zero-latency pagination
- **SQLite database** - Store feedback and reranked results

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

**Required:**
- `SPOTIFY_CLIENT_ID` - From [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- `SPOTIFY_CLIENT_SECRET` - From Spotify Developer Dashboard
- Choose one LLM provider and add its API key:
  - `ANTHROPIC_API_KEY` - From [Anthropic Console](https://console.anthropic.com/)
  - `OPENAI_API_KEY` - From [OpenAI Platform](https://platform.openai.com/api-keys)
  - `GEMINI_API_KEY` - From [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3. Run the Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /health
```

### Analyze Photo and Get Song Recommendations
```
POST /api/analyze
Content-Type: multipart/form-data

Body:
- photo: image file (png, jpg, jpeg, gif, webp, heic, heif, mpo)

Response:
{
  "success": true,
  "analysis": {
    "mood": "happy",
    "themes": ["summer", "beach", "vacation"],
    "description": "...",
    "genres": ["pop", "indie", "electronic"],
    "energy": 0.8,
    "valence": 0.9,
    "keywords": ["sunshine", "waves", "relaxing"]
  },
  "songs": [
    {
      "id": "...",
      "name": "Song Name",
      "artist": "Artist Name",
      "album": "Album Name",
      "preview_url": "...",
      "spotify_url": "...",
      "album_art": "...",
      "duration_ms": 180000
    },
    // ... 4 more songs (30 total cached for "load more")
  ],
  "session_id": "..."  // Used for feedback and "load more"
}

Note: Background reranking starts automatically after returning initial songs
```

### Load More Songs
```
POST /api/more-songs
Content-Type: application/json

Body:
{
  "session_id": "...",  // From /api/analyze response
  "offset": 5           // Optional, defaults to 5
}

Response:
{
  "success": true,
  "songs": [ ... ],     // Next 5 songs (potentially reranked)
  "cached": true        // true if instant from cache
}
```

### Submit User Feedback
```
POST /api/feedback
Content-Type: application/json

Body:
{
  "session_id": "...",
  "song_id": "...",
  "song_name": "Song Name",
  "artist_name": "Artist Name",
  "feedback": 1         // 1 for like, -1 for dislike
}

Response:
{
  "success": true,
  "feedback_id": 42
}
```

### Get Feedback Statistics
```
GET /api/feedback/stats

Response:
{
  "likes": 150,
  "dislikes": 30,
  "total": 180,
  "like_rate": 0.833
}
```

### Get Spotify Auth URL
```
GET /api/spotify/auth

Response:
{
  "auth_url": "https://accounts.spotify.com/authorize?..."
}
```

### Spotify OAuth Callback
```
POST /api/spotify/callback
Content-Type: application/json

Body:
{
  "code": "authorization_code"
}

Response:
{
  "success": true,
  "token_info": { ... }
}
```

## Project Structure

```
backend/
├── app.py                       # Main Flask application
├── requirements.txt             # Python dependencies
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration management
├── services/
│   ├── __init__.py
│   ├── image_analyzer.py       # LLM image analysis
│   ├── spotify_service.py      # Spotify API integration
│   ├── feedback_store.py       # User feedback database layer
│   └── verify_llm.py           # Background LLM reranking
├── tests/                      # Test files
│   ├── test_feedback_reranking.py
│   ├── test_performance.py
│   └── ...
├── docs/                       # Documentation
│   ├── FEEDBACK_RERANKING.md
│   ├── PERFORMANCE_ANALYSIS.md
│   ├── OPTIMIZATION_SUMMARY.md
│   ├── TESTING_GUIDE.md
│   └── REFACTOR_SUMMARY.md
├── uploads/                    # Temporary file storage
└── storybeats_feedback.db      # SQLite database (auto-created)
```

## How It Works

### Initial Upload Flow
1. User uploads a photo intended for Instagram story
2. Image is analyzed by LLM (Claude/GPT-4) to extract:
   - Mood and emotional tone
   - Visual themes
   - Suggested music genres
   - Energy and valence levels
   - Descriptive keywords
3. Analysis is used to search Spotify for matching songs
4. **Top 5 songs returned immediately** (7-10 seconds)
5. **30 total songs cached** for instant "load more"
6. **Background thread starts** to verify and rerank all cached songs

### Background Reranking (Phase 2)
1. After returning initial results, a background thread starts
2. LLM analyzes the image alongside all 30 cached songs
3. Songs are reranked by confidence score (0.0-1.0)
4. Reranked results stored in database and session cache
5. When user clicks "Load More", they get **improved recommendations**

### User Feedback Loop (Phase 1)
1. User can like/dislike songs via `/api/feedback` endpoint
2. Feedback stored in SQLite database with image analysis context
3. Data used to analyze patterns and improve future recommendations

### Performance
- **Initial response**: 7-10s (user sees songs immediately)
- **Background reranking**: 5-10s (doesn't block user)
- **Load more**: <0.01s (instant from reranked cache)
- **Cost**: ~$0.008 per upload (with Anthropic Claude)

## Development

To run in development mode:
```bash
export FLASK_ENV=development
python app.py
```

## Testing

Run the complete test suite:
```bash
# Test feedback and reranking features
python3 tests/test_feedback_reranking.py

# Test performance optimizations
python3 tests/test_performance.py

# Test "load more" functionality
python3 tests/test_load_more.py

# Or run all tests
python3 -m pytest tests/
```

## Database

The application uses SQLite to store:
- **User feedback** (likes/dislikes with image analysis context)
- **Session data** (image hashes, analyses, timestamps)
- **Reranked results** (LLM-verified song rankings)

Database is automatically created on first run as `storybeats_feedback.db`.

### Database Schema
- `sessions` - Track each image upload session
- `feedback` - Store user likes/dislikes
- `reranked_results` - Cache LLM-verified rankings

See `FEEDBACK_RERANKING.md` for detailed schema documentation.

## Advanced Features

### Feedback System
Track user preferences to improve recommendations:
```javascript
// Like a song
fetch('/api/feedback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    song_id: song.id,
    song_name: song.name,
    artist_name: song.artist,
    feedback: 1  // 👍
  })
});
```

### Load More (Instant)
Pre-cached songs make pagination instant:
```javascript
// Load more songs
fetch('/api/more-songs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    offset: 5  // Optional
  })
});
```

## Documentation

- **[FEEDBACK_RERANKING.md](docs/FEEDBACK_RERANKING.md)** - Detailed documentation of feedback and reranking system
- **[PERFORMANCE_ANALYSIS.md](docs/PERFORMANCE_ANALYSIS.md)** - Performance optimizations and benchmarks
- **[OPTIMIZATION_SUMMARY.md](docs/OPTIMIZATION_SUMMARY.md)** - Summary of optimization improvements
- **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Guide for running tests
- **[REFACTOR_SUMMARY.md](docs/REFACTOR_SUMMARY.md)** - Summary of code refactoring

## Notes

- Uploaded images are temporarily stored and deleted after background reranking
- Maximum file size: 16MB
- Supported formats: PNG, JPG, JPEG, GIF, WebP, HEIC, HEIF, MPO
- LLM analysis includes fallback to default values on error
- Background reranking runs automatically, doesn't block user
- Database grows with user feedback (consider periodic cleanup in production)
