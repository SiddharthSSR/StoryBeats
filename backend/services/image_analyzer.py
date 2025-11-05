import base64
from anthropic import Anthropic
from openai import OpenAI
import json
from config import Config


class ImageAnalyzer:
    """Service for analyzing images using LLMs"""

    def __init__(self):
        """Initialize LLM client based on configuration"""
        self.provider = Config.LLM_PROVIDER
        self.client = None
        self.model = None

    def _get_client(self):
        """Lazy initialization of LLM client"""
        if self.client is None:
            if self.provider == 'anthropic':
                self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
                self.model = Config.ANTHROPIC_MODEL
            elif self.provider == 'openai':
                self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.model = Config.OPENAI_MODEL
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        return self.client

    def _encode_image(self, image_path):
        """
        Encode image to base64 with optimization

        Resizes large images to max 1024px width to reduce base64 size
        and speed up LLM processing without losing visual quality for analysis
        """
        from PIL import Image
        import io

        # Open and potentially resize the image
        img = Image.open(image_path)

        # Max width for encoding (reduces payload size significantly)
        MAX_WIDTH = 1024

        # Only resize if image is larger than MAX_WIDTH
        if img.width > MAX_WIDTH:
            # Calculate new height maintaining aspect ratio
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
            print(f"[ImageAnalyzer] Resized image from {Image.open(image_path).size} to {img.size} for faster processing")

        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if img.mode not in ('RGB', 'JPEG'):
            img = img.convert('RGB')

        # Save to bytes buffer with moderate quality (reduces size further)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)

        # Encode to base64
        return base64.b64encode(buffer.read()).decode('utf-8')

    def _get_image_type(self, image_path):
        """Get image MIME type from file extension"""
        extension = image_path.lower().split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        return mime_types.get(extension, 'image/jpeg')

    def analyze_image(self, image_path):
        """
        Analyze an image and extract mood, themes, and music preferences

        Args:
            image_path (str): Path to the image file

        Returns:
            dict: Analysis results including mood, genres, energy, valence, keywords
        """
        print(f"[ImageAnalyzer] analyze_image called with provider: {self.provider}")
        print(f"[ImageAnalyzer] Image path: {image_path}")

        if self.provider == 'anthropic':
            print(f"[ImageAnalyzer] Using Anthropic")
            return self._analyze_with_anthropic(image_path)
        elif self.provider == 'openai':
            print(f"[ImageAnalyzer] Using OpenAI")
            return self._analyze_with_openai(image_path)
        else:
            print(f"[ImageAnalyzer] WARNING: Unknown provider '{self.provider}', using fallback")
            return self._get_default_analysis()

    def _analyze_with_anthropic(self, image_path):
        """Analyze image using Anthropic's Claude"""
        try:
            # Get client
            client = self._get_client()

            # Encode image
            image_data = self._encode_image(image_path)
            media_type = self._get_image_type(image_path)

            # Create the prompt
            prompt = """Analyze this image that will be used as an Instagram story.
I need you to suggest music that would match this image's vibe. Be specific and nuanced in your analysis.

Please provide a detailed analysis in JSON format with the following structure:
{
    "mood": "primary emotional mood - be specific (e.g., peaceful, melancholic, energetic, romantic, nostalgic, adventurous, dreamy, confident, cozy, vibrant)",
    "themes": ["theme1", "theme2", "theme3"],
    "description": "detailed description of the image's atmosphere, setting, colors, mood, and overall vibe",
    "genres": ["genre1", "genre2", "genre3", "genre4"],
    "energy": 0.0-1.0 (how energetic the vibe is),
    "valence": 0.0-1.0 (how positive/happy the vibe is),
    "danceability": 0.0-1.0 (how suitable for dancing),
    "acousticness": 0.0-1.0 (acoustic vs electronic),
    "tempo": 60-180 (beats per minute - slow to fast),
    "instrumentalness": 0.0-1.0 (presence of vocals vs instrumental),
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "music_style": "brief description of what kind of music would fit (e.g., 'soft acoustic with soothing vocals', 'upbeat dance tracks', 'soulful melodies')",
    "cultural_vibe": "indian/western/global/fusion - based on visual elements, clothing, setting, or aesthetic"
}

Important guidelines:
- Be very specific with mood (avoid generic terms like "happy" - use "joyful", "content", "euphoric", etc.)
- Genres should include both international and Indian styles when appropriate:
  International: indie, pop, rock, hip-hop, electronic, jazz, r-n-b, soul, alternative, folk, ambient, house
  Indian: bollywood, desi-pop, indie-hindi, punjabi, sufi, carnatic, hindustani-classical, indi-pop
- Consider the setting, colors, activities, expressions, and overall aesthetic
- Energy: 0.0 = very calm/meditative, 0.3 = relaxed/chill, 0.5 = moderate, 0.7 = lively, 1.0 = very energetic/intense
- Valence: 0.0 = melancholic/somber, 0.3 = thoughtful/reflective, 0.5 = neutral, 0.7 = positive/cheerful, 1.0 = euphoric/ecstatic
- Danceability: 0.0 = not danceable (ambient, meditative), 0.3 = gentle sway, 0.5 = moderate movement, 0.7 = groovy/rhythmic, 1.0 = club/party dance
- Acousticness: 0.0 = fully electronic/synthesized, 0.3 = electronic with organic elements, 0.5 = mixed, 0.7 = mostly acoustic, 1.0 = pure acoustic instruments
- Tempo: 60-80 = slow/ballad, 80-100 = relaxed/chill, 100-120 = moderate, 120-140 = upbeat, 140-180 = fast/energetic
- Instrumentalness: 0.0 = vocal-heavy (singing throughout), 0.3 = vocals with instrumental breaks, 0.5 = balanced, 0.7 = mostly instrumental, 1.0 = purely instrumental
- Keywords should capture the essence, setting, and feeling (e.g., "sunset", "friends", "peaceful", "urban", "traditional")
- Music style should describe the instrumentation and feel
- Cultural vibe helps determine language mix in songs (indian = more Hindi/regional, western = more English, global = mixed)

Return ONLY the JSON object, no additional text."""

            # Make API call
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Parse response
            response_text = message.content[0].text
            analysis = json.loads(response_text)

            return analysis

        except Exception as e:
            print(f"Error analyzing image with Anthropic: {e}")
            # Return default analysis on error
            return self._get_default_analysis()

    def _analyze_with_openai(self, image_path):
        """Analyze image using OpenAI's GPT-4 Vision"""
        try:
            print(f"[OpenAI] Starting image analysis with model: {Config.OPENAI_MODEL}")

            # Get client
            client = self._get_client()
            print(f"[OpenAI] Client initialized successfully")

            # Encode image
            image_data = self._encode_image(image_path)
            media_type = self._get_image_type(image_path)
            print(f"[OpenAI] Image encoded, type: {media_type}, size: {len(image_data)} chars")

            prompt = """Analyze this image that will be used as an Instagram story.
I need you to suggest music that would match this image's vibe. Be specific and nuanced in your analysis.

Please provide a detailed analysis in JSON format with the following structure:
{
    "mood": "primary emotional mood - be specific (e.g., peaceful, melancholic, energetic, romantic, nostalgic, adventurous, dreamy, confident, cozy, vibrant)",
    "themes": ["theme1", "theme2", "theme3"],
    "description": "detailed description of the image's atmosphere, setting, colors, mood, and overall vibe",
    "genres": ["genre1", "genre2", "genre3", "genre4"],
    "energy": 0.0-1.0 (how energetic the vibe is),
    "valence": 0.0-1.0 (how positive/happy the vibe is),
    "danceability": 0.0-1.0 (how suitable for dancing),
    "acousticness": 0.0-1.0 (acoustic vs electronic),
    "tempo": 60-180 (beats per minute - slow to fast),
    "instrumentalness": 0.0-1.0 (presence of vocals vs instrumental),
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "music_style": "brief description of what kind of music would fit (e.g., 'soft acoustic with soothing vocals', 'upbeat dance tracks', 'soulful melodies')",
    "cultural_vibe": "indian/western/global/fusion - based on visual elements, clothing, setting, or aesthetic"
}

Important guidelines:
- Be very specific with mood (avoid generic terms like "happy" - use "joyful", "content", "euphoric", etc.)
- Genres should include both international and Indian styles when appropriate:
  International: indie, pop, rock, hip-hop, electronic, jazz, r-n-b, soul, alternative, folk, ambient, house
  Indian: bollywood, desi-pop, indie-hindi, punjabi, sufi, carnatic, hindustani-classical, indi-pop
- Consider the setting, colors, activities, expressions, and overall aesthetic
- Energy: 0.0 = very calm/meditative, 0.3 = relaxed/chill, 0.5 = moderate, 0.7 = lively, 1.0 = very energetic/intense
- Valence: 0.0 = melancholic/somber, 0.3 = thoughtful/reflective, 0.5 = neutral, 0.7 = positive/cheerful, 1.0 = euphoric/ecstatic
- Danceability: 0.0 = not danceable (ambient, meditative), 0.3 = gentle sway, 0.5 = moderate movement, 0.7 = groovy/rhythmic, 1.0 = club/party dance
- Acousticness: 0.0 = fully electronic/synthesized, 0.3 = electronic with organic elements, 0.5 = mixed, 0.7 = mostly acoustic, 1.0 = pure acoustic instruments
- Tempo: 60-80 = slow/ballad, 80-100 = relaxed/chill, 100-120 = moderate, 120-140 = upbeat, 140-180 = fast/energetic
- Instrumentalness: 0.0 = vocal-heavy (singing throughout), 0.3 = vocals with instrumental breaks, 0.5 = balanced, 0.7 = mostly instrumental, 1.0 = purely instrumental
- Keywords should capture the essence, setting, and feeling (e.g., "sunset", "friends", "peaceful", "urban", "traditional")
- Music style should describe the instrumentation and feel
- Cultural vibe helps determine language mix in songs (indian = more Hindi/regional, western = more English, global = mixed)

Return ONLY the JSON object, no additional text."""

            # Make API call
            print(f"[OpenAI] Calling API with model: {self.model}")
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1024
            )

            print(f"[OpenAI] API call successful!")
            # Parse response
            response_text = response.choices[0].message.content
            print(f"[OpenAI] Response received: {response_text[:200]}...")

            # Remove markdown code fences if present
            if response_text.strip().startswith('```'):
                # Remove opening fence
                response_text = response_text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]  # Remove ```json
                elif response_text.startswith('```'):
                    response_text = response_text[3:]  # Remove ```

                # Remove closing fence
                if response_text.endswith('```'):
                    response_text = response_text[:-3]

                response_text = response_text.strip()
                print(f"[OpenAI] Cleaned response (removed markdown): {response_text[:200]}...")

            analysis = json.loads(response_text)
            print(f"[OpenAI] JSON parsed successfully: {analysis}")

            return analysis

        except Exception as e:
            import traceback
            print(f"Error analyzing image with OpenAI: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Full traceback: {traceback.format_exc()}")
            # Return default analysis on error
            return self._get_default_analysis()

    def _get_default_analysis(self):
        """Return a default analysis when LLM analysis fails"""
        return {
            "mood": "happy",
            "themes": ["general", "lifestyle", "moments"],
            "description": "A casual Instagram story moment",
            "genres": ["pop", "indie", "electronic"],
            "energy": 0.6,
            "valence": 0.7,
            "danceability": 0.5,
            "acousticness": 0.4,
            "tempo": 110,
            "instrumentalness": 0.2,
            "keywords": ["vibes", "chill", "lifestyle", "moments", "mood"],
            "music_style": "upbeat pop with good vibes",
            "cultural_vibe": "global"
        }
