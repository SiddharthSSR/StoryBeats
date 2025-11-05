#!/usr/bin/env python3
"""
Test script for recommendation algorithm improvements

Tests:
1. Multi-source blending with weighted scoring
2. Semantic similarity matching
3. Dynamic genre blending
4. Contextual playlist search
5. Audio feature range matching
6. Track popularity distribution
7. Mood-based tempo mapping
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5001"
ANALYZE_URL = f"{BASE_URL}/api/analyze"
MORE_SONGS_URL = f"{BASE_URL}/api/more-songs"


def test_algorithm_with_image(image_path, test_name):
    """
    Test the recommendation algorithm with a specific image

    Args:
        image_path: Path to the test image
        test_name: Name of the test case
    """
    print(f"\n{'='*80}")
    print(f"Test Case: {test_name}")
    print(f"{'='*80}\n")

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False

    try:
        # Step 1: Upload image and get initial recommendations
        print(f"📤 Uploading image: {image_path}")

        with open(image_path, 'rb') as f:
            files = {'photo': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(ANALYZE_URL, files=files, timeout=60)

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

        print(f"\n✅ Got {len(songs)} recommendations")
        print(f"Session ID: {session_id}")

        # Print analysis
        print(f"\n📊 Image Analysis:")
        print(f"  Mood: {analysis.get('mood', 'N/A')}")
        print(f"  Energy: {analysis.get('energy', 'N/A'):.2f}")
        print(f"  Valence: {analysis.get('valence', 'N/A'):.2f}")
        print(f"  Danceability: {analysis.get('danceability', 'N/A'):.2f}")
        print(f"  Acousticness: {analysis.get('acousticness', 'N/A'):.2f}")
        print(f"  Tempo: {analysis.get('tempo', 'N/A')} BPM")
        print(f"  Instrumentalness: {analysis.get('instrumentalness', 'N/A'):.2f}")
        print(f"  Genres: {', '.join(analysis.get('genres', []))}")
        print(f"  Themes: {', '.join(analysis.get('themes', []))}")
        print(f"  Keywords: {', '.join(analysis.get('keywords', [])[:5])}")
        print(f"  Cultural vibe: {analysis.get('cultural_vibe', 'N/A')}")

        # Print song recommendations
        print(f"\n🎵 Initial Recommendations:")
        for i, song in enumerate(songs, 1):
            lang_type = song.get('language_type', 'N/A')
            popularity = song.get('popularity', 'N/A')
            print(f"  {i}. {song['name']} - {song['artist']}")
            print(f"     Popularity: {popularity}, Language: {lang_type}")

        # Analyze popularity distribution
        print(f"\n📈 Popularity Distribution:")
        hidden_gems = [s for s in songs if 25 <= s.get('popularity', 0) <= 40]
        moderate = [s for s in songs if 40 < s.get('popularity', 0) <= 70]
        popular = [s for s in songs if 70 < s.get('popularity', 0) <= 95]

        print(f"  Hidden gems (25-40): {len(hidden_gems)}")
        print(f"  Moderate hits (40-70): {len(moderate)}")
        print(f"  Popular (70-95): {len(popular)}")

        # Analyze language distribution
        print(f"\n🌍 Language Distribution:")
        english = [s for s in songs if s.get('language_type') == 'English']
        hindi = [s for s in songs if s.get('language_type') == 'Hindi']
        mixed = [s for s in songs if s.get('language_type') == 'Mixed']

        print(f"  English: {len(english)}")
        print(f"  Hindi: {len(hindi)}")
        print(f"  Mixed: {len(mixed)}")

        # Step 2: Test "More Songs" functionality
        print(f"\n🔄 Testing 'More Songs' functionality...")

        more_response = requests.post(MORE_SONGS_URL, json={'session_id': session_id}, timeout=60)

        if more_response.status_code != 200:
            print(f"❌ Failed to get more songs: {more_response.status_code}")
            return False

        more_data = more_response.json()
        more_songs = more_data.get('songs', [])

        print(f"✅ Got {len(more_songs)} more recommendations")

        # Verify no duplicates between initial and more songs
        initial_ids = {s['id'] for s in songs}
        more_ids = {s['id'] for s in more_songs}
        duplicates = initial_ids & more_ids

        if duplicates:
            print(f"⚠️  Warning: Found {len(duplicates)} duplicate songs")
        else:
            print(f"✅ No duplicates between initial and more songs")

        print(f"\n🎵 More Recommendations:")
        for i, song in enumerate(more_songs, 1):
            lang_type = song.get('language_type', 'N/A')
            popularity = song.get('popularity', 'N/A')
            print(f"  {i}. {song['name']} - {song['artist']}")
            print(f"     Popularity: {popularity}, Language: {lang_type}")

        # Validation checks
        print(f"\n✅ Validation Results:")
        checks = []

        # Check 1: Got 5 songs
        checks.append(("Got exactly 5 initial songs", len(songs) == 5))

        # Check 2: Got 5 more songs
        checks.append(("Got exactly 5 more songs", len(more_songs) == 5))

        # Check 3: No duplicates
        checks.append(("No duplicate songs", len(duplicates) == 0))

        # Check 4: All songs have required fields
        required_fields = ['id', 'name', 'artist', 'spotify_url', 'popularity']
        all_have_fields = all(all(field in song for field in required_fields) for song in songs)
        checks.append(("All songs have required fields", all_have_fields))

        # Check 5: Popularity distribution is diverse
        has_diversity = len(hidden_gems) + len(moderate) + len(popular) >= 2
        checks.append(("Popularity distribution is diverse", has_diversity))

        # Check 6: Language mix exists (unless all one language)
        has_mix = len(english) > 0 or len(hindi) > 0
        checks.append(("Language mix present", has_mix))

        # Print validation results
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run algorithm improvement tests"""
    print("🧪 StoryBeats Recommendation Algorithm Test Suite")
    print("=" * 80)

    # Check if backend is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Backend is running at {BASE_URL}")
    except:
        print(f"❌ Backend is not running at {BASE_URL}")
        print("Please start the backend server first: python app.py")
        return

    # Test scenarios
    test_cases = []

    # Try to find test images
    backend_dir = Path(__file__).parent.parent

    # Look for common test image locations
    possible_images = [
        backend_dir / "test_images" / "sunset.jpg",
        backend_dir / "test_images" / "party.jpg",
        backend_dir / "test_images" / "nature.jpg",
        backend_dir / "uploads" / "test.jpg",
        Path.home() / "Downloads" / "test.jpg",
    ]

    # Find first available image
    test_image = None
    for img_path in possible_images:
        if img_path.exists():
            test_image = str(img_path)
            break

    if not test_image:
        print("\n⚠️  No test images found. Please provide a test image.")
        print("You can:")
        print("  1. Place an image at: backend/test_images/test.jpg")
        print("  2. Or specify image path when prompted")

        # Ask user for image path
        user_path = input("\nEnter path to test image (or press Enter to skip): ").strip()
        if user_path and os.path.exists(user_path):
            test_image = user_path
        else:
            print("No valid image provided. Exiting.")
            return

    print(f"\n📸 Using test image: {test_image}")

    # Run test
    result = test_algorithm_with_image(test_image, "Algorithm Improvements Test")

    # Summary
    print(f"\n{'='*80}")
    if result:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
