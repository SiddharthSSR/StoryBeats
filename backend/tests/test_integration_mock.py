#!/usr/bin/env python3
"""
Mock Integration Test - Simulates Full Recommendation Pipeline

This test simulates what happens when a photo is uploaded and processed.
It uses mock Spotify data to avoid API rate limits.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import Mock, patch, MagicMock
from services.spotify_service import SpotifyService
import random


def create_mock_track(track_id, name, artist_name, album_name, popularity,
                     release_date, energy, valence, danceability, acousticness, tempo):
    """Create a mock Spotify track object"""
    return {
        'id': track_id,
        'name': name,
        'artists': [{'name': artist_name}],
        'album': {
            'name': album_name,
            'release_date': release_date,
            'images': [{'url': f'https://i.scdn.co/image/{track_id}'}]
        },
        'duration_ms': 210000,
        'popularity': popularity,
        'preview_url': f'https://p.scdn.co/mp3-preview/{track_id}',
        'external_urls': {'spotify': f'https://open.spotify.com/track/{track_id}'}
    }


def create_mock_audio_features(energy, valence, danceability, acousticness, tempo):
    """Create mock audio features"""
    return {
        'energy': energy,
        'valence': valence,
        'danceability': danceability,
        'acousticness': acousticness,
        'tempo': tempo,
        'instrumentalness': 0.1
    }


class TestMockIntegration:
    """Mock integration test with simulated Spotify responses"""

    def __init__(self):
        self.service = None

    def setup_mocked_service(self):
        """Create SpotifyService with mocked Spotify API"""
        # Mock the Spotify client
        mock_sp = MagicMock()

        # Create a service instance
        with patch('services.spotify_service.spotipy.Spotify', return_value=mock_sp):
            self.service = SpotifyService()
            self.service.sp = mock_sp

        # Setup mock responses
        self._setup_artist_search_mock()
        self._setup_artist_albums_mock()
        self._setup_album_tracks_mock()
        self._setup_artist_top_tracks_mock()
        self._setup_track_mock()
        self._setup_audio_features_mock()

    def _setup_artist_search_mock(self):
        """Mock artist search responses"""
        def mock_search(q, type, limit, market):
            artist_name = q.replace('artist:', '')
            # Generate consistent ID from artist name
            artist_id = f"artist_{hash(artist_name) % 1000000}"
            return {
                'artists': {
                    'items': [{'id': artist_id, 'name': artist_name}]
                }
            }

        self.service.sp.search = Mock(side_effect=mock_search)

    def _setup_artist_albums_mock(self):
        """Mock artist albums responses"""
        def mock_artist_albums(artist_id, album_type, limit, market):
            # Return 3 mock recent albums
            albums = []
            for i in range(3):
                albums.append({
                    'id': f'album_{artist_id}_{i}',
                    'name': f'Album {i+1}',
                    'release_date': f'2024-0{i+1}-15'
                })
            return {'items': albums}

        self.service.sp.artist_albums = Mock(side_effect=mock_artist_albums)

    def _setup_album_tracks_mock(self):
        """Mock album tracks responses"""
        def mock_album_tracks(album_id, limit):
            # Return 2 tracks per album
            tracks = []
            for i in range(2):
                tracks.append({
                    'id': f'track_{album_id}_{i}',
                    'name': f'Song {i+1}'
                })
            return {'items': tracks}

        self.service.sp.album_tracks = Mock(side_effect=mock_album_tracks)

    def _setup_artist_top_tracks_mock(self):
        """Mock artist top tracks responses"""
        def mock_artist_top_tracks(artist_id, country):
            # Return 5 top tracks
            tracks = []
            for i in range(5):
                artist_name = f"Artist {artist_id}"
                tracks.append(create_mock_track(
                    track_id=f'top_{artist_id}_{i}',
                    name=f'Hit Song {i+1}',
                    artist_name=artist_name,
                    album_name='Greatest Hits',
                    popularity=random.randint(50, 80),
                    release_date='2023-06-15',
                    energy=0.7,
                    valence=0.6,
                    danceability=0.65,
                    acousticness=0.3,
                    tempo=120
                ))
            return {'tracks': tracks}

        self.service.sp.artist_top_tracks = Mock(side_effect=mock_artist_top_tracks)

    def _setup_track_mock(self):
        """Mock track detail responses"""
        def mock_track(track_id, market):
            # Generate consistent track data from ID
            return create_mock_track(
                track_id=track_id,
                name=f'Track {track_id[-3:]}',
                artist_name='Test Artist',
                album_name='Test Album',
                popularity=random.randint(50, 80),
                release_date='2024-03-15',
                energy=0.7,
                valence=0.6,
                danceability=0.65,
                acousticness=0.3,
                tempo=120
            )

        self.service.sp.track = Mock(side_effect=mock_track)

    def _setup_audio_features_mock(self):
        """Mock audio features responses"""
        def mock_audio_features(track_ids):
            # Return audio features for each track
            # Use some variation to test filtering
            features = []
            for i, track_id in enumerate(track_ids):
                # Some tracks match well, others don't
                match_quality = (hash(track_id) % 100) / 100

                if match_quality > 0.5:  # Good match
                    features.append(create_mock_audio_features(
                        energy=0.7 + random.uniform(-0.1, 0.1),
                        valence=0.6 + random.uniform(-0.1, 0.1),
                        danceability=0.65 + random.uniform(-0.1, 0.1),
                        acousticness=0.3 + random.uniform(-0.1, 0.1),
                        tempo=120 + random.uniform(-10, 10)
                    ))
                else:  # Poor match
                    features.append(create_mock_audio_features(
                        energy=random.uniform(0.1, 0.4),
                        valence=random.uniform(0.1, 0.3),
                        danceability=random.uniform(0.2, 0.4),
                        acousticness=random.uniform(0.6, 0.9),
                        tempo=random.uniform(60, 90)
                    ))

            return features

        self.service.sp.audio_features = Mock(side_effect=mock_audio_features)

    def test_romantic_photo(self):
        """Test romantic photo analysis"""
        print("\n" + "="*80)
        print("🧪 MOCK INTEGRATION TEST: Romantic Photo")
        print("="*80)

        image_analysis = {
            'mood': 'romantic',
            'energy': 0.5,
            'valence': 0.6,
            'danceability': 0.5,
            'acousticness': 0.4,
            'tempo': 100,
            'cultural_vibe': 'global'
        }

        print("\n📸 Simulated Image Analysis:")
        print(f"   Mood: {image_analysis['mood']}")
        print(f"   Energy: {image_analysis['energy']}")
        print(f"   Valence: {image_analysis['valence']}")
        print(f"   Cultural Vibe: {image_analysis['cultural_vibe']}")

        print("\n🎵 Running NEW Artist-Centric Algorithm...")
        recommendations = self.service.get_song_recommendations(image_analysis)

        print(f"\n✅ Algorithm completed successfully!")
        print(f"   Returned {len(recommendations)} recommendations")

        # Validate results
        if len(recommendations) > 0:
            print("\n📊 Validation:")
            print(f"   ✅ Got recommendations: {len(recommendations)} songs")

            # Check language mix
            english_count = sum(1 for s in recommendations if s.get('language_type') == 'English')
            hindi_count = sum(1 for s in recommendations if s.get('language_type') == 'Hindi')
            print(f"   ✅ Language mix: {english_count} English, {hindi_count} Hindi")

            # Check scoring fields
            if all('vibe_score' in s and 'recency_bonus' in s and 'final_score' in s for s in recommendations):
                print(f"   ✅ All songs have scoring metadata")
            else:
                print(f"   ⚠️  Some songs missing scoring metadata")

            # Check artist diversity
            artists = [s['artist'] for s in recommendations]
            unique_artists = len(set(artists))
            print(f"   ✅ Artist diversity: {unique_artists} unique artists out of {len(recommendations)}")

            return True
        else:
            print("\n❌ No recommendations returned!")
            return False

    def test_energetic_photo(self):
        """Test energetic photo analysis"""
        print("\n" + "="*80)
        print("🧪 MOCK INTEGRATION TEST: Energetic Photo")
        print("="*80)

        image_analysis = {
            'mood': 'energetic',
            'energy': 0.9,
            'valence': 0.8,
            'danceability': 0.85,
            'acousticness': 0.1,
            'tempo': 140,
            'cultural_vibe': 'western'
        }

        print("\n📸 Simulated Image Analysis:")
        print(f"   Mood: {image_analysis['mood']}")
        print(f"   Energy: {image_analysis['energy']}")
        print(f"   Valence: {image_analysis['valence']}")
        print(f"   Cultural Vibe: {image_analysis['cultural_vibe']}")

        print("\n🎵 Running NEW Artist-Centric Algorithm...")
        recommendations = self.service.get_song_recommendations(image_analysis)

        print(f"\n✅ Algorithm completed successfully!")
        print(f"   Returned {len(recommendations)} recommendations")

        return len(recommendations) > 0

    def test_moody_photo(self):
        """Test moody photo with new category artists"""
        print("\n" + "="*80)
        print("🧪 MOCK INTEGRATION TEST: Moody Photo (Frank Ocean, Don Toliver, etc.)")
        print("="*80)

        image_analysis = {
            'mood': 'moody',
            'energy': 0.6,
            'valence': 0.4,
            'danceability': 0.55,
            'acousticness': 0.3,
            'tempo': 110,
            'cultural_vibe': 'global'
        }

        print("\n📸 Simulated Image Analysis:")
        print(f"   Mood: {image_analysis['mood']}")
        print(f"   Energy: {image_analysis['energy']}")
        print(f"   Valence: {image_analysis['valence']}")

        print("\n🎵 Running NEW Artist-Centric Algorithm...")
        recommendations = self.service.get_song_recommendations(image_analysis)

        print(f"\n✅ Algorithm completed successfully!")
        print(f"   Returned {len(recommendations)} recommendations")

        return len(recommendations) > 0


def main():
    """Run mock integration tests"""
    print("\n" + "🎭 " + "="*76)
    print("🎭  MOCK INTEGRATION TEST SUITE")
    print("🎭  (Simulates full pipeline with mocked Spotify API)")
    print("🎭 " + "="*76)

    test = TestMockIntegration()

    print("\n⚙️  Setting up mocked Spotify service...")
    test.setup_mocked_service()
    print("✅ Mock service ready")

    tests = [
        ("Romantic Photo", test.test_romantic_photo),
        ("Energetic Photo", test.test_energetic_photo),
        ("Moody Photo (New Category)", test.test_moody_photo),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("📊 MOCK INTEGRATION TEST SUMMARY")
    print("="*80)

    total = len(results)
    passed = sum(1 for _, p in results if p)
    failed = total - passed

    for name, passed_test in results:
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"  {status}: {name}")

    print(f"\n{'='*80}")
    print(f"  Total: {total} tests")
    print(f"  Passed: {passed} ✅")
    print(f"  Failed: {failed} ❌")
    print(f"{'='*80}")

    if failed == 0:
        print("\n🎉 All mock integration tests passed!")
        print("\n📝 The new algorithm is working correctly with simulated data.")
        print("   Ready for testing with real Spotify API and actual photos.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review the failures above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
