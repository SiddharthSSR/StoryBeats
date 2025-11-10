import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from datetime import datetime
import threading
from services.feedback_store import get_feedback_store
from services.audio_feature_analytics import get_audio_feature_analytics

try:
    from spotipy.retry import SpotifyRetry
except ImportError:  # Older spotipy versions expose retries as integers only
    SpotifyRetry = None


class SpotifyService:
    """Service for interacting with Spotify API - Artist-Centric Algorithm"""

    # Algorithm Configuration
    RECENT_TRACKS_RATIO = 0.6  # 60% from last 18 months
    CLASSIC_TRACKS_RATIO = 0.4  # 40% all-time top tracks
    POPULARITY_MIN = 47
    POPULARITY_MAX = 85
    VIBE_THRESHOLD = 0.75  # Strict matching
    AUDIO_RANGE_TOLERANCE = 0.15  # ±0.15 for tight matching
    TRACKS_PER_ARTIST_RECENT = 10
    TRACKS_PER_ARTIST_TOP = 5
    MAX_TRACKS_PER_ARTIST = 2

    # Scoring Weights
    VIBE_WEIGHT = 0.5
    RECENCY_WEIGHT = 0.3
    POPULARITY_WEIGHT = 0.2

    # Curated Artist Lists - English (Mainstream Pop + Indie Mix)
    ENGLISH_ARTISTS = {
        'romantic': [
            'Cigarettes After Sex', 'The Neighbourhood', 'Lauv', 'Gracie Abrams',
            'Conan Gray', 'Jeremy Zucker', 'mxmtoon', 'girl in red'
        ],
        'energetic': [
            'Tame Impala', 'Glass Animals', 'MGMT', 'Foster The People',
            'Two Door Cinema Club', 'The Strokes', 'Arctic Monkeys', 'Phoenix'
        ],
        'peaceful': [
            'Bon Iver', 'Novo Amor', 'Phoebe Bridgers', 'Iron & Wine',
            'Sufjan Stevens', 'Fleet Foxes', 'Jose Gonzalez', 'Ben Howard'
        ],
        'melancholic': [
            'Radiohead', 'Mazzy Star', 'The National', 'Daughter',
            'Sleeping At Last', 'Mitski', 'Phoebe Bridgers', 'Elliott Smith'
        ],
        'happy': [
            'Two Door Cinema Club', 'Passion Pit', 'Phoenix', 'COIN',
            'MGMT', 'Young The Giant', 'Grouplove', 'Smallpools'
        ],
        'confident': [
            'The Weeknd', 'Travis Scott', 'Dua Lipa', 'Billie Eilish',
            'Khalid', 'Post Malone', 'Doja Cat', 'SZA'
        ],
        'nostalgic': [
            'The 1975', 'Arctic Monkeys', 'Mac DeMarco', 'MGMT',
            'Tame Impala', 'Vampire Weekend', 'The Strokes', 'Kings of Leon'
        ],
        'dreamy': [
            'Beach House', 'M83', 'ODESZA', 'Clairo',
            'Men I Trust', 'Still Woozy', 'Rex Orange County', 'Kali Uchis'
        ],
        'moody': [
            'Frank Ocean', 'Don Toliver', 'Travis Scott', 'SZA',
            'The Weeknd', 'Bryson Tiller', 'PartyNextDoor', '6LACK'
        ]
    }

    # Curated Artist Lists - Hindi (Bollywood + Indie Hindi + Punjabi)
    HINDI_ARTISTS = {
        'romantic': [
            'Arijit Singh', 'Atif Aslam', 'Shreya Ghoshal', 'Armaan Malik',
            'Jubin Nautiyal', 'Prateek Kuhad', 'Raghav Chaitanya'
        ],
        'energetic': [
            'Badshah', 'Diljit Dosanjh', 'Divine', 'Raftaar',
            'Nucleya', 'Karan Aujla', 'Seedhe Maut', 'The Local Train'
        ],
        'peaceful': [
            'A.R. Rahman', 'Shaan', 'Lucky Ali', 'Prateek Kuhad',
            'Mohit Chauhan', 'Sonu Nigam', 'Papon', 'When Chai Met Toast'
        ],
        'melancholic': [
            'Mohit Chauhan', 'KK', 'Sonu Nigam', 'Jubin Nautiyal',
            'Arijit Singh', 'Atif Aslam', 'Prateek Kuhad'
        ],
        'happy': [
            'Guru Randhawa','Darshan Raval', 'Diljit Dosanjh',
            'Harrdy Sandhu', 'Asees Kaur', 'When Chai Met Toast', 'Sunidhi Chauhan'
        ],
        'confident': [
            'Badshah', 'Divine', 'Raftaar', 'Ikka',
            'Seedhe Maut', 'Prabh Deep', 'Naezy', 'MC Stan'
        ],
        'nostalgic': [
            'Kishore Kumar', 'R.D. Burman', 'Mohammed Rafi', 'Kumar Sanu',
            'Alka Yagnik', 'Udit Narayan', 'Sonu Nigam', 'Lucky Ali'
        ],
        'dreamy': [
            'Prateek Kuhad', 'When Chai Met Toast', 'The Local Train',
            'Zaeden', 'Lifafa', 'Kamakshi Khanna', 'Shankar Mahadevan'
        ],
        'moody': [
            'Prateek Kuhad', 'The Local Train', 'Lifafa',
            'Seedhe Maut', 'Prabh Deep', 'Dropped Out', 'Sez on the Beat'
        ]
    }

    # Mood Fallback Mapping
    MOOD_FALLBACK = {
        'calm': 'peaceful',
        'relaxed': 'peaceful',
        'chill': 'moody',
        'sad': 'melancholic',
        'joyful': 'happy',
        'upbeat': 'energetic',
        'adventurous': 'energetic',
        'cozy': 'peaceful',
        'vibrant': 'energetic',
        'reflective': 'melancholic',
        'serene': 'peaceful',
        'dark': 'moody',
        'atmospheric': 'moody',
        'love': 'romantic',
        'thoughtful': 'melancholic'
    }

    def __init__(self):
        """Initialize Spotify client"""
        self.client_credentials = SpotifyClientCredentials(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET
        )
        # Configure Spotify client with sensible timeout and retry defaults
        timeout_seconds = int(os.getenv('SPOTIFY_REQUEST_TIMEOUT', '15'))
        retry_attempts = int(os.getenv('SPOTIFY_REQUEST_RETRIES', '3'))

        retry_strategy = None
        if SpotifyRetry:
            retry_strategy = SpotifyRetry(
                total=retry_attempts,
                backoff_factor=1,
                status_forcelist=(429, 500, 502, 503, 504)
            )
        else:
            # Fallback: older spotipy versions expect an int for retries
            retry_strategy = retry_attempts

        self.sp = spotipy.Spotify(
            client_credentials_manager=self.client_credentials,
            requests_timeout=timeout_seconds,
            retries=retry_strategy
        )

        print(
            f"[SpotifyService] Initialized Spotify client with timeout={timeout_seconds}s, "
            f"retries={retry_attempts}"
        )

        # Cache for artist ID lookups (artist_name -> artist_id)
        self.artist_id_cache = {}

        # Performance caches with timestamps
        self.top_tracks_cache = {}  # {artist_id: (tracks, timestamp)}
        self.albums_cache = {}  # {artist_id: (album_ids, timestamp)}
        self.cache_lock = threading.Lock()  # Thread-safe cache access

        # Cache expiration times (in seconds)
        self.TOP_TRACKS_CACHE_TTL = 3600  # 1 hour
        self.ALBUMS_CACHE_TTL = 1800  # 30 minutes

    def get_auth_url(self):
        """Get Spotify OAuth authorization URL"""
        sp_oauth = SpotifyOAuth(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=Config.SPOTIFY_REDIRECT_URI,
            scope=Config.SPOTIFY_SCOPE
        )
        return sp_oauth.get_authorize_url()

    def get_access_token(self, code):
        """Exchange authorization code for access token"""
        sp_oauth = SpotifyOAuth(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=Config.SPOTIFY_REDIRECT_URI,
            scope=Config.SPOTIFY_SCOPE
        )
        token_info = sp_oauth.get_access_token(code)
        return token_info

    def _adjust_tempo_for_mood(self, tempo, mood, energy):
        """
        Adjust tempo based on mood to ensure it makes sense

        Returns: Adjusted tempo (BPM)
        """
        mood_lower = mood.lower()

        # Define tempo ranges for different moods
        mood_tempo_ranges = {
            'energetic': (120, 140),
            'hype': (125, 145),
            'excited': (120, 140),
            'party': (110, 130),
            'happy': (100, 125),
            'joyful': (105, 125),
            'upbeat': (110, 130),
            'calm': (70, 95),
            'peaceful': (65, 90),
            'relaxed': (75, 105),
            'chill': (80, 110),
            'mellow': (70, 100),
            'melancholic': (70, 95),
            'sad': (65, 90),
            'emotional': (70, 100),
            'romantic': (60, 90),
            'dreamy': (75, 100),
            'nostalgic': (80, 105),
            'contemplative': (70, 95),
            'confident': (100, 120),
            'adventurous': (110, 130)
        }

        # Find matching mood range
        tempo_range = None
        for mood_key, (min_tempo, max_tempo) in mood_tempo_ranges.items():
            if mood_key in mood_lower:
                tempo_range = (min_tempo, max_tempo)
                break

        # If no specific mood match, use energy to determine range
        if not tempo_range:
            if energy >= 0.7:  # High energy
                tempo_range = (110, 135)
            elif energy >= 0.4:  # Medium energy
                tempo_range = (90, 115)
            else:  # Low energy
                tempo_range = (70, 95)

        min_tempo, max_tempo = tempo_range

        # Adjust tempo if it's outside the expected range
        if tempo < min_tempo:
            adjusted_tempo = min_tempo + 5  # Slightly above minimum
            print(f"[SpotifyService] Adjusted tempo from {tempo} to {adjusted_tempo} BPM (mood: {mood}, range: {min_tempo}-{max_tempo})")
            return adjusted_tempo
        elif tempo > max_tempo:
            adjusted_tempo = max_tempo - 5  # Slightly below maximum
            print(f"[SpotifyService] Adjusted tempo from {tempo} to {adjusted_tempo} BPM (mood: {mood}, range: {min_tempo}-{max_tempo})")
            return adjusted_tempo
        else:
            print(f"[SpotifyService] Tempo {tempo} BPM is appropriate for mood: {mood} (range: {min_tempo}-{max_tempo})")
            return tempo

    def _determine_language_mix(self, image_analysis):
        """
        Dynamically determine language/genre mix based on image content

        Returns: (english_count, hindi_count) tuple
        """
        mood = image_analysis.get('mood', '').lower()
        themes = [t.lower() for t in image_analysis.get('themes', [])]
        keywords = [k.lower() for k in image_analysis.get('keywords', [])]
        cultural_vibe = image_analysis.get('cultural_vibe', 'global').lower()

        # Start with base mix
        english_count = 3
        hindi_count = 2

        # Cultural vibe override (strongest signal)
        if cultural_vibe == 'indian':
            english_count = 2
            hindi_count = 3
        elif cultural_vibe == 'western':
            english_count = 4
            hindi_count = 1

        # Adjust based on themes and keywords
        all_terms = ' '.join(themes + keywords)

        # Strong Indian indicators → more Hindi
        indian_indicators = ['temple', 'festival', 'traditional', 'culture', 'heritage', 'indian', 'desi', 'bollywood']
        indian_score = sum(1 for ind in indian_indicators if ind in all_terms)

        # Strong Western indicators → more English
        western_indicators = ['urban', 'modern', 'city', 'nightlife', 'club', 'tech', 'metropolitan', 'western']
        western_score = sum(1 for ind in western_indicators if ind in all_terms)

        # Nature/Travel → balanced mix
        nature_indicators = ['nature', 'landscape', 'mountain', 'beach', 'ocean', 'forest', 'travel', 'adventure']
        nature_score = sum(1 for ind in nature_indicators if ind in all_terms)

        # Apply adjustments
        if indian_score > western_score + 1:
            hindi_count = min(hindi_count + 1, 4)
            english_count = max(5 - hindi_count, 1)
        elif western_score > indian_score + 1:
            english_count = min(english_count + 1, 4)
            hindi_count = max(5 - english_count, 1)
        elif nature_score >= 2:
            # Balanced mix for nature/travel
            english_count = 3
            hindi_count = 2

        print(f"[SpotifyService] Dynamic language mix: {english_count} English, {hindi_count} Hindi")
        print(f"[SpotifyService] Indicators - Indian: {indian_score}, Western: {western_score}, Nature: {nature_score}")

        return english_count, hindi_count

    def _calculate_semantic_similarity(self, track, image_keywords, image_themes, mood):
        """
        Calculate semantic similarity between track metadata and image analysis

        Returns a boost score (0-20) based on keyword/theme matches
        """
        similarity_score = 0

        # Combine track name, artist names, album name for matching
        track_name = track.get('name', '').lower()
        artist_names = ' '.join([a['name'].lower() for a in track.get('artists', [])])
        album_name = track.get('album', {}).get('name', '').lower()

        track_text = f"{track_name} {artist_names} {album_name}"

        # Check for keyword matches (each keyword match = +3 points)
        for keyword in image_keywords:
            if keyword.lower() in track_text:
                similarity_score += 3

        # Check for theme matches (each theme match = +5 points)
        for theme in image_themes:
            if theme.lower() in track_text:
                similarity_score += 5

        # Check for mood match in track name (mood match = +4 points)
        if mood.lower() in track_text:
            similarity_score += 4

        # Cap at 20 to avoid over-boosting
        return min(similarity_score, 20)

    # ============================================================================
    # NEW ARTIST-CENTRIC ALGORITHM HELPER METHODS
    # ============================================================================

    def _normalize_mood(self, mood):
        """
        Normalize mood to one of our 9 categories

        Args:
            mood (str): Mood from LLM analysis

        Returns:
            str: Normalized mood category
        """
        mood_lower = mood.lower()

        # Check if mood is already in our list
        if mood_lower in self.ENGLISH_ARTISTS:
            return mood_lower

        # Try fallback mapping
        if mood_lower in self.MOOD_FALLBACK:
            return self.MOOD_FALLBACK[mood_lower]

        # Partial matching (e.g., "very romantic" -> "romantic")
        for key_mood in self.ENGLISH_ARTISTS.keys():
            if key_mood in mood_lower:
                return key_mood

        # Default fallback
        print(f"[SpotifyService] Unknown mood '{mood}', defaulting to 'happy'")
        return 'happy'

    def _search_artist_by_name(self, artist_name, market='US'):
        """
        Search for an artist by name and return their Spotify ID

        Uses caching to avoid repeated API calls

        Args:
            artist_name (str): Artist name
            market (str): Market code (US or IN)

        Returns:
            str or None: Artist ID if found, None otherwise
        """
        # Check cache first
        cache_key = f"{artist_name}_{market}"
        if cache_key in self.artist_id_cache:
            return self.artist_id_cache[cache_key]

        try:
            results = self.sp.search(q=f'artist:{artist_name}', type='artist', limit=1, market=market)
            if results['artists']['items']:
                artist_id = results['artists']['items'][0]['id']
                self.artist_id_cache[cache_key] = artist_id
                return artist_id
        except Exception as e:
            print(f"[SpotifyService] Error searching for artist '{artist_name}': {e}")

        return None

    def _get_artist_recent_albums(self, artist_id, market='US'):
        """
        Get artist's recent albums/singles from last 18 months

        Args:
            artist_id (str): Spotify artist ID
            market (str): Market code

        Returns:
            list: List of album IDs
        """
        from datetime import datetime, timedelta

        try:
            eighteen_months_ago = datetime.now() - timedelta(days=540)
            albums = []

            # Get albums and singles
            results = self.sp.artist_albums(
                artist_id,
                album_type='album,single',
                limit=50
            )

            for album in results['items']:
                # Parse release date
                release_date_str = album.get('release_date', '')
                if not release_date_str:
                    continue

                try:
                    # Handle different date formats (YYYY, YYYY-MM, YYYY-MM-DD)
                    if len(release_date_str) == 4:  # Year only
                        release_date = datetime.strptime(release_date_str, '%Y')
                    elif len(release_date_str) == 7:  # Year-Month
                        release_date = datetime.strptime(release_date_str, '%Y-%m')
                    else:  # Full date
                        release_date = datetime.strptime(release_date_str, '%Y-%m-%d')

                    # Only include if within last 18 months
                    if release_date >= eighteen_months_ago:
                        albums.append(album['id'])
                except ValueError:
                    continue

            return albums

        except Exception as e:
            print(f"[SpotifyService] Error getting recent albums for artist {artist_id}: {e}")
            return []

    def _get_tracks_from_albums(self, album_ids, limit_per_album=5):
        """
        Get tracks from multiple albums

        Args:
            album_ids (list): List of album IDs
            limit_per_album (int): Max tracks per album

        Returns:
            list: List of track objects
        """
        tracks = []

        for album_id in album_ids[:10]:  # Max 10 albums to avoid too many API calls
            try:
                album_tracks = self.sp.album_tracks(album_id, limit=50)
                for item in album_tracks['items'][:limit_per_album]:
                    if item and item.get('id'):
                        tracks.append(item)
            except Exception as e:
                print(f"[SpotifyService] Error getting tracks from album {album_id}: {e}")
                continue

        return tracks

    def _calculate_recency_bonus(self, release_date_str):
        """
        Calculate recency bonus based on release date

        Args:
            release_date_str (str): Release date in ISO format (YYYY-MM-DD)

        Returns:
            float: Recency bonus (0.3 to 1.0)
        """
        from datetime import datetime

        try:
            # Handle different date formats
            if len(release_date_str) == 4:  # Year only
                release_date = datetime.strptime(release_date_str, '%Y')
            elif len(release_date_str) == 7:  # Year-Month
                release_date = datetime.strptime(release_date_str, '%Y-%m')
            else:  # Full date
                release_date = datetime.strptime(release_date_str, '%Y-%m-%d')

            days_since_release = (datetime.now() - release_date).days

            if days_since_release <= 180:  # Last 6 months
                return 1.0
            elif days_since_release <= 365:  # Last year
                return 0.8
            elif days_since_release <= 540:  # Last 18 months
                return 0.6
            else:  # Older tracks
                return 0.3

        except Exception:
            return 0.5  # Default if date parsing fails

    def _calculate_vibe_match_score(self, track_features, target_energy, target_valence,
                                    target_danceability, target_acousticness, target_tempo):
        """
        Calculate how well a track matches the target vibe

        Args:
            track_features (dict): Track audio features from Spotify
            target_energy, target_valence, etc.: Target values from image analysis

        Returns:
            float: Vibe match score (0.0 to 1.0)
        """
        if not track_features:
            return 0.0

        # Calculate proximity scores for each feature
        energy_score = 1.0 - abs(track_features.get('energy', 0.5) - target_energy)
        valence_score = 1.0 - abs(track_features.get('valence', 0.5) - target_valence)
        danceability_score = 1.0 - abs(track_features.get('danceability', 0.5) - target_danceability)
        acousticness_score = 1.0 - abs(track_features.get('acousticness', 0.5) - target_acousticness)

        # Tempo matching (normalize to 0-1 scale)
        track_tempo = track_features.get('tempo', 120)
        tempo_diff = abs(track_tempo - target_tempo)
        tempo_score = max(0, 1.0 - (tempo_diff / 50))  # 50 BPM tolerance

        # Weighted average (energy and valence most important)
        vibe_match_score = (
            energy_score * 0.30 +
            valence_score * 0.30 +
            danceability_score * 0.20 +
            acousticness_score * 0.10 +
            tempo_score * 0.10
        )

        return vibe_match_score

    def _estimate_audio_features_from_mood(self, normalized_mood):
        """
        Estimate audio features when Spotify API is unavailable
        Returns approximate features based on mood category
        """
        mood_features = {
            'romantic': {'energy': 0.4, 'valence': 0.6, 'danceability': 0.5, 'acousticness': 0.6, 'tempo': 95},
            'energetic': {'energy': 0.9, 'valence': 0.8, 'danceability': 0.85, 'acousticness': 0.1, 'tempo': 140},
            'peaceful': {'energy': 0.3, 'valence': 0.5, 'danceability': 0.3, 'acousticness': 0.7, 'tempo': 85},
            'melancholic': {'energy': 0.3, 'valence': 0.2, 'danceability': 0.3, 'acousticness': 0.6, 'tempo': 80},
            'happy': {'energy': 0.7, 'valence': 0.8, 'danceability': 0.7, 'acousticness': 0.3, 'tempo': 120},
            'confident': {'energy': 0.8, 'valence': 0.7, 'danceability': 0.75, 'acousticness': 0.2, 'tempo': 125},
            'nostalgic': {'energy': 0.5, 'valence': 0.5, 'danceability': 0.5, 'acousticness': 0.5, 'tempo': 105},
            'dreamy': {'energy': 0.4, 'valence': 0.6, 'danceability': 0.4, 'acousticness': 0.5, 'tempo': 100},
            'moody': {'energy': 0.5, 'valence': 0.4, 'danceability': 0.55, 'acousticness': 0.3, 'tempo': 110}
        }
        return mood_features.get(normalized_mood, mood_features['happy'])

    def _enhance_audio_features(self, track, normalized_mood, language):
        """
        Enhanced audio feature estimation using track metadata

        Args:
            track: Track object with metadata
            normalized_mood: Normalized mood category
            language: 'english' or 'hindi'

        Returns:
            dict: Enhanced audio features
        """
        # Start with mood-based baseline
        features = self._estimate_audio_features_from_mood(normalized_mood).copy()

        # Extract metadata
        artist_name = track.get('_artist_name', '').lower()
        track_name = track.get('name', '').lower()
        album_name = track.get('album', {}).get('name', '').lower()
        release_date = track.get('album', {}).get('release_date', '')

        # === ENGLISH ARTIST PATTERNS ===
        if language == 'english':
            # Indie/Acoustic artists
            if any(word in artist_name for word in ['bon iver', 'novo amor', 'phoebe', 'cigarettes after sex']):
                features['acousticness'] = min(0.9, features['acousticness'] + 0.3)
                features['energy'] = max(0.2, features['energy'] - 0.2)
                features['danceability'] = max(0.2, features['danceability'] - 0.2)

            # Electronic/Synth artists
            elif any(word in artist_name for word in ['m83', 'odesza', 'beach house', 'tame impala', 'mgmt']):
                features['energy'] = min(0.9, features['energy'] + 0.1)
                features['acousticness'] = max(0.1, features['acousticness'] - 0.3)
                features['tempo'] = min(140, features['tempo'] + 10)

            # Hip-hop/R&B artists (moody category)
            elif any(word in artist_name for word in ['frank ocean', 'don toliver', 'travis scott', 'sza', 'weeknd', 'bryson']):
                features['energy'] = max(0.4, min(0.7, features['energy']))
                features['danceability'] = min(0.8, features['danceability'] + 0.1)
                features['tempo'] = max(85, min(115, features['tempo']))

            # Indie rock/alternative
            elif any(word in artist_name for word in ['arctic monkeys', 'the strokes', 'phoenix', 'two door']):
                features['energy'] = min(0.85, features['energy'] + 0.15)
                features['acousticness'] = max(0.15, features['acousticness'] - 0.2)
                features['tempo'] = min(130, features['tempo'] + 5)

        # === HINDI ARTIST PATTERNS ===
        elif language == 'hindi':
            # Bollywood romantic singers
            if any(word in artist_name for word in ['arijit', 'atif', 'shreya', 'armaan', 'jubin']):
                features['valence'] = min(0.8, features['valence'] + 0.1)
                features['acousticness'] = min(0.7, features['acousticness'] + 0.2)
                features['energy'] = max(0.3, min(0.6, features['energy']))
                features['tempo'] = max(80, min(110, features['tempo']))

            # Punjabi/Hip-hop artists
            elif any(word in artist_name for word in ['badshah', 'divine', 'raftaar', 'diljit', 'guru randhawa', 'seedhe maut']):
                features['energy'] = min(0.95, features['energy'] + 0.2)
                features['danceability'] = min(0.95, features['danceability'] + 0.2)
                features['tempo'] = min(145, features['tempo'] + 15)
                features['acousticness'] = max(0.05, features['acousticness'] - 0.3)

            # Indie/Singer-songwriter (Prateek, Anuv, etc.)
            elif any(word in artist_name for word in ['prateek', 'anuv', 'raghav', 'when chai met toast', 'local train', 'lifafa']):
                features['acousticness'] = min(0.85, features['acousticness'] + 0.25)
                features['energy'] = max(0.25, features['energy'] - 0.15)
                features['valence'] = max(0.4, min(0.7, features['valence']))
                features['tempo'] = max(75, min(105, features['tempo']))

            # Electronic/Producer (Nucleya, etc.)
            elif any(word in artist_name for word in ['nucleya', 'sez on the beat', 'dropped out']):
                features['energy'] = min(0.95, features['energy'] + 0.25)
                features['danceability'] = min(0.95, features['danceability'] + 0.25)
                features['acousticness'] = max(0.05, features['acousticness'] - 0.4)
                features['tempo'] = min(150, features['tempo'] + 20)

            # Classical/Sufi influenced
            elif any(word in artist_name for word in ['a.r. rahman', 'hariharan', 'shaan']):
                features['acousticness'] = min(0.8, features['acousticness'] + 0.2)
                features['energy'] = max(0.3, features['energy'] - 0.1)
                features['tempo'] = max(70, min(100, features['tempo']))

        # === TRACK NAME PATTERNS ===
        # Remix/DJ versions
        if any(word in track_name or word in album_name for word in ['remix', 'mix', 'edit', 'version']):
            features['energy'] = min(0.95, features['energy'] + 0.15)
            features['danceability'] = min(0.95, features['danceability'] + 0.15)
            features['tempo'] = min(145, features['tempo'] + 10)

        # Acoustic/Unplugged versions
        elif any(word in track_name or word in album_name for word in ['acoustic', 'unplugged', 'stripped', 'piano']):
            features['acousticness'] = min(0.95, features['acousticness'] + 0.3)
            features['energy'] = max(0.2, features['energy'] - 0.25)

        # Live versions
        elif any(word in track_name or word in album_name for word in ['live', 'session']):
            features['acousticness'] = min(0.8, features['acousticness'] + 0.15)

        # === RELEASE YEAR ADJUSTMENTS ===
        if release_date:
            try:
                year = int(release_date[:4])
                # Newer songs tend to have more production
                if year >= 2023:
                    features['energy'] = min(0.95, features['energy'] + 0.05)
                elif year >= 2020:
                    features['energy'] = min(0.9, features['energy'] + 0.03)
                # Older songs might be more acoustic
                elif year < 2010:
                    features['acousticness'] = min(0.85, features['acousticness'] + 0.1)
            except:
                pass

        # Ensure values stay in valid range [0.0, 1.0]
        for key in ['energy', 'valence', 'danceability', 'acousticness']:
            features[key] = max(0.0, min(1.0, features[key]))

        # Tempo should be reasonable
        features['tempo'] = max(60, min(180, features['tempo']))

        return features

    def _get_cached_top_tracks(self, artist_id, country):
        """
        Get artist top tracks with caching (1 hour TTL)
        Thread-safe with cache lock
        """
        cache_key = f"{artist_id}_{country}"

        # Check cache
        with self.cache_lock:
            if cache_key in self.top_tracks_cache:
                tracks, timestamp = self.top_tracks_cache[cache_key]
                # Check if cache is still valid
                if (datetime.now() - timestamp).total_seconds() < self.TOP_TRACKS_CACHE_TTL:
                    return tracks

        # Cache miss or expired - fetch from API
        try:
            response = self.sp.artist_top_tracks(artist_id, country=country)
            tracks = response.get('tracks', [])

            # Store in cache
            with self.cache_lock:
                self.top_tracks_cache[cache_key] = (tracks, datetime.now())

            return tracks
        except Exception as e:
            print(f"    Error getting top tracks: {e}")
            return []

    def _get_cached_recent_albums(self, artist_id):
        """
        Get artist recent albums with caching (30 min TTL)
        Thread-safe with cache lock
        """
        # Check cache
        with self.cache_lock:
            if artist_id in self.albums_cache:
                album_ids, timestamp = self.albums_cache[artist_id]
                # Check if cache is still valid
                if (datetime.now() - timestamp).total_seconds() < self.ALBUMS_CACHE_TTL:
                    return album_ids

        # Cache miss or expired - fetch from API
        album_ids = self._get_artist_recent_albums(artist_id)

        # Store in cache
        with self.cache_lock:
            self.albums_cache[artist_id] = (album_ids, datetime.now())

        return album_ids

    def _process_single_artist(self, artist_name, language, market, normalized_mood):
        """
        Process a single artist and return tracks (for parallel execution)

        Args:
            artist_name: Artist name
            language: 'english' or 'hindi'
            market: 'US' or 'IN'
            normalized_mood: Mood category

        Returns:
            list: Tracks from this artist with metadata
        """
        artist_id = self._search_artist_by_name(artist_name, market=market)
        if not artist_id:
            return []

        tracks = []

        # Get top tracks (40%) - cached
        top_tracks = self._get_cached_top_tracks(artist_id, market)
        for track in top_tracks[:self.TRACKS_PER_ARTIST_TOP]:
            if track and track.get('id'):
                track['_track_type'] = 'top'
                track['_artist_name'] = artist_name
                track['_language'] = language
                tracks.append(track)

        # Get recent tracks (60%) - cached album list
        recent_album_ids = self._get_cached_recent_albums(artist_id)
        recent_track_items = self._get_tracks_from_albums(recent_album_ids, limit_per_album=2)
        recent_track_items = recent_track_items[:self.TRACKS_PER_ARTIST_RECENT]

        # Batch fetch full track details for recent tracks
        recent_track_ids = [t['id'] for t in recent_track_items if t and t.get('id')]
        if recent_track_ids:
            try:
                # Spotify supports up to 50 tracks per call
                full_tracks = self.sp.tracks(recent_track_ids, market=market)
                for track in full_tracks.get('tracks', []):
                    if track:
                        track['_track_type'] = 'recent'
                        track['_artist_name'] = artist_name
                        track['_language'] = language
                        tracks.append(track)
            except Exception as e:
                print(f"    Error batch fetching tracks: {e}")

        return tracks

    def _generate_all_songs_with_diversity(self, scored_tracks, english_count, hindi_count, max_songs=30):
        """
        Generate multiple songs from scored tracks with diversity rules applied.

        This generates more songs than needed (up to max_songs) so they can be cached
        and used for "load more" requests without re-running the algorithm.

        Args:
            scored_tracks: List of tracks with scores
            english_count: Target ratio for English songs in first batch
            hindi_count: Target ratio for Hindi songs in first batch
            max_songs: Maximum number of songs to generate

        Returns:
            List of formatted song dictionaries
        """
        all_songs = []
        artist_counts = {}

        # Separate by language
        english_pool = [t for t in scored_tracks if t.get('_language') == 'english']
        hindi_pool = [t for t in scored_tracks if t.get('_language') == 'hindi']

        # Track how many of each language we've added
        english_added = 0
        hindi_added = 0

        # For the first 5 songs, maintain the target ratio
        # After that, alternate between languages to maintain variety

        def format_track(track, lang_type):
            """Helper to format a track into song dictionary"""
            return {
                'id': track['id'],
                'name': track['name'],
                'artist': ', '.join([a['name'] for a in track['artists']]),
                'album': track['album']['name'],
                'preview_url': track.get('preview_url'),
                'spotify_url': track['external_urls']['spotify'],
                'album_cover': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'duration_ms': track['duration_ms'],
                'popularity': track.get('popularity', 0),
                'language_type': lang_type,
                'vibe_score': round(track['_vibe_score'], 2),
                'recency_bonus': round(track['_recency_bonus'], 2),
                'final_score': round(track['_final_score'], 2)
            }

        # Phase 1: Fill first 5 songs with target ratio
        english_idx = 0
        hindi_idx = 0

        while len(all_songs) < 5 and (english_idx < len(english_pool) or hindi_idx < len(hindi_pool)):
            # Determine which language to add next based on target ratio
            if english_added < english_count and english_idx < len(english_pool):
                track = english_pool[english_idx]
                english_idx += 1

                artist_name = track.get('_artist_name', 'Unknown')
                if artist_counts.get(artist_name, 0) >= self.MAX_TRACKS_PER_ARTIST:
                    continue

                artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
                all_songs.append(format_track(track, 'English'))
                english_added += 1

            elif hindi_added < hindi_count and hindi_idx < len(hindi_pool):
                track = hindi_pool[hindi_idx]
                hindi_idx += 1

                artist_name = track.get('_artist_name', 'Unknown')
                if artist_counts.get(artist_name, 0) >= self.MAX_TRACKS_PER_ARTIST:
                    continue

                artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
                all_songs.append(format_track(track, 'Hindi'))
                hindi_added += 1

            else:
                # Target ratio met but need more songs - add from any available pool
                if english_idx < len(english_pool):
                    track = english_pool[english_idx]
                    english_idx += 1

                    artist_name = track.get('_artist_name', 'Unknown')
                    if artist_counts.get(artist_name, 0) >= self.MAX_TRACKS_PER_ARTIST:
                        continue

                    artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
                    all_songs.append(format_track(track, 'English'))
                    english_added += 1

                elif hindi_idx < len(hindi_pool):
                    track = hindi_pool[hindi_idx]
                    hindi_idx += 1

                    artist_name = track.get('_artist_name', 'Unknown')
                    if artist_counts.get(artist_name, 0) >= self.MAX_TRACKS_PER_ARTIST:
                        continue

                    artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
                    all_songs.append(format_track(track, 'Hindi'))
                    hindi_added += 1
                else:
                    # No more tracks available - break to avoid infinite loop
                    break

        # Phase 2: Fill remaining slots (up to max_songs) alternating between languages
        while len(all_songs) < max_songs and (english_idx < len(english_pool) or hindi_idx < len(hindi_pool)):
            # Alternate: add English if we have more Hindi, or vice versa
            if english_added <= hindi_added and english_idx < len(english_pool):
                track = english_pool[english_idx]
                english_idx += 1

                artist_name = track.get('_artist_name', 'Unknown')
                if artist_counts.get(artist_name, 0) >= self.MAX_TRACKS_PER_ARTIST:
                    continue

                artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
                all_songs.append(format_track(track, 'English'))
                english_added += 1

            elif hindi_idx < len(hindi_pool):
                track = hindi_pool[hindi_idx]
                hindi_idx += 1

                artist_name = track.get('_artist_name', 'Unknown')
                if artist_counts.get(artist_name, 0) >= self.MAX_TRACKS_PER_ARTIST:
                    continue

                artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
                all_songs.append(format_track(track, 'Hindi'))
                hindi_added += 1
            else:
                # Try English again if Hindi is exhausted
                if english_idx < len(english_pool):
                    track = english_pool[english_idx]
                    english_idx += 1

                    artist_name = track.get('_artist_name', 'Unknown')
                    if artist_counts.get(artist_name, 0) >= self.MAX_TRACKS_PER_ARTIST:
                        continue

                    artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
                    all_songs.append(format_track(track, 'English'))
                    english_added += 1
                else:
                    # Both pools exhausted - break to avoid infinite loop
                    break

        return all_songs

    def get_song_recommendations(self, image_analysis, offset=0, excluded_ids=None):
        """
        Get song recommendations using Artist-Centric Algorithm with Recency

        NEW ALGORITHM:
        1. Normalize mood to one of 9 categories
        2. Get curated artists for that mood (7-8 per language)
        3. For each artist: Get 60% recent tracks + 40% top tracks
        4. Filter by strict vibe matching (>0.75)
        5. Score by: vibe (50%) + recency (30%) + popularity (20%)
        6. Use top tracks as seeds for Recommendations API
        7. Get related artists' tracks
        8. Apply diversity rules and return final 5

        Args:
            image_analysis (dict): Contains mood, energy, valence, etc.
            offset (int): For pagination (unused in new algo, kept for compatibility)
            excluded_ids (list): Track IDs to exclude

        Returns:
            list: 5 song recommendations with full metadata
        """
        try:
            from datetime import datetime

            # Extract analysis data
            mood = image_analysis.get('mood', 'happy')
            energy = image_analysis.get('energy', 0.5)
            valence = image_analysis.get('valence', 0.5)
            danceability = image_analysis.get('danceability', 0.5)
            acousticness = image_analysis.get('acousticness', 0.5)
            tempo = image_analysis.get('tempo', 120)
            cultural_vibe = image_analysis.get('cultural_vibe', 'global')

            excluded_ids = excluded_ids or []

            print(f"\n{'='*80}")
            print(f"[NEW ALGORITHM] Starting artist-centric recommendations")
            print(f"[NEW ALGORITHM] Mood: {mood}, Energy: {energy:.2f}, Valence: {valence:.2f}")
            print(f"[NEW ALGORITHM] Cultural vibe: {cultural_vibe}")
            print(f"[NEW ALGORITHM] Excluding {len(excluded_ids)} tracks")
            print(f"{'='*80}\n")

            # Step 1: Normalize mood to our 9 categories
            normalized_mood = self._normalize_mood(mood)
            print(f"[Step 1] Normalized mood: '{mood}' → '{normalized_mood}'")

            # Step 2: Get curated artists for this mood
            english_artists = self.ENGLISH_ARTISTS.get(normalized_mood, self.ENGLISH_ARTISTS['happy'])
            hindi_artists = self.HINDI_ARTISTS.get(normalized_mood, self.HINDI_ARTISTS['happy'])

            print(f"[Step 2] English artists: {english_artists[:3]}... ({len(english_artists)} total)")
            print(f"[Step 2] Hindi artists: {hindi_artists[:3]}... ({len(hindi_artists)} total)")

            # Step 3: Get tracks from artists (60% recent + 40% top tracks) - PARALLEL
            print(f"\n[Step 3] Fetching tracks in parallel...")
            import time
            start_time = time.time()

            all_tracks_with_metadata = []

            # Prepare artist tasks for parallel execution
            artist_tasks = []

            # Add English artists
            for artist_name in english_artists:
                artist_tasks.append((artist_name, 'english', 'US', normalized_mood))

            # Add Hindi artists
            for artist_name in hindi_artists:
                artist_tasks.append((artist_name, 'hindi', 'IN', normalized_mood))

            # Process artists in parallel (max 6 workers to avoid rate limiting)
            with ThreadPoolExecutor(max_workers=6) as executor:
                # Submit all artist processing tasks
                future_to_artist = {
                    executor.submit(self._process_single_artist, *task): task[0]
                    for task in artist_tasks
                }

                # Collect results as they complete
                for future in as_completed(future_to_artist):
                    artist_name = future_to_artist[future]
                    try:
                        tracks = future.result()
                        if tracks:
                            all_tracks_with_metadata.extend(tracks)
                            print(f"  ✓ Processed: {artist_name} ({len(tracks)} tracks)")
                        else:
                            print(f"  ⚠️  No tracks from: {artist_name}")
                    except Exception as e:
                        print(f"  ❌ Error processing {artist_name}: {e}")

            elapsed = time.time() - start_time
            print(f"\n[Step 3] Total tracks collected: {len(all_tracks_with_metadata)} in {elapsed:.2f}s ⚡")

            # Deduplicate tracks by ID (keep first occurrence)
            seen_ids = set()
            unique_tracks = []
            for track in all_tracks_with_metadata:
                track_id = track.get('id')
                if track_id and track_id not in seen_ids:
                    seen_ids.add(track_id)
                    unique_tracks.append(track)

            all_tracks_with_metadata = unique_tracks
            print(f"[Step 3] After deduplication: {len(all_tracks_with_metadata)} unique tracks")

            # Step 4: Get audio features and filter by vibe matching
            print(f"\n[Step 4] Filtering by vibe matching (threshold: {self.VIBE_THRESHOLD})...")

            track_ids = [t['id'] for t in all_tracks_with_metadata if t.get('id')]

            # Batch get audio features (max 50 at a time to avoid URL length issues)
            all_audio_features = []
            audio_features_working = True

            for i in range(0, len(track_ids), 50):
                batch = track_ids[i:i+50]
                try:
                    features = self.sp.audio_features(batch)
                    if features:
                        all_audio_features.extend(features)
                    else:
                        all_audio_features.extend([None] * len(batch))
                except Exception as e:
                    print(f"  Error getting audio features batch {i//50 + 1}: {str(e)[:100]}")
                    audio_features_working = False
                    # Use enhanced estimated features based on track metadata
                    for j, track in enumerate(all_tracks_with_metadata[i:i+50]):
                        language = track.get('_language', 'english')
                        estimated = self._enhance_audio_features(track, normalized_mood, language)
                        all_audio_features.append(estimated)

            if not audio_features_working:
                print(f"  ⚠️  Audio features API unavailable, using enhanced estimates (artist patterns + metadata)")

            # Adjust vibe threshold based on whether we're using real or estimated features
            effective_vibe_threshold = 0.5 if not audio_features_working else self.VIBE_THRESHOLD

            # Filter and score tracks
            # Get feedback-based preferences (Phase 1A: Artist Boosting & Phase 1B: Audio Feature Learning)
            mood = image_analysis.get('mood')
            feedback_store = get_feedback_store()
            audio_analytics = get_audio_feature_analytics()

            # Phase 1A: Get liked and disliked artists (require at least 1 feedback to count)
            liked_artists = feedback_store.get_liked_artists(mood=mood, min_likes=1)
            disliked_artists = feedback_store.get_disliked_artists(mood=mood, min_dislikes=1)

            # Convert to sets for faster lookup
            liked_artist_names = set([artist for artist, _ in liked_artists])
            disliked_artist_names = set([artist for artist, _ in disliked_artists])

            # Phase 1B: Get audio feature preferences
            audio_preferences = audio_analytics.get_preferred_audio_features(mood=mood)
            has_audio_preferences = audio_preferences.get('metadata', {}).get('has_enough_data', False)

            if liked_artist_names or disliked_artist_names or has_audio_preferences:
                print(f"\n[Feedback] Using learned preferences:")
                if liked_artist_names or disliked_artist_names:
                    print(f"  [Phase 1A] Liked artists: {list(liked_artist_names)[:5]}")
                    print(f"  [Phase 1A] Disliked artists: {list(disliked_artist_names)[:5]}")
                if has_audio_preferences:
                    print(f"  [Phase 1B] Audio feature preferences learned from {audio_preferences['metadata']['liked_count']} liked songs")

            scored_tracks = []
            for i, track in enumerate(all_tracks_with_metadata):
                if i >= len(all_audio_features):
                    break

                features = all_audio_features[i]
                if not features:
                    continue

                # Calculate vibe match score
                vibe_score = self._calculate_vibe_match_score(
                    features, energy, valence, danceability, acousticness, tempo
                )

                # Filter by threshold (adjusted for estimated features)
                if vibe_score < effective_vibe_threshold:
                    continue

                # Filter by popularity
                popularity = track.get('popularity', 0)
                if popularity < self.POPULARITY_MIN or popularity > self.POPULARITY_MAX:
                    continue

                # Filter by excluded IDs
                if track['id'] in excluded_ids:
                    continue

                # Calculate recency bonus
                release_date = track.get('album', {}).get('release_date', '')
                recency_bonus = self._calculate_recency_bonus(release_date) if release_date else 0.5

                # Calculate final score
                final_score = (
                    vibe_score * self.VIBE_WEIGHT +
                    recency_bonus * self.RECENCY_WEIGHT +
                    (popularity / 100) * self.POPULARITY_WEIGHT
                )

                # Apply feedback-based adjustments
                # Phase 1A: Artist preference boosting
                artist_name = track.get('artists', [{}])[0].get('name', '')
                feedback_multiplier = 1.0

                if artist_name in liked_artist_names:
                    feedback_multiplier = 1.3  # 30% boost for liked artists
                    track['_feedback_boost'] = 'liked_artist'
                elif artist_name in disliked_artist_names:
                    feedback_multiplier = 0.7  # 30% penalty for disliked artists
                    track['_feedback_boost'] = 'disliked_artist'

                final_score *= feedback_multiplier

                # Phase 1B: Audio feature preference boosting
                if has_audio_preferences and features:
                    audio_boost, audio_reason = audio_analytics.calculate_audio_feature_boost(features, mood=mood)
                    final_score *= audio_boost

                    # Track audio feature boost for debugging
                    track['_audio_feature_boost'] = audio_reason
                    if audio_reason in ['perfect_match', 'good_match']:
                        # Mark tracks that got boosted
                        if '_feedback_boost' not in track:
                            track['_feedback_boost'] = f'audio_{audio_reason}'
                        else:
                            track['_feedback_boost'] += f'+audio_{audio_reason}'

                track['_vibe_score'] = vibe_score
                track['_recency_bonus'] = recency_bonus
                track['_final_score'] = final_score
                track['_audio_features'] = features

                scored_tracks.append(track)

            print(f"[Step 4] Tracks passing filters: {len(scored_tracks)}")

            # Step 5: Sort by final score
            scored_tracks.sort(key=lambda x: x['_final_score'], reverse=True)

            # Step 6: Determine language mix for first 5 songs
            english_count, hindi_count = self._determine_language_mix(image_analysis)
            print(f"\n[Step 5] Language mix: {english_count} English, {hindi_count} Hindi")

            # Step 7: Generate ALL songs with diversity (for caching)
            all_available_songs = self._generate_all_songs_with_diversity(
                scored_tracks,
                english_count,
                hindi_count,
                max_songs=30  # Generate up to 30 songs for "load more"
            )

            print(f"[Step 6] Generated {len(all_available_songs)} total songs for caching")

            # Return first 5 songs from the full list
            final_songs = all_available_songs[:5]

            # Final summary
            print(f"\n{'='*80}")
            print(f"[FINAL] Returning {len(final_songs)} songs (with {len(all_available_songs)} total available for 'load more')")
            for i, song in enumerate(final_songs, 1):
                print(f"  {i}. [{song['language_type']}] {song['name']} - {song['artist']}")
                print(f"     Vibe: {song['vibe_score']}, Recency: {song['recency_bonus']}, Score: {song['final_score']}")
            print(f"{'='*80}\n")

            # Return dict with both first batch and full list for caching
            return {
                'songs': final_songs,
                'all_songs': all_available_songs  # For "load more" caching
            }

        except Exception as e:
            print(f"\n[ERROR] Exception in get_song_recommendations: {e}")
            import traceback
            traceback.print_exc()
            return {'songs': [], 'all_songs': []}

    def _get_mood_playlists(self, mood, genres, themes, keywords=None):
        """
        Get contextual playlist IDs based on mood, themes, and keywords

        Uses both curated playlists and contextual search
        """
        mood_lower = mood.lower()
        playlist_ids = []

        # Map moods to Spotify's curated playlists (high quality, verified)
        curated_map = {
            'calm': ['37i9dQZF1DWZd79rJ6a7lp', '37i9dQZF1DX4sWSpwq3LiO'],  # Peaceful Piano, Chill Lofi
            'peaceful': ['37i9dQZF1DWZd79rJ6a7lp', '37i9dQZF1DX4sWSpwq3LiO'],
            'relaxed': ['37i9dQZF1DWZd79rJ6a7lp', '37i9dQZF1DX0XUfTFmNBRM'],
            'happy': ['37i9dQZF1DXdPec7aLTmlC', '37i9dQZF1DX0UrRvztWcAU'],  # Happy Hits, Feel Good
            'energetic': ['37i9dQZF1DX76Wlfdnj7AP', '37i9dQZF1DX0vHZ8elq0UK'],  # Beast Mode, Energy
            'melancholic': ['37i9dQZF1DX7qK8ma5wgG1', '37i9dQZF1DWX83CujKHHOn'],  # Sad Indie, Sad Songs
            'romantic': ['37i9dQZF1DX50KsbC0ZOeI', '37i9dQZF1DX1n9whBbREo9'],  # Love Songs, Romance
        }

        # Start with curated playlists for the mood (1-2 playlists)
        for key, playlists in curated_map.items():
            if key in mood_lower:
                playlist_ids.extend(playlists[:1])  # Take only 1 curated
                break

        # Now search for contextual playlists using themes and keywords
        search_terms = []

        # Combine keywords and themes to create contextual search terms
        if keywords:
            # e.g., "sunset beach chill", "workout motivation", "coffee shop acoustic"
            for keyword in keywords[:3]:
                search_terms.append(f"{keyword} {mood}")

        if themes:
            # e.g., "nature peaceful playlist", "party energy playlist"
            for theme in themes[:2]:
                search_terms.append(f"{theme} {mood} playlist")

        # Add genre-based searches
        if genres:
            search_terms.append(f"{mood} {genres[0]}")

        # Search for contextual playlists
        for term in search_terms[:3]:  # Limit to 3 searches
            try:
                results = self.sp.search(q=term, type='playlist', limit=2)
                if results['playlists']['items']:
                    # Add playlist IDs from search results
                    for playlist in results['playlists']['items'][:1]:  # Take top 1 from each search
                        playlist_ids.append(playlist['id'])
                        print(f"[SpotifyService] Found contextual playlist for '{term}': {playlist['name']}")
            except Exception as e:
                print(f"Contextual playlist search error for '{term}': {e}")
                continue

        # Fallback if no playlists found
        if not playlist_ids:
            try:
                results = self.sp.search(q=f"{mood} {genres[0] if genres else 'indie'}", type='playlist', limit=2)
                if results['playlists']['items']:
                    playlist_ids = [p['id'] for p in results['playlists']['items'][:2]]
            except:
                playlist_ids = ['37i9dQZF1DXcBWIGoYBM5M']  # Today's Top Hits as last resort

        print(f"[SpotifyService] Using {len(playlist_ids)} playlists (curated + contextual)")
        return playlist_ids[:4]  # Max 4 playlists to avoid too many API calls

    def _get_hindi_mood_playlists(self, mood, genres, themes, keywords=None):
        """
        Get Hindi/Bollywood playlist IDs based on mood, themes, and keywords

        Similar to English playlists but focused on Hindi/Bollywood music
        """
        mood_lower = mood.lower()
        playlist_ids = []

        # Search for Hindi playlists based on mood
        search_terms = []

        # Mood-based Hindi playlist searches
        hindi_mood_terms = {
            'calm': ['peaceful bollywood songs', 'soothing hindi music', 'calm bollywood'],
            'peaceful': ['peaceful hindi songs', 'relaxing bollywood', 'soft hindi music'],
            'relaxed': ['chill bollywood', 'relaxed hindi songs', 'easy listening hindi'],
            'happy': ['happy bollywood songs', 'cheerful hindi music', 'feel good bollywood'],
            'joyful': ['joyful bollywood', 'uplifting hindi songs', 'happy hindi music'],
            'energetic': ['energetic bollywood', 'dance bollywood hits', 'party hindi songs'],
            'confident': ['confident bollywood', 'powerful hindi songs', 'motivational bollywood'],
            'melancholic': ['sad bollywood songs', 'emotional hindi music', 'heartbreak bollywood'],
            'nostalgic': ['old bollywood hits', 'retro hindi songs', 'classic bollywood'],
            'romantic': ['romantic bollywood songs', 'love hindi music', 'romantic hindi'],
            'adventurous': ['adventurous bollywood', 'upbeat hindi songs', 'energetic bollywood']
        }

        # Add mood-based search terms
        for key, terms in hindi_mood_terms.items():
            if key in mood_lower:
                search_terms.extend(terms[:2])
                break

        # Add keyword and theme-based searches
        if keywords:
            for keyword in keywords[:2]:
                search_terms.append(f"{keyword} bollywood {mood}")

        if themes:
            for theme in themes[:2]:
                search_terms.append(f"{theme} hindi {mood}")

        # Always add some general Hindi searches
        search_terms.append('trending bollywood songs')
        search_terms.append('latest hindi hits')

        # Search for playlists
        for term in search_terms[:5]:  # Limit to 5 searches
            try:
                results = self.sp.search(q=term, type='playlist', limit=2, market='IN')
                if results['playlists']['items']:
                    for playlist in results['playlists']['items']:
                        if playlist and playlist.get('id'):
                            playlist_ids.append(playlist['id'])
                            print(f"[SpotifyService] Found Hindi playlist: {playlist.get('name', 'Unknown')} for '{term}'")
            except Exception as e:
                print(f"[SpotifyService] Error searching Hindi playlists for '{term}': {e}")
                continue

        print(f"[SpotifyService] Found {len(playlist_ids)} Hindi playlists for mood '{mood}'")
        return playlist_ids[:6]  # Return top 6 playlists

    def _find_playlist_by_name(self, name, market='IN', limit=5):
        """Try to locate a Spotify playlist by its display name."""
        try:
            results = self.sp.search(q=name, type='playlist', limit=limit, market=market)
            if results and results.get('playlists', {}).get('items'):
                for playlist in results['playlists']['items']:
                    playlist_name = playlist.get('name', '').strip().lower()
                    if playlist_name == name.lower() and playlist.get('id'):
                        return playlist['id']
        except Exception as exc:
            print(f"[SpotifyService] Failed to locate playlist '{name}': {exc}")
        return None

    def _get_trending_hindi_tracks(self, energy, valence, danceability, acousticness, tempo, offset=0):
        """
        Get trending Hindi songs from popular playlists and filter by audio features

        This approach is more reliable than search terms - we pull from curated playlists
        and let Spotify's audio features do the matching
        """
        hindi_tracks = []

        # Search for popular Hindi/Bollywood playlists dynamically
        print(f"[SpotifyService] Searching for trending Hindi playlists...")

        try:
            # Search for multiple types of Hindi playlists
            search_terms = [
                'bollywood hits',
                'trending hindi songs',
                'latest bollywood',
                'indie hindi',
                'hindi chart toppers',
                self.TRENDING_NOW_INDIA_PLAYLIST_NAME
            ]

            playlist_ids = []

            # Always try to include Spotify's "Trending Now India" playlist if available
            trending_now_playlist_id = self._find_playlist_by_name(self.TRENDING_NOW_INDIA_PLAYLIST_NAME)
            if trending_now_playlist_id:
                playlist_ids.append(trending_now_playlist_id)
                print("[SpotifyService] Added 'Trending Now India' playlist via direct lookup")

            for term in search_terms[:5]:  # Use top search terms, including trending
                try:
                    results = self.sp.search(q=term, type='playlist', limit=3, market='IN')
                    if results and 'playlists' in results and results['playlists']['items']:
                        for playlist in results['playlists']['items']:
                            if not playlist or not playlist.get('id'):
                                continue

                            playlist_id = playlist['id']
                            playlist_name = playlist.get('name', 'Unknown')

                            # Prioritize exact match for Trending Now India
                            if playlist_id not in playlist_ids:
                                playlist_ids.append(playlist_id)
                                print(f"[SpotifyService] Found Hindi playlist: {playlist_name}")

                            if playlist_name.strip().lower() == self.TRENDING_NOW_INDIA_PLAYLIST_NAME.lower():
                                print("[SpotifyService] Confirmed 'Trending Now India' playlist from search")
                except Exception as e:
                    print(f"[SpotifyService] Error searching for Hindi playlist with '{term}': {e}")
                    continue

            if not playlist_ids:
                print("[SpotifyService] No Hindi playlists found")
                return []

            # Preserve order but remove duplicates to avoid redundant API calls
            unique_playlist_ids = []
            for playlist_id in playlist_ids:
                if playlist_id not in unique_playlist_ids:
                    unique_playlist_ids.append(playlist_id)

            playlist_ids = unique_playlist_ids

            # Fetch tracks from found playlists
            for playlist_id in playlist_ids[:4]:  # Use top playlists with trending bias
                try:
                    playlist = self.sp.playlist_tracks(playlist_id, limit=30, offset=offset % 50)
                    if playlist and 'items' in playlist:
                        for item in playlist['items']:
                            if item['track'] and item['track']['id']:
                                track = item['track']
                                track['_source'] = 'trending_hindi_playlist'
                                track['_source_weight'] = 0.9  # Slightly below recommendations but higher than generic playlists
                                hindi_tracks.append(track)
                except Exception as e:
                    print(f"[SpotifyService] Error fetching tracks from playlist {playlist_id}: {e}")
                    continue

        except Exception as e:
            print(f"[SpotifyService] Error in Hindi playlist search: {e}")
            return []

        if not hindi_tracks:
            print("[SpotifyService] No Hindi tracks found from playlists")
            return []

        print(f"[SpotifyService] Found {len(hindi_tracks)} Hindi tracks from playlists")

        # Now get audio features for these tracks to filter by vibe
        try:
            track_ids = [t['id'] for t in hindi_tracks[:50]]  # Limit to 50 for API efficiency
            audio_features_list = self.sp.audio_features(track_ids)

            # Match tracks by audio features (similar to how recommendations API works)
            matched_tracks = []

            for i, track in enumerate(hindi_tracks[:50]):
                if i >= len(audio_features_list) or not audio_features_list[i]:
                    continue

                features = audio_features_list[i]

                # Calculate how well this track matches the desired vibe
                # Using a scoring system based on feature proximity
                energy_score = 1.0 - abs(features.get('energy', 0.5) - energy)
                valence_score = 1.0 - abs(features.get('valence', 0.5) - valence)
                danceability_score = 1.0 - abs(features.get('danceability', 0.5) - danceability)
                acousticness_score = 1.0 - abs(features.get('acousticness', 0.5) - acousticness)

                # Tempo matching (normalize to 0-1 scale)
                track_tempo = features.get('tempo', 120)
                tempo_diff = abs(track_tempo - tempo)
                tempo_score = max(0, 1.0 - (tempo_diff / 50))  # 50 BPM tolerance

                # Weighted average (prioritize energy and valence)
                vibe_match_score = (
                    energy_score * 0.3 +
                    valence_score * 0.3 +
                    danceability_score * 0.15 +
                    acousticness_score * 0.15 +
                    tempo_score * 0.1
                )

                # Only include tracks with good vibe match (>0.6 threshold)
                if vibe_match_score > 0.6:
                    track['_vibe_match_score'] = vibe_match_score
                    track['_audio_features'] = features
                    matched_tracks.append(track)

            # Sort by vibe match score
            matched_tracks.sort(key=lambda x: x['_vibe_match_score'], reverse=True)

            top_matches = matched_tracks[:30]
            print(f"[SpotifyService] Matched {len(matched_tracks)} Hindi tracks by vibe (threshold: 0.6), using top {len(top_matches)}")

            return top_matches

        except Exception as e:
            print(f"[SpotifyService] Error getting audio features for Hindi tracks: {e}")
            # Fallback: return tracks without filtering
            return hindi_tracks[:30]

    def _get_seed_tracks(self, mood, genres, offset):
        """Get seed tracks for recommendations"""
        try:
            # Search for popular artists/tracks in the genre and mood
            genre_str = genres[0] if genres else 'pop'
            query = f"{mood} {genre_str}"

            results = self.sp.search(q=query, type='track', limit=10, offset=offset % 20)
            if results and 'tracks' in results and 'items' in results['tracks']:
                # Filter for popular tracks
                popular_tracks = [t for t in results['tracks']['items'] if t.get('popularity', 0) > 50]
                return popular_tracks[:5] if popular_tracks else results['tracks']['items'][:5]
        except Exception as e:
            print(f"Seed track error: {e}")

        return []

    def _get_hindi_recommendations(self, mood, genres, energy, valence, danceability,
                                   acousticness, tempo, instrumentalness, offset,
                                   energy_min, energy_max, valence_min, valence_max,
                                   danceability_min, danceability_max, acousticness_min,
                                   acousticness_max, tempo_min, tempo_max,
                                   instrumentalness_min, instrumentalness_max):
        """
        Get Hindi/Bollywood song recommendations using Spotify Recommendations API

        Uses the same approach as English songs for consistent quality
        """
        try:
            # Get seed tracks for Hindi/Bollywood music
            seed_tracks = self._get_hindi_seed_tracks(mood, genres, offset)

            if not seed_tracks:
                print("[SpotifyService] No Hindi seed tracks found")
                return []

            print(f"[SpotifyService] Using Hindi seed tracks: {[t['name'] for t in seed_tracks[:3]]}")
            seed_ids = [t['id'] for t in seed_tracks[:5]]

            # Use Spotify Recommendations API with same audio features as English
            print(f"[SpotifyService] Getting Hindi recommendations with audio ranges")
            rec_results = self.sp.recommendations(
                seed_tracks=seed_ids,
                limit=20,
                market='IN',  # Focus on Indian market for better Hindi results
                target_energy=energy,
                min_energy=energy_min,
                max_energy=energy_max,
                target_valence=valence,
                min_valence=valence_min,
                max_valence=valence_max,
                target_danceability=danceability,
                min_danceability=danceability_min,
                max_danceability=danceability_max,
                target_acousticness=acousticness,
                min_acousticness=acousticness_min,
                max_acousticness=acousticness_max,
                target_tempo=tempo,
                min_tempo=tempo_min,
                max_tempo=tempo_max,
                target_instrumentalness=instrumentalness,
                min_instrumentalness=instrumentalness_min,
                max_instrumentalness=instrumentalness_max,
            )

            if rec_results and 'tracks' in rec_results:
                print(f"[SpotifyService] Got {len(rec_results['tracks'])} Hindi recommendations")
                return rec_results['tracks']

        except Exception as e:
            print(f"[SpotifyService] Error getting Hindi recommendations: {e}")

        return []

    def _get_hindi_seed_tracks(self, mood, genres, offset):
        """
        Get seed tracks for Hindi/Bollywood recommendations

        Searches for popular Hindi/Bollywood tracks matching the mood
        """
        try:
            # Search for popular Hindi tracks based on mood and genre
            # Use Bollywood/Hindi-specific search terms
            hindi_queries = [
                f"bollywood {mood}",
                f"hindi {mood}",
                "bollywood chartbusters",
                "trending hindi songs",
                "indie hindi hits",
            ]

            # Pick a search query based on mood/genre
            if 'romantic' in mood.lower() or 'love' in mood.lower():
                query = f"romantic bollywood songs"
            elif 'energetic' in mood.lower() or 'dance' in mood.lower():
                query = f"bollywood dance hits"
            elif 'peaceful' in mood.lower() or 'calm' in mood.lower():
                query = f"soothing hindi songs"
            elif 'melancholic' in mood.lower() or 'sad' in mood.lower():
                query = f"sad bollywood songs"
            else:
                # Use first hindi query with mood
                query = hindi_queries[0]

            print(f"[SpotifyService] Searching for Hindi seed tracks with: '{query}'")
            results = self.sp.search(q=query, type='track', limit=10, offset=offset % 20, market='IN')

            if results and 'tracks' in results and 'items' in results['tracks']:
                # Filter for popular tracks
                popular_tracks = [t for t in results['tracks']['items'] if t.get('popularity', 0) > 40]
                seed_tracks = popular_tracks[:5] if popular_tracks else results['tracks']['items'][:5]
                print(f"[SpotifyService] Found {len(seed_tracks)} Hindi seed tracks")
                return seed_tracks

        except Exception as e:
            print(f"[SpotifyService] Error getting Hindi seed tracks: {e}")

        return []

    def _get_smart_search_terms(self, mood, genres, themes, keywords, language='english'):
        """Generate smart search terms avoiding cliches"""
        terms = []
        mood_lower = mood.lower()

        if language == 'hindi':
            # Hindi/Bollywood-specific search terms
            hindi_mood_terms = {
                'calm': ['peaceful bollywood', 'soothing hindi', 'calm desi music'],
                'peaceful': ['soft bollywood', 'relaxing hindi', 'peaceful desi'],
                'relaxed': ['chill bollywood', 'easy listening hindi', 'relaxed desi'],
                'happy': ['happy bollywood', 'cheerful hindi', 'upbeat desi'],
                'joyful': ['joyful bollywood', 'feel good hindi', 'happy desi'],
                'energetic': ['energetic bollywood', 'dance hindi', 'party desi'],
                'confident': ['powerful bollywood', 'motivational hindi', 'confident desi'],
                'melancholic': ['sad bollywood', 'emotional hindi', 'heartbreak desi'],
                'nostalgic': ['old bollywood', 'retro hindi', 'classic desi'],
                'romantic': ['romantic bollywood', 'love hindi', 'romantic desi'],
                'adventurous': ['upbeat bollywood', 'energetic hindi', 'adventurous desi']
            }

            for key, search_terms in hindi_mood_terms.items():
                if key in mood_lower:
                    terms.extend(search_terms)
                    break

            # Add Hindi-specific genre terms
            if genres:
                for g in genres[:2]:
                    if 'bollywood' in g.lower() or 'hindi' in g.lower():
                        terms.append(f"{g} {mood}")

            # Add keywords with Hindi/Bollywood context
            if keywords:
                for keyword in keywords[:3]:
                    if keyword.lower() not in ['vibes', 'chill', 'lifestyle', 'moments', 'mood', 'general']:
                        terms.append(f"{keyword} bollywood")

            # Fallback for Hindi
            if not terms:
                terms = [f"bollywood {mood}", "latest hindi hits", "trending desi music"]

        else:
            # English/International search terms
            mood_terms = {
                'calm': ['indie folk', 'bedroom pop', 'alt-pop chill', 'atmospheric'],
                'peaceful': ['ambient pop', 'dream pop', 'soft indie'],
                'relaxed': ['chill indie', 'lo-fi beats', 'acoustic pop'],
                'happy': ['indie pop', 'alt-pop upbeat', 'indie dance'],
                'joyful': ['feel good indie', 'uplifting pop', 'happy vibes'],
                'energetic': ['indie rock', 'alt-rock', 'electronic pop'],
                'confident': ['upbeat pop', 'indie anthem', 'empowering'],
                'melancholic': ['sad indie', 'indie folk emotional', 'alternative'],
                'nostalgic': ['retro indie', 'throwback', 'nostalgic vibes'],
                'romantic': ['indie love songs', 'dreamy pop', 'soft rock'],
                'adventurous': ['indie rock', 'alternative adventure', 'upbeat indie']
            }

            for key, search_terms in mood_terms.items():
                if key in mood_lower:
                    terms.extend(search_terms)
                    break

            # Add genre if not too generic
            if genres:
                for g in genres[:2]:
                    if g.lower() not in ['pop', 'rock', 'bollywood', 'hindi']:  # Skip overly generic
                        terms.append(g)

            # Add themes
            if themes:
                for theme in themes[:2]:
                    if theme.lower() not in ['general', 'lifestyle', 'moments']:
                        terms.append(f"{theme} {genres[0] if genres else 'indie'}")

            # Add keywords from image analysis
            if keywords:
                for keyword in keywords[:3]:
                    if keyword.lower() not in ['vibes', 'chill', 'lifestyle', 'moments', 'mood', 'general']:
                        terms.append(f"{keyword} {mood}")

            # Fallback for English
            if not terms:
                terms = [f"indie {mood}", "alternative", "new music"]

        return terms

    def _get_indian_search_terms(self, mood, genres, themes, keywords):
        """Generate search terms for Hindi/Indian music"""
        terms = []

        # Mood-based terms for Indian music (refined for better vibe matching)
        mood_terms = {
            'calm': ['peaceful hindi', 'sufi calm', 'acoustic hindi', 'indie hindi chill'],
            'peaceful': ['sufi', 'meditation hindi', 'peaceful bollywood', 'sufi qawwali classics'],
            'relaxed': ['chill hindi', 'indie hindi', 'lo-fi hindi', 'mellow bollywood'],
            'happy': ['feel good bollywood', 'upbeat hindi', 'happy indie hindi'],  # Removed party terms
            'joyful': ['romantic hindi', 'melodious bollywood', 'soothing hindi love'],  # More melodious, less party
            'dreamy': ['sufi romantic', 'ethereal hindi', 'romantic ballad hindi', 'soothing hindi vocals'],  # New: for dreamy moods
            'energetic': ['punjabi bhangra', 'high energy hindi', 'gym workout hindi'],
            'confident': ['desi hip-hop', 'rap hindi', 'urban desi', 'hip-hop hindi'],  # More hip-hop focused
            'melancholic': ['sad hindi songs', 'emotional bollywood', 'heartbreak hindi', 'soulful hindi ballads'],
            'nostalgic': ['90s bollywood', 'retro hindi', 'classic hindi songs', 'old is gold hindi'],
            'romantic': ['romantic hindi', 'love songs bollywood', 'sufi romantic', 'hindi love ballads'],
            'adventurous': ['road trip hindi', 'travel playlist hindi', 'uplifting bollywood'],
            'reflective': ['thoughtful hindi', 'indie hindi acoustic', 'sufi', 'meaningful lyrics hindi'],  # New: for reflective moods
            'serenity': ['peaceful sufi', 'calm hindi', 'meditation bollywood', 'ambient hindi'],  # New: for serene moods
        }

        mood_lower = mood.lower()

        # Try to match mood more flexibly
        matched = False
        for key, search_terms in mood_terms.items():
            if key in mood_lower:
                terms.extend(search_terms)
                matched = True
                break

        # If no exact match, try partial matching for compound moods
        if not matched:
            if any(x in mood_lower for x in ['dream', 'elegant', 'grace']):
                terms.extend(mood_terms.get('dreamy', []))
            elif any(x in mood_lower for x in ['reflect', 'contemplate', 'thought']):
                terms.extend(mood_terms.get('reflective', []))
            elif any(x in mood_lower for x in ['seren', 'tranquil', 'quiet']):
                terms.extend(mood_terms.get('serenity', []))

        # Check if Indian genres were suggested
        indian_genres = []
        for g in genres:
            g_lower = g.lower()
            if any(x in g_lower for x in ['bollywood', 'hindi', 'punjabi', 'sufi', 'desi', 'carnatic', 'hindustani', 'indi-pop']):
                indian_genres.append(g_lower)

        # Add Indian genre-specific terms
        if indian_genres:
            terms.extend(indian_genres[:2])
        else:
            # Add general Bollywood/Hindi as fallback
            terms.append('trending hindi songs')
            terms.append('latest bollywood')

        # Add keywords from image analysis for Indian songs
        if keywords:
            for keyword in keywords[:2]:
                if keyword.lower() not in ['vibes', 'chill', 'lifestyle', 'moments', 'mood', 'general']:
                    terms.append(f"{keyword} hindi")

        # Add mood-appropriate Indian artists (more selective)
        # Only add artists that match the specific mood
        if any(x in mood_lower for x in ['romantic', 'love', 'dreamy', 'joyful']):
            terms.append('romantic hindi ballad')
            terms.append('soulful bollywood love')
        elif any(x in mood_lower for x in ['calm', 'peaceful', 'serene', 'reflect']):
            terms.append('sufi playlist')
            terms.append('soothing hindi vocals')
        elif any(x in mood_lower for x in ['sad', 'melanchol', 'emotional']):
            terms.append('heartbreak hindi songs')
            terms.append('emotional ballad hindi')
        elif any(x in mood_lower for x in ['energetic', 'party', 'hype']):
            terms.append('punjabi party hits')
            terms.append('punjabi workout')
        elif any(x in mood_lower for x in ['confident', 'swagger', 'boss']):
            terms.append('desi rap')
            terms.append('desi hip-hop hits')
        elif any(x in mood_lower for x in ['nostalgic', 'retro', 'classic']):
            terms.append('90s evergreen hindi')
            terms.append('retro bollywood classics')
        else:
            # For other moods, use more general but quality terms
            terms.append('indie hindi')
            terms.append('bollywood chartbusters')

        # Fallback
        if not terms:
            terms = ['latest hindi songs', 'bollywood 2024', 'indie hindi']

        return terms

    def get_track_details(self, track_id):
        """Get detailed information about a specific track"""
        try:
            track = self.sp.track(track_id)
            return {
                'id': track['id'],
                'name': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'preview_url': track.get('preview_url'),
                'spotify_url': track['external_urls']['spotify'],
                'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity']
            }
        except Exception as e:
            print(f"Error getting track details: {e}")
            return None
