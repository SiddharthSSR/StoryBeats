# 🎵 StoryBeats

An AI-powered web application that analyzes your Instagram story photos and suggests the perfect Spotify songs to match the vibe! Get personalized music recommendations with a smart mix of English and Hindi/Indian songs.

## ✨ Features

### 🎨 Smart Photo Analysis
- **AI-Powered Image Understanding**: Uses OpenAI GPT-4o or Anthropic Claude to deeply analyze your photos
- **Nuanced Mood Detection**: Goes beyond basic emotions - detects specific moods like "peaceful", "nostalgic", "vibrant", "dreamy"
- **Cultural Context Awareness**: Identifies Indian, Western, or Global aesthetic to provide appropriate language mix
- **Detailed Vibe Analysis**: Analyzes colors, setting, atmosphere, themes, energy levels, and emotional tone

### 🎵 Intelligent Music Recommendations
- **Smart Language Mix**:
  - Indian vibe → 3 Hindi/Indian + 2 English songs
  - Western vibe → 4 English + 1 Hindi song
  - Global/Fusion → Balanced 3 English + 2 Hindi mix
- **Trending & Quality Songs**: Only recommends popular, high-quality tracks (popularity ≥ 40)
- **No Duplicates**: Advanced session tracking ensures you never see the same song twice
- **Artist Diversity**: Maximum 2 songs per artist for varied recommendations
- **Get More Songs**: Refresh to get 5 new recommendations that match your photo's vibe

### 🎯 Music Discovery
- **Curated Playlists**: Pulls from Spotify's official mood-based playlists
- **English Tracks**: Indie, Alternative, Pop, Electronic, R&B, and more
- **Hindi/Indian Tracks**: Bollywood, Sufi, Punjabi, Indie Hindi, Desi Pop
- **Current Music**: Filters for recent releases (2023-2024)
- **Audio Preview**: Listen to 30-second previews directly in the app
- **Direct Spotify Links**: One-click to open songs in Spotify

### 💎 User Experience
- **Beautiful Dark UI**: Spotify-inspired design with smooth animations
- **Drag & Drop Upload**: Easy photo upload with preview
- **Responsive Design**: Works perfectly on desktop and mobile
- **Real-time Analysis**: See detailed mood breakdown with visual progress bars
- **Session Persistence**: Keep your analysis and get more songs without re-uploading

## 🏗️ Project Structure

```
StoryBeats/
├── .gitignore                      # Root gitignore
├── README.md                       # This file
├── SETUP_GUIDE.md                  # Detailed setup instructions
│
├── backend/                        # Flask Backend API
│   ├── .env                        # Environment variables (not in git)
│   ├── .env.example                # Environment template
│   ├── .gitignore                  # Backend gitignore
│   ├── app.py                      # Main Flask application
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── config/                     # Configuration
│   │   ├── __init__.py
│   │   └── settings.py             # App settings & validation
│   │
│   ├── services/                   # Business Logic
│   │   ├── __init__.py
│   │   ├── image_analyzer.py       # AI image analysis (OpenAI/Anthropic)
│   │   └── spotify_service.py      # Spotify API integration
│   │
│   ├── uploads/                    # Temporary photo storage (auto-cleaned)
│   └── venv/                       # Python virtual environment
│
└── frontend/                       # React + Vite Frontend
    ├── index.html                  # HTML entry point
    ├── package.json                # npm dependencies
    ├── vite.config.js              # Vite configuration
    │
    └── src/                        # Source code
        ├── main.jsx                # React entry point
        ├── App.jsx                 # Main App component
        ├── App.css                 # App styles
        ├── index.css               # Global styles
        │
        └── components/             # React Components
            ├── PhotoUpload.jsx     # Photo upload UI
            ├── PhotoUpload.css
            ├── SongResults.jsx     # Results display UI
            └── SongResults.css
```

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask (Python 3.9+)
- **AI/LLM**: OpenAI GPT-4o or Anthropic Claude 3.5 Sonnet
- **Music API**: Spotify Web API
- **Image Processing**: Pillow (PIL)
- **HTTP Client**: httpx, requests
- **Environment**: python-dotenv

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite 7
- **Styling**: Pure CSS with custom design system
- **HTTP Client**: Fetch API

### APIs & Services
- **OpenAI API**: Image analysis with GPT-4o vision model
- **Anthropic API**: Alternative image analysis with Claude
- **Spotify API**: Music recommendations, search, and metadata

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 16 or higher
- Spotify Developer Account
- OpenAI API Key or Anthropic API Key

### 1. Clone the Repository
```bash
git clone <repository-url>
cd StoryBeats
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install
```

### 4. Get API Keys

#### Spotify API
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Get your Client ID and Client Secret
4. Add redirect URI: `http://127.0.0.1:3000/callback`

#### OpenAI API (Recommended)
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` file

#### Anthropic API (Alternative)
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create a new API key
3. Add to `.env` file

### 5. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
# Backend runs on http://127.0.0.1:5001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:3000
```

### 6. Open the App
Visit `http://localhost:3000` in your browser!

## 📖 How It Works

### 1. Photo Upload
User uploads a photo intended for Instagram story via drag & drop or click to upload.

### 2. AI Analysis
The backend sends the image to OpenAI GPT-4o (or Anthropic Claude) which analyzes:
- **Mood**: Specific emotional tone (peaceful, nostalgic, vibrant, etc.)
- **Themes**: Main subjects and concepts in the image
- **Energy Level**: 0.0 (calm/meditative) to 1.0 (intense/energetic)
- **Valence**: 0.0 (melancholic) to 1.0 (euphoric)
- **Cultural Vibe**: Indian, Western, Global, or Fusion aesthetic
- **Music Style**: Type of instrumentation and feel that would match
- **Keywords**: Descriptive terms for better music matching

### 3. Music Recommendation Algorithm

**Step 1: Dual-Track Search**
- Searches **English tracks**: Indie, Alternative, Pop, R&B, Electronic
- Searches **Hindi/Indian tracks**: Bollywood, Sufi, Punjabi, Indie Hindi

**Step 2: Quality Filtering**
- Only songs with Spotify popularity ≥ 40
- Removes duplicates within request
- Tracks previously shown songs via session ID

**Step 3: Smart Ranking**
- Ranks by popularity
- Applies diversity penalty for repeated artists
- Ensures max 2 songs per artist

**Step 4: Language Mix**
Based on cultural vibe analysis:
- Indian aesthetic → 3 Hindi + 2 English
- Western aesthetic → 4 English + 1 Hindi
- Global/Fusion → 3 English + 2 Hindi

**Step 5: Return Results**
Returns 5 diverse, high-quality songs with:
- Song name, artist, album
- Album artwork
- 30-second preview (if available)
- Direct Spotify link

### 4. Get More Songs
User can click "Get 5 More Songs" to get new recommendations:
- Uses same photo analysis
- Excludes previously shown songs
- Maintains quality and diversity standards
- Can be clicked multiple times for infinite variety

## 🎨 UI Features

### Dark Theme
- Spotify-inspired color scheme
- Green accent color (#1db954)
- Smooth animations and transitions
- Glassmorphism effects

### Components
- **PhotoUpload**: Drag & drop zone with preview
- **SongResults**:
  - Photo analysis card with mood details
  - Energy and positivity progress bars
  - Song cards with album art
  - Audio preview players
  - Spotify links

### Responsive Design
- Desktop-optimized layout
- Mobile-friendly interface
- Touch-friendly controls
- Adaptive typography

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Spotify API
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:3000/callback

# LLM Provider ('openai' or 'anthropic')
LLM_PROVIDER=openai

# OpenAI (if using)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Anthropic (if using)
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# App Settings
DEBUG=True
PORT=5001
HOST=0.0.0.0
```

## 🎯 API Endpoints

### `POST /api/analyze`
Upload and analyze a photo to get song recommendations.

**Request**: `multipart/form-data` with `photo` file

**Response**:
```json
{
  "success": true,
  "session_id": "abc123...",
  "analysis": {
    "mood": "peaceful",
    "themes": ["nature", "sunset", "solitude"],
    "description": "A serene sunset scene with warm colors...",
    "genres": ["indie", "acoustic", "indie-hindi"],
    "energy": 0.3,
    "valence": 0.7,
    "keywords": ["sunset", "calm", "nature"],
    "music_style": "soft acoustic with soothing vocals",
    "cultural_vibe": "global"
  },
  "songs": [
    {
      "id": "spotify_track_id",
      "name": "Song Name",
      "artist": "Artist Name",
      "album": "Album Name",
      "preview_url": "https://...",
      "spotify_url": "https://open.spotify.com/track/...",
      "album_cover": "https://...",
      "duration_ms": 240000,
      "popularity": 75,
      "language_type": "English"
    }
    // ... 4 more songs
  ]
}
```

### `POST /api/more-songs`
Get more song recommendations for the same photo.

**Request**:
```json
{
  "analysis": { /* previous analysis object */ },
  "offset": 5,
  "session_id": "abc123..."
}
```

**Response**: Same as `/api/analyze` but with different songs

## 🧪 Testing

Upload various types of photos to see how the AI adapts:
- **Landscapes**: Gets calm, ambient music
- **Party/Friends**: Gets upbeat, energetic tracks
- **Sunset/Nature**: Gets peaceful, acoustic songs
- **Traditional/Cultural**: Gets more Hindi/regional music
- **Urban/Modern**: Gets indie, alt-pop tracks

## 📝 Notes

### Important Implementation Details
- Photos are **temporarily stored** and **immediately deleted** after processing
- Session tracking prevents duplicate songs across "Get More" requests
- OpenAI/Anthropic responses are cached for efficiency
- Spotify uses India market (`market='IN'`) for Hindi song searches
- All API calls include proper error handling and fallbacks

### Known Limitations
- Audio previews not available for all tracks (Spotify limitation)
- Maximum 5 songs per request (can get more via "Get More Songs" button)
- Requires active internet connection for all features
- Image analysis quality depends on photo clarity

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome!

## 📄 License

This project is for educational and personal use.

## 🙏 Acknowledgments

- **Spotify** for the comprehensive music API
- **OpenAI** for GPT-4o vision capabilities
- **Anthropic** for Claude's image analysis
- **Vite** for lightning-fast frontend development
- **React** for the component architecture

---

**Built with ❤️ for music lovers who want the perfect soundtrack for their stories!**
