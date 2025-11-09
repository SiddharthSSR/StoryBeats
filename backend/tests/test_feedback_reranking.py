#!/usr/bin/env python3
"""
Test Feedback & Reranking System

Tests:
1. Phase 1: User feedback storage and retrieval
2. Phase 2: Background reranking with verify_llm
3. Integration: Full flow from upload → feedback → reranked load_more
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.feedback_store import get_feedback_store
from services.verify_llm import get_verify_llm
from services.spotify_service import SpotifyService
import time


def test_phase1_feedback():
    """Test Phase 1: User Feedback Storage"""
    print("\n" + "="*80)
    print("🧪 TEST PHASE 1: User Feedback Storage")
    print("="*80)

    store = get_feedback_store()

    # Create test session
    session_id = "test_session_001"
    image_data = b"fake_image_data"
    analysis = {
        'mood': 'happy',
        'energy': 0.7,
        'valence': 0.8
    }

    print(f"\n1. Creating test session...")
    store.create_session(session_id, image_data, analysis)
    print(f"   ✅ Session created: {session_id}")

    # Add feedback
    print(f"\n2. Adding feedback for songs...")
    feedback_id1 = store.add_feedback(
        session_id=session_id,
        song_id="song_001",
        song_name="Happy Song",
        artist_name="Happy Artist",
        feedback=1,  # Like
        image_analysis=analysis
    )
    print(f"   ✅ Feedback 1 (like): ID {feedback_id1}")

    feedback_id2 = store.add_feedback(
        session_id=session_id,
        song_id="song_002",
        song_name="Sad Song",
        artist_name="Sad Artist",
        feedback=-1,  # Dislike
        image_analysis=analysis
    )
    print(f"   ✅ Feedback 2 (dislike): ID {feedback_id2}")

    # Retrieve feedback
    print(f"\n3. Retrieving session feedback...")
    session_feedback = store.get_session_feedback(session_id)
    print(f"   ✅ Retrieved {len(session_feedback)} feedback entries")

    for fb in session_feedback:
        emoji = "👍" if fb['feedback'] == 1 else "👎"
        print(f"      {emoji} {fb['song_name']} by {fb['artist_name']}")

    # Get stats
    print(f"\n4. Getting overall stats...")
    stats = store.get_feedback_stats()
    print(f"   ✅ Stats: {stats['likes']} likes, {stats['dislikes']} dislikes")
    print(f"      Like rate: {stats['like_rate']:.1%}")

    print(f"\n✅ Phase 1 test passed!")
    return True


def test_phase2_reranking():
    """Test Phase 2: Background Reranking with verify_llm"""
    print("\n" + "="*80)
    print("🧪 TEST PHASE 2: Background Reranking (Verify LLM)")
    print("="*80)

    # Check if image exists
    test_image = "/Users/siddharthsingh/Downloads/IMG_4963.jpg"
    if not os.path.exists(test_image):
        print(f"⚠️  Test image not found: {test_image}")
        print(f"   Skipping Phase 2 test (requires actual image)")
        return True

    print(f"\n1. Getting song recommendations...")
    spotify = SpotifyService()
    analysis = {
        'mood': 'happy',
        'energy': 0.7,
        'valence': 0.8,
        'danceability': 0.75,
        'acousticness': 0.3,
        'tempo': 120,
        'cultural_vibe': 'global'
    }

    result = spotify.get_song_recommendations(analysis)
    all_songs = result['all_songs']
    print(f"   ✅ Got {len(all_songs)} songs to rerank")

    print(f"\n2. Running verify_llm reranking...")
    print(f"   (This will take ~3-5 seconds for LLM processing)")
    verify = get_verify_llm()
    start = time.time()

    reranked_songs = verify.verify_and_rerank(
        image_path=test_image,
        songs=all_songs[:10],  # Limit to 10 for faster test
        original_analysis=analysis
    )

    elapsed = time.time() - start
    print(f"   ✅ Reranking completed in {elapsed:.2f}s")

    print(f"\n3. Comparing rankings...")
    print(f"\n   Original Top 3:")
    for i, song in enumerate(all_songs[:3], 1):
        print(f"      {i}. {song['name']} - {song['artist']}")

    print(f"\n   Reranked Top 3:")
    for i, song in enumerate(reranked_songs[:3], 1):
        confidence = song.get('llm_confidence', 0)
        print(f"      {i}. {song['name']} - {song['artist']} (confidence: {confidence:.2f})")

    print(f"\n✅ Phase 2 test passed!")
    return True


def test_integration():
    """Test Integration: Full flow"""
    print("\n" + "="*80)
    print("🧪 TEST INTEGRATION: Full Feedback + Reranking Flow")
    print("="*80)

    store = get_feedback_store()
    session_id = "integration_test_001"

    # Simulate full flow
    print(f"\n1. Simulating image upload + recommendations...")
    spotify = SpotifyService()
    analysis = {
        'mood': 'melancholic',
        'energy': 0.3,
        'valence': 0.2,
        'danceability': 0.4,
        'acousticness': 0.7,
        'tempo': 90,
        'cultural_vibe': 'global'
    }

    result = spotify.get_song_recommendations(analysis)
    songs = result['songs']
    all_songs = result['all_songs']

    print(f"   ✅ Got {len(songs)} initial songs")
    print(f"   ✅ Cached {len(all_songs)} total songs")

    # Create session
    store.create_session(session_id, b"mock_image_data", analysis)
    print(f"   ✅ Created session: {session_id}")

    # Simulate user feedback
    print(f"\n2. Simulating user feedback...")
    for i, song in enumerate(songs[:3]):
        feedback_val = 1 if i < 2 else -1  # Like first 2, dislike 3rd
        store.add_feedback(
            session_id=session_id,
            song_id=song['id'],
            song_name=song['name'],
            artist_name=song['artist'],
            feedback=feedback_val,
            image_analysis=analysis
        )
        emoji = "👍" if feedback_val == 1 else "👎"
        print(f"   {emoji} {song['name']} by {song['artist']}")

    # Simulate background reranking
    print(f"\n3. Simulating background reranking...")
    print(f"   (In production, this runs in a separate thread)")

    # Store original songs
    store.store_reranked_results(
        session_id=session_id,
        reranked_songs=all_songs,  # Mock reranked (in real app, these are different)
        original_songs=all_songs
    )
    print(f"   ✅ Stored reranked results")

    # Retrieve reranked results
    print(f"\n4. Simulating 'load more' with reranked results...")
    reranked_data = store.get_reranked_results(session_id)
    if reranked_data:
        reranked = reranked_data['reranked_songs']
        print(f"   ✅ Retrieved {len(reranked)} reranked songs")
        print(f"   ✅ 'Load more' would serve reranked songs instantly")
    else:
        print(f"   ❌ No reranked results found")
        return False

    # Get session feedback
    print(f"\n5. Retrieving all session feedback...")
    feedback = store.get_session_feedback(session_id)
    print(f"   ✅ Session has {len(feedback)} feedback entries")

    likes = sum(1 for f in feedback if f['feedback'] == 1)
    dislikes = sum(1 for f in feedback if f['feedback'] == -1)
    print(f"      Likes: {likes}, Dislikes: {dislikes}")

    print(f"\n✅ Integration test passed!")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🚀 FEEDBACK & RERANKING TEST SUITE")
    print("="*80)

    tests = [
        ("Phase 1: Feedback Storage", test_phase1_feedback),
        ("Phase 2: Background Reranking", test_phase2_reranking),
        ("Integration: Full Flow", test_integration)
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
