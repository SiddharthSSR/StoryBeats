#!/usr/bin/env python3
"""
Test script to verify session cleanup mechanism
"""
import sys
sys.path.insert(0, '/Users/siddharthsingh/codingtensor/StoryBeats/backend')

from datetime import datetime, timedelta
import secrets

# Import from app
from app import session_songs, cleanup_expired_sessions, SESSION_EXPIRY_HOURS

def test_session_cleanup():
    """Test session cleanup removes expired sessions"""
    print("=" * 60)
    print("Session Cleanup Test")
    print("=" * 60)
    print()

    # Clear any existing sessions
    session_songs.clear()

    # Create some test sessions
    print("Creating test sessions...")

    # Active session (not expired)
    active_id = secrets.token_urlsafe(32)
    session_songs[active_id] = {
        'songs': ['song1', 'song2'],
        'expires_at': datetime.now() + timedelta(hours=1)
    }
    print(f"  ✓ Created active session: {active_id[:10]}...")

    # Expired session (1 hour ago)
    expired_id_1 = secrets.token_urlsafe(32)
    session_songs[expired_id_1] = {
        'songs': ['song3', 'song4'],
        'expires_at': datetime.now() - timedelta(hours=1)
    }
    print(f"  ✓ Created expired session 1: {expired_id_1[:10]}...")

    # Expired session (2 hours ago)
    expired_id_2 = secrets.token_urlsafe(32)
    session_songs[expired_id_2] = {
        'songs': ['song5', 'song6'],
        'expires_at': datetime.now() - timedelta(hours=2)
    }
    print(f"  ✓ Created expired session 2: {expired_id_2[:10]}...")

    # Another active session
    active_id_2 = secrets.token_urlsafe(32)
    session_songs[active_id_2] = {
        'songs': ['song7', 'song8'],
        'expires_at': datetime.now() + timedelta(minutes=30)
    }
    print(f"  ✓ Created active session 2: {active_id_2[:10]}...")

    print(f"\nTotal sessions before cleanup: {len(session_songs)}")
    print(f"  Active: 2")
    print(f"  Expired: 2")
    print()

    # Run cleanup
    print("Running cleanup_expired_sessions()...")
    removed_count = cleanup_expired_sessions()
    print()

    # Check results
    print("Results:")
    print(f"  Sessions removed: {removed_count}")
    print(f"  Sessions remaining: {len(session_songs)}")
    print()

    # Verify
    if removed_count == 2:
        print("✅ PASS: Correctly removed 2 expired sessions")
    else:
        print(f"❌ FAIL: Expected to remove 2 sessions, removed {removed_count}")

    if len(session_songs) == 2:
        print("✅ PASS: 2 active sessions remain")
    else:
        print(f"❌ FAIL: Expected 2 remaining sessions, found {len(session_songs)}")

    if active_id in session_songs and active_id_2 in session_songs:
        print("✅ PASS: Active sessions were preserved")
    else:
        print("❌ FAIL: Active sessions were removed!")

    if expired_id_1 not in session_songs and expired_id_2 not in session_songs:
        print("✅ PASS: Expired sessions were removed")
    else:
        print("❌ FAIL: Expired sessions still exist!")

    print()
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)


def test_session_id_security():
    """Test that session IDs are secure and random"""
    print()
    print("=" * 60)
    print("Session ID Security Test")
    print("=" * 60)
    print()

    # Generate multiple session IDs
    ids = [secrets.token_urlsafe(32) for _ in range(5)]

    print("Generated 5 session IDs:")
    for i, sid in enumerate(ids, 1):
        print(f"  {i}. {sid}")
    print()

    # Check uniqueness
    if len(ids) == len(set(ids)):
        print("✅ PASS: All session IDs are unique")
    else:
        print("❌ FAIL: Duplicate session IDs found!")

    # Check length (should be 43 characters for 32 bytes URL-safe)
    if all(len(sid) == 43 for sid in ids):
        print("✅ PASS: All session IDs have correct length (43 chars)")
    else:
        print("❌ FAIL: Session IDs have incorrect length!")

    # Check they're URL-safe (no special characters except - and _)
    import re
    if all(re.match(r'^[A-Za-z0-9_-]+$', sid) for sid in ids):
        print("✅ PASS: All session IDs are URL-safe")
    else:
        print("❌ FAIL: Session IDs contain invalid characters!")

    print()
    print("=" * 60)


if __name__ == "__main__":
    test_session_cleanup()
    test_session_id_security()
