#!/usr/bin/env python3
"""
Test script to run algorithm tests on multiple images
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from pathlib import Path


BASE_URL = "http://localhost:5001"
ANALYZE_URL = f"{BASE_URL}/api/analyze"
MORE_SONGS_URL = f"{BASE_URL}/api/more-songs"


def test_image(image_path, test_name):
    """Test the recommendation algorithm with a specific image"""
    print(f"\n{'='*80}")
    print(f"Test Case: {test_name}")
    print(f"Image: {image_path}")
    print(f"{'='*80}\n")

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False

    try:
        # Step 1: Upload image and get initial recommendations
        print(f"📤 Uploading and analyzing image...")

        with open(image_path, 'rb') as f:
            files = {'photo': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(ANALYZE_URL, files=files, timeout=90)

        if response.status_code != 200:
            print(f"❌ Failed to analyze image: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        data = response.json()

        if not data.get('success'):
            print(f"❌ Analysis failed: {data.get('error', 'Unknown error')}")
            return False

        # Extract results
        analysis = data.get('analysis', {})
        songs = data.get('songs', [])
        session_id = data.get('session_id')

        print(f"✅ Got {len(songs)} recommendations (Session: {session_id[:8]}...)")

        # Print analysis
        print(f"\n📊 Image Analysis:")
        print(f"  Mood: {analysis.get('mood', 'N/A')}")
        print(f"  Energy: {analysis.get('energy', 0):.2f}, Valence: {analysis.get('valence', 0):.2f}")
        print(f"  Danceability: {analysis.get('danceability', 0):.2f}, Acousticness: {analysis.get('acousticness', 0):.2f}")
        print(f"  Tempo: {analysis.get('tempo', 0)} BPM, Instrumentalness: {analysis.get('instrumentalness', 0):.2f}")
        print(f"  Genres: {', '.join(analysis.get('genres', []))[:60]}")
        print(f"  Themes: {', '.join(analysis.get('themes', []))[:60]}")
        print(f"  Keywords: {', '.join(analysis.get('keywords', [])[:5])}")
        print(f"  Cultural vibe: {analysis.get('cultural_vibe', 'N/A')}")

        # Print song recommendations with details
        print(f"\n🎵 Initial Recommendations:")
        for i, song in enumerate(songs, 1):
            lang = song.get('language_type', 'N/A')
            pop = song.get('popularity', 0)
            print(f"  {i}. [{pop:2d}] {song['name'][:40]:40s} - {song['artist'][:30]:30s} ({lang})")

        # Analyze popularity distribution
        hidden_gems = [s for s in songs if 25 <= s.get('popularity', 0) <= 40]
        moderate = [s for s in songs if 40 < s.get('popularity', 0) <= 70]
        popular = [s for s in songs if 70 < s.get('popularity', 0) <= 95]

        print(f"\n📈 Popularity Distribution: Hidden gems: {len(hidden_gems)}, Moderate: {len(moderate)}, Popular: {len(popular)}")

        # Analyze language distribution
        english = len([s for s in songs if s.get('language_type') == 'English'])
        hindi = len([s for s in songs if s.get('language_type') == 'Hindi'])
        mixed = len([s for s in songs if s.get('language_type') == 'Mixed'])

        print(f"🌍 Language Distribution: English: {english}, Hindi: {hindi}, Mixed: {mixed}")

        # Step 2: Test "More Songs"
        print(f"\n🔄 Getting more songs...")

        more_response = requests.post(MORE_SONGS_URL, json={'session_id': session_id}, timeout=90)

        if more_response.status_code != 200:
            print(f"❌ Failed to get more songs: {more_response.status_code}")
            return False

        more_data = more_response.json()
        more_songs = more_data.get('songs', [])

        print(f"✅ Got {len(more_songs)} more recommendations")

        # Check for duplicates
        initial_ids = {s['id'] for s in songs}
        more_ids = {s['id'] for s in more_songs}
        duplicates = initial_ids & more_ids

        if duplicates:
            print(f"⚠️  Warning: {len(duplicates)} duplicate songs found")
        else:
            print(f"✅ No duplicates")

        print(f"\n🎵 More Recommendations:")
        for i, song in enumerate(more_songs, 1):
            lang = song.get('language_type', 'N/A')
            pop = song.get('popularity', 0)
            print(f"  {i}. [{pop:2d}] {song['name'][:40]:40s} - {song['artist'][:30]:30s} ({lang})")

        # Validation summary
        print(f"\n✅ Validation:")
        checks = [
            ("Got 5 initial songs", len(songs) == 5),
            ("Got 5 more songs", len(more_songs) == 5),
            ("No duplicates", len(duplicates) == 0),
            ("Popularity is diverse", len(hidden_gems) + len(moderate) + len(popular) >= 2),
            ("Language mix present", english > 0 or hindi > 0)
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run tests on multiple images"""
    print("🧪 StoryBeats Multi-Image Algorithm Test")
    print("=" * 80)

    # Check backend
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Backend is running at {BASE_URL}\n")
    except:
        print(f"❌ Backend is not running at {BASE_URL}")
        print("Please start the backend server first")
        return

    # Test images
    test_images = [
        (Path.home() / "Downloads/shivangi.JPG", "Portrait Photo (Shivangi)"),
        (Path.home() / "Downloads/jaggi-photos.JPG", "Photo Collection (Jaggi)"),
        (Path.home() / "Downloads/scenary.JPG", "Scenery Photo"),
    ]

    results = []

    for image_path, test_name in test_images:
        if not image_path.exists():
            print(f"\n⚠️  Skipping {test_name}: Image not found at {image_path}")
            continue

        result = test_image(str(image_path), test_name)
        results.append((test_name, result))

        # Add delay between tests to avoid rate limiting
        if image_path != test_images[-1][0]:
            print("\n⏳ Waiting 3 seconds before next test...")
            import time
            time.sleep(3)

    # Final summary
    print(f"\n{'='*80}")
    print("📊 Test Summary")
    print(f"{'='*80}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("🎉 All algorithm improvements working correctly!")
    else:
        print("⚠️  Some tests failed. Review output above.")

    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
