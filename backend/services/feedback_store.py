#!/usr/bin/env python3
"""
Feedback Storage Service
Stores user feedback (likes/dislikes) for song recommendations
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import threading

class FeedbackStore:
    """
    Manages user feedback and session data

    Features:
    - Store song feedback (like/dislike)
    - Track sessions by image analysis
    - Store reranked results per session
    - Query feedback patterns for model improvement
    """

    def __init__(self, db_path: str = "storybeats_feedback.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()

    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Sessions table: Track each image upload session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                image_hash TEXT,
                analysis JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Feedback table: Store user likes/dislikes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                song_id TEXT,
                song_name TEXT,
                artist_name TEXT,
                feedback INTEGER,  -- 1 for like, -1 for dislike
                image_analysis JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Reranked results cache: Store LLM-reranked songs per session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reranked_results (
                session_id TEXT PRIMARY KEY,
                reranked_songs JSON,
                original_songs JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_song ON feedback(song_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_hash ON sessions(image_hash)")

        conn.commit()
        print("✅ Database initialized: storybeats_feedback.db")

    def create_session(self, session_id: str, image_data: bytes, analysis: Dict) -> str:
        """
        Create a new session for an image upload

        Args:
            session_id: Unique session identifier
            image_data: Raw image bytes for hashing
            analysis: Image analysis result from LLM

        Returns:
            session_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Hash image to detect duplicates
        image_hash = hashlib.md5(image_data).hexdigest()

        cursor.execute("""
            INSERT OR REPLACE INTO sessions (session_id, image_hash, analysis)
            VALUES (?, ?, ?)
        """, (session_id, image_hash, json.dumps(analysis)))

        conn.commit()
        return session_id

    def add_feedback(self, session_id: str, song_id: str, song_name: str,
                    artist_name: str, feedback: int, image_analysis: Dict) -> int:
        """
        Record user feedback for a song

        Args:
            session_id: Session ID
            song_id: Spotify track ID
            song_name: Song name
            artist_name: Artist name
            feedback: 1 for like, -1 for dislike
            image_analysis: The analysis that led to this recommendation

        Returns:
            feedback_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO feedback (session_id, song_id, song_name, artist_name, feedback, image_analysis)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, song_id, song_name, artist_name, feedback, json.dumps(image_analysis)))

        conn.commit()
        return cursor.lastrowid

    def get_session_feedback(self, session_id: str) -> List[Dict]:
        """Get all feedback for a session"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM feedback WHERE session_id = ?
        """, (session_id,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def store_reranked_results(self, session_id: str, reranked_songs: List[Dict],
                               original_songs: List[Dict]):
        """
        Store LLM-reranked songs for this session

        Args:
            session_id: Session ID
            reranked_songs: Songs after LLM verification/reranking
            original_songs: Original algorithmic recommendations
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO reranked_results (session_id, reranked_songs, original_songs)
            VALUES (?, ?, ?)
        """, (session_id, json.dumps(reranked_songs), json.dumps(original_songs)))

        conn.commit()
        print(f"✅ Stored reranked results for session {session_id}")

    def get_reranked_results(self, session_id: str) -> Optional[Dict]:
        """
        Get LLM-reranked results for this session

        Returns:
            Dict with 'reranked_songs' and 'original_songs', or None if not available
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT reranked_songs, original_songs FROM reranked_results WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        if row:
            return {
                'reranked_songs': json.loads(row['reranked_songs']),
                'original_songs': json.loads(row['original_songs'])
            }
        return None

    def get_feedback_stats(self) -> Dict:
        """
        Get overall feedback statistics for analytics

        Returns:
            Dict with likes, dislikes, total count, like_rate
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END) as likes,
                SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as dislikes,
                COUNT(*) as total
            FROM feedback
        """)

        row = cursor.fetchone()
        likes = row['likes'] or 0
        dislikes = row['dislikes'] or 0
        total = row['total'] or 0

        return {
            'likes': likes,
            'dislikes': dislikes,
            'total': total,
            'like_rate': likes / total if total > 0 else 0
        }

    def get_top_liked_songs(self, limit: int = 10) -> List[Dict]:
        """
        Get most liked songs across all sessions

        Args:
            limit: Number of top songs to return

        Returns:
            List of dicts with song info and like count
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                song_id,
                song_name,
                artist_name,
                SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END) as likes,
                SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END) as dislikes,
                COUNT(*) as total_feedback
            FROM feedback
            GROUP BY song_id
            HAVING likes > dislikes
            ORDER BY likes DESC, total_feedback DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_liked_artists(self, mood: Optional[str] = None, min_likes: int = 2) -> List[tuple]:
        """
        Get artists that users consistently like

        Args:
            mood: Filter by mood (e.g., "happy", "sad"). None for all moods.
            min_likes: Minimum number of likes required

        Returns:
            List of tuples: [(artist_name, like_count), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT artist_name, COUNT(*) as like_count
            FROM feedback
            WHERE feedback = 1
        """

        params = []
        if mood:
            query += " AND json_extract(image_analysis, '$.mood') = ?"
            params.append(mood)

        query += """
            GROUP BY artist_name
            HAVING like_count >= ?
            ORDER BY like_count DESC
        """
        params.append(min_likes)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [(row['artist_name'], row['like_count']) for row in rows]

    def get_disliked_artists(self, mood: Optional[str] = None, min_dislikes: int = 2) -> List[tuple]:
        """
        Get artists that users consistently dislike

        Args:
            mood: Filter by mood (e.g., "happy", "sad"). None for all moods.
            min_dislikes: Minimum number of dislikes required

        Returns:
            List of tuples: [(artist_name, dislike_count), ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT artist_name, COUNT(*) as dislike_count
            FROM feedback
            WHERE feedback = -1
        """

        params = []
        if mood:
            query += " AND json_extract(image_analysis, '$.mood') = ?"
            params.append(mood)

        query += """
            GROUP BY artist_name
            HAVING dislike_count >= ?
            ORDER BY dislike_count DESC
        """
        params.append(min_dislikes)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [(row['artist_name'], row['dislike_count']) for row in rows]

    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()


# Global instance
_feedback_store = None

def get_feedback_store() -> FeedbackStore:
    """Get singleton FeedbackStore instance"""
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = FeedbackStore()
    return _feedback_store
