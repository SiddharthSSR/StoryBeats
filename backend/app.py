from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from PIL import Image
import os
from dotenv import load_dotenv

from services.image_analyzer import ImageAnalyzer
from services.spotify_service import SpotifyService
from config import Config

# Load environment variables
load_dotenv()

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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize services
image_analyzer = ImageAnalyzer()
spotify_service = SpotifyService()

# Track returned songs per session to avoid duplicates
session_songs = {}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        supported_formats = {'PNG', 'JPEG', 'GIF', 'WEBP'}
        if img.format not in supported_formats:
            return False, f'Unsupported image format: {img.format}. Supported: {", ".join(supported_formats)}'

        return True, None

    except Exception as e:
        return False, f'Invalid image file: {str(e)}'


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
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400

        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Validate image content (prevent malicious files)
            is_valid, error_msg = validate_image(filepath)
            if not is_valid:
                os.remove(filepath)  # Clean up invalid file
                return jsonify({'error': error_msg}), 400

            # Analyze image with LLM
            analysis = image_analyzer.analyze_image(filepath)

            # Get song recommendations from Spotify
            songs = spotify_service.get_song_recommendations(analysis)

            # Create a session ID based on the analysis (to track this photo's songs)
            import hashlib
            session_id = hashlib.md5(str(analysis).encode()).hexdigest()
            session_songs[session_id] = [s['id'] for s in songs]

            # Clean up uploaded file
            os.remove(filepath)

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
        'analysis': {...},
        'offset': 5,
        'session_id': '...'
    }
    Returns: {
        'songs': [...]
    }
    """
    try:
        data = request.json
        if not data or 'analysis' not in data:
            return jsonify({'error': 'No analysis data provided'}), 400

        analysis = data['analysis']
        offset = data.get('offset', 5)
        session_id = data.get('session_id')

        # Get previously returned songs for this session
        excluded_ids = session_songs.get(session_id, []) if session_id else []

        # Get more song recommendations with offset
        songs = spotify_service.get_song_recommendations(analysis, offset=offset, excluded_ids=excluded_ids)

        # Track the new songs
        if session_id:
            session_songs[session_id].extend([s['id'] for s in songs])

        return jsonify({
            'success': True,
            'songs': songs
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
