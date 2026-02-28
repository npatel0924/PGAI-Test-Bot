from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from datetime import datetime
import json
import requests
import uuid

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

from app.bot import PatientSimulatorBot

app = Flask(__name__)

# Store active calls
active_calls = {}

@app.route("/twiml", methods=['POST'])
def twiml():
    call_sid = request.values.get('CallSid')
    scenario = request.args.get('scenario', 'scheduling')
    
    # Reuse existing bot if present
    if call_sid in active_calls:
        bot = active_calls[call_sid]
        print(f"Reusing existing bot for call {call_sid}")
    else:
        bot = PatientSimulatorBot(scenario_type=scenario)
        bot.call_sid = call_sid
        active_calls[call_sid] = bot
        print(f"New call initiated: {call_sid} with scenario: {scenario}")
    
    response = VoiceResponse()
    gather = Gather(
        input='speech',
        action='/process-speech',
        method='POST',
        speech_timeout='5',
        speech_model='experimental_conversations'
    )
    
    # Only say the opening line on the very first turn
    if len(bot.conversation_history) == 0:
        gather.say(bot.opening_line, voice='Polly.Joanna')
    # else: no prompt, just listen
    
    response.append(gather)
    return Response(str(response), mimetype='text/xml')

@app.route("/process-speech", methods=['POST'])
def process_speech():
    """Receive transcribed speech from gather and generate patient response"""
    call_sid = request.values.get('CallSid')
    speech_result = request.values.get('SpeechResult')
    
    print(f"\n>>> /process-speech called for call {call_sid}")
    print(f"Request values: {dict(request.values)}")
    
    if not speech_result:
        print("⚠️ No SpeechResult received – possible timeout or silence.")
        # Optionally end the call or just return OK to continue gathering
        return Response(status=200)
    
    if call_sid not in active_calls:
        print(f"⚠️ Call {call_sid} not found in active_calls")
        return Response(status=200)
    
    bot = active_calls[call_sid]
    
    # Store AI's speech
    bot.conversation_history.append({
        'speaker': 'ai_agent',
        'text': speech_result,
        'timestamp': datetime.now().isoformat(),
        'source': 'gather'
    })
    print(f"✅ AI Agent said: {speech_result}")
    
    # Check for bugs
    bot._check_for_bugs(speech_result)
    
    # Generate patient's response
    try:
        response_data = bot.generate_patient_response()
        print(f"✅ Patient responds: {response_data['text']}")
    except Exception as e:
        print(f"❌ Error generating patient response: {e}")
        # Fallback: say something generic
        twiml_response = VoiceResponse()
        twiml_response.say("I'm sorry, I didn't catch that. Could you repeat?")
        twiml_response.redirect('/twiml')
        return Response(str(twiml_response), mimetype='text/xml')
    
    # Build TwiML to play audio and continue
    twiml_response = VoiceResponse()
    twiml_response.play(response_data['audio_url'])
    twiml_response.redirect(f'/twiml?scenario={bot.scenario_type}')
    return Response(str(twiml_response), mimetype='text/xml')

@app.route("/recording-complete", methods=['POST'])
def recording_complete():
    """Save recording for archival (no longer used for transcription)"""
    call_sid = request.values.get('CallSid')
    recording_url = request.values.get('RecordingUrl')
    recording_duration = request.values.get('RecordingDuration', '0')

    if call_sid in active_calls:
        bot = active_calls[call_sid]
        bot.costs['twilio_minutes'] += int(recording_duration) / 60
        # Optionally download and store the recording file
        try:
            audio_response = requests.get(recording_url)
            # Save the recording if needed (e.g., for audit)
        except Exception as e:
            print(f"Error saving recording: {e}")
    return "OK"

@app.route("/audio/<filename>", methods=['GET'])
def serve_audio(filename):
    """Serve generated audio files"""
    audio_path = os.path.join(PROJECT_ROOT, 'app', 'static', 'audio', filename)
    return send_file(audio_path, mimetype="audio/mpeg")

@app.route("/call-status", methods=['POST'])
def call_status():
    call_sid = request.values.get('CallSid')
    call_status = request.values.get('CallStatus')
    print(f"Call {call_sid} status: {call_status}")
    if call_status == 'completed' and call_sid in active_calls:
        bot = active_calls[call_sid]
        filename = bot.save_conversation()
        print(f"Call {call_sid} completed. Saved to {filename}")
        print(f"Summary: {bot.get_summary()}")
        del active_calls[call_sid]
    return "OK"

@app.route("/recording-status", methods=['POST'])
def recording_status():
    print(f"Recording status: {request.values}")
    return "OK"

@app.route("/health", methods=['GET'])
def health():
    return {
        'status': 'healthy',
        'active_calls': len(active_calls),
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    app.run(port=5000, debug=True)