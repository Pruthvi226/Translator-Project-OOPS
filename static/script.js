// Define the TranslationApp class, which handles all translation-related functionality
class TranslationApp {
  // Constructor initializes the languages and sets up the application
  constructor() {
      // Language codes and names are encapsulated within this.languages
      this.languages = {
          af: 'Afrikaans', am: 'Amharic', ar: 'Arabic', az: 'Azerbaijani', be: 'Belarusian', bg: 'Bulgarian',
          bn: 'Bengali', bs: 'Bosnian', ca: 'Catalan', ceb: 'Cebuano', co: 'Corsican', cs: 'Czech', cy: 'Welsh',
          da: 'Danish', de: 'German', el: 'Greek', en: 'English', eo: 'Esperanto', es: 'Spanish', et: 'Estonian',
          eu: 'Basque', fa: 'Persian', fi: 'Finnish', fr: 'French', fy: 'Frisian', ga: 'Irish', gd: 'Scots Gaelic',
          gl: 'Galician', gu: 'Gujarati', ha: 'Hausa', haw: 'Hawaiian', he: 'Hebrew', hi: 'Hindi', hmn: 'Hmong',
          hr: 'Croatian', ht: 'Haitian Creole', hu: 'Hungarian', hy: 'Armenian', id: 'Indonesian', ig: 'Igbo',
          is: 'Icelandic', it: 'Italian', iw: 'Hebrew', ja: 'Japanese', jw: 'Javanese', ka: 'Georgian', kk: 'Kazakh',
          km: 'Khmer', kn: 'Kannada', ko: 'Korean', ku: 'Kurdish (Kurmanji)', ky: 'Kyrgyz', la: 'Latin',
          lb: 'Luxembourgish', lo: 'Lao', lt: 'Lithuanian', lv: 'Latvian', mg: 'Malagasy', mi: 'Maori', mk: 'Macedonian',
          ml: 'Malayalam', mn: 'Mongolian', mr: 'Marathi', ms: 'Malay', mt: 'Maltese', my: 'Myanmar (Burmese)',
          ne: 'Nepali', nl: 'Dutch', no: 'Norwegian', ny: 'Chichewa', or: 'Odia', pa: 'Punjabi', pl: 'Polish',
          ps: 'Pashto', pt: 'Portuguese', ro: 'Romanian', ru: 'Russian', sd: 'Sindhi', si: 'Sinhala', sk: 'Slovak',
          sl: 'Slovenian', sm: 'Samoan', sn: 'Shona', so: 'Somali', sq: 'Albanian', sr: 'Serbian', st: 'Sesotho',
          su: 'Sundanese', sv: 'Swedish', sw: 'Swahili', ta: 'Tamil', te: 'Telugu', tg: 'Tajik', th: 'Thai',
          tl: 'Filipino', tr: 'Turkish', ug: 'Uyghur', uk: 'Ukrainian', ur: 'Urdu', uz: 'Uzbek', vi: 'Vietnamese',
          xh: 'Xhosa', yi: 'Yiddish', yo: 'Yoruba', 'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
          zu: 'Zulu'
      };

      // Cache DOM elements
      this.inputText = document.getElementById('inputText');
      this.outputText = document.getElementById('outputText');
      this.translateBtn = document.getElementById('translateBtn');
      this.readAloudBtn = document.getElementById('readAloudBtn');
      this.micBtn = document.getElementById('micBtn');
      this.clearBtn = document.getElementById('clearBtn');
      this.sourceLangSelect = document.getElementById('sourceLang');
      this.targetLangSelect = document.getElementById('targetLang');
      this.swapButton = document.getElementById('swapLangs');

      this.recognition = null;
      this.isListening = false;
      this.speechRecognitionLanguages = {
          af: 'af-ZA', am: 'am-ET', ar: 'ar-SA', en: 'en-US', es: 'es-ES', fr: 'fr-FR', de: 'de-DE',
      };

      // Initialize the app
      this.initialize();
  }

  // Initialize the app by setting up event listeners and populating the languages
  initialize() {
      this.populateLanguages();  // Populate the dropdowns with available languages

      // Set default language selections
      this.sourceLangSelect.value = 'auto';  // Default to auto detect
      this.targetLangSelect.value = 'en';    // Default to English

      // Event listeners
      this.translateBtn.addEventListener('click', this.handleTranslate.bind(this));
      this.readAloudBtn.addEventListener('click', this.handleReadAloud.bind(this));
      this.micBtn.addEventListener('click', this.handleMicInput.bind(this));
      this.clearBtn.addEventListener('click', this.handleClear.bind(this));
      this.swapButton.addEventListener('click', this.handleSwapLanguages.bind(this));

      // Initialize language selects using TomSelect
      new TomSelect("#sourceLang", { create: false, sortField: { field: "text", direction: "asc" } });
      new TomSelect("#targetLang", { create: false, sortField: { field: "text", direction: "asc" } });

      // Adjust textarea height based on content
      this.inputText.addEventListener('input', () => this.autoExpand(this.inputText));
      this.outputText.addEventListener('input', () => this.autoExpand(this.outputText));

      // Initialize the textareas when the page loads
      window.addEventListener('load', () => {
          this.autoExpand(this.inputText);
          this.autoExpand(this.outputText);
      });
  }

  // Populate the source and target language dropdowns
  populateLanguages() {
      // Add "Auto Detect" option to source language select
      const autoOption = document.createElement('option');
      autoOption.value = 'auto';
      autoOption.textContent = 'Auto Detect';
      this.sourceLangSelect.appendChild(autoOption);

      // Populate other languages for both source and target selects
      for (const code in this.languages) {
          const option1 = document.createElement('option');
          option1.value = code;
          option1.textContent = this.languages[code];
          this.sourceLangSelect.appendChild(option1);

          const option2 = document.createElement('option');
          option2.value = code;
          option2.textContent = this.languages[code];
          this.targetLangSelect.appendChild(option2);
      }
  }

  // Automatically expand the textarea based on content
  autoExpand(textarea) {
      textarea.style.height = "auto";  // Reset the height to auto
      textarea.style.height = textarea.scrollHeight + "px";  // Set height based on content
  }

  // Handle translation functionality
  async handleTranslate() {
      const text = this.inputText.value.trim();
      if (!text) return;  // Exit if input is empty

      const response = await fetch('/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
              text: text,
              src_lang: this.sourceLangSelect.value,
              target_lang: this.targetLangSelect.value
          })
      });

      const data = await response.json();
      if (data.translated_text) {
          this.outputText.value = data.translated_text;  // Set translated text in output box
      } else {
          alert('Translation error.');
      }
  }

  // Handle the "read aloud" functionality
  async handleReadAloud() {
      const text = this.outputText.value.trim();
      if (!text) return;  // Exit if output text is empty

      const response = await fetch('/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
              text: text,
              lang: this.targetLangSelect.value
          })
      });

      const data = await response.json();
      if (data.audio_url) {
          const audio = new Audio(data.audio_url);
          audio.play();  // Play the audio for TTS
      } else {
          alert('TTS error.');
      }
  }

  // Handle voice input using the microphone
  handleMicInput() {
      if (!('webkitSpeechRecognition' in window)) {
          alert('Speech Recognition not supported');
          return;
      }

      if (!this.recognition) {
          this.recognition = new webkitSpeechRecognition();
          this.recognition.lang = this.speechRecognitionLanguages[this.sourceLangSelect.value] || 'en-US';
          this.recognition.interimResults = false;
          this.recognition.continuous = false;

          this.recognition.onresult = (event) => {
              const transcript = event.results[0][0].transcript;
              this.inputText.value += transcript + " ";  // Add transcript to input text
          };

          this.recognition.onerror = (event) => {
              console.error('Mic error:', event.error);
              alert('Error: ' + event.error);
          };

          this.recognition.onend = () => {
              this.isListening = false;
              this.micBtn.innerText = "🎤 Voice Input";
          };
      }

      if (!this.isListening) {
          this.recognition.start();
          this.isListening = true;
          this.micBtn.innerText = "🔴 Listening...";
      } else {
          this.recognition.stop();
      }
  }

  // Clear input and output text
  handleClear() {
      this.inputText.value = '';
      this.outputText.value = '';
  }

  // Swap the selected languages between source and target
  handleSwapLanguages() {
      const temp = this.sourceLangSelect.value;
      this.sourceLangSelect.value = this.targetLangSelect.value;
      this.targetLangSelect.value = temp;
  }
}

// Instantiate the TranslationApp class to initialize the app
const app = new TranslationApp();
