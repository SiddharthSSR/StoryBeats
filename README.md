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

### 3. Music Recommendation Algorithm (Artist-Centric with Recency)

#### 🎯 **Algorithm Overview**

StoryBeats uses a **sophisticated artist-centric recommendation system** that combines:
- **Curated Quality Artists** (72 hand-picked artists across 9 moods)
- **Recency-Based Track Selection** (60% recent releases, 40% proven hits)
- **Strict Vibe Matching** (>0.75 similarity threshold)
- **Multiple Spotify APIs** (artist_top_tracks, artist_albums, artist_related_artists, recommendations)

This ensures you get **fresh, high-quality tracks** that perfectly match your photo's vibe!

---

#### 📊 **9 Mood Categories**

The algorithm maps your photo's mood to one of 9 categories, each with 7-8 curated quality artists:

| Mood | Description | Example Photos | English Artists | Hindi Artists |
|------|-------------|----------------|----------------|---------------|
| **romantic** | Love songs, dreamy vibes | Couples, dates, sunsets | Cigarettes After Sex, Lauv, Gracie Abrams | Arijit Singh, Atif Aslam, Prateek Kuhad |
| **energetic** | High energy, upbeat | Gym, parties, dancing | Tame Impala, Glass Animals, Arctic Monkeys | Badshah, Diljit Dosanjh, Divine |
| **peaceful** | Calm, relaxing, soothing | Nature, meditation, cafes | Bon Iver, Novo Amor, Phoebe Bridgers | A.R. Rahman, Lucky Ali, When Chai Met Toast |
| **melancholic** | Sad, emotional, reflective | Rain, alone, thoughtful | Radiohead, Mazzy Star, Mitski | Mohit Chauhan, KK, Anuv Jain |
| **happy** | Joyful, uplifting, cheerful | Celebrations, friends | Two Door Cinema Club, Phoenix, COIN | Guru Randhawa, Neha Kakkar, Ritviz |
| **confident** | Bold, swagger, powerful | Fashion, urban, boss mode | The Weeknd, Travis Scott, Dua Lipa | Badshah, Divine, Seedhe Maut |
| **nostalgic** | Retro, classic, memories | Old photos, throwback | The 1975, Arctic Monkeys, Mac DeMarco | Kishore Kumar, Kumar Sanu, Lucky Ali |
| **dreamy** | Ethereal, soft, aesthetic | Clouds, soft light, aesthetic | Beach House, Clairo, ODESZA | Prateek Kuhad, Ritviz, Lifafa |
| **moody** | Dark, atmospheric, cinematic | Night city, urban, vibe | Frank Ocean, Don Toliver, SZA | The Local Train, Prabh Deep, Seedhe Maut |

---

#### 🎨 **Complete Artist Lists**

**ENGLISH ARTISTS** (Mainstream Pop + Indie Mix)

```
romantic:      Cigarettes After Sex, The Neighbourhood, Lauv, Gracie Abrams,
               Conan Gray, Jeremy Zucker, mxmtoon, girl in red

energetic:     Tame Impala, Glass Animals, MGMT, Foster The People,
               Two Door Cinema Club, The Strokes, Arctic Monkeys, Phoenix

peaceful:      Bon Iver, Novo Amor, Phoebe Bridgers, Iron & Wine,
               Sufjan Stevens, Fleet Foxes, Jose Gonzalez, Ben Howard

melancholic:   Radiohead, Mazzy Star, The National, Daughter,
               Sleeping At Last, Mitski, Phoebe Bridgers, Elliott Smith

happy:         Two Door Cinema Club, Passion Pit, Phoenix, COIN,
               MGMT, Young The Giant, Grouplove, Smallpools

confident:     The Weeknd, Travis Scott, Dua Lipa, Billie Eilish,
               Khalid, Post Malone, Doja Cat, SZA

nostalgic:     The 1975, Arctic Monkeys, Mac DeMarco, MGMT,
               Tame Impala, Vampire Weekend, The Strokes, Kings of Leon

dreamy:        Beach House, M83, ODESZA, Clairo,
               Men I Trust, Still Woozy, Rex Orange County, Kali Uchis

moody:         Frank Ocean, Don Toliver, Travis Scott, SZA,
               The Weeknd, Bryson Tiller, PartyNextDoor, 6LACK
```

**HINDI ARTISTS** (Bollywood + Indie Hindi + Punjabi)

```
romantic:      Arijit Singh, Atif Aslam, Shreya Ghoshal, Armaan Malik,
               Jubin Nautiyal, Prateek Kuhad, Anuv Jain, Raghav Chaitanya

energetic:     Badshah, Diljit Dosanjh, Divine, Raftaar,
               Nucleya, Ritviz, Seedhe Maut, The Local Train

peaceful:      A.R. Rahman, Shaan, Lucky Ali, Prateek Kuhad,
               Mohit Chauhan, Sonu Nigam, Papon, When Chai Met Toast

melancholic:   Mohit Chauhan, KK, Sonu Nigam, Jubin Nautiyal,
               Arijit Singh, Atif Aslam, Anuv Jain, Prateek Kuhad

happy:         Guru Randhawa, Neha Kakkar, Darshan Raval, Ritviz,
               Diljit Dosanjh, Harrdy Sandhu, Asees Kaur, When Chai Met Toast

confident:     Badshah, Divine, Raftaar, Ikka,
               Seedhe Maut, Prabh Deep, Naezy, MC Stan

nostalgic:     Kishore Kumar, R.D. Burman, Mohammed Rafi, Kumar Sanu,
               Alka Yagnik, Udit Narayan, Sonu Nigam, Lucky Ali

dreamy:        Prateek Kuhad, Anuv Jain, Ritviz, When Chai Met Toast,
               The Local Train, Zaeden, Lifafa, Kamakshi Khanna

moody:         Anuv Jain, Prateek Kuhad, The Local Train, Lifafa,
               Seedhe Maut, Prabh Deep, Dropped Out, Sez on the Beat
```

---

#### 🔄 **Recommendation Pipeline**

```
📸 Photo Upload
       ↓
🤖 LLM Analysis → Extract (mood, energy, valence, tempo, themes)
       ↓
🎯 Map mood to 1 of 9 categories
       ↓
    ┌──────┴──────┐
    ↓             ↓
ENGLISH (7-8)  HINDI (7-8)
 artists         artists
    ↓             ↓
FOR EACH ARTIST:
  ├─ Get recent albums (last 18 months)
  │  └─ Take 10 tracks → 60% of pool
  │
  └─ Get top tracks (all-time)
     └─ Take 5 tracks → 40% of pool
       ↓
COMBINE: ~120 tracks total (15 × 8 artists)
       ↓
FILTER by audio features:
  ├─ Calculate vibe_score for each track
  ├─ Keep only: vibe_score > 0.75 (strict!)
  ├─ Popularity range: 47-85
  └─ Tempo validation by mood
       ↓
~40-50 high-quality tracks remain
       ↓
SORT by composite score:
  ├─ vibe_match_score × 0.5 (most important)
  ├─ recency_bonus × 0.3 (prefer fresh)
  └─ popularity/100 × 0.2 (quality indicator)
       ↓
USE TOP 20 as seeds for Recommendations API:
  ├─ seed_tracks=[top_10_track_ids]
  ├─ seed_artists=[3_best_artist_ids]
  ├─ target_energy, target_valence, etc.
  └─ min/max ranges (±0.15, tight!)
       ↓
GET RELATED ARTISTS:
  └─ sp.artist_related_artists(top_3_artists)
     └─ Get their top 5 tracks each
       ↓
FINAL POOL: ~60-70 high-quality tracks
       ↓
APPLY DIVERSITY & SELECTION:
  ├─ Max 2 tracks per artist
  ├─ Balanced popularity distribution
  ├─ Deduplicate by track_id
  └─ Sort by final_score
       ↓
SELECT FINAL 5 TRACKS:
  ├─ 2-3 English (based on cultural_vibe)
  └─ 2-3 Hindi (based on cultural_vibe)
       ↓
🎵 RETURN TO USER
```

---

#### ⚙️ **Algorithm Configuration**

```python
# Recency Split
RECENT_TRACKS_RATIO = 0.6      # 60% from last 18 months
CLASSIC_TRACKS_RATIO = 0.4     # 40% all-time top tracks

# Quality Filters
POPULARITY_MIN = 47            # Minimum popularity score
POPULARITY_MAX = 85            # Maximum (avoid overplayed)
VIBE_THRESHOLD = 0.75          # Strict vibe matching (0.0-1.0)
AUDIO_RANGE_TOLERANCE = 0.15   # ±0.15 for energy, valence, etc.

# Track Selection
TRACKS_PER_ARTIST_RECENT = 10  # From recent albums
TRACKS_PER_ARTIST_TOP = 5      # All-time top tracks
MAX_TRACKS_PER_ARTIST = 2      # In final selection

# Scoring Weights
VIBE_WEIGHT = 0.5              # 50% - vibe matching
RECENCY_WEIGHT = 0.3           # 30% - track freshness
POPULARITY_WEIGHT = 0.2        # 20% - quality/popularity

# Spotify API Usage
MARKETS = {
    'english': 'US',           # US market for English
    'hindi': 'IN'              # India market for Hindi
}
```

---

#### 🎵 **Vibe Matching Formula**

The algorithm calculates a **vibe match score** for each track:

```python
vibe_match_score = (
    (1.0 - abs(track_energy - target_energy)) × 0.30 +
    (1.0 - abs(track_valence - target_valence)) × 0.30 +
    (1.0 - abs(track_danceability - target_danceability)) × 0.20 +
    (1.0 - abs(track_acousticness - target_acousticness)) × 0.10 +
    tempo_score × 0.10
)

# Only keep tracks with vibe_match_score > 0.75
```

**Recency Bonus Calculation:**

```python
days_since_release = (today - release_date).days

if days_since_release ≤ 180:     # Last 6 months
    recency_bonus = 1.0
elif days_since_release ≤ 365:   # Last year
    recency_bonus = 0.8
elif days_since_release ≤ 540:   # Last 18 months
    recency_bonus = 0.6
else:                             # Older classics
    recency_bonus = 0.3
```

**Final Track Score:**

```python
final_score = (
    vibe_match_score × 0.5 +
    recency_bonus × 0.3 +
    (popularity / 100) × 0.2
)
```

---

#### ✨ **Key Improvements Over Previous Algorithm**

| Aspect | Before | After |
|--------|--------|-------|
| **Artist Quality** | Random from playlists | 72 hand-picked quality artists |
| **Track Freshness** | Mixed/unknown | 60% recent (last 18 months) |
| **Vibe Matching** | 0.6 threshold (loose) | 0.75 threshold (strict) |
| **Audio Ranges** | ±0.2 (wide) | ±0.15 (tight) |
| **Sources** | 4 mixed sources | Single artist-centric source |
| **Popularity** | 25-95 (too wide) | 47-85 (sweet spot) |
| **Hindi Quality** | Generic playlists | Bollywood + Indie bands curated |
| **Artist Pool** | Unknown/random | 7-8 quality artists per mood |
| **APIs Used** | 3 APIs | 5 APIs (added artist APIs) |

---

#### 🚀 **Spotify APIs Used**

1. **`sp.artist_albums(artist_id, album_type='single,album')`** - Get recent releases
2. **`sp.album_tracks(album_id)`** - Get tracks from albums
3. **`sp.artist_top_tracks(artist_id, market)`** - Get proven hits
4. **`sp.artist_related_artists(artist_id)`** - Find similar artists
5. **`sp.recommendations(seed_tracks, seed_artists, ...)`** - Generate recommendations
6. **`sp.audio_features(track_ids)`** - Analyze audio characteristics

---

#### 🎯 **Language Mix Strategy**

Based on cultural vibe analysis:
- **Indian aesthetic** → 3 Hindi + 2 English
- **Western aesthetic** → 4 English + 1 Hindi
- **Global/Fusion** → 3 English + 2 Hindi (balanced)

---

#### 💎 **Return Format**

Returns 5 diverse, high-quality songs with:
- Song name, artist, album
- Album artwork (high resolution)
- 30-second preview (if available)
- Direct Spotify link
- Popularity score
- Language type (English/Hindi)
- Popularity bucket (hidden gem/moderate/popular)

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

## 🚀 Next Steps

### For Users

**Enhance Your Experience:**
- Try different types of photos (landscapes, portraits, food, events)
- Experiment with various moods and settings
- Use "Get 5 More Songs" to discover more music
- Create playlists from your favorite recommendations
- Share your photo + song combos on Instagram stories

### For Developers

**Feature Ideas:**
- **User Authentication**: Add login/signup for personalized experience
- **Save Favorites**: Allow users to save their favorite song-photo combinations
- **Playlist Creation**: Auto-create Spotify playlists from recommendations
- **Instagram Integration**: Direct sharing to Instagram Stories with music
- **Video Support**: Analyze video clips for music recommendations
- **Multi-Language Support**: Add Spanish, French, Korean, etc.
- **Mood History**: Track user's mood patterns over time
- **Collaborative Playlists**: Share and collaborate on music discoveries
- **Advanced Filters**: Filter by genre, era, tempo, or energy level
- **Lyrics Integration**: Show lyrics for recommended songs

**Technical Improvements:**
- Add user analytics and recommendation tracking
- Implement caching for faster repeat requests
- Add rate limiting to prevent API quota exhaustion
- Create automated tests for backend and frontend
- Set up CI/CD pipeline for automated deployments
- Add error monitoring (Sentry, LogRocket)
- Optimize image upload size and processing
- Add progressive web app (PWA) support

**Deployment:**
- **Backend Options**: Heroku, Railway, DigitalOcean, AWS EC2, Google Cloud Run
- **Frontend Options**: Vercel, Netlify, GitHub Pages, Cloudflare Pages
- **Database**: Add PostgreSQL/MongoDB for user data and favorites
- **CDN**: Use Cloudflare or AWS CloudFront for faster asset delivery
- **Monitoring**: Set up uptime monitoring and performance tracking

**Marketing & Community:**
- Create demo video showing the app in action
- Add screenshots to README
- Write blog post about the development process
- Share on Product Hunt, Hacker News, Reddit
- Create social media presence
- Build community around music discovery

### Project Roadmap

**Phase 1: MVP (Completed)**
- ✅ AI image analysis
- ✅ Spotify integration
- ✅ Language mixing algorithm
- ✅ Beautiful UI
- ✅ Session management

**Phase 2: Enhancement (Suggested)**
- User authentication
- Save favorite combinations
- Playlist creation
- Enhanced analytics
- Mobile app (React Native)

**Phase 3: Growth (Future)**
- Multi-platform support (TikTok, YouTube Shorts)
- Premium features
- API for third-party integrations
- Community features
- International expansion

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome!

**How to Contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Areas for Contribution:**
- Bug fixes and improvements
- New features from the roadmap above
- Documentation improvements
- UI/UX enhancements
- Performance optimizations
- Test coverage
- Language translations

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
