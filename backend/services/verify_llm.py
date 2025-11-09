#!/usr/bin/env python3
"""
Verify LLM Service
Post-hoc verification and reranking of song recommendations using LLM
"""

import base64
import json
from typing import List, Dict, Optional
from anthropic import Anthropic
from openai import OpenAI
from config import Config


class VerifyLLM:
    """
    LLM-based verification service for song recommendations

    Features:
    - Verifies if recommended songs match the image vibe
    - Reranks songs based on LLM understanding of context
    - Provides explanations for why songs match/don't match
    """

    def __init__(self):
        """Initialize LLM client"""
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

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        from PIL import Image
        import io

        img = Image.open(image_path)

        # Resize for faster processing
        MAX_WIDTH = 512  # Smaller than analysis since we just need vibe check
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        image_bytes = buffer.getvalue()

        return base64.b64encode(image_bytes).decode('utf-8')

    def verify_and_rerank(self, image_path: str, songs: List[Dict],
                          original_analysis: Dict) -> List[Dict]:
        """
        Verify if songs match the image and rerank them

        Args:
            image_path: Path to the original image
            songs: List of recommended songs (up to 30)
            original_analysis: Original LLM analysis of the image

        Returns:
            Reranked list of songs with confidence scores
        """
        print(f"\n[VERIFY_LLM] Starting verification for {len(songs)} songs...")

        client = self._get_client()

        # Prepare song descriptions for LLM
        song_descriptions = []
        for i, song in enumerate(songs[:30], 1):  # Limit to 30 to stay within context
            desc = f"{i}. \"{song['name']}\" by {song['artist']}"
            if song.get('album'):
                desc += f" (Album: {song['album']})"
            song_descriptions.append(desc)

        songs_text = "\n".join(song_descriptions)

        # Create verification prompt
        prompt = f"""You are a music recommendation expert. Analyze this image and verify if the recommended songs match the vibe.

**Original Analysis:**
- Mood: {original_analysis.get('mood')}
- Energy: {original_analysis.get('energy')}
- Valence: {original_analysis.get('valence')}
- Cultural Vibe: {original_analysis.get('cultural_vibe')}

**Recommended Songs:**
{songs_text}

**Your Task:**
1. Look at the image carefully
2. Consider the mood, energy, colors, and atmosphere
3. Evaluate how well EACH song matches the image vibe
4. Rerank the songs from BEST match to WORST match

**Output Format (JSON only, no explanation):**
{{
  "reranked_indices": [3, 1, 7, ...],  // List of song numbers in best-to-worst order
  "confidence_scores": {{
    "1": 0.95,  // Confidence that song 1 matches (0.0-1.0)
    "2": 0.87,
    ...
  }},
  "top_match_reason": "Brief reason why the top song is best match"
}}

Only return valid JSON, nothing else."""

        try:
            if self.provider == 'anthropic':
                # Encode image
                image_data = self._encode_image(image_path)

                response = client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }]
                )
                result_text = response.content[0].text

            elif self.provider == 'openai':
                # OpenAI implementation
                image_data = self._encode_image(image_path)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }],
                    max_tokens=2000
                )
                result_text = response.choices[0].message.content

            # Parse LLM response
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            verification = json.loads(result_text)

            # Apply reranking
            reranked_songs = self._apply_reranking(songs, verification)

            print(f"[VERIFY_LLM] ✅ Reranked {len(reranked_songs)} songs")
            print(f"[VERIFY_LLM] Top match: {reranked_songs[0]['name']} "
                  f"(confidence: {reranked_songs[0].get('llm_confidence', 0):.2f})")
            print(f"[VERIFY_LLM] Reason: {verification.get('top_match_reason', 'N/A')}")

            return reranked_songs

        except Exception as e:
            print(f"[VERIFY_LLM] ⚠️  Verification failed: {e}")
            print(f"[VERIFY_LLM] Falling back to original ranking")
            # Return original songs if verification fails
            return songs

    def _apply_reranking(self, songs: List[Dict], verification: Dict) -> List[Dict]:
        """
        Apply LLM reranking to songs

        Args:
            songs: Original song list
            verification: LLM verification result

        Returns:
            Reranked songs with confidence scores
        """
        reranked_indices = verification.get('reranked_indices', [])
        confidence_scores = verification.get('confidence_scores', {})

        # Rerank songs
        reranked_songs = []
        for idx in reranked_indices:
            if 1 <= idx <= len(songs):
                song = songs[idx - 1].copy()  # Convert to 0-indexed
                song['llm_confidence'] = confidence_scores.get(str(idx), 0.5)
                song['llm_verified'] = True
                reranked_songs.append(song)

        # Add any songs that weren't in reranked_indices
        reranked_ids = set(reranked_indices)
        for i, song in enumerate(songs, 1):
            if i not in reranked_ids:
                song_copy = song.copy()
                song_copy['llm_confidence'] = 0.3  # Low confidence for non-reranked
                song_copy['llm_verified'] = False
                reranked_songs.append(song_copy)

        return reranked_songs


# Global instance
_verify_llm = None


def get_verify_llm() -> VerifyLLM:
    """Get singleton VerifyLLM instance"""
    global _verify_llm
    if _verify_llm is None:
        _verify_llm = VerifyLLM()
    return _verify_llm
