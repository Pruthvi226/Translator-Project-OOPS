from flask import Flask, render_template, request, jsonify, send_file
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import uuid

app = Flask(__name__)

class TranslationService:
    def translate_text(self, text, src_lang='auto', target_lang='en'):
        translator = GoogleTranslator(source=src_lang, target=target_lang)
        return translator.translate(text)

    def generate_tts(self, text, lang='en'):
        # Create a unique filename using UUID to avoid conflicts
        filename = f"static/{uuid.uuid4().hex}.mp3"
        # Use gTTS to generate speech and save it to the file
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        return filename

translator_service = TranslationService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text')
    src_lang = data.get('src_lang', 'auto')
    target_lang = data.get('target_lang', 'en')

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    try:
        translated_text = translator_service.translate_text(text, src_lang, target_lang)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get('text')
    lang = data.get('lang')

    if not text or not lang:
        return jsonify({'error': 'Text and language are required'}), 400

    try:
        # Generate the TTS file and get its path
        filename = translator_service.generate_tts(text, lang)
        # Return the URL where the audio file can be accessed
        return jsonify({'audio_url': f'/{filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<filename>')
def serve_audio(filename):
    # Serve the generated audio file
    return send_file(f"static/{filename}")

if __name__ == '__main__':
    # Ensure 'static' folder exists to store the MP3 files
    if not os.path.exists('static'):
        os.makedirs('static')
    # Run the Flask app in debug mode
    app.run(debug=True)