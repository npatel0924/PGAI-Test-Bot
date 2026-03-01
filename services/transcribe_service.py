import openai
import os
from typing import Dict, Any
import tempfile

class WhisperService:
    """Service for OpenAI Whisper speech-to-text"""
    
    def __init__(self):
        # instantiate a client; support both new-style `OpenAI` client and
        # legacy module-level API (openai<1.0). Prefer `OpenAI` if available.
        api_key = os.getenv('OPENAI_API_KEY')
        if hasattr(openai, 'OpenAI'):
            try:
                self.client = openai.OpenAI(api_key=api_key)
            except TypeError:
                openai.api_key = api_key
                self.client = openai
        else:
            openai.api_key = api_key
            self.client = openai
        self.model = "whisper-1"
        
    def transcribe_audio(self, audio_data: bytes, duration_seconds: int) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper API
        """
        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # Open the file for Whisper
                with open(temp_file.name, "rb") as audio_file:
                    try:
                        # Preferred new-style client call
                        transcript = self.client.audio.transcriptions.create(
                            model=self.model,
                            file=audio_file,
                            response_format="json"
                        )
                        text = getattr(transcript, 'text', None) or transcript.get('text', '')
                    except Exception as e_primary:
                        print(f"Whisper primary call failed: {e_primary}")
                        try:
                            # Fallback to module-level helper
                            alt = openai.Audio.transcribe(model=self.model, file=audio_file)
                            text = getattr(alt, 'text', None) or alt.get('text', '')
                        except Exception as e_fallback:
                            print(f"Whisper fallback failed: {e_fallback}")
                            raise

            return {
                "success": True,
                "text": text,
                "confidence": 0.85,
                "duration": duration_seconds
            }
            
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def transcribe_from_url(self, audio_url: str, duration_seconds: int) -> Dict[str, Any]:
        """
        Transcribe audio from a URL
        """
        import requests
        
        try:
            # Download audio
            response = requests.get(audio_url)
            response.raise_for_status()
            
            return self.transcribe_audio(response.content, duration_seconds)
            
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }