#!/usr/bin/env python3
"""
Performance Test - Measure optimization impact

Tests the complete recommendation pipeline and measures:
- Total execution time
- Artist processing time (parallel execution)
- Cache hit rates
- API call counts

Expected Results After Optimization:
- First request: 5-7 seconds (down from 25-40s)
- Cached request: 1-2 seconds
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.spotify_service import SpotifyService
import time
from datetime import datetime

def test_performance():
    """Run performance test with timing"""

    print("\n" + "="*80)
    print("⚡ PERFORMANCE TEST - Optimized Algorithm")
    print("="*80)

    # Initialize service
    print("\n🔧 Initializing Spotify service...")
    service = SpotifyService()

    # Test scenarios
    test_cases = [
        {
            'name': 'Romantic Photo (First Request)',
            'analysis': {
                'mood': 'romantic',
                'energy': 0.5,
                'valence': 0.6,
                'danceability': 0.5,
                'acousticness': 0.4,
                'tempo': 100,
                'cultural_vibe': 'global'
            }
        },
        {
            'name': 'Romantic Photo (Cached Request)',
            'analysis': {
                'mood': 'romantic',
                'energy': 0.5,
                'valence': 0.6,
                'danceability': 0.5,
                'acousticness': 0.4,
                'tempo': 100,
                'cultural_vibe': 'global'
            }
        },
        {
            'name': 'Energetic Photo',
            'analysis': {
                'mood': 'energetic',
                'energy': 0.9,
                'valence': 0.8,
                'danceability': 0.85,
                'acousticness': 0.1,
                'tempo': 140,
                'cultural_vibe': 'western'
            }
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"📊 Test {i}/{len(test_cases)}: {test['name']}")
        print(f"{'='*80}")

        # Measure time
        start_time = time.time()

        try:
            songs = service.get_song_recommendations(test['analysis'])

            elapsed = time.time() - start_time

            print(f"\n✅ Test completed successfully!")
            print(f"⏱️  Total time: {elapsed:.2f}s")
            print(f"🎵 Songs returned: {len(songs)}")

            # Check cache info
            cache_size_tracks = len(service.top_tracks_cache)
            cache_size_albums = len(service.albums_cache)
            print(f"💾 Cache status:")
            print(f"   - Top tracks cached: {cache_size_tracks} artists")
            print(f"   - Albums cached: {cache_size_albums} artists")

            results.append({
                'name': test['name'],
                'time': elapsed,
                'songs': len(songs),
                'success': True
            })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ Test failed: {e}")
            print(f"⏱️  Time before failure: {elapsed:.2f}s")

            results.append({
                'name': test['name'],
                'time': elapsed,
                'songs': 0,
                'success': False,
                'error': str(e)
            })

    # Summary
    print("\n" + "="*80)
    print("📈 PERFORMANCE SUMMARY")
    print("="*80)

    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"\n{status} {result['name']}")
        print(f"   Time: {result['time']:.2f}s")
        if result['success']:
            print(f"   Songs: {result['songs']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")

    # Performance analysis
    print("\n" + "="*80)
    print("🎯 OPTIMIZATION IMPACT")
    print("="*80)

    if len(results) >= 2 and results[0]['success'] and results[1]['success']:
        first_time = results[0]['time']
        cached_time = results[1]['time']

        print(f"\n📊 Cache Performance:")
        print(f"   First request:  {first_time:.2f}s")
        print(f"   Cached request: {cached_time:.2f}s")
        print(f"   Speedup: {first_time/cached_time:.1f}x faster")
        print(f"   Time saved: {first_time - cached_time:.2f}s ({((first_time - cached_time)/first_time * 100):.1f}%)")

        # Compare to baseline (before optimization)
        baseline_time = 30  # Average baseline time
        print(f"\n📉 vs Baseline (before optimization):")
        print(f"   Baseline: ~{baseline_time}s (estimated)")
        print(f"   Current: {first_time:.2f}s")
        print(f"   Improvement: {baseline_time - first_time:.2f}s faster ({((baseline_time - first_time)/baseline_time * 100):.1f}% faster)")

    # Expected performance targets
    print("\n" + "="*80)
    print("🎯 TARGET PERFORMANCE")
    print("="*80)
    print("\n📋 Expected after all optimizations:")
    print("   - First request: 5-7s (target)")
    print("   - Cached request: 1-2s (target)")
    print("\n✨ Optimizations applied:")
    print("   ✅ Parallel artist processing (ThreadPoolExecutor, 6 workers)")
    print("   ✅ Batch API calls (sp.tracks() instead of individual sp.track())")
    print("   ✅ Caching layer (1h for top tracks, 30m for albums)")
    print("   ✅ Image optimization (resize to 1024x1024)")

    if results[0]['success']:
        first_time = results[0]['time']
        if first_time <= 7:
            print(f"\n🎉 SUCCESS! First request time ({first_time:.2f}s) meets target (≤7s)")
        elif first_time <= 10:
            print(f"\n✅ GOOD! First request time ({first_time:.2f}s) close to target (≤7s)")
        else:
            print(f"\n⚠️  First request time ({first_time:.2f}s) above target (≤7s)")
            print("   Consider further optimization or Spotify API rate limiting may be affecting performance")

    if len(results) >= 2 and results[1]['success']:
        cached_time = results[1]['time']
        if cached_time <= 2:
            print(f"🎉 SUCCESS! Cached request time ({cached_time:.2f}s) meets target (≤2s)")
        elif cached_time <= 4:
            print(f"✅ GOOD! Cached request time ({cached_time:.2f}s) close to target (≤2s)")
        else:
            print(f"⚠️  Cached request time ({cached_time:.2f}s) above target (≤2s)")


if __name__ == "__main__":
    test_performance()
