from datetime import datetime
import json
import os
from typing import List, Dict, Any

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # app/
PROJECT_ROOT = os.path.dirname(BASE_DIR)                # project root

from services.transcribe_service import WhisperService
from services.llm_service import ChatGPTService
from services.tts_service import ElevenLabsService
from scenarios.patient_scenarios import ScenarioManager

class PatientSimulatorBot:
    """
    Main bot class that simulates a patient calling a healthcare provider
    """
    
    def __init__(self, scenario_type: str = "scheduling"):
        self.scenario_type = scenario_type
        self.call_sid = None
        self.conversation_history = []
        self.bugs_found = []
        self.costs = {
            'whisper_minutes': 0,
            'chatgpt_tokens': 0,
            'elevenlabs_characters': 0,
            'twilio_minutes': 0
        }
        
        # Initialize services
        self.whisper_service = WhisperService()
        self.chatgpt_service = ChatGPTService()
        self.elevenlabs_service = ElevenLabsService()
        
        # Load patient scenario
        self.scenario = ScenarioManager.get_scenario(scenario_type)
        self.system_prompt = self.scenario['system_prompt']
        self.patient_persona = self.scenario['persona']
        self.opening_line = self.scenario['opening_line']
        
        print(f"Initialized bot with scenario: {scenario_type}")
    
    def process_ai_response(self, audio_data: bytes, duration_seconds: int) -> Dict[str, Any]:
        """
        Process what the AI agent said (audio -> text via Whisper -> analyze)
        """
        # Track Whisper cost
        self.costs['whisper_minutes'] += duration_seconds / 60
        
        # 1. Transcribe audio to text using Whisper [citation:4]
        transcription = self.whisper_service.transcribe_audio(
            audio_data, 
            duration_seconds
        )
        
        if not transcription['success']:
            return {'error': 'Transcription failed'}
        
        ai_text = transcription['text']
        
        # 2. Store in conversation history
        turn = {
            'speaker': 'ai_agent',
            'text': ai_text,
            'timestamp': datetime.now().isoformat(),
            'duration': duration_seconds
        }
        self.conversation_history.append(turn)
        
        print(f"AI Agent said: {ai_text}")
        
        # 3. Check for bugs
        self._check_for_bugs(ai_text)
        
        return {
            'text': ai_text,
            'success': True
        }
    
    def generate_patient_response(self) -> Dict[str, Any]:
        """
        Generate the patient's next response using ChatGPT [citation:10]
        """
        # 1. Generate response using ChatGPT
        response_data = self.chatgpt_service.generate_response(
            system_prompt=self.system_prompt,
            conversation_history=self.conversation_history,
            patient_persona=self.patient_persona
        )
        
        patient_text = response_data['text']
        
        # Track costs
        self.costs['chatgpt_tokens'] += response_data['tokens_used']
        
        audio_data = self.elevenlabs_service.text_to_speech(patient_text)
        self.costs['elevenlabs_characters'] += len(patient_text)

        # Save audio to a file
        filename = f"audio_{self.call_sid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(PROJECT_ROOT, 'app', 'static', 'audio', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(audio_data)

        audio_url = f"{os.getenv('BASE_URL')}/audio/{filename}"

    # Generate public URL (assumes BASE_URL is set)
        audio_url = f"{os.getenv('BASE_URL')}/audio/{filename}"
        turn = {
            'speaker': 'patient',
            'text': patient_text,
            'audio_url': audio_url,
            'timestamp': datetime.now().isoformat()
        }
        self.conversation_history.append(turn)
        
        print(f"Patient responds: {patient_text}")
        
        return {
            'text': patient_text,
            'audio': audio_data,
            'audio_url': audio_url
        }
    
    def _check_for_bugs(self, response: str):
        """
        Simple bug detection
        """
        # Check for potential hallucinations
        if "insurance" in response.lower() and not any(
            "insurance" in turn['text'].lower() 
            for turn in self.conversation_history[-3:] 
            if turn['speaker'] == 'patient'
        ):
            self.bugs_found.append({
                'type': 'hallucination',
                'description': 'AI mentioned insurance without patient bringing it up',
                'context': response[:200]
            })
        
        # Check for awkward phrasing (too long)
        if len(response.split()) > 40:
            self.bugs_found.append({
                'type': 'verbose',
                'description': 'AI response too long for natural conversation',
                'context': response[:200]
            })
        
        # Check for unhelpful responses
        unhelpful = ['i don\'t know', 'not sure', 'call back later']
        if any(phrase in response.lower() for phrase in unhelpful):
            self.bugs_found.append({
                'type': 'unhelpful',
                'description': 'AI gave unhelpful response',
                'context': response[:200]
            })
    
    def start_call(self, to_number: str) -> str:
        """Initiate an outbound call using Twilio"""
        from twilio.rest import Client
        
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        call = client.calls.create(
            url=f"{os.getenv('BASE_URL')}/twiml?scenario={self.scenario_type}",
            to=to_number,
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            record=True,
            status_callback=f"{os.getenv('BASE_URL')}/call-status",
            status_callback_event=['completed']
        )
        
        self.call_sid = call.sid
        return call.sid
    
    def save_conversation(self):
        """Save conversation to file"""
        filename = f"transcripts/{self.call_sid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('transcripts', exist_ok=True)
        
        data = {
            'call_sid': self.call_sid,
            'scenario': self.scenario_type,
            'scenario_name': self.scenario['name'],
            'timestamp': datetime.now().isoformat(),
            'conversation': self.conversation_history,
            'bugs_found': self.bugs_found,
            'costs': self.costs
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of the call"""
        return {
            'call_sid': self.call_sid,
            'scenario': self.scenario_type,
            'duration_minutes': sum(t.get('duration', 0) for t in self.conversation_history) / 60,
            'num_turns': len(self.conversation_history),
            'bugs_found': len(self.bugs_found),
            'estimated_cost': self._calculate_estimated_cost()
        }
    
    def _calculate_estimated_cost(self) -> float:
        """Calculate estimated API costs"""
        # Rough estimates based on current pricing
        whisper_cost = self.costs['whisper_minutes'] * 0.006  # $0.006/minute
        chatgpt_cost = (self.costs['chatgpt_tokens'] / 1000) * 0.002  # $0.002/1K tokens
        elevenlabs_cost = (self.costs['elevenlabs_characters'] / 1000) * 0.03  # $0.03/1K chars
        twilio_cost = self.costs['twilio_minutes'] * 0.013  # $0.013/minute
        
        return whisper_cost + chatgpt_cost + elevenlabs_cost + twilio_cost
    
    