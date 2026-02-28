from elevenlabs import generate, play, set_api_key
import os
import io

class ElevenLabsService:
    """Service for ElevenLabs text-to-speech"""
    
    def __init__(self):
        set_api_key(os.getenv('ELEVENLABS_API_KEY'))
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')  # Rachel
        self.model = "eleven_monolingual_v1"
        
    def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech audio using ElevenLabs
        """
        try:
            # Generate audio [citation:3]
            audio = generate(
                text=text,
                voice=self.voice_id,
                model=self.model
            )
            
            # Convert to bytes
            if isinstance(audio, bytes):
                return audio
            elif hasattr(audio, 'read'):
                return audio.read()
            else:
                return bytes(audio)
                
        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            # Return empty audio as fallback
            return b''