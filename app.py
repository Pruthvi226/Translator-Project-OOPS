from flask import Flask, render_template, request, jsonify, send_file
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import uuid

app = Flask(__name__)

# 1. TranslationService Class: Handles the translation and text-to-speech (TTS) functionality.
class TranslationService:
    def translate_text(self, text, src_lang='auto', target_lang='en'):
        """
        Translates the given text from source language to target language using Google Translator API.
        Encapsulation: This class encapsulates the translation logic.
        """
        translator = GoogleTranslator(source=src_lang, target=target_lang)
        return translator.translate(text)

    def generate_tts(self, text, lang='en'):
        """
        Generates a TTS (text-to-speech) audio file from the text.
        Encapsulation: This method encapsulates the TTS generation logic.
        """
        filename = f"static/{uuid.uuid4().hex}.mp3"  # Unique filename using UUID
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        return filename  # Returns the path to the generated audio file


# 2. LanguageHandler Class: Manages language-related tasks like validation and defaults.
class LanguageHandler:
    @staticmethod
    def validate_language(lang):
        """
        Validates the language code (for example, 'en', 'es', etc.).
        Static Method: This method doesn't depend on any instance of the class.
        """
        supported_languages = ['auto', 'en', 'es', 'fr', 'de']  # Example supported languages
        if lang not in supported_languages:
            raise ValueError(f"Unsupported language code: {lang}")
        return lang


# Initialize the TranslationService class and LanguageHandler
translator_service = TranslationService()

# 3. Flask Routes & Application Logic

@app.route('/')
def index():
    """
    The home route renders the index.html template for the frontend.
    """
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    """
    Route to handle translation requests.
    The method uses the TranslationService class to translate text.
    """
    data = request.json
    text = data.get('text')
    src_lang = data.get('src_lang', 'auto')
    target_lang = data.get('target_lang', 'en')

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    try:
        # Use the TranslationService to perform the translation
        translated_text = translator_service.translate_text(text, src_lang, target_lang)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts', methods=['POST'])
def tts():
    """
    Route to generate text-to-speech (TTS) for the given text.
    The method uses the TranslationService class to generate the TTS audio file.
    """
    data = request.json
    text = data.get('text')
    lang = data.get('lang')

    if not text or not lang:
        return jsonify({'error': 'Text and language are required'}), 400

    try:
        # Validate language before proceeding
        LanguageHandler.validate_language(lang)  # Using static method from LanguageHandler class
        
        # Generate the TTS file and get its path
        filename = translator_service.generate_tts(text, lang)
        return jsonify({'audio_url': f'/{filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<filename>')
def serve_audio(filename):
    """
    Route to serve the generated TTS audio file.
    """
    return send_file(f"static/{filename}")

# 4. Main block to ensure the application runs
if __name__ == '__main__':
    # Ensure 'static' folder exists to store the MP3 files
    if not os.path.exists('static'):
        os.makedirs('static')

    # Run the Flask app in debug mode
    app.run(debug=True)
