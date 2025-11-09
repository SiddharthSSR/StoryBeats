#!/usr/bin/env python3
"""
Simple test to debug where the app is hanging
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.spotify_service import SpotifyService
from services.image_analyzer import ImageAnalyzer
import time

def test_steps():
    """Test each step individually"""
    print("\n" + "="*80)
    print("🔍 DEBUGGING: Testing Each Step")
    print("="*80)

    # Step 1: Test Spotify service initialization
    print("\n[Step 1] Initializing Spotify service...")
    start = time.time()
    try:
        spotify = SpotifyService()
        print(f"   ✅ Spotify service initialized in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Step 2: Test image analyzer initialization
    print("\n[Step 2] Initializing Image analyzer...")
    start = time.time()
    try:
        analyzer = ImageAnalyzer()
        print(f"   ✅ Image analyzer initialized in {time.time() - start:.2f}s")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Step 3: Test image analysis
    print("\n[Step 3] Testing image analysis...")
    image_path = "/Users/siddharthsingh/Downloads/IMG_4963.jpg"

    if not os.path.exists(image_path):
        print(f"   ⚠️  Image not found: {image_path}")
        print("   Using mock analysis instead...")
        analysis = {
            'mood': 'happy',
            'energy': 0.7,
            'valence': 0.8,
            'danceability': 0.75,
            'acousticness': 0.3,
            'tempo': 120,
            'cultural_vibe': 'global'
        }
    else:
        print(f"   📸 Analyzing image: {os.path.basename(image_path)}")
        start = time.time()
        try:
            analysis = analyzer.analyze_image(image_path)
            elapsed = time.time() - start
            print(f"   ✅ Image analyzed in {elapsed:.2f}s")
            print(f"      Mood: {analysis.get('mood')}")
            print(f"      Energy: {analysis.get('energy')}")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Step 4: Test song recommendations (THIS IS WHERE IT MIGHT HANG)
    print("\n[Step 4] Getting song recommendations...")
    print("   ⏱️  Starting... (timeout in 60 seconds)")
    start = time.time()

    try:
        # Set a timeout using signal (Unix only)
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Song recommendation took too long!")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)  # 60 second timeout

        result = spotify.get_song_recommendations(analysis)

        signal.alarm(0)  # Cancel timeout

        elapsed = time.time() - start
        print(f"   ✅ Recommendations received in {elapsed:.2f}s")

        # Check result format
        if isinstance(result, dict):
            songs = result.get('songs', [])
            all_songs = result.get('all_songs', [])
            print(f"      First batch: {len(songs)} songs")
            print(f"      Total cached: {len(all_songs)} songs")
        elif isinstance(result, list):
            print(f"      ⚠️  Old format returned: {len(result)} songs")
        else:
            print(f"      ❌ Unexpected format: {type(result)}")
            return False

        return True

    except TimeoutError as e:
        elapsed = time.time() - start
        print(f"   ❌ TIMEOUT after {elapsed:.2f}s")
        print(f"      {e}")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ FAILED after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_steps()

    print("\n" + "="*80)
    if success:
        print("✅ All steps completed successfully!")
    else:
        print("❌ Test failed - see error above")
    print("="*80)

    sys.exit(0 if success else 1)
