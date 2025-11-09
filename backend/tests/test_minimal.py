#!/usr/bin/env python3
"""Minimal test to find where it hangs"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Step 1: Imports...")
from services.spotify_service import SpotifyService
print("✅ Imported")

print("\nStep 2: Initialize...")
service = SpotifyService()
print("✅ Initialized")

print("\nStep 3: Call method...")
analysis = {
    'mood': 'happy',
    'energy': 0.7,
    'valence': 0.8,
    'danceability': 0.75,
    'acousticness': 0.3,
    'tempo': 120,
    'cultural_vibe': 'global'
}

result = service.get_song_recommendations(analysis)
print(f"✅ Got result: {type(result)}")

if isinstance(result, dict):
    print(f"   - songs: {len(result.get('songs', []))}")
    print(f"   - all_songs: {len(result.get('all_songs', []))}")
elif isinstance(result, list):
    print(f"   - OLD FORMAT: {len(result)} songs")

print("\n✅ TEST PASSED")
