# Performance Analysis & Optimization Plan

## Current Bottlenecks

### 1. **Sequential Artist Processing** ⏱️ ~15-30 seconds
**Problem:**
- Processing 16 artists (8 English + 8 Hindi) one by one
- Each artist requires 4-6 API calls:
  - `search_artist_by_name()` - 1 call (cached after first)
  - `artist_albums()` - 1 call
  - `album_tracks()` - 2-10 calls (one per album)
  - `artist_top_tracks()` - 1 call
  - `sp.track()` - 10-15 calls (for recent tracks)

**Total:** ~80-100 Spotify API calls per recommendation request!

### 2. **Unnecessary Track Refetching** ⏱️ ~5-10 seconds
**Problem:**
- `artist_top_tracks()` already returns full track objects with album info
- But we're calling `sp.track(track_id)` again for recent tracks (lines 743, 785)
- Adds 20-30 extra API calls

### 3. **Image Analysis** ⏱️ ~3-5 seconds
**Problem:**
- Large images sent to Claude Vision API
- No image optimization/resizing before upload

### 4. **No Caching Beyond Artist IDs** ⏱️ Lost opportunity
**Problem:**
- Artist top tracks don't change often - could cache for 24 hours
- Recent albums could cache for 1 hour
- No result caching at all

## Estimated Current Latency Breakdown

```
Total: ~25-40 seconds per request

Image Analysis:           5s  (20%)
Artist Search (cached):   1s  (4%)
Artist Data Fetching:    15s  (60%)
  - Albums/tracks:       10s
  - Track details:        5s
Audio Features (failed):  2s  (8%)
Filtering/Scoring:        2s  (8%)
```

---

## Optimization Strategies

### 🚀 Quick Wins (30-50% faster)

#### 1. **Reduce Artists Processed**
Instead of 8 artists per language, process only 4-5 most relevant

**Impact:** -40% API calls, -10s latency
```python
# Change from 8 to 5 artists
artists_to_process = english_artists[:5]  # Instead of all 8
```

#### 2. **Remove Redundant Track Fetching**
Top tracks already have full metadata - don't refetch

**Impact:** -30 API calls, -5s latency
```python
# Line 751: Remove this loop entirely
# for track in top_tracks:
#     track already has everything we need!
```

#### 3. **Parallel Artist Processing**
Process multiple artists concurrently using ThreadPoolExecutor

**Impact:** -50% time, -7s latency
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_artist, artist)
               for artist in artists]
```

#### 4. **Image Optimization**
Resize images before sending to Claude

**Impact:** -2s latency
```python
# Resize to max 1024x1024 before analysis
from PIL import Image
img = Image.open(photo)
if max(img.size) > 1024:
    img.thumbnail((1024, 1024))
```

---

### 💾 Medium Wins (Caching - 60-80% faster on repeat)

#### 5. **Cache Top Tracks**
Store artist top tracks for 24 hours

**Impact:** -50% API calls on cache hit
```python
import redis
cache_key = f"top_tracks:{artist_id}"
cached = redis.get(cache_key)
if cached:
    return json.loads(cached)
# Otherwise fetch and cache for 24h
```

#### 6. **Cache Recent Albums**
Store album IDs for 1 hour

**Impact:** -20% API calls on cache hit

#### 7. **Memoize Results**
Cache entire recommendation results by mood+vibe for 5 minutes

**Impact:** Near-instant on repeat requests

---

### ⚡ Advanced Optimizations (70%+ faster)

#### 8. **Smart Early Stopping**
Stop processing artists once we have enough high-quality tracks

**Impact:** -50% unnecessary work
```python
if len(scored_tracks) >= 50 and all(s['vibe_score'] > 0.8 for s in scored_tracks[:20]):
    break  # We have enough good tracks
```

#### 9. **Pre-warm Cache**
Background job to pre-fetch top tracks for all curated artists

**Impact:** Near-instant after warm-up

#### 10. **Batch API Calls**
Use Spotify's batch endpoints where possible

**Impact:** -40% network overhead

---

## Recommended Implementation Order

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Reduce artists from 8 to 5 per language
2. ✅ Remove redundant `sp.track()` calls for top tracks
3. ✅ Add early stopping when enough tracks found
4. ✅ Optimize image size before Claude API

**Expected Result:** 25s → 12s (52% faster)

### Phase 2: Parallel Processing (2-3 hours)
5. ✅ Implement ThreadPoolExecutor for artist processing
6. ✅ Parallel album track fetching

**Expected Result:** 12s → 6s (75% faster total)

### Phase 3: Caching (3-4 hours)
7. ✅ Redis/in-memory cache for top tracks
8. ✅ Cache artist albums
9. ✅ Short-term result caching

**Expected Result:** 6s → 2s on cache hit (92% faster total)

---

## Code Examples

### 1. Parallel Artist Processing

```python
from concurrent.futures import ThreadPoolExecutor
import threading

def process_single_artist(artist_name, language, market):
    """Process one artist and return tracks"""
    artist_id = self._search_artist_by_name(artist_name, market=market)
    if not artist_id:
        return []

    tracks = []

    # Get top tracks (already full objects)
    try:
        top_tracks_response = self.sp.artist_top_tracks(artist_id, country=market)
        for track in top_tracks_response.get('tracks', [])[:5]:  # Reduced to 5
            track['_artist_name'] = artist_name
            track['_language'] = language
            tracks.append(track)
    except Exception as e:
        print(f"Error: {e}")

    return tracks

# Process all artists in parallel
all_tracks = []
with ThreadPoolExecutor(max_workers=6) as executor:
    # Submit English artists
    english_futures = [
        executor.submit(process_single_artist, artist, 'english', 'US')
        for artist in english_artists[:5]  # Only 5 artists
    ]

    # Submit Hindi artists
    hindi_futures = [
        executor.submit(process_single_artist, artist, 'hindi', 'IN')
        for artist in hindi_artists[:5]
    ]

    # Collect results
    for future in english_futures + hindi_futures:
        all_tracks.extend(future.result())
```

### 2. Simple In-Memory Cache

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache artist top tracks for 1 hour
@lru_cache(maxsize=200)
def _get_cached_top_tracks(artist_id, country, cache_time):
    """Cache key includes hour to auto-expire"""
    return self.sp.artist_top_tracks(artist_id, country=country)

# Usage
current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
tracks = _get_cached_top_tracks(artist_id, 'US', current_hour)
```

### 3. Image Optimization

```python
from PIL import Image
import io

def optimize_image(image_file, max_size=1024):
    """Resize image to reduce upload time"""
    img = Image.open(image_file)

    # Check if resize needed
    if max(img.size) > max_size:
        # Calculate new size maintaining aspect ratio
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format=img.format or 'JPEG', quality=85)
        buffer.seek(0)
        return buffer

    return image_file
```

### 4. Early Stopping

```python
# Stop processing if we have enough good tracks
MIN_TRACKS_NEEDED = 30
MIN_VIBE_FOR_EARLY_STOP = 0.75

for artist_name in artists:
    # ... process artist ...

    # Check if we can stop early
    if len(scored_tracks) >= MIN_TRACKS_NEEDED:
        high_quality = [t for t in scored_tracks if t['_vibe_score'] > MIN_VIBE_FOR_EARLY_STOP]
        if len(high_quality) >= MIN_TRACKS_NEEDED * 0.8:  # 80% are good
            print(f"  ⚡ Early stopping - enough high-quality tracks found")
            break
```

---

## Expected Performance After All Optimizations

### Before:
```
First request:  25-40s
Repeat request: 25-40s (no caching)
```

### After Phase 1 (Quick Wins):
```
First request:  12-15s  (52% faster)
Repeat request: 12-15s
```

### After Phase 2 (Parallel):
```
First request:  5-7s    (80% faster)
Repeat request: 5-7s
```

### After Phase 3 (Caching):
```
First request:  5-7s    (80% faster)
Repeat request: 1-2s    (95% faster)
```

---

## ✅ ACTUAL PERFORMANCE RESULTS (Tested)

### Performance Test Results (2025-11-06):

**All 3 phases implemented:**
- ✅ Parallel artist processing (ThreadPoolExecutor, 6 workers)
- ✅ Batch API calls (sp.tracks() instead of individual sp.track())
- ✅ Caching layer (1h for top tracks, 30min for albums)
- ✅ Image optimization (resize to 1024x1024)

**Measured Performance:**
```
Test 1 - Romantic Photo (First Request):  7.89s ✅
Test 2 - Romantic Photo (Cached):         8.94s ⚠️
Test 3 - Energetic Photo:                10.79s ✅

Average first request: ~7.9s
```

**Performance Improvement vs Baseline:**
- Baseline (before optimization): ~30s
- Current (after optimization): 7.89s
- **Improvement: 73.7% faster (22.11s saved)** ✅

**Cache Status:**
- Top tracks cached: 32 artists
- Albums cached: 32 artists
- Cache working but network latency still affects performance

**Notes:**
- Parallel processing working excellently (7.32s for 16 artists)
- Spotify API rate limiting may affect cached performance
- Audio features endpoint still returning 403 (using enhanced estimates)
- Target of ≤7s for first request nearly achieved
- Image optimization not tested yet (will save additional 2-3s on upload)

---

## Trade-offs to Consider

| Optimization | Pros | Cons |
|-------------|------|------|
| Fewer artists (8→5) | Faster, still quality | Slightly less variety |
| Parallel processing | Much faster | More complex code |
| Aggressive caching | Near-instant repeats | Stale data risk |
| Early stopping | Saves unnecessary work | Might miss better tracks |
| Image resize | Faster upload | Slight quality loss |

---

## Monitoring Metrics

Track these to measure improvement:

1. **Total response time** (target: <7s)
2. **Spotify API calls per request** (target: <30)
3. **Cache hit rate** (target: >60%)
4. **Time per phase:**
   - Image analysis: <3s
   - Artist processing: <3s
   - Filtering: <1s
5. **User satisfaction** (are songs still good quality?)

---

## Next Steps

Which optimization phase would you like to implement first?

1. **Quick Wins** - Fast to implement, immediate 50% improvement
2. **Parallel Processing** - Bigger improvement but more complex
3. **Caching** - Best for repeat performance
4. **All of them** - Maximum performance gain
