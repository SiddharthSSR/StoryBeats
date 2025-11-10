from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from PIL import Image
import os
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pillow_heif import register_heif_opener

from services.image_analyzer import ImageAnalyzer
from services.spotify_service import SpotifyService
from services.feedback_store import get_feedback_store
from services.verify_llm import get_verify_llm
from config import Config, validate_config
import threading

# Register HEIF opener with Pillow to support .heic files
register_heif_opener()

# Load environment variables
load_dotenv()

# Validate configuration early to fail fast if critical settings are missing
try:
    validate_config()
except ValueError as config_error:
    # Surface configuration issues clearly before the server starts
    print(f"Configuration error: {config_error}")
    raise

app = Flask(__name__)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# CORS configuration for production
ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://story-beats.vercel.app',  # Production frontend
]

CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS if not Config.DEBUG else "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif', 'mpo'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize services
image_analyzer = ImageAnalyzer()
spotify_service = SpotifyService()
feedback_store = get_feedback_store()
verify_llm = get_verify_llm()

# Track returned songs per session to avoid duplicates
# Structure: {session_id: {'songs': [song_ids], 'expires_at': datetime}}
session_songs = {}
SESSION_EXPIRY_HOURS = 1  # Sessions expire after 1 hour


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_expired_sessions():
    """
    Remove expired sessions to prevent memory leaks

    This function should be called periodically to clean up old sessions.
    In production, consider using a background task or Redis with TTL.
    """
    now = datetime.now()
    expired_sessions = []

    for session_id, session_data in session_songs.items():
        if isinstance(session_data, dict) and 'expires_at' in session_data:
            if session_data['expires_at'] < now:
                expired_sessions.append(session_id)

    for session_id in expired_sessions:
        del session_songs[session_id]

    if expired_sessions:
        print(f"[Cleanup] Removed {len(expired_sessions)} expired sessions")

    return len(expired_sessions)


def background_reranking_task(session_id, image_path, all_songs, analysis):
    """
    Background task to rerank songs using LLM verification

    This runs in a separate thread after returning initial results to user.
    Reranked results are stored and used for subsequent "load more" requests.

    Args:
        session_id: Session ID
        image_path: Path to the saved image file
        all_songs: All 30 cached songs to rerank
        analysis: Original image analysis
    """
    try:
        print(f"\n[BACKGROUND RERANKING] Starting for session {session_id[:8]}...")

        # Verify and rerank songs using LLM
        reranked_songs = verify_llm.verify_and_rerank(
            image_path=image_path,
            songs=all_songs,
            original_analysis=analysis
        )

        # Store reranked results in database
        feedback_store.store_reranked_results(
            session_id=session_id,
            reranked_songs=reranked_songs,
            original_songs=all_songs
        )

        # Update session cache with reranked songs
        if session_id in session_songs:
            session_songs[session_id]['all_songs'] = reranked_songs
            session_songs[session_id]['reranked'] = True
            print(f"[BACKGROUND RERANKING] ✅ Completed for session {session_id[:8]}")

        # Clean up image file
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"[BACKGROUND RERANKING] Cleaned up image file")

    except Exception as e:
        print(f"[BACKGROUND RERANKING] ❌ Failed for session {session_id[:8]}: {e}")
        # Clean up image file even on error
        if os.path.exists(image_path):
            os.remove(image_path)


def validate_image(filepath):
    """
    Validate image file content using Pillow

    Checks:
    1. File is actually a valid image
    2. Image dimensions are reasonable (prevent decompression bombs)
    3. Image format is supported

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Open and verify the image
        img = Image.open(filepath)
        img.verify()  # Verify that it's actually an image

        # Reopen after verify (verify() closes the file)
        img = Image.open(filepath)

        # Check image dimensions to prevent decompression bombs
        # Maximum safe pixels: ~178 million (e.g., 16384 x 10922)
        MAX_PIXELS = 178956970
        width, height = img.size
        total_pixels = width * height

        if total_pixels > MAX_PIXELS:
            return False, f'Image too large: {width}x{height} ({total_pixels} pixels). Maximum: {MAX_PIXELS} pixels'

        # Check for reasonable dimensions
        MAX_DIMENSION = 16384  # 16K resolution
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            return False, f'Image dimensions too large: {width}x{height}. Maximum: {MAX_DIMENSION}x{MAX_DIMENSION}'

        # Minimum dimension check
        MIN_DIMENSION = 10
        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            return False, f'Image too small: {width}x{height}. Minimum: {MIN_DIMENSION}x{MIN_DIMENSION}'

        # Check format is supported
        supported_formats = {'PNG', 'JPEG', 'GIF', 'WEBP', 'HEIC', 'HEIF', 'MPO'}
        if img.format not in supported_formats:
            return False, f'Unsupported image format: {img.format}. Supported: {", ".join(supported_formats)}'

        return True, None

    except Exception as e:
        return False, f'Invalid image file: {str(e)}'


def optimize_image(filepath, max_size=1024):
    """
    Optimize image for faster upload to Claude API

    Resizes image to max dimensions while maintaining aspect ratio.
    Converts to RGB if needed for JPEG compatibility.

    Args:
        filepath: Path to the image file
        max_size: Maximum dimension (width or height) in pixels

    Returns:
        None (modifies file in place)
    """
    try:
        img = Image.open(filepath)

        # Get original dimensions
        width, height = img.size

        # Check if resize is needed
        if max(width, height) > max_size:
            # Calculate new size maintaining aspect ratio
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))

            # Resize image with high-quality resampling
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert RGBA to RGB if needed (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Save optimized image back to filepath
            # Use JPEG format with 85% quality for good balance
            img.save(filepath, 'JPEG', quality=85, optimize=True)

            print(f"  📸 Image optimized: {width}x{height} → {new_width}x{new_height} (saved {((1 - (new_width*new_height)/(width*height))*100):.1f}% pixels)")
        else:
            print(f"  📸 Image already optimal: {width}x{height} (no resize needed)")

    except Exception as e:
        # If optimization fails, continue with original image
        print(f"  ⚠️  Image optimization failed: {e} (using original)")
        pass


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'StoryBeats API'}), 200


@app.route('/api/analyze', methods=['POST'])
@limiter.limit("5 per minute")  # Strict limit: max 5 uploads per minute
def analyze_photo():
    """
    Main endpoint to analyze a photo and get song recommendations

    Expected: multipart/form-data with 'photo' file
    Returns: {
        'analysis': {...},
        'songs': [...]
    }
    """
    try:
        # Check if photo is in request
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo provided'}), 400

        file = request.files['photo']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp, heic, heif, mpo'}), 400

        # Create a secure random session ID FIRST
        session_id = secrets.token_urlsafe(32)

        # Save file with session_id in filename for background reranking
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1] if '.' in filename else 'jpg'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}.{file_extension}")
        file.save(filepath)

        # Also save raw bytes for database (before optimization)
        with open(filepath, 'rb') as f:
            image_data = f.read()

        try:
            # Validate image content (prevent malicious files)
            is_valid, error_msg = validate_image(filepath)
            if not is_valid:
                os.remove(filepath)  # Clean up invalid file
                return jsonify({'error': error_msg}), 400

            # Optimize image for faster Claude API upload (resize to max 1024x1024)
            optimize_image(filepath, max_size=1024)

            # Analyze image with LLM
            analysis = image_analyzer.analyze_image(filepath)

            # Get song recommendations from Spotify
            result = spotify_service.get_song_recommendations(analysis)
            songs = result['songs']  # First 5 songs
            all_songs = result['all_songs']  # Full list for caching (up to 30 songs)

            # Create session in feedback store
            feedback_store.create_session(session_id, image_data, analysis)

            # Store session with analysis, returned songs, and ALL available songs for instant "load more"
            session_songs[session_id] = {
                'analysis': analysis,  # Store analysis for backup
                'songs': [s['id'] for s in songs],  # Track returned song IDs
                'all_songs': all_songs,  # Cache ALL songs for instant "load more"
                'expires_at': datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS),
                'reranked': False  # Track if background reranking completed
            }

            # Start background reranking task (Phase 2)
            # This runs AFTER returning results to user for instant response
            reranking_thread = threading.Thread(
                target=background_reranking_task,
                args=(session_id, filepath, all_songs, analysis),
                daemon=True
            )
            reranking_thread.start()
            print(f"[ANALYZE] Started background reranking for session {session_id[:8]}")

            # Cleanup expired sessions (run occasionally)
            cleanup_expired_sessions()

            # Note: filepath is NOT removed here - background task will clean it up

            return jsonify({
                'success': True,
                'analysis': analysis,
                'songs': songs,
                'session_id': session_id  # Send to frontend to track
            }), 200

        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/spotify/auth', methods=['GET'])
def spotify_auth():
    """Get Spotify authentication URL"""
    try:
        auth_url = spotify_service.get_auth_url()
        return jsonify({'auth_url': auth_url}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/spotify/callback', methods=['POST'])
def spotify_callback():
    """Handle Spotify OAuth callback"""
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({'error': 'No authorization code provided'}), 400

        token_info = spotify_service.get_access_token(code)
        return jsonify({'success': True, 'token_info': token_info}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/more-songs', methods=['POST'])
@limiter.limit("10 per minute")  # Allow more frequent requests for getting more songs
def get_more_songs():
    """
    Get more song recommendations based on previous analysis

    Expected JSON: {
        'session_id': '...'  # Required
        'analysis': {...},   # Optional (retrieved from session if not provided)
        'offset': 5,         # Optional (default 5)
    }
    Returns: {
        'songs': [...]
    }
    """
    try:
        # Input validation
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400

        # Validate session_id type
        if not isinstance(session_id, str) or len(session_id) < 10:
            return jsonify({'error': 'Invalid session_id format'}), 400

        # Check if session exists
        if session_id not in session_songs:
            return jsonify({'error': 'Session not found or expired'}), 404

        session_data = session_songs[session_id]

        # Validate session data structure
        if not isinstance(session_data, dict):
            return jsonify({'error': 'Invalid session data'}), 500

        # Get analysis from session or request
        analysis = data.get('analysis')
        if not analysis:
            # Try to get from session
            analysis = session_data.get('analysis')
            if not analysis:
                return jsonify({'error': 'No analysis data available'}), 400

        offset = data.get('offset', 5)

        # Validate offset
        if not isinstance(offset, int) or offset < 0:
            return jsonify({'error': 'Invalid offset value'}), 400

        # Check if we have cached songs (instant "load more")
        all_songs = session_data.get('all_songs', [])

        if all_songs:
            # INSTANT "load more" - just slice from cached songs!
            print(f"[LOAD MORE] Using cached songs (instant) - {len(all_songs)} available")

            # Get how many songs have been returned so far
            returned_count = len(session_data.get('songs', []))

            # Calculate slice indices
            start_idx = returned_count
            end_idx = start_idx + 5

            # Get next batch from cached songs
            songs = all_songs[start_idx:end_idx]

            print(f"[LOAD MORE] Returning songs {start_idx+1}-{end_idx} from cache")

            # Track the new songs and update expiry
            if songs:
                session_songs[session_id]['songs'].extend([s['id'] for s in songs])
                session_songs[session_id]['expires_at'] = datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)

            return jsonify({
                'success': True,
                'songs': songs,
                'cached': True  # Indicate this was instant from cache
            }), 200

        else:
            # Fallback: Re-run algorithm if cache is not available (backward compatibility)
            print(f"[LOAD MORE] No cached songs, re-running algorithm (slow)")

            excluded_ids = session_data.get('songs', [])
            result = spotify_service.get_song_recommendations(analysis, offset=offset, excluded_ids=excluded_ids)
            songs = result['songs']

            # Track the new songs and update expiry
            if session_id and session_id in session_songs:
                session_songs[session_id]['songs'].extend([s['id'] for s in songs])
                session_songs[session_id]['expires_at'] = datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS)

            return jsonify({
                'success': True,
                'songs': songs,
                'cached': False  # Indicate this was slow from API
            }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
@limiter.limit("20 per minute")  # Allow frequent feedback submissions
def submit_feedback():
    """
    Submit user feedback for a song (Phase 1: User Feedback Loop)

    Expected JSON: {
        'session_id': '...',
        'song_id': '...',
        'song_name': '...',
        'artist_name': '...',
        'feedback': 1 or -1  # 1 for like, -1 for dislike
    }
    Returns: {
        'success': True,
        'feedback_id': ...
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        session_id = data.get('session_id')
        song_id = data.get('song_id')
        song_name = data.get('song_name')
        artist_name = data.get('artist_name')
        feedback = data.get('feedback')

        if not all([session_id, song_id, song_name, artist_name, feedback]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate feedback value
        if feedback not in [1, -1]:
            return jsonify({'error': 'Feedback must be 1 (like) or -1 (dislike)'}), 400

        # Get session data to retrieve image analysis
        if session_id not in session_songs:
            return jsonify({'error': 'Session not found or expired'}), 404

        session_data = session_songs[session_id]
        analysis = session_data.get('analysis', {})

        # Store feedback in database
        feedback_id = feedback_store.add_feedback(
            session_id=session_id,
            song_id=song_id,
            song_name=song_name,
            artist_name=artist_name,
            feedback=feedback,
            image_analysis=analysis
        )

        print(f"[FEEDBACK] Session {session_id[:8]}: "
              f"{'👍' if feedback == 1 else '👎'} \"{song_name}\" by {artist_name}")

        return jsonify({
            'success': True,
            'feedback_id': feedback_id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback/implicit', methods=['POST'])
@limiter.limit("50 per minute")  # Higher limit for implicit signals
def submit_implicit_feedback():
    """
    Submit implicit user feedback (Phase 2: Implicit Signals)

    Tracks user actions like Spotify clicks, preview plays, etc.

    Expected JSON: {
        'session_id': '...',
        'song_id': '...',     # Optional for session-level signals
        'song_name': '...',   # Optional
        'artist_name': '...',  # Optional
        'signal_type': 'spotify_click' | 'preview_play' | 'preview_complete' | 'load_more',
        'weight': 2.0  # Signal strength (2.0 strong, 1.0 medium, 0.5 weak)
    }
    Returns: {
        'success': True,
        'feedback_id': ...
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        session_id = data.get('session_id')
        signal_type = data.get('signal_type')
        weight = data.get('weight', 1.0)

        if not all([session_id, signal_type]):
            return jsonify({'error': 'Missing required fields (session_id, signal_type)'}), 400

        # Get optional song data
        song_id = data.get('song_id', '')
        song_name = data.get('song_name', '')
        artist_name = data.get('artist_name', '')

        # Get session data to retrieve image analysis
        if session_id not in session_songs:
            return jsonify({'error': 'Session not found or expired'}), 404

        session_data = session_songs[session_id]
        analysis = session_data.get('analysis', {})

        # Map signal types to feedback values
        signal_feedback_map = {
            'spotify_click': 1,      # Strong positive
            'preview_play': 1,       # Positive
            'preview_complete': 1,   # Positive
            'load_more': 1,          # Session-level positive
        }

        feedback_value = signal_feedback_map.get(signal_type, 1)

        # Store implicit feedback in database
        feedback_id = feedback_store.add_feedback(
            session_id=session_id,
            song_id=song_id,
            song_name=song_name,
            artist_name=artist_name,
            feedback=feedback_value,
            image_analysis=analysis,
            signal_type=signal_type,
            weight=weight
        )

        signal_icons = {
            'spotify_click': '🎵',
            'preview_play': '▶️',
            'preview_complete': '✅',
            'load_more': '🔄'
        }
        icon = signal_icons.get(signal_type, '📊')

        if song_name:
            print(f"[IMPLICIT] {icon} {signal_type}: \"{song_name}\" by {artist_name} (weight: {weight})")
        else:
            print(f"[IMPLICIT] {icon} {signal_type}: session-level (weight: {weight})")

        return jsonify({
            'success': True,
            'feedback_id': feedback_id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """
    Get overall feedback statistics (for analytics)

    Returns: {
        'likes': ...,
        'dislikes': ...,
        'total': ...,
        'like_rate': ...
    }
    """
    try:
        stats = feedback_store.get_feedback_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
