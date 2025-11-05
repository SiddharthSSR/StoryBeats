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

            # Adjust tempo based on mood to ensure it makes sense
            tempo = self._adjust_tempo_for_mood(tempo, mood, energy)

            # Dynamically determine language mix based on image analysis
            english_count, hindi_count = self._determine_language_mix(image_analysis)

            # Track sources for weighted scoring
            # Strategy 1 (Playlists) = 0.8x weight - curated but less personalized
            # Strategy 2 (Recommendations) = 1.0x weight - best match for audio features
            # Strategy 3 (Search) = 0.6x weight - keyword-based, less precise
            all_tracks = []

            # Strategy 1: Get contextual playlists for the mood/genre/themes/keywords
            mood_playlists = self._get_mood_playlists(mood, genres, themes, keywords)
            playlist_tracks = []

            for playlist_id in mood_playlists[:4]:  # Use top 4 playlists (curated + contextual)
                try:
                    playlist = self.sp.playlist_tracks(playlist_id, limit=20, offset=offset)
                    if playlist and 'items' in playlist:
                        for item in playlist['items']:
                            if item['track'] and item['track']['id']:
                                track = item['track']
                                track['_source'] = 'playlist'
                                track['_source_weight'] = 0.8
                                playlist_tracks.append(track)
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

                        # Use ranges instead of exact targets for more flexible matching
                        # Range is ±0.2 around target (min 0.0, max 1.0)
                        energy_min = max(0.0, energy - 0.2)
                        energy_max = min(1.0, energy + 0.2)
                        valence_min = max(0.0, valence - 0.2)
                        valence_max = min(1.0, valence + 0.2)
                        danceability_min = max(0.0, danceability - 0.2)
                        danceability_max = min(1.0, danceability + 0.2)
                        acousticness_min = max(0.0, acousticness - 0.2)
                        acousticness_max = min(1.0, acousticness + 0.2)
                        instrumentalness_min = max(0.0, instrumentalness - 0.15)
                        instrumentalness_max = min(1.0, instrumentalness + 0.15)

                        # Tempo range is ±15 BPM
                        tempo_min = max(40, tempo - 15)
                        tempo_max = min(200, tempo + 15)

                        print(f"[SpotifyService] Audio ranges - energy:[{energy_min:.2f}-{energy_max:.2f}], valence:[{valence_min:.2f}-{valence_max:.2f}], tempo:[{tempo_min}-{tempo_max}]")

                        rec_results = self.sp.recommendations(
                            seed_tracks=seed_ids,
                            limit=20,
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
                            print(f"[SpotifyService] Got {len(rec_results['tracks'])} from recommendations")
                            for track in rec_results['tracks']:
                                track['_source'] = 'recommendations'
                                track['_source_weight'] = 1.0  # Highest weight - best audio feature match
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
                        for track in results['tracks']['items']:
                            track['_source'] = 'search'
                            track['_source_weight'] = 0.6  # Lower weight - keyword match only
                        english_tracks.extend(results['tracks']['items'])
                except Exception as e:
                    print(f"Search error for term '{term}': {e}")

            # Get Hindi/Indian tracks - Multi-strategy approach (same as English)
            # Strategy 1: Hindi playlists (0.8x weight)
            hindi_playlists = self._get_hindi_mood_playlists(mood, genres, themes, keywords)
            playlist_hindi_tracks = []

            for playlist_id in hindi_playlists[:4]:  # Use top 4 playlists
                try:
                    playlist = self.sp.playlist_tracks(playlist_id, limit=20, offset=offset)
                    if playlist and 'items' in playlist:
                        for item in playlist['items']:
                            if item['track'] and item['track']['id']:
                                track = item['track']
                                track['_source'] = 'hindi_playlist'
                                track['_source_weight'] = 0.8
                                playlist_hindi_tracks.append(track)
                        print(f"[SpotifyService] Got {len(playlist['items'])} tracks from Hindi playlist")
                except Exception as e:
                    print(f"Hindi playlist fetch error: {e}")
                    continue

            hindi_tracks.extend(playlist_hindi_tracks)

            # Strategy 2: Hindi Recommendations API (1.0x weight - highest)
            hindi_recommendations = self._get_hindi_recommendations(
                mood, genres, energy, valence, danceability, acousticness,
                tempo, instrumentalness, offset,
                energy_min, energy_max, valence_min, valence_max,
                danceability_min, danceability_max, acousticness_min, acousticness_max,
                tempo_min, tempo_max, instrumentalness_min, instrumentalness_max
            )

            for track in hindi_recommendations:
                track['_source'] = 'hindi_recommendations'
                track['_source_weight'] = 1.0  # Highest weight

            hindi_tracks.extend(hindi_recommendations)
            print(f"[SpotifyService] Added {len(hindi_recommendations)} Hindi tracks from Recommendations API")

            # Strategy 3: Hindi Search API (0.6x weight)
            hindi_search_terms = self._get_smart_search_terms(mood, genres, themes, keywords, language='hindi')

            for term in hindi_search_terms[:3]:
                try:
                    query = f"{term}"
                    results = self.sp.search(q=query, type='track', limit=15, offset=search_offset, market='IN')
                    if results['tracks']['items']:
                        print(f"[SpotifyService] Found {len(results['tracks']['items'])} Hindi tracks for '{query}'")
                        for track in results['tracks']['items']:
                            track['_source'] = 'hindi_search'
                            track['_source_weight'] = 0.6  # Lower weight
                        hindi_tracks.extend(results['tracks']['items'])
                except Exception as e:
                    print(f"Hindi search error for term '{term}': {e}")

            print(f"[SpotifyService] Total Hindi tracks from all strategies: {len(hindi_tracks)}")

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

                # Apply weighted scoring based on source
                source_weight = track.get('_source_weight', 0.5)  # Default if no source
                base_score = popularity * source_weight

                # Calculate semantic similarity boost
                semantic_boost = self._calculate_semantic_similarity(track, keywords, themes, mood)

                # Apply diversity penalty
                final_score = base_score + semantic_boost - diversity_penalty

                track['_score'] = final_score
                track['_base_score'] = base_score
                track['_semantic_boost'] = semantic_boost
                track['_artist_key'] = artist_key
                unique_tracks.append(track)

            # Sort by final score (source_weight * popularity + semantic_boost - diversity penalty)
            unique_tracks.sort(key=lambda x: x['_score'], reverse=True)

            # Log source distribution and semantic matches
            source_counts = {}
            tracks_with_semantic_boost = 0
            for track in unique_tracks:
                source = track.get('_source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
                if track.get('_semantic_boost', 0) > 0:
                    tracks_with_semantic_boost += 1

            print(f"[SpotifyService] Total unique quality tracks: {len(unique_tracks)}")
            print(f"[SpotifyService] Source distribution: {source_counts}")
            print(f"[SpotifyService] Tracks with semantic matches: {tracks_with_semantic_boost}/{len(unique_tracks)}")

            # Separate tracks by language (heuristic: check if track/artist contains Hindi indicators)
            english_pool = []
            hindi_pool = []

            for track in unique_tracks:
                # Simple heuristic: check artist/album names for Hindi/Indian indicators
                track_text = f"{track['name']} {' '.join([a['name'] for a in track['artists']])} {track['album']['name']}".lower()

                # Check for Indian/Hindi indicators
                is_indian = any(indicator in track_text for indicator in [
                    'bollywood', 'hindi', 'punjabi', 'desi'
                ])

                if is_indian:
                    hindi_pool.append(track)
                else:
                    english_pool.append(track)

            # Create popularity buckets for distribution
            # Target: 1 hidden gem (25-40), 3 moderate (40-70), 1 popular (70-85)
            hidden_gems = [t for t in unique_tracks if 25 <= t.get('popularity', 0) <= 40]
            moderate_hits = [t for t in unique_tracks if 40 < t.get('popularity', 0) <= 70]
            popular_tracks = [t for t in unique_tracks if 70 < t.get('popularity', 0) <= 95]

            print(f"[SpotifyService] Popularity distribution - Hidden gems: {len(hidden_gems)}, Moderate: {len(moderate_hits)}, Popular: {len(popular_tracks)}")

            # Separate each bucket by language
            english_pool = {'hidden': [], 'moderate': [], 'popular': []}
            hindi_pool = {'hidden': [], 'moderate': [], 'popular': []}

            for bucket_name, bucket_tracks in [('hidden', hidden_gems), ('moderate', moderate_hits), ('popular', popular_tracks)]:
                for track in bucket_tracks:
                    # Check if track is from trending Hindi playlists (most reliable indicator)
                    is_from_hindi_playlist = track.get('_source') == 'trending_hindi_playlist'

                    # Fallback: check artist/album names for Hindi/Indian indicators
                    track_text = f"{track['name']} {' '.join([a['name'] for a in track['artists']])} {track['album']['name']}".lower()
                    has_hindi_keywords = any(indicator in track_text for indicator in [
                        'bollywood', 'hindi', 'punjabi', 'desi'
                    ])

                    # Mark as Hindi if from Hindi playlist OR has Hindi keywords
                    if is_from_hindi_playlist or has_hindi_keywords:
                        hindi_pool[bucket_name].append(track)
                    else:
                        english_pool[bucket_name].append(track)

            print(f"[SpotifyService] English pools - Hidden: {len(english_pool['hidden'])}, Moderate: {len(english_pool['moderate'])}, Popular: {len(english_pool['popular'])}")
            print(f"[SpotifyService] Hindi pools - Hidden: {len(hindi_pool['hidden'])}, Moderate: {len(hindi_pool['moderate'])}, Popular: {len(hindi_pool['popular'])}")

            # Select songs with popularity distribution
            final_songs = []
            artists_used = {}

            # Strategy: For each language quota, select from different popularity buckets
            # Try to get: 20% hidden, 60% moderate, 20% popular (roughly)
            for pool, target_count, label in [(english_pool, english_count, 'English'), (hindi_pool, hindi_count, 'Hindi')]:
                selected = 0

                # Calculate target distribution for this language
                # If target_count=3: try 1 moderate, 1 moderate, 1 popular (prioritize moderate)
                # If target_count=2: try 1 moderate, 1 popular
                # If target_count=4: try 1 hidden, 2 moderate, 1 popular
                # If target_count=5: try 1 hidden, 3 moderate, 1 popular

                if target_count >= 4:
                    bucket_targets = [('hidden', 1), ('moderate', target_count - 2), ('popular', 1)]
                elif target_count == 3:
                    bucket_targets = [('moderate', 2), ('popular', 1)]
                elif target_count == 2:
                    bucket_targets = [('moderate', 1), ('popular', 1)]
                else:  # target_count == 1
                    bucket_targets = [('moderate', 1)]

                # Select from each bucket
                for bucket_name, bucket_target in bucket_targets:
                    bucket_selected = 0
                    for track in pool[bucket_name]:
                        if bucket_selected >= bucket_target or selected >= target_count:
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
                            'language_type': label,
                            'popularity_bucket': bucket_name  # Track which bucket this came from
                        })
                        selected += 1
                        bucket_selected += 1

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

            # Log final popularity distribution
            bucket_counts = {}
            for song in final_songs:
                bucket = song.get('popularity_bucket', 'unknown')
                bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

            print(f"[SpotifyService] Final popularity distribution: {bucket_counts}")
            print(f"[SpotifyService] Returning {len(final_songs)} diverse songs with language mix")
            return final_songs

        except Exception as e:
            print(f"Error getting song recommendations: {e}")
            import traceback
            traceback.print_exc()
            return []

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
                'arijit singh'
            ]

            playlist_ids = []
            for term in search_terms[:3]:  # Use top 3 search terms
                try:
                    results = self.sp.search(q=term, type='playlist', limit=2, market='IN')
                    if results and 'playlists' in results and results['playlists']['items']:
                        for playlist in results['playlists']['items']:
                            if playlist and playlist.get('id'):
                                playlist_ids.append(playlist['id'])
                                print(f"[SpotifyService] Found Hindi playlist: {playlist.get('name', 'Unknown')}")
                except Exception as e:
                    print(f"[SpotifyService] Error searching for Hindi playlist with '{term}': {e}")
                    continue

            if not playlist_ids:
                print("[SpotifyService] No Hindi playlists found")
                return []

            # Fetch tracks from found playlists
            for playlist_id in playlist_ids[:3]:  # Use top 3 playlists
                try:
                    playlist = self.sp.playlist_tracks(playlist_id, limit=30, offset=offset % 50)
                    if playlist and 'items' in playlist:
                        for item in playlist['items']:
                            if item['track'] and item['track']['id']:
                                hindi_tracks.append(item['track'])
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

            print(f"[SpotifyService] Matched {len(matched_tracks)} Hindi tracks by vibe (threshold: 0.6)")

            return matched_tracks

        except Exception as e:
            print(f"[SpotifyService] Error getting audio features for Hindi tracks: {e}")
            # Fallback: return tracks without filtering
            return hindi_tracks[:20]

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
                f"arijit singh {mood}",
                "pritam bollywood",
                "ar rahman",
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
            'peaceful': ['sufi', 'meditation hindi', 'peaceful bollywood', 'rahat fateh ali'],
            'relaxed': ['chill hindi', 'indie hindi', 'lo-fi hindi', 'mellow bollywood'],
            'happy': ['feel good bollywood', 'upbeat hindi', 'happy indie hindi'],  # Removed party terms
            'joyful': ['romantic hindi', 'melodious bollywood', 'arijit singh romantic'],  # More melodious, less party
            'dreamy': ['sufi romantic', 'ethereal hindi', 'romantic ballad hindi', 'mohit chauhan'],  # New: for dreamy moods
            'energetic': ['punjabi bhangra', 'high energy hindi', 'gym workout hindi'],
            'confident': ['desi hip-hop', 'rap hindi', 'urban desi', 'hip-hop hindi'],  # More hip-hop focused
            'melancholic': ['sad hindi songs', 'emotional bollywood', 'heartbreak hindi', 'arijit singh sad'],
            'nostalgic': ['90s bollywood', 'retro hindi', 'classic hindi songs', 'old is gold hindi'],
            'romantic': ['romantic hindi', 'love songs bollywood', 'sufi romantic', 'atif aslam'],
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
            terms.append('arijit singh romantic')
            terms.append('atif aslam')
        elif any(x in mood_lower for x in ['calm', 'peaceful', 'serene', 'reflect']):
            terms.append('sufi playlist')
            terms.append('mohit chauhan peaceful')
        elif any(x in mood_lower for x in ['sad', 'melanchol', 'emotional']):
            terms.append('arijit singh sad')
            terms.append('emotional ballad hindi')
        elif any(x in mood_lower for x in ['energetic', 'party', 'hype']):
            terms.append('badshah diljit party')
            terms.append('punjabi workout')
        elif any(x in mood_lower for x in ['confident', 'swagger', 'boss']):
            terms.append('desi rap')
            terms.append('raftaar hip-hop')
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
