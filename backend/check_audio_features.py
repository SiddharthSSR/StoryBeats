#!/usr/bin/env python3
"""
Test script to verify Phase 1B: Audio Feature Learning

Checks:
1. Audio features are being stored in database
2. Learned preferences from feedback
3. Statistics about audio feature learning
"""

import sqlite3
import json
from services.audio_feature_analytics import get_audio_feature_analytics

db_path = "storybeats_feedback.db"

print("\n" + "="*80)
print("PHASE 1B: AUDIO FEATURE LEARNING TEST")
print("="*80)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ============================================================================
# 1. Check if audio features are being stored
# ============================================================================
print("\n📊 Step 1: Checking audio feature storage...")

cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN audio_features IS NOT NULL THEN 1 ELSE 0 END) as with_features
    FROM feedback
""")

row = cursor.fetchone()
total_feedback = row[0]
with_features = row[1]

if total_feedback == 0:
    print("❌ No feedback entries found! Upload a photo and give feedback first.")
    conn.close()
    exit(1)

print(f"  Total feedback entries: {total_feedback}")
print(f"  With audio features: {with_features} ({with_features/total_feedback*100:.1f}%)")

if with_features == 0:
    print("❌ No audio features stored yet!")
    print("   This means feedback was given before Phase 1B was implemented.")
    print("   Upload a new photo and give feedback to test Phase 1B!")
    conn.close()
    exit(1)

print("✅ Audio features are being stored!")

# ============================================================================
# 2. Show example audio features
# ============================================================================
print("\n📝 Step 2: Sample audio features...")

cursor.execute("""
    SELECT song_name, artist_name, audio_features, feedback
    FROM feedback
    WHERE audio_features IS NOT NULL
    LIMIT 3
""")

rows = cursor.fetchall()
if rows:
    for i, row in enumerate(rows, 1):
        song_name, artist_name, audio_features_json, feedback = row
        features = json.loads(audio_features_json)

        print(f"\n  Example {i}: {feedback_emoji(feedback)} \"{song_name}\" by {artist_name}")
        print(f"    Energy: {features.get('energy', 'N/A')}")
        print(f"    Valence: {features.get('valence', 'N/A')}")
        print(f"    Danceability: {features.get('danceability', 'N/A')}")
        print(f"    Acousticness: {features.get('acousticness', 'N/A')}")
        print(f"    Tempo: {features.get('tempo', 'N/A')} BPM")

# ============================================================================
# 3. Get audio feature learning statistics
# ============================================================================
print("\n\n📈 Step 3: Audio Feature Learning Statistics...")

analytics = get_audio_feature_analytics()
stats = analytics.get_feature_learning_stats()

overall = stats['overall']
print(f"\n  Overall Statistics:")
print(f"    Total feedback with audio features: {overall['total']}")
print(f"    Liked songs: {overall['liked']}")
print(f"    Disliked songs: {overall['disliked']}")
print(f"    Has enough data for learning: {'✅ YES' if overall['has_enough_data'] else '❌ NO (need ' + str(stats['min_feedback_required']) + '+ likes)'}")

if stats['by_mood']:
    print(f"\n  By Mood:")
    for mood_stat in stats['by_mood']:
        mood = mood_stat['mood']
        total = mood_stat['total']
        liked = mood_stat['liked']
        has_data = mood_stat['has_enough_data']

        status = "✅" if has_data else "⚠️ "
        print(f"    {status} {mood:15} : {liked:2} liked / {total:2} total")

# ============================================================================
# 4. Show learned preferences (if enough data)
# ============================================================================
print("\n\n🎯 Step 4: Learned Audio Feature Preferences...")

if not overall['has_enough_data']:
    print(f"  ⚠️  Not enough data yet! Need at least {stats['min_feedback_required']} liked songs.")
    print(f"  Currently have {overall['liked']} liked songs with audio features.")
    print("\n  💡 To test Phase 1B:")
    print("     1. Upload a photo")
    print("     2. Like at least 3 songs (👍)")
    print("     3. Run this script again")
else:
    # Show overall preferences
    print("\n  Overall Preferences (all moods):")
    overall_prefs = analytics.get_preferred_audio_features(mood=None)

    if overall_prefs.get('metadata', {}).get('has_enough_data'):
        for feature in ['energy', 'valence', 'danceability', 'acousticness', 'tempo']:
            if feature in overall_prefs:
                pref = overall_prefs[feature]
                target = pref['target']
                min_val = pref['min']
                max_val = pref['max']
                samples = pref['sample_count']

                if feature == 'tempo':
                    print(f"    {feature:15} : {target:6.1f} BPM  (range: {min_val:6.1f} - {max_val:6.1f})  [{samples} samples]")
                else:
                    print(f"    {feature:15} : {target:6.3f}      (range: {min_val:5.3f} - {max_val:5.3f})  [{samples} samples]")

    # Show mood-specific preferences (if available)
    mood_prefs_found = False
    for mood_stat in stats['by_mood']:
        if mood_stat['has_enough_data']:
            mood = mood_stat['mood']
            mood_prefs = analytics.get_preferred_audio_features(mood=mood)

            if not mood_prefs_found:
                print(f"\n  Mood-Specific Preferences:")
                mood_prefs_found = True

            print(f"\n    {mood}:")
            for feature in ['energy', 'valence', 'danceability', 'acousticness', 'tempo']:
                if feature in mood_prefs:
                    pref = mood_prefs[feature]
                    target = pref['target']
                    min_val = pref['min']
                    max_val = pref['max']

                    if feature == 'tempo':
                        print(f"      {feature:15} : {target:6.1f} BPM  (range: {min_val:6.1f} - {max_val:6.1f})")
                    else:
                        print(f"      {feature:15} : {target:6.3f}      (range: {min_val:5.3f} - {max_val:5.3f})")

# ============================================================================
# 5. Test audio feature boost calculation
# ============================================================================
if overall['has_enough_data']:
    print("\n\n🎮 Step 5: Testing Audio Feature Boost...")

    # Get a sample liked song
    cursor.execute("""
        SELECT song_name, artist_name, audio_features
        FROM feedback
        WHERE audio_features IS NOT NULL AND feedback > 0
        LIMIT 1
    """)

    row = cursor.fetchone()
    if row:
        song_name, artist_name, audio_features_json = row
        features = json.loads(audio_features_json)

        boost, reason = analytics.calculate_audio_feature_boost(features, mood=None)

        print(f"\n  Test song: \"{song_name}\" by {artist_name}")
        print(f"  Boost multiplier: {boost}x")
        print(f"  Reason: {reason}")

        if boost > 1.0:
            print(f"  ✅ This song would be boosted in recommendations!")
        elif boost < 1.0:
            print(f"  ⚠️  This song would be penalized in recommendations")
        else:
            print(f"  → This song has neutral scoring")

print("\n" + "="*80)
print("✅ Phase 1B: Audio Feature Learning Test Complete!")
print("="*80 + "\n")

conn.close()


def feedback_emoji(feedback):
    """Helper to convert feedback value to emoji"""
    if feedback > 0:
        return "👍"
    elif feedback < 0:
        return "👎"
    else:
        return "❓"
