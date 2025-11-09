#!/usr/bin/env python3
"""
Quick test to verify infinite loop fix in _generate_all_songs_with_diversity
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.spotify_service import SpotifyService

def test_no_infinite_loop():
    """Test that _generate_all_songs_with_diversity doesn't hang"""
    print("\n" + "="*80)
    print("🧪 Testing Infinite Loop Fix")
    print("="*80)

    service = SpotifyService()

    # Create minimal mock tracks (what the method expects)
    mock_tracks = []
    for i in range(3):
        mock_tracks.append({
            'id': f'eng_track_{i}',
            'name': f'English Track {i}',
            'artists': [{'name': 'Test Artist'}],
            'album': {
                'name': 'Test Album',
                'images': [{'url': 'http://test.com/image.jpg'}]
            },
            'duration_ms': 200000,
            'popularity': 60,
            'preview_url': 'http://test.com/preview.mp3',
            'external_urls': {'spotify': 'http://spotify.com/track'},
            '_language': 'english',
            '_artist_name': f'Artist{i % 2}',  # 2 different artists
            '_vibe_score': 0.85,
            '_recency_bonus': 0.9,
            '_final_score': 0.87
        })

    for i in range(2):
        mock_tracks.append({
            'id': f'hin_track_{i}',
            'name': f'Hindi Track {i}',
            'artists': [{'name': 'Test Artist'}],
            'album': {
                'name': 'Test Album',
                'images': [{'url': 'http://test.com/image.jpg'}]
            },
            'duration_ms': 200000,
            'popularity': 60,
            'preview_url': 'http://test.com/preview.mp3',
            'external_urls': {'spotify': 'http://spotify.com/track'},
            '_language': 'hindi',
            '_artist_name': f'HindiArtist{i}',
            '_vibe_score': 0.85,
            '_recency_bonus': 0.9,
            '_final_score': 0.87
        })

    print(f"\n📊 Test scenario:")
    print(f"   - Mock tracks: 3 English, 2 Hindi")
    print(f"   - Target ratio: 3 English, 2 Hindi")
    print(f"   - Max songs requested: 30")

    print(f"\n⏱️  Running _generate_all_songs_with_diversity...")

    # This should NOT hang!
    import time
    start = time.time()

    try:
        result = service._generate_all_songs_with_diversity(
            scored_tracks=mock_tracks,
            english_count=3,
            hindi_count=2,
            max_songs=30
        )
        elapsed = time.time() - start

        print(f"✅ Completed in {elapsed:.3f}s (no infinite loop!)")
        print(f"   - Returned: {len(result)} songs")
        print(f"   - English: {sum(1 for s in result if s['language_type'] == 'English')}")
        print(f"   - Hindi: {sum(1 for s in result if s['language_type'] == 'Hindi')}")

        if elapsed < 1.0:
            print(f"\n🎉 SUCCESS: No infinite loop detected!")
            return True
        else:
            print(f"\n⚠️  WARNING: Took {elapsed:.2f}s, might be slow")
            return True

    except Exception as e:
        elapsed = time.time() - start
        print(f"\n❌ FAILED after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_no_infinite_loop()
    sys.exit(0 if success else 1)
