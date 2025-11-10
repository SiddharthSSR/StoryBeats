# Recommendation Improvement Roadmap

**Project**: StoryBeats
**Goal**: Continuously improve song recommendations using user feedback
**Status**: Phase 1A Complete ✅

---

## Overview

This document outlines the strategy for improving StoryBeats recommendations using feedback data. Each phase builds on the previous one, creating an increasingly intelligent recommendation system.

### Current State
- ✅ **Phase 1A Complete**: Artist Preference Boosting
  - 30% boost for liked artists
  - 30% penalty for disliked artists
  - Mood-aware preferences
  - Using 47 existing feedback entries

---

## Phase 1B: Audio Feature Learning

**Status**: 🔴 Not Started
**Effort**: 6-8 hours
**Impact**: ⭐⭐⭐⭐⭐ Very High
**Priority**: HIGH - Next to implement

### Objective
Learn what audio characteristics (energy, valence, tempo, etc.) users actually prefer for each mood, rather than using fixed parameters.

### Current Problem
Algorithm uses hardcoded assumptions:
- Happy → Energy: 0.7, Valence: 0.8
- Sad → Energy: 0.3, Valence: 0.3

What if users actually prefer different values?

### Solution
Analyze liked songs to discover optimal audio features:

```python
# For mood="happy", analyze all liked songs:
liked_songs_happy = get_liked_songs(mood="happy")
audio_features = spotify.get_audio_features(liked_songs_happy)

# Calculate optimal ranges
optimal_energy = mean(audio_features.energy) ± std
optimal_valence = mean(audio_features.valence) ± std
optimal_tempo = mean(audio_features.tempo) ± std

# Use learned parameters instead of hardcoded ones
search_with_learned_features(optimal_energy, optimal_valence, ...)
```

### Implementation Steps
1. Add `get_liked_songs_by_mood()` to feedback_store.py
2. Create `learn_audio_preferences()` in new service
3. Cache learned preferences per mood
4. Update spotify_service to use learned params
5. Fall back to defaults if insufficient data (< 5 likes)

### Database Changes
New table:
```sql
CREATE TABLE learned_preferences (
    mood TEXT PRIMARY KEY,
    optimal_energy REAL,
    optimal_valence REAL,
    optimal_danceability REAL,
    optimal_tempo REAL,
    optimal_acousticness REAL,
    sample_size INTEGER,
    last_updated TIMESTAMP
)
```

### Success Metrics
- Like rate increases by 10-15%
- Fewer "wrong mood" complaints
- Algorithm adapts to user preferences over time

### Files to Modify
- `backend/services/feedback_store.py` - Add song queries
- `backend/services/audio_learning.py` - NEW file
- `backend/services/spotify_service.py` - Use learned params
- `backend/tests/test_audio_learning.py` - NEW test file

---

## Phase 2: Implicit Feedback Signals

**Status**: 🔴 Not Started
**Effort**: 2-3 hours
**Impact**: ⭐⭐⭐⭐ High
**Priority**: MEDIUM - Easy win

### Objective
Capture implicit signals beyond explicit like/dislike to gather 10x more data.

### Signals to Track

#### High Value Signals (Strong Positive)
1. **"Open in Spotify" clicks** - User wants to save/play song
2. **Audio preview plays** - User is interested enough to listen
3. **Preview completion** - Listened to full 30s preview

#### Medium Value Signals (Moderate Positive)
4. **"Load More" clicks** - User wants more like this
5. **Time on results page** - Engagement with recommendations
6. **Mouse hover on song card** - Mild interest

#### Negative Signals
7. **Immediate "Upload Another Photo"** - Rejected all songs
8. **Quick exit** - Left page within 5 seconds

### Implementation

#### Frontend Changes
```javascript
// Track Spotify clicks
const handleSpotifyClick = (song) => {
  trackImplicitFeedback(song, 'spotify_click', 2) // weight: 2
  window.open(song.spotify_url)
}

// Track preview plays
const handlePreviewPlay = (song) => {
  trackImplicitFeedback(song, 'preview_play', 1) // weight: 1
}

// Track preview completion
<audio onEnded={() => trackImplicitFeedback(song, 'preview_complete', 1.5)}>

// Track load more
const handleLoadMore = () => {
  trackImplicitFeedback(null, 'load_more', 0.5) // session-level signal
  fetchMoreSongs()
}
```

#### Backend Changes
```python
# New endpoint
@app.route('/api/feedback/implicit', methods=['POST'])
def implicit_feedback():
    data = request.json
    feedback_store.add_implicit_feedback(
        session_id=data['session_id'],
        song_id=data.get('song_id'),
        signal_type=data['signal_type'],  # 'spotify_click', 'preview_play', etc.
        weight=data['weight']
    )
```

### Database Schema
Add to feedback table:
```sql
ALTER TABLE feedback ADD COLUMN signal_type TEXT DEFAULT 'explicit';
ALTER TABLE feedback ADD COLUMN weight REAL DEFAULT 1.0;

-- feedback values:
-- 2.0 = spotify_click (strong positive)
-- 1.5 = preview_complete (strong interest)
-- 1.0 = like / preview_play
-- -1.0 = dislike
```

### Files to Modify
- `frontend/src/components/SongResults.jsx` - Add tracking
- `frontend/src/App.jsx` - Add tracking handlers
- `backend/app.py` - Add implicit feedback endpoint
- `backend/services/feedback_store.py` - Support implicit signals

### Success Metrics
- 10x increase in feedback data points
- Better understanding of user behavior
- More granular preference learning

---

## Phase 3: Feedback Analytics Dashboard

**Status**: 🔴 Not Started
**Effort**: 4-5 hours
**Impact**: ⭐⭐⭐ Medium
**Priority**: MEDIUM - Insight

### Objective
Build analytics to understand what's working and what's not.

### Insights to Track

#### By Mood
```json
{
  "mood": "happy",
  "total_recommendations": 1250,
  "like_rate": 0.28,
  "top_liked_artists": ["Diljit Dosanjh", "Tame Impala"],
  "top_disliked_artists": ["Artist X"],
  "optimal_audio_features": {
    "energy": 0.75,
    "valence": 0.82,
    "tempo": 128
  }
}
```

#### Problem Areas
```json
{
  "low_performing_moods": [
    {"mood": "melancholic", "like_rate": 0.15}
  ],
  "frequently_disliked_artists": [
    {"artist": "X", "dislikes": 15, "context": "wrong for mood"}
  ],
  "underutilized_features": ["acousticness"]
}
```

#### Time Patterns
```json
{
  "by_time_of_day": {
    "morning": {"preferred_energy": 0.6, "top_moods": ["energetic"]},
    "afternoon": {"preferred_energy": 0.7},
    "evening": {"preferred_energy": 0.5},
    "night": {"preferred_energy": 0.3, "top_moods": ["calm", "romantic"]}
  }
}
```

### Implementation

#### Backend Endpoints
```python
# Overall stats
GET /api/feedback/insights

# Mood-specific
GET /api/feedback/insights/mood/{mood}

# Time-based
GET /api/feedback/insights/time-of-day

# Problem detection
GET /api/feedback/insights/problems
```

#### New Methods in feedback_store.py
```python
def get_mood_analytics(self, mood):
    """Get comprehensive analytics for a mood"""

def get_time_of_day_preferences(self):
    """Analyze preferences by time of day"""

def detect_problem_areas(self):
    """Find low-performing moods, artists, etc."""
```

### Files to Create/Modify
- `backend/services/analytics.py` - NEW analytics service
- `backend/app.py` - Add analytics endpoints
- `backend/tests/test_analytics.py` - NEW test file

### Success Metrics
- Clear visibility into what's working
- Data-driven decisions for improvements
- Identify problem areas proactively

---

## Phase 4: Multi-Dimensional Feedback

**Status**: 🔴 Not Started
**Effort**: 8-10 hours
**Impact**: ⭐⭐⭐⭐ High
**Priority**: LOW - Wait for more data

### Objective
Collect richer feedback beyond binary like/dislike.

### Enhanced Feedback Options

#### Option 1: Star Ratings
```
⭐ ⭐ ⭐ ⭐ ⭐  (5 stars - love it!)
⭐ ⭐ ⭐ ⭐ ☆  (4 stars - like it)
⭐ ⭐ ⭐ ☆ ☆  (3 stars - neutral)
⭐ ⭐ ☆ ☆ ☆  (2 stars - not great)
⭐ ☆ ☆ ☆ ☆  (1 star - dislike)
```

#### Option 2: Feedback Reasons
After dislike, ask why:
- ❌ Wrong mood
- 🐌 Too slow
- ⚡ Too fast
- 🎤 Don't like artist
- 🎵 Wrong genre
- 📻 Overplayed

After like, ask what worked:
- ✅ Perfect vibe
- 🎵 Love the artist
- 🎶 Great melody
- 💯 Exactly what I wanted

#### Option 3: Mood Correction
"This song feels more **energetic** than **calm**"

User can correct the mood classification, improving future recommendations.

### UI Design
```jsx
<FeedbackButtons>
  {/* Initial feedback */}
  <button onClick={() => setShowReasons(true)}>👍</button>
  <button onClick={() => setShowReasons(true)}>👎</button>

  {/* After feedback, show reasons */}
  {showReasons && feedback === -1 && (
    <FeedbackReasons>
      <Tag onClick={() => addReason('wrong_mood')}>Wrong mood</Tag>
      <Tag onClick={() => addReason('too_slow')}>Too slow</Tag>
      <Tag onClick={() => addReason('dont_like_artist')}>Don't like artist</Tag>
    </FeedbackReasons>
  )}

  {showReasons && feedback === 1 && (
    <FeedbackReasons>
      <Tag onClick={() => addReason('perfect_vibe')}>Perfect vibe</Tag>
      <Tag onClick={() => addReason('love_artist')}>Love the artist</Tag>
      <Tag onClick={() => addReason('great_melody')}>Great melody</Tag>
    </FeedbackReasons>
  )}
</FeedbackButtons>
```

### Database Schema
```sql
ALTER TABLE feedback ADD COLUMN rating INTEGER; -- 1-5 stars
ALTER TABLE feedback ADD COLUMN reasons TEXT; -- JSON array
ALTER TABLE feedback ADD COLUMN corrected_mood TEXT; -- If user corrects
```

### Files to Modify
- `frontend/src/components/SongResults.jsx` - Enhanced UI
- `frontend/src/components/SongResults.css` - New styles
- `backend/services/feedback_store.py` - Store reasons
- `backend/app.py` - Update feedback endpoint

### Success Metrics
- Understand WHY users like/dislike songs
- Identify specific improvement areas
- Better data for ML models later

---

## Phase 5: Adaptive Language Diversity

**Status**: 🔴 Not Started
**Effort**: 4-6 hours
**Impact**: ⭐⭐⭐ Medium
**Priority**: LOW

### Objective
Learn optimal English/Hindi ratio per user instead of fixed 40/60 split.

### Current Problem
Everyone gets 40% Hindi, 60% English regardless of preference.

### Solution
Track language preferences per user/session:

```python
# Analyze feedback by language
hindi_likes = count_likes(language='hindi')
english_likes = count_likes(language='english')

# Adjust ratio
if hindi_likes > english_likes * 1.5:
    hindi_ratio = 0.7  # User prefers Hindi
elif english_likes > hindi_likes * 1.5:
    hindi_ratio = 0.2  # User prefers English
else:
    hindi_ratio = 0.4  # Balanced
```

### Implementation
```python
def get_preferred_language_mix(self, session_id=None):
    """
    Returns optimal (english_count, hindi_count) based on feedback

    If session_id provided: use session-level preferences
    Otherwise: use global preferences
    """
```

### Files to Modify
- `backend/services/feedback_store.py` - Language analytics
- `backend/services/spotify_service.py` - Use adaptive mix

### Success Metrics
- Users get more songs in preferred languages
- Increased like rate for language-specific preferences

---

## Phase 6: Collaborative Filtering

**Status**: 🔴 Not Started
**Effort**: 2-3 weeks
**Impact**: ⭐⭐⭐⭐⭐ Very High
**Priority**: LOW - Advanced feature

### Objective
Find users with similar taste and recommend songs that worked for them.

### How It Works

#### 1. User Similarity
```python
# User A likes: Radiohead, Tame Impala, Diljit Dosanjh
# User B likes: Radiohead, Tame Impala, Arctic Monkeys

# Similarity score: 0.67 (2 out of 3 artists match)
```

#### 2. Recommendation
```python
# For User A with mood="melancholic":
# Find similar users (similarity > 0.6)
# See what they liked for "melancholic"
# Recommend: Arctic Monkeys (User B loved it)
```

### Algorithm
```python
def find_similar_users(current_user_likes, threshold=0.6):
    """
    Find users with similar taste using Jaccard similarity
    """
    for user in all_users:
        similarity = jaccard(current_user_likes, user.likes)
        if similarity > threshold:
            yield user, similarity

def get_collaborative_recommendations(mood, similar_users):
    """
    Get songs liked by similar users for this mood
    """
    songs = []
    for user, similarity in similar_users:
        user_likes = get_likes(user, mood=mood)
        songs.extend([(song, similarity) for song in user_likes])

    # Weight by similarity and frequency
    return rank_by_popularity_and_similarity(songs)
```

### Implementation Phases

#### 6.1: User Taste Profiles
Build profiles based on liked artists, genres, audio features.

#### 6.2: Similarity Calculation
Calculate pairwise similarity between users.

#### 6.3: Recommendation Blending
Blend collaborative recommendations with algorithmic ones:
- 70% algorithmic (vibe matching)
- 30% collaborative (similar users)

### Files to Create
- `backend/services/collaborative_filtering.py` - NEW
- `backend/tests/test_collaborative.py` - NEW

### Success Metrics
- Discover songs algorithmic matching misses
- Increased diversity in recommendations
- Higher like rate for collaborative suggestions

---

## Phase 7: Machine Learning Model

**Status**: 🔴 Not Started
**Effort**: 1-2 months
**Impact**: ⭐⭐⭐⭐⭐ Very High
**Priority**: FUTURE

### Objective
Train ML model to predict like/dislike probability before showing songs.

### Approach

#### Features
- Audio features (energy, valence, etc.)
- Artist popularity
- Genre
- Mood
- Time of day
- User history
- Collaborative signals

#### Model
- Gradient Boosting (XGBoost/LightGBM)
- Input: Song + Context features
- Output: Probability of like (0.0 - 1.0)

#### Training
```python
# Collect training data
X = [song_features + context_features]
y = [1 if liked, 0 if disliked]

# Train model
model = XGBClassifier()
model.fit(X, y)

# Predict
prob = model.predict_proba(new_song)
if prob > 0.7:
    recommend()
```

### Requirements
- Minimum 500+ feedback entries
- Feature engineering pipeline
- Model retraining schedule (weekly)
- A/B testing framework

---

## Recommended Implementation Order

### 🚀 Sprint 1 (Week 1-2): Quick Wins
1. ✅ **Phase 1A**: Artist Boosting (DONE)
2. **Phase 2**: Implicit Feedback (2-3 hours)
   - Immediate data collection
   - High ROI, low effort

### 📊 Sprint 2 (Week 3-4): Learning & Insights
3. **Phase 3**: Analytics Dashboard (4-5 hours)
   - Understand current performance
   - Data-driven decisions

4. **Phase 1B**: Audio Feature Learning (6-8 hours)
   - Adaptive algorithm
   - Major improvement

### 🎯 Sprint 3 (Month 2): Enhanced Feedback
5. **Phase 4**: Multi-Dimensional Feedback (8-10 hours)
   - Better data quality
   - Understand user intent

6. **Phase 5**: Adaptive Diversity (4-6 hours)
   - Personalized language mix

### 🧠 Sprint 4+ (Month 3+): Advanced
7. **Phase 6**: Collaborative Filtering (2-3 weeks)
   - Requires critical mass of users
   - High complexity, high value

8. **Phase 7**: ML Model (1-2 months)
   - Requires 500+ feedback entries
   - Maximum intelligence

---

## Success Metrics

### Key Performance Indicators

1. **Like Rate**
   - Current: ~23%
   - Target after Phase 1B: 35%
   - Target after Phase 6: 50%+

2. **Engagement**
   - "Load More" click rate
   - Preview play rate
   - Spotify open rate

3. **Retention**
   - Users returning to use app again
   - Multiple uploads per session

4. **Data Collection**
   - Feedback entries per day
   - Implicit signals captured

### Phase-Specific Targets

| Phase | Metric | Target |
|-------|--------|--------|
| 1A (Done) | Like rate | +5% |
| 1B | Like rate | +10-15% |
| 2 | Data points | 10x increase |
| 3 | Insights visibility | 100% |
| 4 | Feedback quality | Rich context |
| 5 | Language satisfaction | +8% |
| 6 | Discovery rate | +20% |
| 7 | Overall like rate | 50%+ |

---

## Dependencies & Prerequisites

### Phase Dependencies
- **Phase 1B** requires Phase 1A (artist boosting data)
- **Phase 6** requires Phases 1-4 (critical mass of data)
- **Phase 7** requires Phases 1-6 (500+ feedback entries)

### Technical Prerequisites
- SQLite database (✅ have)
- User session tracking (✅ have)
- Spotify API access (✅ have)
- Frontend-backend communication (✅ have)

### Data Prerequisites
- **Phase 1B**: 20+ likes per mood (partially met)
- **Phase 6**: 100+ total users (future)
- **Phase 7**: 500+ feedback entries (future)

---

## Risks & Mitigations

### Risk 1: Insufficient Data
**Problem**: Not enough feedback for learning
**Mitigation**:
- Start with implicit signals (Phase 2)
- Encourage feedback with UI/UX improvements
- Fall back to defaults when data insufficient

### Risk 2: Overfitting to Feedback
**Problem**: Algorithm only recommends "safe" songs
**Mitigation**:
- Maintain 20% exploration (random/diverse picks)
- Balance exploitation vs exploration
- Regular diversity checks

### Risk 3: Cold Start Problem
**Problem**: New users have no history
**Mitigation**:
- Use global preferences for first session
- Quick onboarding (ask music preferences)
- Learn rapidly from first few feedbacks

---

## Open Questions

1. **Privacy**: Should we track users across sessions?
   - Currently: Session-based (anonymous)
   - Future: User accounts for personalization?

2. **Exploration vs Exploitation**: How much to stick with safe choices vs try new things?
   - Current: 100% exploitation
   - Proposed: 80/20 split

3. **Feedback Fatigue**: Will users get tired of giving feedback?
   - Solution: Make it effortless (one-click)
   - Gamification? (Badges for feedback milestones)

4. **Multi-User Sessions**: What if multiple people use same device?
   - Current: Session-based, no issue
   - Future with accounts: "Who's listening?" prompt

---

## Notes & Observations

### Current Feedback Patterns (47 entries)
- Like rate: 23.4% (11 likes, 36 dislikes)
- Suggests recommendations need improvement
- Phase 1B should help significantly

### Most Valuable Next Step
**Phase 2 (Implicit Feedback)** + **Phase 1B (Audio Learning)**
- Immediate data boost
- Adaptive algorithm
- High impact, moderate effort

---

## Document Changelog

- **2025-01-09**: Document created with 7 phases outlined
- **Phase 1A**: Completed and deployed (artist boosting)

---

## References

- Original feedback usage plan: `/tmp/feedback_usage_plan.md`
- Implementation summary: `/tmp/feedback_implementation_summary.md`
- Backend README: `backend/README.md`
- Feedback database schema: `backend/services/feedback_store.py`
