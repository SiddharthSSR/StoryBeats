import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # Spotify API Configuration
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:3000/callback')
    SPOTIFY_SCOPE = 'user-read-private user-read-email'

    # LLM Configuration (supports multiple providers)
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'anthropic')  # 'anthropic', 'openai', or 'gemini'

    # Anthropic (Claude)
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-vision-preview')

    # Google Gemini
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro-vision')

    # File Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Application Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')


# Validate required environment variables
def validate_config():
    """Validate that required configuration is present"""
    errors = []

    if not Config.SPOTIFY_CLIENT_ID:
        errors.append("SPOTIFY_CLIENT_ID is required")
    if not Config.SPOTIFY_CLIENT_SECRET:
        errors.append("SPOTIFY_CLIENT_SECRET is required")

    # Check that at least one LLM provider is configured
    llm_configured = False
    if Config.LLM_PROVIDER == 'anthropic' and Config.ANTHROPIC_API_KEY:
        llm_configured = True
    elif Config.LLM_PROVIDER == 'openai' and Config.OPENAI_API_KEY:
        llm_configured = True
    elif Config.LLM_PROVIDER == 'gemini' and Config.GEMINI_API_KEY:
        llm_configured = True

    if not llm_configured:
        errors.append(f"No API key found for LLM_PROVIDER: {Config.LLM_PROVIDER}")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"- {err}" for err in errors))

    return True
