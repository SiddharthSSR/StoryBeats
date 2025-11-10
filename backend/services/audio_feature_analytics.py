#!/usr/bin/env python3
"""
Audio Feature Analytics Module (Phase 1B: Audio Feature Learning)

Analyzes user feedback to learn preferred audio features (energy, valence, etc.)
and provides boosting signals for recommendations.
"""

import json
from typing import Dict, Optional, Tuple
from services.feedback_store import get_feedback_store


class AudioFeatureAnalytics:
    """
    Analyzes feedback data to learn user preferences for audio features

    Computes weighted averages of audio features from liked/disliked songs
    to understand what characteristics users prefer for different moods.
    """

    # Audio features to analyze
    AUDIO_FEATURES = ['energy', 'valence', 'danceability', 'acousticness', 'tempo']

    # Minimum feedback count to consider preferences reliable
    MIN_FEEDBACK_COUNT = 3

    def __init__(self):
        self.feedback_store = get_feedback_store()

    def get_preferred_audio_features(self, mood: Optional[str] = None) -> Dict:
        """
        Get preferred audio features based on user feedback

        Args:
            mood: Filter by mood (e.g., "happy", "sad"). None for all moods.

        Returns:
            Dict with preferred ranges for each audio feature:
            {
                'energy': {'target': 0.7, 'min': 0.5, 'max': 0.9},
                'valence': {'target': 0.8, 'min': 0.6, 'max': 1.0},
                ...
                'metadata': {
                    'liked_count': 10,
                    'disliked_count': 3,
                    'has_enough_data': True
                }
            }
        """
        conn = self.feedback_store._get_connection()
        cursor = conn.cursor()

        # Build query to get feedback with audio features
        query = """
            SELECT audio_features, feedback, weight, signal_type
            FROM feedback
            WHERE audio_features IS NOT NULL
        """

        params = []
        if mood:
            query += " AND json_extract(image_analysis, '$.mood') = ?"
            params.append(mood)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            return {
                'metadata': {
                    'liked_count': 0,
                    'disliked_count': 0,
                    'has_enough_data': False,
                    'message': 'No feedback data with audio features available'
                }
            }

        # Separate liked and disliked songs with their audio features
        liked_features = []
        disliked_features = []

        for row in rows:
            try:
                audio_features = json.loads(row['audio_features'])
                feedback_value = row['feedback']
                weight = row['weight']
                signal_type = row['signal_type']

                # Calculate effective weight (feedback * signal weight)
                effective_weight = weight if feedback_value > 0 else weight

                if feedback_value > 0:  # Liked
                    liked_features.append((audio_features, effective_weight))
                elif feedback_value < 0:  # Disliked
                    disliked_features.append((audio_features, effective_weight))
            except (json.JSONDecodeError, KeyError):
                continue

        liked_count = len(liked_features)
        disliked_count = len(disliked_features)

        # Check if we have enough data
        has_enough_data = liked_count >= self.MIN_FEEDBACK_COUNT

        if not has_enough_data:
            return {
                'metadata': {
                    'liked_count': liked_count,
                    'disliked_count': disliked_count,
                    'has_enough_data': False,
                    'message': f'Need at least {self.MIN_FEEDBACK_COUNT} liked songs with audio features'
                }
            }

        # Compute weighted averages for liked songs
        result = {}

        for feature in self.AUDIO_FEATURES:
            # Compute weighted average for liked songs
            liked_values = []
            liked_weights = []

            for audio_features, weight in liked_features:
                if feature in audio_features and audio_features[feature] is not None:
                    liked_values.append(audio_features[feature])
                    liked_weights.append(weight)

            if not liked_values:
                continue

            # Weighted average
            weighted_sum = sum(v * w for v, w in zip(liked_values, liked_weights))
            total_weight = sum(liked_weights)
            target = weighted_sum / total_weight if total_weight > 0 else sum(liked_values) / len(liked_values)

            # Compute standard deviation for range
            mean = sum(liked_values) / len(liked_values)
            variance = sum((v - mean) ** 2 for v in liked_values) / len(liked_values)
            std_dev = variance ** 0.5

            # Define range as target ± 1 std_dev (or ±0.15 minimum for tight matching)
            range_delta = max(std_dev, 0.15)

            # For tempo, use a larger range (±20 BPM)
            if feature == 'tempo':
                range_delta = max(std_dev, 20)

            # Ensure values stay in valid range
            if feature == 'tempo':
                min_val = max(60, target - range_delta)
                max_val = min(180, target + range_delta)
            else:
                min_val = max(0.0, target - range_delta)
                max_val = min(1.0, target + range_delta)

            result[feature] = {
                'target': round(target, 3),
                'min': round(min_val, 3),
                'max': round(max_val, 3),
                'sample_count': len(liked_values)
            }

        # Add metadata
        result['metadata'] = {
            'liked_count': liked_count,
            'disliked_count': disliked_count,
            'has_enough_data': True,
            'mood': mood if mood else 'all'
        }

        return result

    def calculate_audio_feature_boost(self, track_features: Dict, mood: Optional[str] = None) -> Tuple[float, str]:
        """
        Calculate boost multiplier for a track based on learned audio feature preferences

        Args:
            track_features: Audio features from Spotify for the track
            mood: Current mood context

        Returns:
            Tuple of (boost_multiplier, reason_code)
            - boost_multiplier: 1.0 (neutral), 1.2 (good match), 0.8 (poor match)
            - reason_code: 'perfect_match', 'good_match', 'neutral', 'poor_match', 'no_data'
        """
        if not track_features:
            return 1.0, 'no_features'

        # Get learned preferences
        preferences = self.get_preferred_audio_features(mood)

        if not preferences.get('metadata', {}).get('has_enough_data'):
            return 1.0, 'no_data'

        # Calculate how many features match the preferred range
        matching_features = 0
        total_features = 0
        match_scores = []

        for feature in self.AUDIO_FEATURES:
            if feature not in preferences or feature not in track_features:
                continue

            total_features += 1
            pref = preferences[feature]
            value = track_features[feature]

            if value is None:
                continue

            # Check if value is within preferred range
            if pref['min'] <= value <= pref['max']:
                matching_features += 1

                # Calculate proximity to target (closer = better)
                target = pref['target']
                range_size = pref['max'] - pref['min']

                if range_size > 0:
                    distance = abs(value - target)
                    proximity_score = 1.0 - (distance / range_size)
                    match_scores.append(proximity_score)
                else:
                    match_scores.append(1.0)

        if total_features == 0:
            return 1.0, 'no_data'

        # Calculate match percentage
        match_percentage = matching_features / total_features

        # Calculate average proximity score
        avg_proximity = sum(match_scores) / len(match_scores) if match_scores else 0

        # Determine boost based on match percentage and proximity
        if match_percentage >= 0.8 and avg_proximity >= 0.7:  # 80%+ features match, close to targets
            return 1.25, 'perfect_match'
        elif match_percentage >= 0.6 and avg_proximity >= 0.5:  # 60%+ features match
            return 1.15, 'good_match'
        elif match_percentage >= 0.4:  # 40%+ features match
            return 1.0, 'neutral'
        else:  # Poor match
            return 0.85, 'poor_match'

    def get_feature_learning_stats(self) -> Dict:
        """
        Get statistics about audio feature learning across all moods

        Returns:
            Dict with stats for each mood and overall
        """
        conn = self.feedback_store._get_connection()
        cursor = conn.cursor()

        # Get feedback with audio features grouped by mood
        cursor.execute("""
            SELECT
                json_extract(image_analysis, '$.mood') as mood,
                COUNT(*) as count,
                SUM(CASE WHEN feedback > 0 THEN 1 ELSE 0 END) as liked,
                SUM(CASE WHEN feedback < 0 THEN 1 ELSE 0 END) as disliked
            FROM feedback
            WHERE audio_features IS NOT NULL
            GROUP BY mood
            ORDER BY count DESC
        """)

        mood_stats = []
        for row in cursor.fetchall():
            mood_stats.append({
                'mood': row['mood'],
                'total': row['count'],
                'liked': row['liked'],
                'disliked': row['disliked'],
                'has_enough_data': row['liked'] >= self.MIN_FEEDBACK_COUNT
            })

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN feedback > 0 THEN 1 ELSE 0 END) as liked,
                SUM(CASE WHEN feedback < 0 THEN 1 ELSE 0 END) as disliked
            FROM feedback
            WHERE audio_features IS NOT NULL
        """)

        overall_row = cursor.fetchone()

        return {
            'overall': {
                'total': overall_row['total'],
                'liked': overall_row['liked'],
                'disliked': overall_row['disliked'],
                'has_enough_data': overall_row['liked'] >= self.MIN_FEEDBACK_COUNT
            },
            'by_mood': mood_stats,
            'min_feedback_required': self.MIN_FEEDBACK_COUNT
        }


# Global instance
_audio_feature_analytics = None

def get_audio_feature_analytics() -> AudioFeatureAnalytics:
    """Get singleton AudioFeatureAnalytics instance"""
    global _audio_feature_analytics
    if _audio_feature_analytics is None:
        _audio_feature_analytics = AudioFeatureAnalytics()
    return _audio_feature_analytics
