#!/usr/bin/env python3
"""Quick script to check implicit feedback"""
import sqlite3

db_path = "storybeats_feedback.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n" + "="*80)
print("IMPLICIT FEEDBACK CHECK")
print("="*80)

# Count by signal type
cursor.execute("""
    SELECT signal_type, COUNT(*) as count
    FROM feedback
    GROUP BY signal_type
    ORDER BY count DESC
""")

print("\n📊 Feedback by Type:")
for row in cursor.fetchall():
    signal_type = row[0] or 'explicit'
    count = row[1]
    icons = {
        'explicit': '👍👎',
        'spotify_click': '🎵',
        'preview_play': '▶️',
        'preview_complete': '✅',
        'load_more': '🔄'
    }
    icon = icons.get(signal_type, '📊')
    print(f"  {icon} {signal_type:20} : {count:3} entries")

# Get recent implicit signals
cursor.execute("""
    SELECT signal_type, weight, song_name, artist_name, created_at
    FROM feedback
    WHERE signal_type IS NOT NULL AND signal_type <> 'explicit'
    ORDER BY created_at DESC
    LIMIT 10
""")

rows = cursor.fetchall()
if rows:
    print("\n📝 Recent Implicit Signals (last 10):")
    print("-"*80)
    for row in rows:
        signal_type, weight, song_name, artist_name, created_at = row
        song_display = f'"{song_name}" by {artist_name}' if song_name else 'session-level'
        print(f"  {signal_type:20} | weight:{weight:3.1f} | {song_display}")
else:
    print("\n❌ No implicit signals yet!")
    print("   Try these actions in the UI:")
    print("   1. Click 'Open in Spotify'")
    print("   2. Play a song preview")
    print("   3. Click 'Get 5 More Songs'")

print("="*80 + "\n")
conn.close()
