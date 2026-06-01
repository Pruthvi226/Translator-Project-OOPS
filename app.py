from flask import Flask, render_template, request, jsonify, send_file
from deep_translator import GoogleTranslator
from gtts import gTTS
from dotenv import load_dotenv
import google.generativeai as genai
import os
import uuid

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize Google Gemini API if key is present
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_UNLOCKED = False

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Verify connectivity / model availability
        ai_model = genai.GenerativeModel("gemini-1.5-flash")
        AI_UNLOCKED = True
        print("[AI Translator] Google Gemini API successfully configured and unlocked!")
    except Exception as e:
        print(f"[AI Translator] Error configuring Gemini API: {e}")
        AI_UNLOCKED = False
else:
    print("[AI Translator] GEMINI_API_KEY not found in environment. Running in Standard (Fallback) Mode.")


# =====================================================================
# 1. TRANSLATION SERVICES (OOP ENCAPSULATION)
# =====================================================================

class StandardTranslationService:
    """
    Handles translation and text-to-speech using standard free APIs.
    This serves as the robust fallback.
    """
    def translate_text(self, text, src_lang='auto', target_lang='en'):
        """Translates text using deep-translator (Google Translate wrapper)."""
        translator = GoogleTranslator(source=src_lang, target=target_lang)
        return translator.translate(text)

    def generate_tts(self, text, lang='en'):
        """Generates a Text-to-Speech MP3 audio file using gTTS."""
        # Ensure static folder exists
        if not os.path.exists('static'):
            os.makedirs('static')
            
        filename = f"static/{uuid.uuid4().hex}.mp3"
        # gTTS doesn't support 'auto' as language for speech synthesis, fallback to English
        synth_lang = 'en' if lang == 'auto' else lang
        try:
            tts = gTTS(text=text, lang=synth_lang)
            tts.save(filename)
        except Exception as e:
            # Fallback to general English synthesis if target language fails
            print(f"[TTS Fallback] Failed for language {synth_lang}, trying 'en'. Error: {e}")
            tts = gTTS(text=text, lang='en')
            tts.save(filename)
        return filename


class AITranslatorService:
    """
    Handles advanced cognitive translation, linguistic analysis,
    and interactive chat using Google's Gemini LLM.
    """
    def __init__(self):
        # Using gemini-1.5-flash for rapid, cost-effective, high-quality translation tasks
        self.model = genai.GenerativeModel("gemini-1.5-flash") if AI_UNLOCKED else None

    def translate_with_tone(self, text, src_lang='auto', target_lang='en', tone='professional'):
        """Translates text using Gemini with a specific context and tone."""
        if not AI_UNLOCKED or not self.model:
            raise RuntimeError("Gemini AI Service is not unlocked.")

        prompt = (
            f"You are an elite, professional translator. Translate the following text from "
            f"'{src_lang}' (source language) to '{target_lang}' (target language).\n\n"
            f"Requirements:\n"
            f"1. Maintain a '{tone}' tone (e.g. formal, casual, poetic, professional, slang/idiomatic, academic).\n"
            f"2. Keep the translation natural, accurate, and culturally appropriate.\n"
            f"3. Provide ONLY the translated text as the output. Do not add any quotes, markdown blocks, "
            f"introductory text, notes, or explanations.\n\n"
            f"Text to translate:\n{text}"
        )
        
        response = self.model.generate_content(prompt)
        translated_text = response.text.strip()
        
        # Clean up any potential accidental markdown code block wraps returned by LLM
        if translated_text.startswith("```") and translated_text.endswith("```"):
            lines = translated_text.split("\n")
            if len(lines) > 2:
                translated_text = "\n".join(lines[1:-1]).strip()
                
        return translated_text

    def generate_linguistic_insights(self, original_text, translated_text, src_lang, target_lang):
        """Generates detailed grammar breakdowns, vocabulary tables, and idioms in markdown."""
        if not AI_UNLOCKED or not self.model:
            raise RuntimeError("Gemini AI Service is not unlocked.")

        prompt = (
            f"You are a professional language teacher and linguistic analyst.\n"
            f"Analyze the translation from source language '{src_lang}' to target language '{target_lang}'.\n\n"
            f"Original Text: \"{original_text}\"\n"
            f"Translated Text: \"{translated_text}\"\n\n"
            f"Please generate a clean, beautiful analysis with the following structured sections:\n"
            f"1. **Grammar Breakdown**: Highlight 2-3 key grammatical patterns, verb tenses, sentence structures, "
            f"or agreement rules utilized in this translation. Keep the points educational and concise.\n"
            f"2. **Vocabulary Spotlight**: Construct a Markdown table featuring 3-5 important words or phrases. "
            f"Columns MUST be: `Vocabulary` | `Meaning/Translation` | `Part of Speech` | `Linguistic Tip / Nuance`.\n"
            f"3. **Cultural Context & Idioms**: Provide brief context on idiomatic equivalents, cultural nuances, "
            f"or interesting language trivia related to this translation. If there isn't a direct nuance, offer "
            f"a common idiom or helpful speaking tip in the target language.\n\n"
            f"Formatting: Return the response strictly in clean GitHub Flavored Markdown. Do not include any "
            f"greeting, intro, conversational filler, or wrap-up text."
        )
        
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def chat_tutor_response(self, original_text, translated_text, src_lang, target_lang, question, chat_history=None):
        """Answers a user's question about the translation in an interactive personal tutor tone."""
        if not AI_UNLOCKED or not self.model:
            raise RuntimeError("Gemini AI Service is not unlocked.")

        history_context = ""
        if chat_history:
            history_context = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-6:]])

        prompt = (
            f"You are 'Fluent Flow AI', a highly supportive, knowledgeable, and friendly personal language tutor.\n"
            f"The user is studying a translation.\n"
            f"Source Text ({src_lang}): \"{original_text}\"\n"
            f"Translation ({target_lang}): \"{translated_text}\"\n\n"
            f"Context (Previous Chat History):\n{history_context}\n\n"
            f"User's Question: \"{question}\"\n\n"
            f"Provide a clear, engaging, and brief explanation (1-2 short paragraphs max). Focus on teaching "
            f"pronunciation, alternate word choices, grammatical rules, or cultural differences related to their query. "
            f"Use clean Markdown formatting. Keep it encouraging and friendly!"
        )

        response = self.model.generate_content(prompt)
        return response.text.strip()


# Instantiate Services
standard_service = StandardTranslationService()
ai_service = AITranslatorService()


# =====================================================================
# 2. FLASK ROUTES
# =====================================================================

@app.route('/')
def index():
    """Renders the main single-page application frontend."""
    return render_template('index.html')


@app.route('/ai-status', methods=['GET'])
def ai_status():
    """Informs the frontend whether Gemini advanced AI capabilities are active."""
    return jsonify({
        'unlocked': AI_UNLOCKED,
        'mode': 'Advanced AI (Gemini)' if AI_UNLOCKED else 'Standard (Free API)'
    })


@app.route('/translate', methods=['POST'])
def translate():
    """
    Main translation endpoint. Handles standard translation requests
    and dynamically routes to LLM-translation if Gemini is unlocked and AI mode is requested.
    """
    data = request.json or {}
    text = data.get('text', '').strip()
    src_lang = data.get('src_lang', 'auto')
    target_lang = data.get('target_lang', 'en')
    use_ai = data.get('use_ai', False)
    tone = data.get('tone', 'professional').lower()

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    try:
        if use_ai and AI_UNLOCKED:
            print(f"[Translation] Translating using Gemini AI (Tone: {tone})...")
            translated_text = ai_service.translate_with_tone(text, src_lang, target_lang, tone)
            return jsonify({
                'translated_text': translated_text,
                'method': 'gemini_ai',
                'tone': tone
            })
        else:
            print(f"[Translation] Translating using Standard Google Translate...")
            translated_text = standard_service.translate_text(text, src_lang, target_lang)
            return jsonify({
                'translated_text': translated_text,
                'method': 'standard',
                'tone': 'default'
            })
    except Exception as e:
        print(f"[Translation Error] {e}")
        # Graceful fallback to standard translation if AI fails midway
        try:
            print("[Translation] AI failed, attempting Standard fallback...")
            translated_text = standard_service.translate_text(text, src_lang, target_lang)
            return jsonify({
                'translated_text': translated_text,
                'method': 'standard_fallback',
                'error_msg': str(e)
            })
        except Exception as fallback_err:
            return jsonify({'error': f"Translation failed: {str(fallback_err)}"}), 500


@app.route('/ai-insights', methods=['POST'])
def ai_insights():
    """Generates grammar, vocabulary spotlight, and cultural tips using Gemini."""
    if not AI_UNLOCKED:
        return jsonify({'error': 'Advanced AI is locked. Add GEMINI_API_KEY to unlock.'}), 403

    data = request.json or {}
    original_text = data.get('original_text', '').strip()
    translated_text = data.get('translated_text', '').strip()
    src_lang = data.get('src_lang', 'auto')
    target_lang = data.get('target_lang', 'en')

    if not original_text or not translated_text:
        return jsonify({'error': 'Original and translated text are required'}), 400

    try:
        insights = ai_service.generate_linguistic_insights(original_text, translated_text, src_lang, target_lang)
        return jsonify({'insights': insights})
    except Exception as e:
        return jsonify({'error': f"Failed to generate AI insights: {str(e)}"}), 500


@app.route('/chat', methods=['POST'])
def chat():
    """Converses with the language tutor AI regarding the translation context."""
    if not AI_UNLOCKED:
        return jsonify({'error': 'Advanced AI is locked. Add GEMINI_API_KEY to unlock.'}), 403

    data = request.json or {}
    original_text = data.get('original_text', '').strip()
    translated_text = data.get('translated_text', '').strip()
    src_lang = data.get('src_lang', 'auto')
    target_lang = data.get('target_lang', 'en')
    question = data.get('question', '').strip()
    chat_history = data.get('chat_history', [])

    if not original_text or not translated_text or not question:
        return jsonify({'error': 'Translation context and user question are required'}), 400

    try:
        reply = ai_service.chat_tutor_response(original_text, translated_text, src_lang, target_lang, question, chat_history)
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': f"Tutor chat failed: {str(e)}"}), 500


@app.route('/tts', methods=['POST'])
def tts():
    """Generates Text-to-Speech (TTS) MP3 file for the translated text."""
    data = request.json or {}
    text = data.get('text', '').strip()
    lang = data.get('lang', 'en')

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    try:
        filename = standard_service.generate_tts(text, lang)
        return jsonify({'audio_url': f'/{filename}'})
    except Exception as e:
        return jsonify({'error': f"TTS generation failed: {str(e)}"}), 500


@app.route('/static/<filename>')
def serve_audio(filename):
    """Serves the generated TTS audio files."""
    return send_file(f"static/{filename}")


# Ensure static directory exists
if not os.path.exists('static'):
    os.makedirs('static')

# Clean up static directory of old audio files on start
try:
    for file in os.listdir('static'):
        if file.endswith('.mp3'):
            os.remove(os.path.join('static', file))
    print("[AI Translator] Cleaned old audio assets.")
except Exception as e:
    print(f"[AI Translator] Error cleaning static folder: {e}")


if __name__ == '__main__':
    # Run Flask local development server
    app.run(host='0.0.0.0', port=5000, debug=True)
