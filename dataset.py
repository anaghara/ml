import json
import os
import random
import tempfile
import time
import string
import nltk
import numpy as np
import pandas as pd
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from nltk import pos_tag
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

# Initialize speech recognizer
recognizer = sr.Recognizer()

def speak_gTTS(text):
    """Function to speak the given text using Google's Text-to-Speech via gTTS."""
    with tempfile.NamedTemporaryFile(delete=True) as fp:
        tts = gTTS(text=text, lang='en')
        tts.save(f"{fp.name}.mp3")
        sound = AudioSegment.from_mp3(f"{fp.name}.mp3")
        play(sound)

def recognize_speech():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio)
        return query
    except sr.UnknownValueError:
        speak_gTTS("Sorry, I couldn't understand what you said.")
        return None
    except sr.RequestError:
        speak_gTTS("Sorry, I'm unable to access the Google Speech Recognition API.")
        return None

def my_tokenizer(doc):
    """Tokenizes, removes stopwords and punctuation, and lemmatizes the text."""
    lemmatizer = WordNetLemmatizer()
    stopwords_list = set(stopwords.words('english'))
    
    words = word_tokenize(doc.lower())
    pos_tags = pos_tag(words)
    
    filtered_words = [(word, tag) for word, tag in pos_tags if word not in stopwords_list and word not in string.punctuation]
    
    lemmas = [lemmatizer.lemmatize(word, get_wordnet_pos(tag)) for word, tag in filtered_words]
    return lemmas

def get_wordnet_pos(treebank_tag):
    """Converts treebank POS tags to WordNet POS tags."""
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN  # Treat as noun if unknown

# Load and preprocess data
data_files = ['./S08_question_answer_pairs (1).txt', './S09_question_answer_pairs.txt', './S10_question_answer_pairs.txt']
data_frames = []
for file in data_files:
    df = pd.read_csv(file, sep='\t', encoding='ISO-8859-1' if 'S10' in file else 'utf-8')
    data_frames.append(df)
data = pd.concat(data_frames, ignore_index=True)
data.dropna(subset=['Question', 'Answer'], inplace=True)
data.drop_duplicates(subset='Question', inplace=True)
data['Question'] = data['Question'].str.strip().str.lower()
data['Answer'] = data['Answer'].str.strip().str.lower()

# Vectorization and SVD
tfidf_vectorizer = TfidfVectorizer(tokenizer=my_tokenizer)
tfidf_matrix = tfidf_vectorizer.fit_transform(data['Question'])

def find_answer(question):
    """Finds the answer to a given question using cosine similarity."""
    query_vector = tfidf_vectorizer.transform([question])
    similarity = cosine_similarity(query_vector, tfidf_matrix)
    index = np.argmax(similarity)
    return data.iloc[index]['Answer']

def ask_in_loop():
    """Asks continuously for user input, provides answers, and prints them."""
    while True:
        speak_gTTS("Please ask your question, or say 'stop' to exit.")
        question = recognize_speech()
        
        if question is None or question.lower() == 'stop':
            speak_gTTS("Goodbye!")
            print("Session ended by user.")  # Print session end confirmation
            break
        
        print(f"Question: {question}")  # Print the recognized question
        answer = find_answer(question)
        
        print(f"Answer: {answer}")  # Print the provided answer
        speak_gTTS("Here's the answer to your question:")
        speak_gTTS(answer)


if __name__ == "__main__":
    ask_in_loop()
