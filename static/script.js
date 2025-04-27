const inputText = document.getElementById('inputText');
const outputText = document.getElementById('outputText');
const translateBtn = document.getElementById('translateBtn');
const readAloudBtn = document.getElementById('readAloudBtn');
const micBtn = document.getElementById('micBtn');
const clearBtn = document.getElementById('clearBtn');
const sourceLangSelect = document.getElementById('sourceLang');
const targetLangSelect = document.getElementById('targetLang');
const swapButton = document.getElementById('swapLangs');

let recognition;
let isListening = false;

const languages = {
    auto: 'Auto Detect',
    af: 'Afrikaans',
    am: 'Amharic',
    ar: 'Arabic',
    en: 'English',
    es: 'Spanish',
    fr: 'French',
    de: 'German',
    // Add more languages as needed
};

const speechRecognitionLanguages = {
    af: 'af-ZA', am: 'am-ET', ar: 'ar-SA', en: 'en-US', es: 'es-ES', fr: 'fr-FR', de: 'de-DE',
};

const autoExpand = (textarea) => {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
};

inputText.addEventListener('input', () => autoExpand(inputText));
outputText.addEventListener('input', () => autoExpand(outputText));

window.addEventListener('load', () => {
    autoExpand(inputText);
    autoExpand(outputText);
});

function populateLanguages() {
    for (const code in languages) {
        const option1 = document.createElement('option');
        option1.value = code;
        option1.textContent = languages[code];
        sourceLangSelect.appendChild(option1);

        const option2 = document.createElement('option');
        option2.value = code;
        option2.textContent = languages[code];
        targetLangSelect.appendChild(option2);
    }
}

populateLanguages();

new TomSelect("#sourceLang", {
    create: false,
    sortField: {
        field: "text",
        direction: "asc"
    }
});

new TomSelect("#targetLang", {
    create: false,
    sortField: {
        field: "text",
        direction: "asc"
    }
});

translateBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    if (!text) return;

    const response = await fetch('/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: text,
            src_lang: sourceLangSelect.value,
            target_lang: targetLangSelect.value
        })
    });

    const data = await response.json();
    if (data.translated_text) {
        outputText.value = data.translated_text;
    } else {
        alert('Translation error.');
    }
});

readAloudBtn.addEventListener('click', async () => {
    const text = outputText.value.trim();
    if (!text) return;

    const response = await fetch('/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: text,
            lang: targetLangSelect.value
        })
    });

    const data = await response.json();
    if (data.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.play();
    } else {
        alert('TTS error.');
    }
});

micBtn.addEventListener('click', () => {
    if (!('webkitSpeechRecognition' in window)) {
        alert('Speech Recognition not supported');
        return;
    }

    if (!recognition) {
        recognition = new webkitSpeechRecognition();
        recognition.lang = speechRecognitionLanguages[sourceLangSelect.value] || 'en-US';
        recognition.interimResults = false;
        recognition.continuous = false;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            inputText.value += transcript + " ";
        };

        recognition.onerror = (event) => {
            console.error('Mic error:', event.error);
            alert('Error: ' + event.error);
        };

        recognition.onend = () => {
            isListening = false;
            micBtn.innerText = "🎤 Voice Input";
        };
    }

    if (!isListening) {
        recognition.start();
        isListening = true;
        micBtn.innerText = "🔴 Listening...";
    } else {
        recognition.stop();
    }
});

clearBtn.addEventListener('click', () => {
    inputText.value = '';
    outputText.value = '';
});

swapButton.addEventListener('click', () => {
    const temp = sourceLangSelect.value;
    sourceLangSelect.value = targetLangSelect.value;
    targetLangSelect.value = temp;
});
