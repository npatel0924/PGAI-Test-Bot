import openai
import os
from typing import List, Dict, Any

class ChatGPTService:
    """Service for ChatGPT conversation generation"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-3.5-turbo"  # or "gpt-4" for better responses
        
    def generate_response(self,
                         system_prompt: str,
                         conversation_history: List[Dict],
                         patient_persona: Dict) -> Dict[str, Any]:
        """
        Generate patient's next response using ChatGPT
        """
        # Build messages with proper role structure [citation:10]
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(system_prompt, patient_persona)
            }
        ]
        
        # Add conversation history (last 10 turns for context)
        for turn in conversation_history[-10:]:
            role = "assistant" if turn['speaker'] == 'patient' else "user"
            messages.append({
                "role": role,
                "content": turn['text']
            })
        
        # Add instruction for next response
        messages.append({
            "role": "user",
            "content": "Generate the patient's next natural response based on the conversation so far. Keep it brief (1-2 sentences) and conversational."
        })
        
        try:
            # Call ChatGPT API [citation:10]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            return {
                "text": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": self.model
            }
            
        except Exception as e:
            print(f"ChatGPT error: {e}")
            return {
                "text": "I'm sorry, could you repeat that?",
                "tokens_used": 0,
                "model": self.model
            }
    
    def _build_system_prompt(self, base_prompt: str, persona: Dict) -> str:
        """Build complete system prompt with persona details"""
        return f"""{base_prompt}

Patient Persona:
- Name: {persona.get('name', 'Patient')}
- Age: {persona.get('age', 'Adult')}
- Personality: {persona.get('personality', 'Cooperative')}
- Communication style: {persona.get('style', 'Normal')}
- Specific concerns: {persona.get('concerns', 'None')}

Guidelines:
1. Stay in character throughout the conversation
2. Respond naturally to what the agent says
3. Don't reveal you're a bot or testing system
4. Keep responses conversational (1-2 sentences typically)
5. If confused, ask for clarification
6. Be realistic about healthcare knowledge"""