import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from config import Config


class SpotifyService:
    """Service for interacting with Spotify API"""

    def __init__(self):
        """Initialize Spotify client"""
        self.client_credentials = SpotifyClientCredentials(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET
        )
        self.sp = spotipy.Spotify(client_credentials_manager=self.client_credentials)

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

    def get_song_recommendations(self, image_analysis, offset=0, excluded_ids=None):
        """
        Get song recommendations based on image analysis using trending/popular songs

        Args:
            image_analysis (dict): Contains mood, themes, keywords, and genres
            offset (int): Offset for getting different recommendations (pagination)
            excluded_ids (list): List of track IDs to exclude (already returned)

        Returns:
            list: Top 5 song recommendations with details
        """
        try:
            # Extract relevant data from analysis
            mood = image_analysis.get('mood', 'happy')
            genres = image_analysis.get('genres', ['pop'])
            energy = image_analysis.get('energy', 0.5)
            valence = image_analysis.get('valence', 0.5)
            danceability = image_analysis.get('danceability', 0.5)
            acousticness = image_analysis.get('acousticness', 0.5)
            tempo = image_analysis.get('tempo', 120)
            instrumentalness = image_analysis.get('instrumentalness', 0.2)
            keywords = image_analysis.get('keywords', [])
            themes = image_analysis.get('themes', [])

            excluded_ids = excluded_ids or []
            cultural_vibe = image_analysis.get('cultural_vibe', 'global')
            music_style = image_analysis.get('music_style', '')

            print(f"[SpotifyService] Getting recommendations with mood={mood}")
            print(f"[SpotifyService] Audio Features - energy={energy:.2f}, valence={valence:.2f}, danceability={danceability:.2f}, acousticness={acousticness:.2f}, tempo={tempo}, instrumentalness={instrumentalness:.2f}")
            print(f"[SpotifyService] Genres: {genres}, Themes: {themes}, Keywords: {keywords}")
            print(f"[SpotifyService] Cultural vibe: {cultural_vibe}, Music style: {music_style}")
            print(f"[SpotifyService] Excluding {len(excluded_ids)} previously returned tracks")

            # Determine language mix based on cultural vibe
            # indian = 3 Hindi/regional + 2 English
            # western = 4 English + 1 Hindi
            # global/fusion = 3 English + 2 Hindi
            if cultural_vibe.lower() == 'indian':
                hindi_count = 3
                english_count = 2
            elif cultural_vibe.lower() == 'western':
                hindi_count = 1
                english_count = 4
            else:  # global or fusion
                hindi_count = 2
                english_count = 3

            print(f"[SpotifyService] Target mix: {english_count} English, {hindi_count} Hindi/Indian")

            all_tracks = []

            # Strategy 1: Get curated playlists for the mood/genre
            mood_playlists = self._get_mood_playlists(mood, genres, themes)
            playlist_tracks = []

            for playlist_id in mood_playlists[:3]:  # Use top 3 playlists
                try:
                    playlist = self.sp.playlist_tracks(playlist_id, limit=20, offset=offset)
                    if playlist and 'items' in playlist:
                        for item in playlist['items']:
                            if item['track'] and item['track']['id']:
                                playlist_tracks.append(item['track'])
                        print(f"[SpotifyService] Got {len(playlist['items'])} tracks from playlist")
                except Exception as e:
                    print(f"Playlist fetch error: {e}")
                    continue

            all_tracks.extend(playlist_tracks)

            # Strategy 2: Use Spotify recommendations with seed tracks from popular artists
            if len(all_tracks) < 20:
                try:
                    # Get seed tracks based on mood/genre
                    seed_tracks = self._get_seed_tracks(mood, genres, offset)

                    if seed_tracks:
                        print(f"[SpotifyService] Using seed tracks: {[t['name'] for t in seed_tracks[:3]]}")
                        seed_ids = [t['id'] for t in seed_tracks[:5]]

                        rec_results = self.sp.recommendations(
                            seed_tracks=seed_ids,
                            limit=20,
                            target_energy=energy,
                            target_valence=valence,
                            target_danceability=danceability,
                            target_acousticness=acousticness,
                            target_tempo=tempo,
                            target_instrumentalness=instrumentalness,
                        )

                        if rec_results and 'tracks' in rec_results:
                            print(f"[SpotifyService] Got {len(rec_results['tracks'])} from recommendations")
                            all_tracks.extend(rec_results['tracks'])
                except Exception as e:
                    print(f"Recommendations error: {e}")

            # Strategy 3: Search with better terms - separate English and Hindi
            english_tracks = []
            hindi_tracks = []

            # Get English/International tracks
            english_terms = self._get_smart_search_terms(mood, genres, themes, keywords, language='english')
            search_offset = offset % 50

            for term in english_terms[:3]:
                try:
                    # Removed year restriction to allow more diverse results
                    query = f"{term}"
                    results = self.sp.search(q=query, type='track', limit=15, offset=search_offset)
                    if results['tracks']['items']:
                        print(f"[SpotifyService] Found {len(results['tracks']['items'])} English tracks for '{query}'")
                        english_tracks.extend(results['tracks']['items'])
                except Exception as e:
                    print(f"Search error for term '{term}': {e}")

            # Get Hindi/Indian tracks
            hindi_terms = self._get_indian_search_terms(mood, genres, themes, keywords)

            for term in hindi_terms[:3]:
                try:
                    # Search for Indian music
                    query = f"{term}"
                    results = self.sp.search(q=query, type='track', limit=15, offset=search_offset, market='IN')
                    if results['tracks']['items']:
                        print(f"[SpotifyService] Found {len(results['tracks']['items'])} Hindi/Indian tracks for '{query}'")
                        hindi_tracks.extend(results['tracks']['items'])
                except Exception as e:
                    print(f"Search error for Hindi term '{term}': {e}")

            # Add both to all_tracks for processing
            all_tracks.extend(english_tracks)
            all_tracks.extend(hindi_tracks)

            # Remove duplicates and filter for quality
            seen_ids = set()
            seen_artists = set()
            unique_tracks = []

            # Filter for high-quality tracks (lowered to include hidden gems)
            MIN_POPULARITY = 25  # Minimum popularity score for quality (was 40, lowered for more variety)
            MAX_POPULARITY = 95  # Maximum popularity to avoid only mainstream hits

            for track in all_tracks:
                if not track or not track.get('id'):
                    continue

                track_id = track['id']
                popularity = track.get('popularity', 0)

                # Skip if duplicate, previously returned, or low quality
                if track_id in seen_ids or track_id in excluded_ids:
                    continue

                # Only include tracks with balanced popularity (not too low, not too high)
                if popularity < MIN_POPULARITY or popularity > MAX_POPULARITY:
                    continue

                seen_ids.add(track_id)

                # Add diversity score (prefer different artists)
                artist_names = [artist['name'] for artist in track.get('artists', [])]
                artist_key = tuple(sorted(artist_names))

                # Penalize if we've seen this artist too many times
                artist_count = seen_artists.count(artist_key) if hasattr(seen_artists, 'count') else 0
                diversity_penalty = artist_count * 5  # Reduce score for repeated artists

                track['_score'] = popularity - diversity_penalty
                track['_artist_key'] = artist_key
                unique_tracks.append(track)

            # Sort by adjusted score (popularity - diversity penalty)
            unique_tracks.sort(key=lambda x: x['_score'], reverse=True)

            print(f"[SpotifyService] Total unique quality tracks: {len(unique_tracks)}")

            # Separate tracks by language (heuristic: check if track/artist contains Hindi indicators)
            english_pool = []
            hindi_pool = []

            for track in unique_tracks:
                # Simple heuristic: check artist/album names for Hindi/Indian indicators
                track_text = f"{track['name']} {' '.join([a['name'] for a in track['artists']])} {track['album']['name']}".lower()

                # Check for Indian/Hindi indicators
                is_indian = any(indicator in track_text for indicator in [
                    'bollywood', 'hindi', 'punjabi', 'desi', 'arijit', 'badshah',
                    'atif', 'shreya', 'neha', 'armaan', 'pritam', 'ar rahman',
                    'mohit chauhan', 'sunidhi', 'sonu nigam', 'kumar sanu'
                ])

                if is_indian:
                    hindi_pool.append(track)
                else:
                    english_pool.append(track)

            print(f"[SpotifyService] Pools - English: {len(english_pool)}, Hindi: {len(hindi_pool)}")

            # Select songs maintaining the desired mix
            final_songs = []
            artists_used = {}

            # First, try to get the desired mix
            for pool, target_count, label in [(english_pool, english_count, 'English'), (hindi_pool, hindi_count, 'Hindi')]:
                selected = 0
                for track in pool:
                    if selected >= target_count:
                        break

                    artist_key = track['_artist_key']

                    # Limit to max 2 songs from the same artist
                    if artists_used.get(artist_key, 0) >= 2:
                        continue

                    # Skip if already added
                    if any(s['id'] == track['id'] for s in final_songs):
                        continue

                    artists_used[artist_key] = artists_used.get(artist_key, 0) + 1

                    final_songs.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'preview_url': track.get('preview_url'),
                        'spotify_url': track['external_urls']['spotify'],
                        'album_cover': track['album']['images'][0]['url'] if track['album']['images'] else None,
                        'duration_ms': track['duration_ms'],
                        'popularity': track.get('popularity', 0),
                        'language_type': label
                    })
                    selected += 1

                print(f"[SpotifyService] Selected {selected} {label} songs")

            # If we don't have 5 songs, fill from any pool
            if len(final_songs) < 5:
                print("[SpotifyService] Filling remaining slots with best available")
                for track in unique_tracks:
                    if len(final_songs) >= 5:
                        break

                    # Skip if already added
                    if any(s['id'] == track['id'] for s in final_songs):
                        continue

                    final_songs.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'preview_url': track.get('preview_url'),
                        'spotify_url': track['external_urls']['spotify'],
                        'album_cover': track['album']['images'][0]['url'] if track['album']['images'] else None,
                        'duration_ms': track['duration_ms'],
                        'popularity': track.get('popularity', 0),
                        'language_type': 'Mixed'
                    })

            print(f"[SpotifyService] Returning {len(final_songs)} diverse songs with language mix")
            return final_songs

        except Exception as e:
            print(f"Error getting song recommendations: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_mood_playlists(self, mood, genres, themes):
        """Get curated playlist IDs based on mood"""
        mood_lower = mood.lower()

        # Map moods to Spotify's curated playlists
        playlist_map = {
            'calm': ['37i9dQZF1DWZd79rJ6a7lp', '37i9dQZF1DX4sWSpwq3LiO', '37i9dQZF1DX3Ogo9pFvBkY'],  # Peaceful Piano, Chill Lofi, Calming Acoustic
            'peaceful': ['37i9dQZF1DWZd79rJ6a7lp', '37i9dQZF1DX4sWSpwq3LiO'],
            'relaxed': ['37i9dQZF1DWZd79rJ6a7lp', '37i9dQZF1DX0XUfTFmNBRM'],
            'happy': ['37i9dQZF1DXdPec7aLTmlC', '37i9dQZF1DX0UrRvztWcAU', '37i9dQZF1DX3rxVfibe1L0'],  # Happy Hits, Feel Good, Mood Booster
            'energetic': ['37i9dQZF1DX76Wlfdnj7AP', '37i9dQZF1DX0vHZ8elq0UK', '37i9dQZF1DX32NsLKyzScr'],  # Beast Mode, Energy, Power Hour
            'melancholic': ['37i9dQZF1DX7qK8ma5wgG1', '37i9dQZF1DWX83CujKHHOn', '37i9dQZF1DX3YSRoSdA634'],  # Sad Indie, Sad Songs, Life Sucks
            'romantic': ['37i9dQZF1DX50KsbC0ZOeI', '37i9dQZF1DX1n9whBbREo9'],  # Love Songs, Romance
        }

        # Try to find matching mood playlist
        for key, playlists in playlist_map.items():
            if key in mood_lower:
                return playlists

        # Fallback: search for playlists with mood term
        try:
            results = self.sp.search(q=f"{mood} {genres[0] if genres else ''}", type='playlist', limit=3)
            if results['playlists']['items']:
                return [p['id'] for p in results['playlists']['items'][:3]]
        except:
            pass

        return ['37i9dQZF1DXcBWIGoYBM5M']  # Today's Top Hits as fallback

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

    def _get_smart_search_terms(self, mood, genres, themes, keywords, language='english'):
        """Generate smart search terms avoiding cliches"""
        terms = []

        # Mood-based terms (more specific and current) - English/International
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

        mood_lower = mood.lower()
        for key, search_terms in mood_terms.items():
            if key in mood_lower:
                terms.extend(search_terms)
                break

        # Add genre if not too generic
        if genres:
            for g in genres[:2]:
                if g.lower() not in ['pop', 'rock', 'bollywood', 'hindi']:  # Skip overly generic and Indian
                    terms.append(g)

        # Add themes
        if themes:
            for theme in themes[:2]:
                if theme.lower() not in ['general', 'lifestyle', 'moments']:
                    terms.append(f"{theme} {genres[0] if genres else 'indie'}")

        # Add keywords from image analysis to make search more specific
        if keywords:
            for keyword in keywords[:3]:
                if keyword.lower() not in ['vibes', 'chill', 'lifestyle', 'moments', 'mood', 'general']:
                    terms.append(f"{keyword} {mood}")

        # Fallback
        if not terms:
            terms = [f"indie {mood}", "alternative", "new music"]

        return terms

    def _get_indian_search_terms(self, mood, genres, themes, keywords):
        """Generate search terms for Hindi/Indian music"""
        terms = []

        # Mood-based terms for Indian music
        mood_terms = {
            'calm': ['peaceful hindi', 'sufi', 'acoustic hindi', 'indie hindi chill'],
            'peaceful': ['sufi calm', 'meditation hindi', 'peaceful bollywood'],
            'relaxed': ['chill hindi', 'indie hindi', 'lo-fi hindi'],
            'happy': ['upbeat bollywood', 'happy hindi', 'punjabi party'],
            'joyful': ['celebration hindi', 'happy punjabi', 'desi pop'],
            'energetic': ['punjabi bhangra', 'high energy hindi', 'party bollywood'],
            'confident': ['desi hip-hop', 'rap hindi', 'badshah'],
            'melancholic': ['sad hindi songs', 'emotional bollywood', 'breakup hindi'],
            'nostalgic': ['90s bollywood', 'retro hindi', 'old hindi songs'],
            'romantic': ['romantic hindi', 'love songs bollywood', 'sufi romantic'],
            'adventurous': ['road trip hindi', 'travel hindi', 'upbeat bollywood']
        }

        mood_lower = mood.lower()
        for key, search_terms in mood_terms.items():
            if key in mood_lower:
                terms.extend(search_terms)
                break

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

        # Add specific Indian artists for better results
        terms.append('arijit singh')  # Popular across moods
        if 'energetic' in mood_lower or 'happy' in mood_lower:
            terms.append('badshah diljit')
        elif 'romantic' in mood_lower:
            terms.append('atif aslam')
        elif 'calm' in mood_lower or 'peaceful' in mood_lower:
            terms.append('mohit chauhan')

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
