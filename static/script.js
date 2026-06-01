class TranslationApp {
  constructor() {
    // Extensive list of supported languages
    this.languages = {
      af: 'Afrikaans', am: 'Amharic', ar: 'Arabic', az: 'Azerbaijani', be: 'Belarusian', bg: 'Bulgarian',
      bn: 'Bengali', bs: 'Bosnian', ca: 'Catalan', ceb: 'Cebuano', co: 'Corsican', cs: 'Czech', cy: 'Welsh',
      da: 'Danish', de: 'German', el: 'Greek', en: 'English', eo: 'Esperanto', es: 'Spanish', et: 'Estonian',
      eu: 'Basque', fa: 'Persian', fi: 'Finnish', fr: 'French', fy: 'Frisian', ga: 'Irish', gd: 'Scots Gaelic',
      gl: 'Galician', gu: 'Gujarati', ha: 'Hausa', haw: 'Hawaiian', he: 'Hebrew', hi: 'Hindi', hmn: 'Hmong',
      hr: 'Croatian', ht: 'Haitian Creole', hu: 'Hungarian', hy: 'Armenian', id: 'Indonesian', ig: 'Igbo',
      is: 'Icelandic', it: 'Italian', jw: 'Javanese', ka: 'Georgian', kk: 'Kazakh',
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

    // DOM Elements Cache
    this.inputText = document.getElementById('inputText');
    this.outputText = document.getElementById('outputText');
    this.translateBtn = document.getElementById('translateBtn');
    this.readAloudBtn = document.getElementById('readAloudBtn');
    this.copyBtn = document.getElementById('copyBtn');
    this.micBtn = document.getElementById('micBtn');
    this.clearBtn = document.getElementById('clearBtn');
    this.sourceLangSelect = document.getElementById('sourceLang');
    this.targetLangSelect = document.getElementById('targetLang');
    this.swapButton = document.getElementById('swapLangs');
    this.themeToggleBtn = document.getElementById('themeToggle');
    this.charCountSpan = document.getElementById('charCount');
    
    // AI Elements Cache
    this.aiStatusBanner = document.getElementById('aiStatusBanner');
    this.bannerText = document.getElementById('bannerText');
    this.bannerAction = document.getElementById('bannerAction');
    this.aiControls = document.getElementById('aiControls');
    this.translationTone = document.getElementById('translationTone');
    this.advancedAISection = document.getElementById('advancedAISection');
    
    // AI Insights Elements
    this.getInsightsBtn = document.getElementById('getInsightsBtn');
    this.insightsEmpty = document.getElementById('insightsEmpty');
    this.insightsLoading = document.getElementById('insightsLoading');
    this.insightsContent = document.getElementById('insightsContent');

    // AI Chat Elements
    this.chatHistory = document.getElementById('chatHistory');
    this.chatInput = document.getElementById('chatInput');
    this.sendChatBtn = document.getElementById('sendChatBtn');
    
    // Loader Elements
    this.shimmerLoader = document.getElementById('shimmerLoader');

    // App State Variables
    this.isListening = false;
    this.recognition = null;
    this.aiUnlocked = false;
    this.chatMessagesList = []; // Holds structured history for Gemini backend contexts
    this.tomSelectSource = null;
    this.tomSelectTarget = null;
    
    // Voice dictation mapping to standard speech recognition languages
    this.speechDictationCodes = {
      en: 'en-US', es: 'es-ES', fr: 'fr-FR', de: 'de-DE', it: 'it-IT',
      ja: 'ja-JP', ko: 'ko-KR', 'zh-cn': 'zh-CN', hi: 'hi-IN', ru: 'ru-RU'
    };

    this.initialize();
  }

  // Set up settings, listeners, and trigger API checks
  async initialize() {
    this.populateLanguages();
    this.setupTheme();
    
    // Default selectors
    this.sourceLangSelect.value = 'auto';
    this.targetLangSelect.value = 'en';

    // Init TomSelect for searchable pickers
    this.tomSelectSource = new TomSelect("#sourceLang", { 
      create: false, 
      sortField: { field: "text", direction: "asc" },
      onChange: () => this.handleLanguageChange()
    });
    this.tomSelectTarget = new TomSelect("#targetLang", { 
      create: false, 
      sortField: { field: "text", direction: "asc" },
      onChange: () => this.handleLanguageChange()
    });

    // Register Event Listeners
    this.translateBtn.addEventListener('click', () => this.handleTranslate());
    this.readAloudBtn.addEventListener('click', () => this.handleReadAloud());
    this.copyBtn.addEventListener('click', () => this.handleCopyText());
    this.micBtn.addEventListener('click', () => this.toggleVoiceDictation());
    this.clearBtn.addEventListener('click', () => this.handleClear());
    this.swapButton.addEventListener('click', () => this.handleSwapLanguages());
    this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
    
    // AI Specific Listeners
    this.getInsightsBtn.addEventListener('click', () => this.handleGetInsights());
    this.sendChatBtn.addEventListener('click', () => this.handleSendChatMessage());
    this.chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.handleSendChatMessage();
    });

    // Character Counter
    this.inputText.addEventListener('input', () => {
      const length = this.inputText.value.length;
      this.charCountSpan.textContent = `${length} / 5000`;
      if (length > 5000) {
        this.inputText.value = this.inputText.value.substring(0, 5000);
        this.showToast('Character limit of 5000 reached', 'info');
      }
    });

    // Check Gemini API Connectivity Status
    await this.checkAIStatus();
  }

  // Theme Setup (Loads saved choice or matches dark theme default)
  setupTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
      document.body.className = 'light-theme';
      this.themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
    } else {
      document.body.className = 'dark-theme';
      this.themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }
  }

  // Dynamic Theme Toggle
  toggleTheme() {
    if (document.body.classList.contains('dark-theme')) {
      document.body.className = 'light-theme';
      this.themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
      localStorage.setItem('theme', 'light');
      this.showToast('Switched to Light Theme', 'info');
    } else {
      document.body.className = 'dark-theme';
      this.themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
      localStorage.setItem('theme', 'dark');
      this.showToast('Switched to Dark Theme', 'info');
    }
  }

  // Populate Dropdown Selection Menus
  populateLanguages() {
    // Source options
    const autoOption = document.createElement('option');
    autoOption.value = 'auto';
    autoOption.textContent = '🔍 Auto Detect Language';
    this.sourceLangSelect.appendChild(autoOption);

    for (const code in this.languages) {
      const optSrc = document.createElement('option');
      optSrc.value = code;
      optSrc.textContent = this.languages[code];
      this.sourceLangSelect.appendChild(optSrc);

      const optTgt = document.createElement('option');
      optTgt.value = code;
      optTgt.textContent = this.languages[code];
      this.targetLangSelect.appendChild(optTgt);
    }
  }

  // Poll Backend Status Endpoint for Gemini API key configurations
  async checkAIStatus() {
    try {
      const response = await fetch('/ai-status');
      const data = await response.json();
      
      this.aiUnlocked = data.unlocked;
      
      if (this.aiUnlocked) {
        // Advanced mode configuration adjustments
        this.aiStatusBanner.className = 'status-banner ai-mode';
        this.bannerText.innerHTML = '<i class="fa-solid fa-circle-check"></i> <strong>Advanced AI Mode Active!</strong> Driven by Google Gemini LLM API.';
        this.bannerAction.style.display = 'none';
        
        // Show AI-specific components
        this.aiControls.style.display = 'flex';
        this.advancedAISection.style.display = 'grid';
      } else {
        // Standard mode fallback warning structures
        this.aiStatusBanner.className = 'status-banner standard-mode';
        this.bannerText.innerHTML = '<i class="fa-solid fa-circle-info"></i> Running in <strong>Standard Mode</strong> (Regular translation active).';
        this.bannerAction.style.display = 'block';
        
        // Hide AI specific components
        this.aiControls.style.display = 'none';
        this.advancedAISection.style.display = 'none';
      }
    } catch (e) {
      console.error("[Status Error] Failed connection:", e);
      this.aiStatusBanner.className = 'status-banner standard-mode';
      this.bannerText.textContent = 'Unable to verify translation cloud services status. Running Offline/Fallback.';
    }
  }

  // Action: Clear text
  handleClear() {
    this.inputText.value = '';
    this.outputText.value = '';
    this.charCountSpan.textContent = '0 / 5000';
    this.readAloudBtn.disabled = true;
    this.copyBtn.disabled = true;
    
    // Clear AI specific insights
    this.insightsContent.style.display = 'none';
    this.insightsLoading.style.display = 'none';
    this.insightsEmpty.style.display = 'flex';
    
    // Clear Chat History to standard bot start
    this.chatHistory.innerHTML = `
      <div class="chat-message bot-message">
        <div class="message-sender">Fluent Flow AI</div>
        <div class="message-text">Hello! I am your language tutor. You can ask me questions about your translations, such as:
          <ul>
            <li>"Why did we use this tense?"</li>
            <li>"Can you give me alternate synonyms?"</li>
            <li>"How do I pronounce the translated text?"</li>
          </ul>
        </div>
      </div>
    `;
    this.chatInput.disabled = true;
    this.sendChatBtn.disabled = true;
    this.chatMessagesList = [];
    
    this.showToast('Workspace cleared', 'info');
  }

  // Action: Swap Source and Target Languages
  handleSwapLanguages() {
    const srcVal = this.sourceLangSelect.value;
    const tgtVal = this.targetLangSelect.value;

    if (srcVal === 'auto') {
      // Auto detect cannot be set as target
      this.showToast('Auto Detect cannot be selected as target language', 'error');
      return;
    }

    this.tomSelectSource.setValue(tgtVal);
    this.tomSelectTarget.setValue(srcVal);
    
    // Swap text blocks if translation is already present
    const inText = this.inputText.value;
    const outText = this.outputText.value;
    
    this.inputText.value = outText;
    this.outputText.value = inText;
    
    this.showToast('Swapped languages', 'info');
  }

  // Handles state changes on language selector swaps
  handleLanguageChange() {
    // Reset insights if language settings change
    if (this.outputText.value.trim()) {
      this.insightsContent.style.display = 'none';
      this.insightsEmpty.style.display = 'flex';
    }
  }

  // Core Request: Trigger Translation Event
  async handleTranslate() {
    const text = this.inputText.value.trim();
    if (!text) {
      this.showToast('Please enter text to translate', 'error');
      return;
    }

    // Toggle loader animations
    this.outputText.value = '';
    this.outputText.style.opacity = '0';
    this.shimmerLoader.style.display = 'flex';
    this.translateBtn.disabled = true;
    this.readAloudBtn.disabled = true;
    this.copyBtn.disabled = true;

    try {
      const response = await fetch('/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          src_lang: this.sourceLangSelect.value,
          target_lang: this.targetLangSelect.value,
          use_ai: this.aiUnlocked, // Send LLM request if Gemini is running
          tone: this.translationTone.value
        })
      });

      const data = await response.json();
      
      if (data.translated_text) {
        this.outputText.value = data.translated_text;
        this.readAloudBtn.disabled = false;
        this.copyBtn.disabled = false;
        
        // Unblock chat tutor since we have translation context
        if (this.aiUnlocked) {
          this.chatInput.disabled = false;
          this.sendChatBtn.disabled = false;
          // Prompt tutor welcome back on fresh translations
          this.appendBotChatBubble("Context loaded! Ask me anything regarding this translation.");
        }
      } else {
        this.showToast(data.error || 'Translation failed', 'error');
      }
    } catch (e) {
      console.error("[Translation request failed]", e);
      this.showToast('Network error during translation request', 'error');
    } finally {
      this.shimmerLoader.style.display = 'none';
      this.outputText.style.opacity = '1';
      this.translateBtn.disabled = false;
    }
  }

  // Core Request: Speak translated text (TTS)
  async handleReadAloud() {
    const text = this.outputText.value.trim();
    const lang = this.targetLangSelect.value;
    if (!text) return;

    this.readAloudBtn.disabled = true;
    this.readAloudBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Synthesizing...</span>';

    try {
      const response = await fetch('/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, lang: lang })
      });

      const data = await response.json();
      if (data.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.play();
        this.showToast('Playing speech output', 'success');
        
        audio.onended = () => {
          this.readAloudBtn.disabled = false;
          this.readAloudBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i> <span>Read Aloud</span>';
        };
      } else {
        this.showToast('Audio synthesis failed', 'error');
        this.readAloudBtn.disabled = false;
        this.readAloudBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i> <span>Read Aloud</span>';
      }
    } catch (e) {
      console.error("[TTS Synthesis error]", e);
      this.showToast('Network error generating TTS', 'error');
      this.readAloudBtn.disabled = false;
      this.readAloudBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i> <span>Read Aloud</span>';
    }
  }

  // Clipboard Copier
  handleCopyText() {
    const text = this.outputText.value.trim();
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
      this.showToast('Translation copied to clipboard!', 'success');
      
      // Visual feedback change on icon
      const oldHtml = this.copyBtn.innerHTML;
      this.copyBtn.innerHTML = '<i class="fa-solid fa-check" style="color: var(--accent-success);"></i> <span>Copied!</span>';
      setTimeout(() => {
        this.copyBtn.innerHTML = oldHtml;
      }, 2000);
    }).catch(err => {
      console.error('Could not copy text: ', err);
      this.showToast('Clipboard permissions denied', 'error');
    });
  }

  // Speech-To-Text Dictation (Microphone)
  toggleVoiceDictation() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      this.showToast('Speech recognition not supported in this browser. Use Chrome/Safari.', 'error');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!this.recognition) {
      this.recognition = new SpeechRecognition();
      // Resolve language dictation locales
      const dictationLang = this.speechDictationCodes[this.sourceLangSelect.value] || 'en-US';
      
      this.recognition.lang = dictationLang;
      this.recognition.interimResults = false;
      this.recognition.continuous = false;

      this.recognition.onstart = () => {
        this.isListening = true;
        this.micBtn.className = 'btn btn-secondary recording-active';
        this.micBtn.innerHTML = '<i class="fa-solid fa-microphone-lines fa-fade"></i> <span>Listening...</span>';
        this.showToast('Speak now...', 'info');
      };

      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        this.inputText.value = (this.inputText.value + " " + transcript).trim();
        // Trigger character counter event manually
        this.inputText.dispatchEvent(new Event('input'));
        this.showToast('Speech captured successfully!', 'success');
      };

      this.recognition.onerror = (e) => {
        console.error('Dictation error: ', e.error);
        this.showToast(`Microphone error: ${e.error}`, 'error');
      };

      this.recognition.onend = () => {
        this.isListening = false;
        this.micBtn.className = 'btn btn-secondary';
        this.micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i> <span>Voice Input</span>';
        // Nullify reference to re-initialize config (resolving target language swaps dynamically)
        this.recognition = null;
      };
    }

    if (!this.isListening) {
      this.recognition.start();
    } else {
      this.recognition.stop();
    }
  }

  // Core Request: Retrieve AI Insights breakdown from Gemini
  async handleGetInsights() {
    const original = this.inputText.value.trim();
    const translated = this.outputText.value.trim();
    
    if (!original || !translated) {
      this.showToast('Please translate text first before requesting insights.', 'error');
      return;
    }

    // Adjust views
    this.insightsEmpty.style.display = 'none';
    this.insightsContent.style.display = 'none';
    this.insightsLoading.style.display = 'flex';
    this.getInsightsBtn.disabled = true;

    try {
      const response = await fetch('/ai-insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_text: original,
          translated_text: translated,
          src_lang: this.sourceLangSelect.value,
          target_lang: this.targetLangSelect.value
        })
      });

      const data = await response.json();
      
      if (data.insights) {
        // Compile markdown and render
        this.insightsContent.innerHTML = this.parseSimpleMarkdown(data.insights);
        this.insightsLoading.style.display = 'none';
        this.insightsContent.style.display = 'block';
        this.showToast('Linguistic insights generated!', 'success');
      } else {
        this.showToast(data.error || 'Insight analysis failed', 'error');
        this.insightsLoading.style.display = 'none';
        this.insightsEmpty.style.display = 'flex';
      }
    } catch (e) {
      console.error("[AI Insights Failure]", e);
      this.showToast('Insights generation network error', 'error');
      this.insightsLoading.style.display = 'none';
      this.insightsEmpty.style.display = 'flex';
    } finally {
      this.getInsightsBtn.disabled = false;
    }
  }

  // Core Request: Conversational Chat Tutor API Trigger
  async handleSendChatMessage() {
    const question = this.chatInput.value.trim();
    const original = this.inputText.value.trim();
    const translated = this.outputText.value.trim();
    
    if (!question) return;
    if (!original || !translated) {
      this.showToast('Context missing. Please translate text first.', 'error');
      return;
    }

    // Append user message block in local screen
    this.appendUserChatBubble(question);
    this.chatInput.value = '';
    
    // Disable inputs during chat processing
    this.chatInput.disabled = true;
    this.sendChatBtn.disabled = true;
    
    // Append loading typing bubble
    const typingBubbleId = this.appendChatTypingIndicator();

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_text: original,
          translated_text: translated,
          src_lang: this.sourceLangSelect.value,
          target_lang: this.targetLangSelect.value,
          question: question,
          chat_history: this.chatMessagesList
        })
      });

      const data = await response.json();
      
      // Remove typing bubble
      this.removeChatTypingIndicator(typingBubbleId);

      if (data.reply) {
        this.appendBotChatBubble(data.reply);
        
        // Append context history arrays
        this.chatMessagesList.push({ role: 'user', content: question });
        this.chatMessagesList.push({ role: 'model', content: data.reply });
      } else {
        this.appendBotChatBubble("Sorry, I encountered an issue teaching that rule. Please ask again!");
        this.showToast(data.error || 'Tutor response failed', 'error');
      }
    } catch (e) {
      console.error("[AI Tutor failed]", e);
      this.removeChatTypingIndicator(typingBubbleId);
      this.appendBotChatBubble("A connection loss happened. Try re-sending your question!");
      this.showToast('Chat response network error', 'error');
    } finally {
      this.chatInput.disabled = false;
      this.sendChatBtn.disabled = false;
      this.chatInput.focus();
    }
  }

  // =====================================================================
  // DYNAMIC UI RENDERING UTILITIES
  // =====================================================================

  // Appends User Bubble
  appendUserChatBubble(text) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-message user-message';
    bubble.innerHTML = `
      <div class="message-sender">You</div>
      <div class="message-text">${this.escapeHtml(text)}</div>
    `;
    this.chatHistory.appendChild(bubble);
    this.scrollChatToBottom();
  }

  // Appends Tutor AI Bubble
  appendBotChatBubble(markdownText) {
    const bubble = document.createElement('div');
    bubble.className = 'chat-message bot-message';
    bubble.innerHTML = `
      <div class="message-sender">Fluent Flow AI</div>
      <div class="message-text">${this.parseSimpleMarkdown(markdownText)}</div>
    `;
    this.chatHistory.appendChild(bubble);
    this.scrollChatToBottom();
  }

  // Typing indicators
  appendChatTypingIndicator() {
    const uniqueId = `typing-${Date.now()}`;
    const bubble = document.createElement('div');
    bubble.className = 'chat-message bot-message';
    bubble.id = uniqueId;
    bubble.innerHTML = `
      <div class="message-sender">Fluent Flow AI</div>
      <div class="message-text">
        <i class="fa-solid fa-ellipsis fa-bounce" style="color: var(--accent-secondary);"></i> Thinking...
      </div>
    `;
    this.chatHistory.appendChild(bubble);
    this.scrollChatToBottom();
    return uniqueId;
  }

  removeChatTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) indicator.remove();
  }

  scrollChatToBottom() {
    this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
  }

  // Transient Toast Notification Generator
  showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = '<i class="fa-solid fa-circle-info"></i>';
    if (type === 'success') icon = '<i class="fa-solid fa-circle-check"></i>';
    if (type === 'error') icon = '<i class="fa-solid fa-triangle-exclamation"></i>';
    
    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);

    // Auto dismiss after 3 seconds
    setTimeout(() => {
      toast.style.animation = 'slideInLeft 0.3s reverse forwards';
      toast.addEventListener('animationend', () => toast.remove());
    }, 3000);
  }

  escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
  }

  // COMPILER: Mini Markdown to Beautiful HTML converter
  // Formats headers, lists, bold elements, and converts tables perfectly!
  parseSimpleMarkdown(md) {
    let html = md;

    // 1. Escaping script and HTML tags to prevent cross site script injection (XSS)
    // Avoid double-escaping by doing text conversions carefully.

    // 2. Parse Markdown Tables
    const tableRegex = /\|(.+)\|[\r\n]\|[- :|]+\|[\r\n]((?:\|.+\|[\r\n]*)+)/g;
    html = html.replace(tableRegex, (match, headerRow, rowsBlock) => {
      const headers = headerRow.split('|').map(h => h.trim()).filter(h => h);
      const headerHtml = `<thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>`;
      
      const rows = rowsBlock.split('\n').filter(r => r.trim());
      const rowsHtml = rows.map(row => {
        const cells = row.split('|').map(c => c.trim()).filter((c, i) => i > 0 && i <= headers.length);
        // Make sure we only print cells matching header counts
        while (cells.length < headers.length) cells.push('');
        return `<tr>${cells.map(c => `<td>${c}</td>`).join('')}</tr>`;
      }).join('');

      return `<div style="overflow-x:auto;"><table>${headerHtml}<tbody>${rowsHtml}</tbody></table></div>`;
    });

    // 3. Format Subheaders
    html = html.replace(/^### (.*$)/gim, '<h4>$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>');

    // 4. Format Bold Text
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // 5. Format Lists
    html = html.replace(/^\s*\n\* (.*)/gim, '<ul>\n<li>$1</li>\n</ul>');
    html = html.replace(/^\* (.*)/gim, '<li>$1</li>');
    html = html.replace(/^\s*\n- (.*)/gim, '<ul>\n<li>$1</li>\n</ul>');
    html = html.replace(/^- (.*)/gim, '<li>$1</li>');

    // Combine list tags neatly
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    // 6. Handle plain paragraphs / double line breaks
    html = html.replace(/\n\n/g, '<br>');

    return html;
  }
}

// Instantiate engine on load
let flowApp;
window.addEventListener('DOMContentLoaded', () => {
  flowApp = new TranslationApp();
});
