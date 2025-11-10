import json

# Read the most recent session data
sessions_file = "session_songs.json"
try:
    with open(sessions_file, 'r') as f:
        data = json.load(f)
        print("\nChecking preview availability in recent sessions...\n")
        
        for session_id, session_data in list(data.items())[-3:]:
            songs = session_data.get('all_songs', [])
            with_preview = sum(1 for s in songs if s.get('preview_url'))
            total = len(songs)
            print(f"Session {session_id[:8]}:")
            print(f"  Songs with preview: {with_preview}/{total} ({with_preview/total*100:.1f}%)")
            
            if with_preview > 0:
                print(f"  Example songs with previews:")
                for song in songs[:10]:
                    if song.get('preview_url'):
                        print(f"    ✓ {song['name']} by {song['artist']}")
                        break
except FileNotFoundError:
    print("No session data yet. Upload a photo first!")
except Exception as e:
    print(f"Error: {e}")
