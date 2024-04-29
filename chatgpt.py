import os
import openai
import time
import speech_recognition as sr
from gtts import gTTS
import tempfile
from pydub import AudioSegment
from pydub.playback import play
import json
from googletrans import Translator
import serial
import random

openai.api_key = "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"
model = 'gpt-3.5-turbo'

# Set up the speech recognition engine
r = sr.Recognizer()

school_name = "xyme International"
teacher_name = "Iris"
current_language = 'en'
greetings_to_detect = ["hello iris", "teacher", "iris"]
greetings = [
    f"What's up,  I am {teacher_name}, your AI teacher at {school_name}.",
]

def get_random_greeting():
    return random.choice(greetings)

# Connect to Arduino through serial communication
ser = serial.Serial('COM3', 9600)

# Variable to indicate whether listening should start
start_listening = False

# Function to send data to Arduino through serial and print the data
def send_data_to_arduino(data):
    print(f"Sending to Arduino: {data.decode('utf-8')}")
    ser.write(data)

# Function to read data from Arduino through serial
def read_data_from_arduino():
    global start_listening
    
    while ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').strip()
        print(f"from Arduino: {data}")
        # Process data from Arduino as needed
        # Toggle start_listening flag based on received command
        if data.upper() == 'START':
            start_listening = True
            print("Start listening...")
            provide_audio_feedback("Hello, World!.,i am IRIS your Ai teacher at Xyme International school., how can i help you!")
        elif data.upper() == 'STOP':
            start_listening = False
            print("Stop listening...")
        elif data.upper() == 'Z':
            inaugural_address_text = f"Ladies and gentleman, esteemed guests, and our brilliant students {school_name}’ of .I am you’re A I teacher, today marks a significant moment in our educational  journey. Let us embrace the synergy of technology and  learning. This A I tirelessly devoted to cultivating  knowledge, will empower students on their educational  voyage. Together let’s embark on a future where  innovation and education walk hand in hand. Welcome  to a new era of limitless possibilities!"
            provide_audio_feedback(inaugural_address_text, language=current_language)
        
# Function to play the generated speech
def play_audio(response_text, language='en'):
    with tempfile.NamedTemporaryFile(delete=True) as temp_wav:
        tts = gTTS(response_text, lang=language)
        tts.save(f"{temp_wav.name}.mp3")
        sound = AudioSegment.from_mp3(f"{temp_wav.name}.mp3")
        
        play_object = play(sound)

        if play_object is not None:
            # Wait for the audio to finish playing
            play_object.wait_done()

            print("Audio playback is over")
            
            # Send signal to Arduino that audio playback is over
            send_data_to_arduino(b't')

# Function to provide short audio feedback
def provide_audio_feedback(feedback_text, language='en'):
    play_audio(feedback_text, language)

# Process OpenAI API response
def process_api_response(api_request):
    response_text = api_request['choices'][0]['message']['content'].strip()
    return response_text

# Function to play the network error audio
def play_network_error_audio():
    network_error_text = "Network error. Please check your connection."
    play_audio(network_error_text)

# Function for handling network connection errors with OpenAI API
def handle_network_error():
    play_network_error_audio()
    print("Network error. Retrying in 5 seconds...")
    time.sleep(5)

# Function to translate text to English
def translate_to_english(text, source_language):
    if source_language != 'en':
        translator = Translator()
        translation = translator.translate(text, src=source_language, dest='en')
        return translation.text
    else:
        return text

# Function to translate text back to the original language
def translate_to_original(text, original_language):
    if original_language != 'en':
        translator = Translator()
        translation = translator.translate(text, src='en', dest=original_language)
        return translation.text
    else:
        return text

def generate_random_question():
    questions = [
        "What is the capital of France?",
        
    ]
    return random.choice(questions)

# Function to play a sound file
def play_sound_file(file_path):
    os.system(f"start {file_path}")  # On Windows
    # For Linux or macOS, you can use:
    # os.system(f"afplay {file_path}")  # macOS
    # os.system(f"aplay {file_path}")   # Linux

def load_conversation_history():
    try:
        with open('conversation_history.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {'conversations': []}

# Function to listen for input and respond
def listen_and_respond(source, conversation_history):
    global start_listening
    global current_language

    print("Listening...")

    while True:
        try:
            # Read data from Arduino
            read_data_from_arduino()

            # Check if listening should start
            if not start_listening:
                time.sleep(0.1)  # Short break to reduce delay
                continue

            # Stop listening to the microphone while playing audio
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=4.5)  # Adjust the timeout value as needed

            if current_language == 'ml':
                text = r.recognize_google(audio, language='ml-IN')
            elif current_language == 'hi':
                text = r.recognize_google(audio, language='hi-IN')
            else:
                text = r.recognize_google(audio, language='en-IN')
            send_data_to_arduino(b'U')
            print(f"You said ({current_language}): {text}")

            # Check for language switch commands
            if 'switch to english' in text.lower() or (current_language == 'ml' and 'ഇംഗ്ലീഷിലേക്ക് മാറുക' in text.lower()) or (current_language == 'hi' and 'अंग्रेज़ी में स्विच करें' in text.lower()):
                current_language = 'en'
                print("Switching to English...")
                provide_audio_feedback("Switching to English.", language='en')
                continue
           

            conversation_history['conversations']. append({'user': text, 'language': current_language})

            text_english = translate_to_english(text, current_language)

            valid_phrases = [
                "Who", "What", "When", "Where", "Why", "How",
            ]

            # Check for valid phrases
            if any(phrase.lower() in text_english.lower() for phrase in valid_phrases):
                while True:
                    try:
                        api_request = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[ 
                                {"role": "system", "content": f"You are a humanoid ai teacher named {teacher_name} who teach students in {school_name} school in kerala in the banks of menachil river ,developed by makerlabs an Educational Tech,  answer in 40 words"},
                                {"role": "user", "content": text_english}
                            ],
                            temperature=0.7,
                            max_tokens=100
                        )

                        response_text = process_api_response(api_request)

                        print(f"OpenAI response: {response_text}")
                        response_text_original_lang = translate_to_original(response_text, current_language)

                        provide_audio_feedback(response_text_original_lang, language=current_language)
                        send_data_to_arduino(b't')

                        conversation_history['conversations'][-1]['ai'] = response_text_original_lang

                        save_conversation_history(conversation_history)

                        break
                    
                    except openai.error.OpenAIError as e:
                        if 'network' in str(e).lower():
                            handle_network_error()
                            play_network_error_audio()
                        else:
                            raise

            elif any(greeting.lower() in text.lower() for greeting in greetings_to_detect):
                feedback_text = get_random_greeting()
                provide_audio_feedback(feedback_text, language=current_language)
             # Check for inaugural address
            elif 'inaugural address' in text.lower() or'say inagural speech' in text.lower():
              #  sound_file_path =r"D:\Project Ai\Data\Sounds\introduction_xim.mp3"
              #  play_sound_file(sound_file_path)

            
                break
            # If none of the conditions match, do nothing
            else:
                break
                
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

# Function to save conversation history to a JSON file
def save_conversation_history(conversation_history):
    with open('conversation_history.json', 'w') as file:
        json.dump(conversation_history, file)

# Load conversation history
conversation_history = load_conversation_history()

# Start listening and responding
with sr.Microphone() as source:
    while True:
        try:
            listen_and_respond(source, conversation_history)
        except KeyboardInterrupt:
            print("Exiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            continue
