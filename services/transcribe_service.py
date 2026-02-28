import openai
import os
from typing import Dict, Any
import tempfile

class WhisperService:
    """Service for OpenAI Whisper speech-to-text"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
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
                    transcript = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        response_format="json"
                    )
            
            return {
                "success": True,
                "text": transcript.text,
                "confidence": 0.85,  # Whisper doesn't provide confidence scores
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