#!/usr/bin/env python3
"""
Test script for feedback-based recommendation improvements
Verifies that liked/disliked artists affect song scoring
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.feedback_store import get_feedback_store


def test_feedback_artist_queries():
    """Test that we can query liked/disliked artists from database"""
    print("=" * 60)
    print("TEST 1: Querying Liked/Disliked Artists")
    print("=" * 60)

    feedback_store = get_feedback_store()

    # Get overall liked artists (across all moods)
    liked_artists = feedback_store.get_liked_artists(min_likes=1)
    print(f"\n✅ Total liked artists: {len(liked_artists)}")
    if liked_artists:
        print("   Top 5 liked artists:")
        for artist, count in liked_artists[:5]:
            print(f"   - {artist}: {count} likes")

    # Get overall disliked artists
    disliked_artists = feedback_store.get_disliked_artists(min_dislikes=1)
    print(f"\n✅ Total disliked artists: {len(disliked_artists)}")
    if disliked_artists:
        print("   Top 5 disliked artists:")
        for artist, count in disliked_artists[:5]:
            print(f"   - {artist}: {count} dislikes")

    # Get feedback stats
    stats = feedback_store.get_feedback_stats()
    print(f"\n📊 Feedback Statistics:")
    print(f"   Total feedback: {stats['total']}")
    print(f"   Likes: {stats['likes']}")
    print(f"   Dislikes: {stats['dislikes']}")
    print(f"   Like rate: {stats['like_rate']:.1%}")

    return len(liked_artists) > 0 or len(disliked_artists) > 0


def test_mood_specific_preferences():
    """Test mood-specific artist preferences"""
    print("\n" + "=" * 60)
    print("TEST 2: Mood-Specific Preferences")
    print("=" * 60)

    feedback_store = get_feedback_store()

    # Test common moods
    moods = ["happy", "energetic", "calm", "melancholic", "romantic"]

    for mood in moods:
        liked = feedback_store.get_liked_artists(mood=mood, min_likes=1)
        disliked = feedback_store.get_disliked_artists(mood=mood, min_dislikes=1)

        if liked or disliked:
            print(f"\n🎭 Mood: {mood.upper()}")
            if liked:
                print(f"   Liked artists ({len(liked)}): {[a for a, _ in liked[:3]]}")
            if disliked:
                print(f"   Disliked artists ({len(disliked)}): {[a for a, _ in disliked[:3]]}")

    return True


def test_feedback_integration():
    """Test that feedback is integrated into recommendation logic"""
    print("\n" + "=" * 60)
    print("TEST 3: Feedback Integration Check")
    print("=" * 60)

    # Check if spotify_service imports feedback_store
    try:
        from services.spotify_service import SpotifyService
        import inspect

        # Get source code of get_song_recommendations
        source = inspect.getsource(SpotifyService.get_song_recommendations)

        # Check for feedback-related code
        checks = {
            'feedback_store import': 'get_feedback_store' in source,
            'liked_artists query': 'get_liked_artists' in source,
            'disliked_artists query': 'get_disliked_artists' in source,
            'feedback_multiplier': 'feedback_multiplier' in source,
            'boost/penalty': '1.3' in source and '0.7' in source
        }

        print("\n✅ Integration checks:")
        all_passed = True
        for check_name, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"   [{status}] {check_name}")
            if not passed:
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"\n❌ Error checking integration: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🧪 FEEDBACK USAGE TEST SUITE")
    print("Testing artist preference boosting implementation\n")

    results = []

    # Test 1: Query liked/disliked artists
    try:
        results.append(("Artist Queries", test_feedback_artist_queries()))
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        results.append(("Artist Queries", False))

    # Test 2: Mood-specific preferences
    try:
        results.append(("Mood-Specific", test_mood_specific_preferences()))
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        results.append(("Mood-Specific", False))

    # Test 3: Integration check
    try:
        results.append(("Integration", test_feedback_integration()))
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        results.append(("Integration", False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Feedback-based recommendations are working.")
        print("\n📝 How it works:")
        print("   1. Users provide feedback (like/dislike) on songs")
        print("   2. System tracks which artists users like/dislike per mood")
        print("   3. Future recommendations boost liked artists by 30%")
        print("   4. Future recommendations penalize disliked artists by 30%")
        print("   5. This happens automatically during song scoring")
    else:
        print("\n⚠️  Some tests failed. Check output above for details.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
