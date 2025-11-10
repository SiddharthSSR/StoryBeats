# Context-Aware Recommendation System

## Overview

StoryBeats now uses a **context-aware recommendation algorithm** that generates diverse, personalized song recommendations based on the actual content and context of uploaded photos, rather than relying on fixed artist lists.

---

## Problem with Previous Approach

### Artist-Centric Algorithm (Old)

The previous algorithm followed this flow:
```
Photo → LLM Analysis → Mood → Fixed 8 Artists → Top Tracks → Same Songs
```

**Issues:**
- **Repetitive recommendations**: Same songs (Bijuria, UFO, Tu Pyaasa Hai) appeared across different photos
- **Limited diversity**: Only 8 curated artists per mood → small song pool
- **Ignored rich context**: Keywords, themes, description from LLM analysis were unused
- **Poor scalability**: Adding new artists required manual curation
- **Same vibe ≠ Same songs**: Photos with similar moods got identical recommendations

**Example:**
- Photo 1: Sunset at beach (peaceful mood) → Prateek Kuhad, Anuv Jain → Same 5 songs
- Photo 2: Mountain meditation (peaceful mood) → Prateek Kuhad, Anuv Jain → **Same 5 songs**

---

## Solution: Context-Aware Algorithm

### New Flow

```
Photo → LLM Analysis (mood, keywords, themes, description)
      ↓
Build Smart Search Queries ("sunset beach chill", "mountain ambient peaceful")
      ↓
Search Spotify for Contextual Seed Tracks
      ↓
Feed Seeds to Spotify Recommendations API (their trained ML)
      ↓
Filter by Vibe Match + Popularity
      ↓
Score by: Context (30%) + Vibe (40%) + Recency (20%) + Popularity (10%)
      ↓
Apply Diversity Rules (max 2 per artist, language mix)
      ↓
Return Top 30 Songs (5 shown, 25 cached for "load more")
```

---

## How It Works

### 1. Extract Rich Context from LLM Analysis

Instead of just using mood, we now leverage **all** context from the LLM:

```python
# Old approach: Only mood
mood = "peaceful"  # → Same artists every time

# New approach: Full context
mood = "peaceful"
keywords = ["sunset", "beach", "ocean", "relaxation"]
themes = ["nature", "coastal scenery"]
description = "Golden sunset over calm ocean waves with peaceful ambiance"
music_style = "ambient chill"
cultural_vibe = "global"
```

### 2. Build Smart Search Queries

We generate multiple weighted search queries from context:

**Query Priority:**
1. **Music style + mood** (weight: 1.0) - Most specific
   - Example: `"ambient chill peaceful"`

2. **Theme + mood** (weight: 0.9) - Captures photo essence
   - Example: `"nature peaceful music"`, `"coastal scenery peaceful music"`

3. **Keyword combinations** (weight: 0.8) - Specific context
   - Example: `"sunset beach peaceful"`, `"ocean relaxation peaceful"`

4. **Single keyword + mood** (weight: 0.7) - Medium specificity
   - Example: `"sunset peaceful"`, `"beach peaceful"`

5. **Mood + genre fallback** (weight: 0.5) - Generic
   - Example: `"peaceful ambient chill"`

**Language Support:**
- Primary language based on cultural_vibe (Indian → Hindi, Western → English)
- Secondary language queries added for diversity (80% of primary weight)
- Example Hindi query: `"sunset beach peaceful hindi bollywood"`

### 3. Search Spotify for Seed Tracks

For each query (top 8), we search Spotify:
```python
# Example search for "sunset beach peaceful"
results = spotify.search(q="sunset beach peaceful", type='track', limit=10)

# Filter by moderate popularity (>30) and deduplicate
# Tag with search weight for later scoring
```

**Output:** 15-20 diverse seed tracks from contextual searches

### 4. Spotify Recommendations API

We use Spotify's trained ML model to get recommendations:

```python
# Feed top 5 seeds to Spotify Recommendations API
spotify.recommendations(
    seed_tracks=[seed1, seed2, seed3, seed4, seed5],
    target_energy=0.3,
    target_valence=0.5,
    target_danceability=0.3,
    target_acousticness=0.7,
    target_tempo=85,
    # ± 15% tolerance on all features
)
```

**Why this works:**
- Spotify's ML knows similar songs better than we do
- Context-driven seeds → context-relevant recommendations
- Different seeds → different recommendations every time

### 5. Filter & Score Tracks

**Filters:**
- Vibe match score > 0.6 (audio features proximity)
- Popularity: 47-85 (not too obscure, not too mainstream)
- Exclude already returned tracks

**Scoring Formula:**
```
Base Score = (40% × Vibe Match) + (30% × Context Relevance) +
             (20% × Recency) + (10% × Popularity)

Final Score = Base Score × Feedback Multipliers
```

**Feedback Integration (Phase 1A & 1B):**
- **Phase 1A - Artist Boosting:**
  - Liked artist → 1.3× boost
  - Disliked artist → 0.7× penalty

- **Phase 1B - Audio Feature Learning:**
  - Perfect match → 1.25× boost
  - Good match → 1.15× boost
  - Poor match → 0.85× penalty

### 6. Apply Diversity Rules

- **Max 2 tracks per artist** - Prevents artist domination
- **Language mix** - Dynamic based on cultural_vibe (e.g., 3 English + 2 Hindi)
- **Deduplication** - Track by ID to avoid repeats in "load more"

---

## Architecture

### File Structure

```
services/
├── spotify_service.py
│   ├── get_context_aware_recommendations()      # Main entry point
│   ├── _build_contextual_search_queries()       # Query generation
│   ├── _search_contextual_seeds()               # Spotify search
│   ├── _get_artist_fallback_seeds()             # Fallback to curated artists
│   ├── _get_recommendations_from_seeds()        # Spotify Recommendations API
│   ├── _score_contextual_tracks()               # Scoring & filtering
│   └── _generate_all_songs_with_diversity()     # Diversity rules
```

### Key Functions

#### `get_context_aware_recommendations(image_analysis, offset=0, excluded_ids=None)`
**Main entry point** for context-aware recommendations.

**Input:**
- `image_analysis`: Dict with mood, keywords, themes, description, audio features
- `offset`: Pagination offset (unused, kept for backward compatibility)
- `excluded_ids`: List of track IDs to exclude

**Output:**
```python
{
    'songs': [song1, song2, song3, song4, song5],  # First 5 songs
    'all_songs': [song1, ..., song30]              # Full list for caching
}
```

**Error Handling:**
- Falls back to artist-centric algorithm if context search fails
- Graceful degradation if Spotify API errors occur

#### `_build_contextual_search_queries(mood, keywords, themes, description, music_style, cultural_vibe)`
Generates smart search queries from image context.

**Logic:**
1. Determine primary/secondary language from cultural_vibe
2. Build queries from music_style, themes, keyword combinations
3. Add mood + genre fallback queries
4. Add secondary language versions for diversity
5. Deduplicate and sort by weight

**Output:**
```python
[
    {'query': 'ambient chill peaceful', 'language': 'english', 'weight': 1.0},
    {'query': 'nature peaceful music', 'language': 'english', 'weight': 0.9},
    {'query': 'sunset beach peaceful', 'language': 'english', 'weight': 0.8},
    ...
]
```

#### `_search_contextual_seeds(search_queries, cultural_vibe, max_seeds_per_query=3)`
Searches Spotify for seed tracks using contextual queries.

**Process:**
1. Use market='IN' for Indian vibe, 'US' otherwise
2. For each query (top 8), search Spotify with limit=10
3. Filter by popularity > 30
4. Deduplicate by track ID
5. Tag with search weight and query
6. Return top 20 seeds

#### `_get_artist_fallback_seeds(mood, cultural_vibe, max_seeds=10)`
Fallback to curated artists if contextual search fails (<5 seeds found).

**Logic:**
- Get top 3 artists from mood-based lists (English + Hindi)
- Prioritize based on cultural_vibe
- Get top tracks from these artists
- Tag with lower weight (0.6) than contextual seeds

#### `_get_recommendations_from_seeds(seed_tracks, energy, valence, ...)`
Uses Spotify Recommendations API with seed tracks.

**Process:**
1. Sort seeds by weight, take top 5
2. Calculate audio feature ranges (target ± 15%)
3. Call Spotify Recommendations API with 50 limit
4. Include seed tracks themselves (they're contextually relevant)

#### `_score_contextual_tracks(tracks, seed_tracks, image_analysis, excluded_ids)`
Filters and scores tracks.

**Filters:**
- Excluded IDs
- Popularity: 47-85
- Vibe match > 0.6

**Scoring:**
```python
base_score = (
    vibe_score * 0.4 +
    context_score * 0.3 +
    recency_bonus * 0.2 +
    (popularity / 100) * 0.1
)

# Apply feedback multipliers (Phase 1A & 1B)
if artist in liked_artists:
    base_score *= 1.3
if artist in disliked_artists:
    base_score *= 0.7
if audio_features match preferences:
    base_score *= 1.15 to 1.25
```

---

## Benefits

### 1. **Diverse Recommendations**
Different contexts → different seeds → different recommendations

**Example:**
- **Photo 1**: Beach sunset → Seeds: "ocean sunset chill" → Songs: Tycho, Bonobo, Ólafur Arnalds
- **Photo 2**: Mountain meditation → Seeds: "mountain ambient peaceful" → Songs: Nils Frahm, Max Richter, Hammock
- **Result**: Completely different songs despite same "peaceful" mood!

### 2. **Leverages Spotify's ML**
We don't need to know which songs are similar - Spotify does that for us!

### 3. **Scalable**
No manual artist curation needed. System adapts to new music automatically.

### 4. **Context-Rich**
Uses **all** information from LLM analysis:
- ✅ Mood
- ✅ Keywords
- ✅ Themes
- ✅ Description
- ✅ Music style
- ✅ Cultural vibe
- ✅ Audio features

Old algorithm used only mood and audio features.

### 5. **Feedback Integration**
Seamlessly integrates with Phase 1A (artist boosting) and Phase 1B (audio feature learning).

### 6. **Graceful Fallback**
If contextual search fails, falls back to curated artists - no complete failures.

---

## Comparison: Old vs New

| Aspect | Artist-Centric (Old) | Context-Aware (New) |
|--------|---------------------|---------------------|
| **Diversity** | Low (same artists → same songs) | High (different contexts → different songs) |
| **Context Usage** | Mood only | Mood + keywords + themes + description + music_style |
| **Scalability** | Manual artist curation | Automatic via Spotify search & recommendations |
| **Repetition** | High (Bijuria, UFO, Tu Pyaasa Hai) | Low (diverse seed selection) |
| **Spotify API Usage** | Top Tracks only | Search + Recommendations API (trained ML) |
| **Fallback** | None (relies on fixed artists) | Artist-based seeds if context fails |
| **Scoring Weights** | Vibe (50%) + Recency (30%) + Popularity (20%) | Context (30%) + Vibe (40%) + Recency (20%) + Popularity (10%) |
| **Feedback Integration** | ✅ Phase 1A & 1B | ✅ Phase 1A & 1B |

---

## Testing Guidelines

### Test Scenarios

1. **Same Mood, Different Context**
   - Upload beach photo (peaceful)
   - Upload forest photo (peaceful)
   - Verify: Different songs (not just Prateek Kuhad every time)

2. **Cultural Vibe Switching**
   - Upload Diwali celebration (Indian vibe)
   - Upload NYC skyline (Western vibe)
   - Verify: Language mix adjusts (more Hindi for Diwali, more English for NYC)

3. **Keyword Diversity**
   - Upload sunset photo (keywords: sunset, ocean, beach)
   - Upload mountain photo (keywords: mountain, hiking, adventure)
   - Verify: Completely different song selections

4. **Fallback Testing**
   - Test with generic photos (no strong keywords/themes)
   - Verify: System falls back to artist-based seeds gracefully

5. **Load More Diversity**
   - Upload photo, get 5 songs
   - Click "Load More" 3-4 times
   - Verify: No duplicate songs, maintains diversity

### Expected Behavior

**Good Output:**
- 5 unique songs per request
- Max 2 songs from same artist
- Songs match photo vibe and context
- No repeated songs across multiple loads
- Different photos → different songs (even same mood)

**Red Flags:**
- Same songs appearing for different photos
- All songs from 1-2 artists
- Songs don't match photo context at all
- Duplicates in "load more"

---

## Performance

### Optimization Features

1. **Batch API Calls**
   - Audio features fetched in batches of 50
   - Parallel processing where possible

2. **Caching**
   - Artist ID cache (prevents repeated lookups)
   - Top tracks cache (1 hour TTL)
   - Albums cache (30 min TTL)
   - Session-level song caching (up to 30 songs)

3. **Request Efficiency**
   - Max 8 contextual search queries
   - Top 5 seeds to Recommendations API
   - 50 recommendations per request

### Typical Performance

- **Initial recommendation**: 3-5 seconds
- **Load more (cached)**: <100ms (instant)
- **Load more (re-run)**: 3-5 seconds

---

## Configuration

### Tunable Parameters

Located in `spotify_service.py`:

```python
# Scoring weights (must sum to 1.0)
CONTEXT_WEIGHT = 0.3
VIBE_WEIGHT = 0.4
RECENCY_WEIGHT = 0.2
POPULARITY_WEIGHT = 0.1

# Filters
VIBE_THRESHOLD = 0.6  # Relaxed from 0.75 for more diversity
POPULARITY_MIN = 47
POPULARITY_MAX = 85

# Diversity rules
MAX_TRACKS_PER_ARTIST = 2

# Query generation
MAX_SEARCH_QUERIES = 10
MAX_SEEDS_PER_QUERY = 3
TOTAL_SEEDS_LIMIT = 20

# Recommendations
SPOTIFY_REC_LIMIT = 50
AUDIO_TOLERANCE = 0.15  # ±15% for all audio features
TEMPO_TOLERANCE = 20    # ±20 BPM
```

### Adjusting for More/Less Diversity

**More Diversity:**
- Increase `MAX_SEARCH_QUERIES` (more varied seeds)
- Decrease `VIBE_THRESHOLD` (accept wider vibe matches)
- Increase `MAX_SEEDS_PER_QUERY` (more seeds per search)

**More Accuracy:**
- Decrease `VIBE_THRESHOLD` to 0.75 (stricter vibe matching)
- Decrease `AUDIO_TOLERANCE` to 0.10 (tighter audio feature matching)
- Increase `VIBE_WEIGHT` to 0.5, decrease `CONTEXT_WEIGHT` to 0.2

---

## Migration Notes

### Backward Compatibility

- Old `get_song_recommendations()` function **still exists** for backward compatibility
- New system is a **drop-in replacement** - same input/output format
- Fallback to old algorithm if new one fails (exception handling)

### Breaking Changes

None! The API contract remains identical:
```python
# Both return the same format
result = spotify_service.get_song_recommendations(analysis)
result = spotify_service.get_context_aware_recommendations(analysis)

# Both return:
# {
#     'songs': [song1, ..., song5],
#     'all_songs': [song1, ..., song30]
# }
```

---

## Future Improvements

### Potential Enhancements

1. **Time-of-Day Context**
   - Morning photos → upbeat songs
   - Night photos → mellow songs

2. **Seasonal Context**
   - Summer → tropical, upbeat
   - Winter → cozy, acoustic

3. **Activity Recognition**
   - Workout photos → high energy
   - Reading photos → instrumental, ambient

4. **Collaborative Filtering**
   - "Users who liked this photo also liked..."
   - Cross-user pattern learning

5. **Genre Mixing**
   - Detect when photo suggests genre fusion
   - Example: Indian + Electronic → Nucleya, Ritviz

6. **Dynamic Weight Tuning**
   - A/B test different scoring weights
   - Learn optimal weights from user feedback

---

## Troubleshooting

### Common Issues

**Issue: Getting same songs for different photos**
- Check: Are keywords/themes too generic? ("vibes", "mood" → ignored)
- Solution: Improve LLM prompt to generate specific keywords

**Issue: No recommendations returned**
- Check: Logs for Spotify API errors
- Fallback: Should automatically use artist-centric algorithm
- Debug: Verify search queries being generated

**Issue: Poor vibe matching**
- Check: Audio features from LLM analysis (too extreme?)
- Solution: Adjust `VIBE_THRESHOLD` or `AUDIO_TOLERANCE`

**Issue: Too many songs from one artist**
- Check: `MAX_TRACKS_PER_ARTIST` setting
- Solution: Decrease from 2 to 1 if needed

---

## Conclusion

The **context-aware recommendation system** solves the core problem of repetitive recommendations by leveraging the full richness of LLM image analysis and Spotify's trained ML models. Instead of relying on fixed artist lists, we now generate diverse, contextual search queries that lead to unique seed tracks, which then feed into Spotify's Recommendations API for intelligent song discovery.

**Key Takeaway**: Different contexts → different seeds → different recommendations → happy users! 🎵

---

**Last Updated**: 2025-01-11
**Version**: 2.0 (Context-Aware Algorithm)
**Authors**: StoryBeats Team
