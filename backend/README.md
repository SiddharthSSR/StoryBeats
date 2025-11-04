# StoryBeats Backend API

Flask-based REST API for analyzing Instagram story photos and recommending Spotify songs.

## Features

- Photo upload and analysis using LLM (Claude/GPT-4)
- Mood and theme detection from images
- Spotify song recommendations based on image analysis
- Support for multiple LLM providers (Anthropic, OpenAI, Gemini)

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
- photo: image file (png, jpg, jpeg, gif, webp)

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
    // ... 4 more songs
  ]
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
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── services/
│   ├── __init__.py
│   ├── image_analyzer.py    # LLM image analysis
│   └── spotify_service.py   # Spotify API integration
└── uploads/                 # Temporary file storage
```

## How It Works

1. User uploads a photo intended for Instagram story
2. Image is analyzed by LLM (Claude/GPT-4) to extract:
   - Mood and emotional tone
   - Visual themes
   - Suggested music genres
   - Energy and valence levels
   - Descriptive keywords
3. Analysis is used to search Spotify for matching songs
4. Top 5 song recommendations are returned with full metadata

## Development

To run in development mode:
```bash
export FLASK_ENV=development
python app.py
```

## Notes

- Uploaded images are temporarily stored and deleted after processing
- Maximum file size: 16MB
- Supported formats: PNG, JPG, JPEG, GIF, WebP
- LLM analysis includes fallback to default values on error
