import openai
import os
from typing import List, Dict, Any

class ChatGPTService:
    """Service for ChatGPT conversation generation"""
    
    def __init__(self):
        # Build an OpenAI client that supports both the new `OpenAI` class
        # and the legacy module-level API (openai<1.0). Prefer `OpenAI` when
        # available; otherwise set `openai.api_key` and use module functions.
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
        # Map local `speaker` labels to ChatGPT roles:
        # - ai_agent -> 'user' (things the patient is responding to)
        # - patient -> 'assistant' (previous patient replies)
        for turn in conversation_history[-10:]:
            if turn.get('speaker') == 'ai_agent':
                role = 'user'
            else:
                role = 'assistant'
            messages.append({
                "role": role,
                "content": turn.get('text', '')
            })
        
        # Add instruction for next response
        messages.append({
            "role": "user",
            "content": "Generate the patient's next natural response based on the conversation so far. Keep it brief (1-2 sentences) and conversational."
        })
        
        try:
            # Preferred client call (new-style client)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            text = getattr(response.choices[0].message, 'content', None) or getattr(response.choices[0], 'message', {}).get('content', '')
            tokens_used = getattr(response, 'usage', {}).get('total_tokens', 0)
            return {
                "text": text,
                "tokens_used": tokens_used,
                "model": self.model
            }

        except Exception as primary_exc:
            # Fallbacks for alternate openai package shapes
            print(f"ChatGPT primary call failed: {primary_exc}")
            try:
                # Legacy / module-level ChatCompletion interface
                alt_resp = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150
                )
                text = alt_resp['choices'][0]['message']['content'] if 'choices' in alt_resp else ''
                tokens = alt_resp.get('usage', {}).get('total_tokens', 0)
                return {
                    'text': text,
                    'tokens_used': tokens,
                    'model': self.model
                }
            except Exception as fallback_exc:
                print(f"ChatGPT fallback call failed: {fallback_exc}")
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