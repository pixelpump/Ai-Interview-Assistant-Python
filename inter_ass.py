import eel
import speech_recognition as sr
from openai import OpenAI
import threading
import json
import os
import base64
import time
import re

eel.init('web')

class AudioAssistant:
    def __init__(self):
        self.setup_audio()
        self.is_listening = False
        self.client = None
        self.api_key = None
        self.tts_enabled = True  # Set this to True by default
        self.is_speaking = False
        self.audio_playing = False
        self.load_api_key()

    def setup_audio(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)

    def load_api_key(self):
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.set_api_key(config.get('api_key'))

    def set_api_key(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)
        with open('config.json', 'w') as f:
            json.dump({'api_key': api_key}, f)

    def delete_api_key(self):
        self.api_key = None
        self.client = None
        if os.path.exists('config.json'):
            os.remove('config.json')

    def has_api_key(self):
        return self.api_key is not None

    def toggle_listening(self):
        if not self.client:
            return False
        self.is_listening = not self.is_listening
        if self.is_listening:
            threading.Thread(target=self.listen_and_process, daemon=True).start()
        return self.is_listening

    def listen_and_process(self):
        cooldown_time = 2  # Cooldown period in seconds
        last_speak_time = 0
        
        while self.is_listening:
            current_time = time.time()
            if not self.is_speaking and not self.audio_playing and (current_time - last_speak_time) > cooldown_time:
                try:
                    with self.mic as source:
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio)
                    if self.is_question(text):
                        capitalized_text = text[0].upper() + text[1:]
                        if not capitalized_text.endswith('?'):
                            capitalized_text += '?'
                        eel.update_ui(f"Q: {capitalized_text}", "")
                        self.is_speaking = True
                        response = self.get_ai_response(capitalized_text)
                        eel.update_ui("", f"{response}")
                        self.is_speaking = False
                        last_speak_time = time.time()  # Update the last speak time
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    eel.update_ui(f"An error occurred: {str(e)}", "")
            else:
                time.sleep(0.1)  # Short sleep to prevent busy waiting

    def is_question(self, text):
        # Convert to lowercase for easier matching
        text = text.lower().strip()
        
        # List of question words and phrases
        question_starters = [
            "what", "why", "how", "when", "where", "who", "which",
            "can", "could", "would", "should", "is", "are", "do", "does",
            "am", "was", "were", "have", "has", "had", "will", "shall"
        ]
        
        # Check if the text starts with a question word
        if any(text.startswith(starter) for starter in question_starters):
            return True
        
        # Check for question mark at the end
        if text.endswith('?'):
            return True
        
        # Check for inverted word order (e.g., "Are you...?", "Can we...?")
        if re.match(r'^(are|can|could|do|does|have|has|will|shall|should|would|am|is)\s', text):
            return True
        
        # Check for specific phrases that indicate a question
        question_phrases = [
            "tell me about", "i'd like to know", "can you explain",
            "i was wondering", "do you know", "what about", "how about"
        ]
        if any(phrase in text for phrase in question_phrases):
            return True
        
        # If none of the above conditions are met, it's probably not a question
        return False

    def get_ai_response(self, question):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": question}
                ]
            )
            text_response = response.choices[0].message.content.strip()
            
            if self.tts_enabled:
                speech_response = self.client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=text_response
                )
                
                audio_base64 = base64.b64encode(speech_response.content).decode('utf-8')
                return json.dumps({"text": text_response, "audio": audio_base64})
            
            return json.dumps({"text": text_response, "audio": None})
        except Exception as e:
            print(f"Error in get_ai_response: {str(e)}")  # Add this line for debugging
            return json.dumps({"text": f"Error getting AI response: {str(e)}", "audio": None})

assistant = AudioAssistant()

@eel.expose
def toggle_listening():
    return assistant.toggle_listening()

@eel.expose
def save_api_key(api_key):
    try:
        assistant.set_api_key(api_key)
        return True
    except Exception as e:
        print(f"Error saving API key: {str(e)}")
        return False

@eel.expose
def delete_api_key():
    try:
        assistant.delete_api_key()
        return True
    except Exception as e:
        print(f"Error deleting API key: {str(e)}")
        return False

@eel.expose
def has_api_key():
    return assistant.has_api_key()

@eel.expose
def toggle_tts():
    assistant.tts_enabled = not assistant.tts_enabled
    return assistant.tts_enabled

@eel.expose
def speaking_ended():
    assistant.is_speaking = False

@eel.expose
def audio_playback_started():
    assistant.audio_playing = True

@eel.expose
def audio_playback_ended():
    assistant.audio_playing = False
    assistant.is_speaking = False

eel.start('index.html', size=(960, 840))