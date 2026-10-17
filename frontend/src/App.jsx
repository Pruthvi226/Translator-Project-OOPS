import React, { useEffect, useRef, useState } from 'react';
import { ArrowDownToLine, ArrowLeftRight, ArrowRight, AudioLines, BookOpen, Check, ChevronRight, Clipboard, FileText, Globe2, History, Image, Languages, LayoutDashboard, LogOut, Menu, MessageCircle, Mic, Moon, Plus, Send, Settings, ShieldCheck, Sparkles, Sun, Trash2, Volume2, X } from 'lucide-react';
import { api, apiAvailable, browserOnly, download, setToken } from './api';

import { clearDeviceData, devicePreferences, deviceUser, extractOnDevice } from './browser';

const defaultLanguages = { en: 'English', hi: 'Hindi', kn: 'Kannada', ta: 'Tamil', te: 'Telugu', mr: 'Marathi', bn: 'Bengali', es: 'Spanish', fr: 'French', de: 'German', ja: 'Japanese', ar: 'Arabic' };
const navigation = [['translate', Languages, 'Translation studio'], ['tutor', MessageCircle, 'Language tutor'], ['history', History, 'Your translations'], ['vocabulary', BookOpen, 'Vocabulary'], ['evaluation', LayoutDashboard, 'Usage & evaluation']];
const modes = [['text', Languages, 'Text'], ['voice', AudioLines, 'Voice'], ['image', Image, 'Image'], ['document', FileText, 'Document']];
const initialTheme = () => { try { return localStorage.getItem('fluentflow-theme') || 'light'; } catch { return 'light'; } };

export default function App() {
  const [page, setPage] = useState('translate');
  const [mode, setMode] = useState('text');
  const [theme, setTheme] = useState(initialTheme);
  const [mobile, setMobile] = useState(false);
  const [caps, setCaps] = useState(null);
  const [serviceOffline, setServiceOffline] = useState(false);
  const [user, setUser] = useState(browserOnly ? deviceUser : null);
  const [auth, setAuthState] = useState(null);
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [text, setText] = useState('');
  const [src, setSrc] = useState(browserOnly ? 'en' : 'auto');
  const [target, setTarget] = useState(() => browserOnly ? devicePreferences().target_lang || 'hi' : 'hi');
  const [tone, setTone] = useState('professional');
  const [provider, setProvider] = useState('auto');
  const [result, setResult] = useState(null);
  const [file, setFile] = useState(null);
  const [ocrLanguage, setOcrLanguage] = useState('eng');
  const [job, setJob] = useState(null);
  const [preview, setPreview] = useState('');
  const [items, setItems] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [question, setQuestion] = useState('');
  const [turns, setTurns] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [useRag, setUseRag] = useState(false);
  const [session, setSession] = useState(() => crypto.randomUUID());
  const [recording, setRecording] = useState(false);
  const recorder = useRef(null);
  const stream = useRef(null);
  const recognition = useRef(null);
  const audio = useRef(null);
  const audioUrl = useRef(null);
  const languages = caps?.languages || defaultLanguages;
  const message = (error) => { setNotice(error.message || String(error)); if (error.status === 401) { setToken(''); setUser(null); setAuth('login'); } };

  useEffect(() => { api('/capabilities').then(setCaps).catch(() => { setServiceOffline(true); if (apiAvailable) setNotice('Translation service is unavailable. Please try again later.'); }); }, []);
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    try { localStorage.setItem('fluentflow-theme', theme); } catch { /* private browsing */ }
  }, [theme]);
  useEffect(() => { if (!notice) return; const timer = setTimeout(() => setNotice(''), 6500); return () => clearTimeout(timer); }, [notice]);
  useEffect(() => {
    if (!file || !file.type.startsWith('image/')) { setPreview(''); return; }
    const url = URL.createObjectURL(file); setPreview(url); return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => () => { recognition.current?.abort(); stream.current?.getTracks().forEach(t => t.stop()); audio.current?.pause(); window.speechSynthesis?.cancel(); if (audioUrl.current) URL.revokeObjectURL(audioUrl.current); }, []);
  useEffect(() => {
    setItems([]);
    if (!user) return;
    if (page === 'history' || page === 'vocabulary') api(page === 'history' ? '/history?limit=100' : '/vocabulary').then(setItems).catch(message);
    if (page === 'evaluation') api('/metrics').then(setMetrics).catch(message);
    if (page === 'tutor') api('/tutor-sessions').then(setSessions).catch(message);
  }, [page, user]);
  useEffect(() => {
    if (!job || !['queued', 'running'].includes(job.status)) return;
    const timer = setInterval(() => api(`/documents/${job.id}`).then(next => { setJob(next); if (next.status === 'failed') setNotice(next.error); }).catch(message), 5000);
    return () => clearInterval(timer);
  }, [job]);

  const setAuth = (value) => { if (value && serviceOffline) { setNotice('Translation service is not connected yet.'); return; } setAuthState(value); };
  const requireUser = () => { if (serviceOffline) { setNotice('Translation service is not connected yet.'); return false; } if (user) return true; setAuth('signup'); return false; };
  async function authenticate(event) {
    event.preventDefault(); setBusy(true);
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const response = await api(`/auth/${auth}`, { method: 'POST', body: JSON.stringify(data) });
      setToken(response.access_token);
      const profile = await api('/me'); setUser(profile); setAuth(null);
      if (profile.preferences.theme) setTheme(profile.preferences.theme);
      if (profile.preferences.target_lang) setTarget(profile.preferences.target_lang);
      setNotice('Your private workspace is ready.');
    } catch (e) { message(e); } finally { setBusy(false); }
  }
  async function translate() {
    if (!requireUser()) return;
    setBusy(true); setResult(null);
    try {
      let response;
      if (browserOnly) {
        const extracted = ['image', 'document'].includes(mode) ? await extractOnDevice(file, mode, ocrLanguage) : text;
        if (!extracted.trim()) throw new Error('No text found. For scanned PDFs, upload a page as an image instead.');
        response = await api('/translate', { method: 'POST', body: JSON.stringify({ text: extracted, src_lang: src, target_lang: target }) });
        if (['image', 'document'].includes(mode)) response.extracted_text = extracted;
      } else if (mode === 'text') response = await api('/translate', { method: 'POST', body: JSON.stringify({ text, src_lang: src, target_lang: target, tone, provider }) });
      else {
        if (!file) throw new Error('Choose a file first.');
        if (file.size > (caps?.upload_limit_mb || 10) * 1024 * 1024) throw new Error('File exceeds the upload size limit.');
        const body = new FormData(); body.append('file', file); body.append('target_lang', target);
        if (mode === 'image') body.append('ocr_language', ocrLanguage);
        response = await api(mode === 'image' ? '/image/translate' : mode === 'voice' ? '/speech/translate' : '/documents', { method: 'POST', body });
      }
      if (mode === 'document' && !browserOnly) setJob(response);
      else { setResult(response); if (response.transcription || response.extracted_text) setText(response.transcription || response.extracted_text); }
    } catch (e) { message(e); } finally { setBusy(false); }
  }
  async function speak() {
    if (!requireUser() || !result) return;
    try {
      if (browserOnly) {
        if (!window.speechSynthesis) throw new Error('Speech playback is unavailable in this browser.');
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(result.translated_text); utterance.lang = target;
        const voices = window.speechSynthesis.getVoices(); const voice = voices.find(v => v.lang.split('-')[0] === target);
        if (voices.length && !voice) throw new Error('No voice is installed for this language on your device.');
        if (voice) utterance.voice = voice;
        utterance.onerror = () => setNotice('Speech playback failed. Check your device voices and try again.');
        window.speechSynthesis.speak(utterance); return;
      }
      audio.current?.pause();
      if (audioUrl.current) URL.revokeObjectURL(audioUrl.current);
      const blob = await api('/speech/synthesize', { method: 'POST', body: JSON.stringify({ text: result.translated_text, lang: target }), raw: true });
      audioUrl.current = URL.createObjectURL(blob); audio.current = new Audio(audioUrl.current); await audio.current.play();
    } catch (e) { message(e); }
  }
  async function recordAudio() {
    if (recording) { recorder.current?.stop(); return; }
    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) throw new Error('Microphone recording requires a supported browser and HTTPS or localhost.');
      stream.current = await navigator.mediaDevices.getUserMedia({ audio: true });
      const type = ['audio/webm', 'audio/mp4', 'audio/ogg'].find(t => MediaRecorder.isTypeSupported(t));
      recorder.current = new MediaRecorder(stream.current, type ? { mimeType: type } : {});
      const chunks = [];
      recorder.current.ondataavailable = e => chunks.push(e.data);
      recorder.current.onstop = () => {
        const mime = recorder.current.mimeType.split(';')[0];
        setFile(new File(chunks, `recording.${mime.includes('mp4') ? 'm4a' : mime.includes('ogg') ? 'ogg' : 'webm'}`, { type: mime }));
        stream.current.getTracks().forEach(t => t.stop()); setRecording(false);
      };
      recorder.current.start(); setRecording(true);
      setTimeout(() => { if (recorder.current?.state === 'recording') recorder.current.stop(); }, 60000);
    } catch (e) { stream.current?.getTracks().forEach(t => t.stop()); message(e); }
  }
  function dictate() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) { setNotice('Browser dictation is unavailable. Type your message instead, or use a browser with speech recognition.'); return; }
    recognition.current = new Recognition(); recognition.current.lang = src === 'auto' ? 'en-US' : src;
    recognition.current.onresult = e => { setText(old => `${old} ${e.results[0][0].transcript}`.trim().slice(0, browserOnly ? 5000 : 50000)); setResult(null); };
    recognition.current.onerror = e => setNotice(`Dictation failed: ${e.error}`); recognition.current.start();
  }
  async function ask(event) {
    event?.preventDefault(); if (!requireUser() || !question.trim()) return;
    setBusy(true);
    try {
      const reply = await api('/tutor', { method: 'POST', body: JSON.stringify({ question, session_id: session, translation_id: result?.id || null, use_rag: useRag }) });
      setTurns(old => [...old, { question, ...reply }]); setQuestion('');
      api('/tutor-sessions').then(setSessions).catch(message);
    } catch (e) { message(e); } finally { setBusy(false); }
  }
  function logout() { setToken(''); setUser(null); setResult(null); setText(''); setItems([]); setTurns([]); setSessions([]); setJob(null); setFile(null); setMetrics(null); setSession(crypto.randomUUID()); }
  function navigate(next) { setPage(next); setMobile(false); }
  const reset = () => { setText(''); setResult(null); setFile(null); setJob(null); };
  const invalidate = (setter) => e => { setter(e.target.value); setResult(null); setJob(null); };
  const title = { translate: 'Translation studio', tutor: 'Your language companion', history: 'Your translations', vocabulary: 'Words worth keeping', evaluation: 'A clear view of performance', settings: 'Make yourself at home', home: 'A world of understanding.' }[page];

  return <div className="app-shell">
    <aside className={`sidebar ${mobile ? 'open' : ''}`}>
      <button className="brand" onClick={() => navigate('home')} aria-label="FluentFlow AI home"><span className="brand-icon"><AudioLines size={25} /></span><span>FluentFlow<span className="ai-label">AI</span></span></button>
      <div className="workspace-label">YOUR WORKSPACE</div>
      <nav aria-label="Main navigation">{navigation.filter(([id]) => !browserOnly || id !== 'tutor').map(([id, Icon, label]) => <button key={id} className={`nav-link ${page === id ? 'active' : ''}`} onClick={() => navigate(id)}><Icon size={19}/><span>{label}</span>{id === 'tutor' && <span className="tiny-badge">AI</span>}</button>)}</nav>
      {!browserOnly && <div className="sidebar-tip"><div className="tip-icon"><Sparkles size={20}/></div><strong>A little practice.<br/>A world of possibility.</strong><p>Go beyond the translation. Discover the meaning behind every word.</p><button onClick={() => navigate('tutor')}>Meet your AI tutor <ArrowRight size={15}/></button></div>}
      <div className="sidebar-bottom"><button className={`nav-link ${page === 'settings' ? 'active' : ''}`} onClick={() => navigate('settings')}><Settings size={19}/> Settings</button><button className="profile" onClick={() => user ? navigate('settings') : setAuth('login')}><span className="avatar">{user ? user.name.slice(0, 2).toUpperCase() : 'FF'}</span><span><strong>{user?.name || 'Your personal workspace'}</strong><small>{browserOnly ? 'Saved in this browser' : user ? 'Private account' : 'Sign in to save your progress'}</small></span><ChevronRight size={16}/></button></div>
    </aside>
    {mobile && <button className="sidebar-overlay" aria-label="Close navigation" onClick={() => setMobile(false)}/>}
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb"><button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setMobile(true)}><Menu size={20}/></button><span>Workspace</span><ChevronRight size={14}/><strong>{page === 'translate' ? 'Translation studio' : title}</strong></div><div className="top-actions"><span className={`connection ${caps?.providers.length ? 'connected' : ''}`}><span/>{browserOnly ? 'Browser mode · no account needed' : serviceOffline ? 'Translation service offline' : caps === null ? 'Connecting to API' : caps.providers.length ? 'Providers configured' : 'Provider setup needed'}</span><button className="icon-button" aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`} onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>{theme === 'light' ? <Moon size={18}/> : <Sun size={18}/>}</button>{browserOnly ? null : user ? <button className="text-button" disabled={busy} onClick={logout}><LogOut size={16}/> Sign out</button> : <button className="small-primary" disabled={serviceOffline} onClick={() => setAuth('login')}>Sign in <ArrowRight size={14}/></button>}</div></header>
      <main>
        <div className="page-heading"><div><div className="eyebrow"><span/> LANGUAGE WITHOUT LIMITS</div><h1>{title}<span className="heading-dot">.</span></h1><p>{page === 'translate' ? 'Find the right words. Keep the original feeling.' : 'Turn everyday curiosity into lasting understanding.'}</p></div>{page === 'translate' && <div className="heading-note"><Globe2 size={17}/><span>Different languages.<br/><strong>One human connection.</strong></span></div>}</div>
        {browserOnly && <div className="service-notice" role="status"><Globe2 size={18}/><span>Free browser mode: text is sent to MyMemory for translation, subject to its daily quota. History stays on this device. Choose the source language before translating. Public translations can contain errors; review important text.</span></div>}
        {serviceOffline && <div className="service-notice" role="status"><Globe2 size={18}/><span>Translation service is not connected. Explore the workspace; translation and account features will be available when the service is online.</span></div>}
        {page === 'home' && <section className="hero panel"><span className="pill"><Sparkles size={15}/> Multimodal translation & intelligent language learning</span><h2>More than words.<br/><em>A way to connect.</em></h2><p>{browserOnly ? 'Translate text, dictate a message, or read words from an image or document. Save useful translations and vocabulary on this device.' : 'Translate a thought, a conversation, or a page. Then explore the grammar, context, and culture that bring it to life.'}</p><button className="primary" onClick={() => navigate('translate')}>Open translation studio <ArrowRight size={18}/></button><div className="hero-features">{modes.map(([id, Icon, label]) => <button key={id} onClick={() => { setMode(id); navigate('translate'); }}><Icon size={24}/>{label} translation <ArrowRight size={15}/></button>)}</div></section>}
        {page === 'translate' && <>
          <div className="studio-toolbar"><div className="mode-tabs" role="tablist" aria-label="Translation mode">{modes.map(([id, Icon, label]) => <button key={id} role="tab" aria-selected={mode === id} className={mode === id ? 'selected' : ''} disabled={busy} onClick={() => { setMode(id); setFile(null); setJob(null); setResult(null); }}><Icon size={17}/>{label}</button>)}</div><span className="privacy-caption"><ShieldCheck size={15}/> {browserOnly ? 'Files processed on your device' : 'Private by design'}</span></div>
          <section className="translation-card" aria-label="Translation workspace">
            <div className="language-bar"><div className="language-select"><span className="language-symbol">A</span><select aria-label="Source language" disabled={busy || (!browserOnly && mode !== 'text')} value={browserOnly || mode === 'text' ? src : 'auto'} onChange={invalidate(setSrc)}>{!browserOnly && <option value="auto">Detect language</option>}{Object.entries(languages).map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select>{src === 'auto' && <span className="auto-pill">AUTO</span>}</div><button className="swap-button" aria-label="Swap languages" onClick={() => { const detected = src === 'auto' ? result?.detected_language : src; if (!languages[detected]) { setNotice('Select a source language or translate first to swap.'); return; } setSrc(target); setTarget(detected); setText(result?.translated_text || ''); setResult(null); }}><ArrowLeftRight size={18}/></button><div className="language-select target-select"><Globe2 size={17}/><select aria-label="Target language" disabled={busy} value={target} onChange={invalidate(setTarget)}>{Object.entries(languages).map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></div></div>
            <div className="translation-panes"><div className="input-pane">
              {(mode === 'text' || (browserOnly && mode === 'voice')) ? <><textarea aria-label="Text to translate" disabled={busy} value={text} onChange={invalidate(setText)} maxLength={browserOnly ? 5000 : 50000} placeholder={browserOnly && mode === 'voice' ? 'Click the microphone below, then speak. Your browser may use an online speech service.' : 'What would you like to say?'}/><div className="pane-footer"><div><button className="icon-button" aria-label="Dictate text" onClick={dictate}><Mic size={18}/></button><button className="icon-button" aria-label="Clear workspace" onClick={reset}><Trash2 size={17}/></button></div><span>{text.length.toLocaleString()} / {browserOnly ? '5,000' : '50,000'}</span></div></> : <div className="upload-area"><div className="upload-glyph">{mode === 'voice' ? <AudioLines size={32}/> : mode === 'image' ? <Image size={32}/> : <FileText size={32}/>}</div><h3>{mode === 'voice' ? 'Let your voice travel' : mode === 'image' ? 'Find the words in your image' : 'Give your document a new language'}</h3><p>{mode === 'voice' ? 'Record a message or choose an audio file.' : 'Choose a file to extract and translate its text.'}</p>{mode === 'voice' && <button className={`secondary ${recording ? 'recording' : ''}`} onClick={recordAudio}><Mic size={16}/>{recording ? 'Stop recording' : 'Record audio'}</button>}<label className="file-label">{file ? file.name : 'Choose a file'}<input aria-label={`Upload ${mode}`} type="file" accept={mode === 'image' ? '.png,.jpg,.jpeg,.webp' : mode === 'voice' ? '.wav,.mp3,.m4a,.ogg,.webm,.flac' : '.pdf,.docx,.txt'} onChange={e => { setFile(e.target.files[0] || null); setResult(null); setJob(null); }}/></label><small>{mode === 'image' ? 'PNG, JPG, WEBP' : mode === 'voice' ? 'WAV, MP3, M4A, OGG, WEBM, FLAC · up to 5 minutes' : (browserOnly ? 'Text PDFs, DOCX, TXT · up to 5,000 characters' : 'PDF, DOCX, TXT · up to 50,000 characters')} · {caps?.upload_limit_mb || 10} MB max</small>{browserOnly && mode === 'image' && <small>OCR runs on this device; language models download on first use. Choose the source language above to match the image.</small>}{mode === 'image' && <label className="ocr-select">Image text language<select value={ocrLanguage} onChange={e => setOcrLanguage(e.target.value)}>{Object.entries({eng:'English',hin:'Hindi',kan:'Kannada',tam:'Tamil',tel:'Telugu',fra:'French',deu:'German',spa:'Spanish',jpn:'Japanese',ara:'Arabic'}).map(([id,name]) => <option key={id} value={id}>{name}</option>)}</select></label>}{mode === 'voice' && !caps?.speech && <small>Server recognition requires ENABLE_SPEECH=true.</small>}{preview && <img className="upload-preview" src={preview} alt="Image selected for translation"/>}</div>}
            </div><div className={`output-pane ${busy ? 'loading' : ''}`}><div className="output-label">TRANSLATION {result?.detected_language && <span>Detected: {languages[result.detected_language] || result.detected_language}</span>}</div>{busy ? <div className="loading-content" role="status"><span className="spinner"/> Finding the right words…</div> : (result || job?.status === 'completed') ? <div className="translated-content" dir="auto">{result?.translated_text || job.translated_text}</div> : <div className="output-empty"><div className="empty-art"><Languages size={32}/><span className="spark spark-one">✦</span><span className="spark spark-two">✧</span></div><h3>{job && ['queued', 'running'].includes(job.status) ? 'Your document is being translated' : 'A new perspective starts here'}</h3><p>{job && ['queued', 'running'].includes(job.status) ? 'This workspace will update when it is ready.' : job?.status === 'failed' ? job.error : 'Your translation will appear here.'}</p></div>}<div className="pane-footer"><span>{result?.providers?.join(' + ') || (job?.status === 'completed' ? job.providers?.join(' + ') : 'Thoughtfully translated.')}</span><div><button className="icon-button" aria-label="Play translated audio" disabled={!result} onClick={speak}><Volume2 size={18}/></button><button className="icon-button" aria-label="Copy translation" disabled={!result && job?.status !== 'completed'} onClick={() => navigator.clipboard.writeText(result?.translated_text || job.translated_text).then(() => setNotice('Copied to clipboard.')).catch(message)}><Clipboard size={17}/></button><button className="icon-button" aria-label="Download translation" disabled={!result && job?.status !== 'completed'} onClick={() => download(new Blob([result?.translated_text || job.translated_text], { type: 'text/plain;charset=utf-8' }), 'fluentflow-translation.txt')}><ArrowDownToLine size={18}/></button></div></div></div></div>
            <div className="translation-controls"><div className="control-fields">{!browserOnly && <><label><span>{browserOnly ? 'Tone (AI backend required)' : 'Tone'}</span><select aria-label="Translation tone" value={mode === 'text' ? tone : 'professional'} onChange={invalidate(setTone)} disabled={browserOnly || busy || mode !== 'text'}>{['professional','formal','casual','academic','creative','conversational'].map(t => <option key={t} value={t}>{t[0].toUpperCase()+t.slice(1)}</option>)}</select></label><span className="control-divider"/></>}<label><span>Engine</span><select aria-label="Translation engine" value={mode === 'text' ? provider : 'auto'} onChange={invalidate(setProvider)} disabled={browserOnly || busy || mode !== 'text'}><option value="auto">{browserOnly ? 'MyMemory · free' : 'Auto · best available'}</option>{caps?.providers.map(p => <option key={p.id} value={p.id}>{p.id}</option>)}</select></label></div><button className="primary translate-action" disabled={busy || recording || ((mode === 'text' || (browserOnly && mode === 'voice')) ? !text.trim() : !file)} onClick={translate}><Sparkles size={17}/>{busy ? 'Translating…' : 'Translate'}<ArrowRight size={17}/></button></div>
          </section>
          {result?.warnings?.map(w => <p className="inline-note" key={w}>{w}</p>)}
          {result?.fallback && <p className="inline-note">A fallback provider completed this translation.</p>}
          {(result?.transcription || result?.extracted_text) && <div className="panel extracted"><h3>{result.transcription ? 'Original transcription' : 'Extracted text'}</h3><p dir="auto">{result.transcription || result.extracted_text}</p></div>}
          {job?.status === 'completed' && <button className="secondary download-docx" onClick={() => api(`/documents/${job.id}/download?format=docx`, { raw: true }).then(b => download(b, 'fluentflow-translation.docx')).catch(message)}><ArrowDownToLine size={16}/> Download as Word document</button>}
          {!browserOnly && <div className="below-studio"><section className="tutor-banner"><span className="tutor-banner-icon"><Sparkles size={25}/></span><div><div className="mini-eyebrow">DON’T JUST TRANSLATE. UNDERSTAND.</div><h3>There’s a story behind every sentence.</h3><p>Explore grammar, discover expressions, and make the language your own.</p></div><button onClick={() => navigate('tutor')}>Explore with AI tutor <ArrowRight size={16}/></button></section><div className="studio-footnote"><span><Check size={14}/> Context-aware translation</span><span><Check size={14}/> Indian & global languages</span><span><Check size={14}/> Your words, your workspace</span></div></div>}
          <section className="suggestion-section"><div className="section-caption">A LITTLE INSPIRATION <span>Try a conversation starter</span></div><div className="suggestions">{[['Everyday connection', 'It’s lovely to meet you. How has your day been?'], ['A new adventure', 'Could you recommend a quiet place to watch the sunset?'], ['A thoughtful message', 'Thank you for your time. I look forward to working together.']].map(([label, sample]) => <button key={label} onClick={() => { setMode('text'); setText(sample); setResult(null); }}><span>{label}</span><p>{sample}</p><ArrowRight size={15}/></button>)}</div></section>
        </>}
        {page === 'tutor' && <section className="panel tutor-panel"><div className="panel-title"><span className="tutor-banner-icon"><Sparkles size={22}/></span><div><h2>A little curiosity goes a long way.</h2><p>Ask about grammar, natural expressions, pronunciation, or your last translation.</p></div><button className="icon-button" aria-label="New learning session" onClick={() => { setSession(crypto.randomUUID()); setTurns([]); }}><Plus size={20}/></button></div>{sessions.length > 0 && <details className="session-picker"><summary>Past learning sessions</summary><div>{sessions.map(saved => <button key={saved.id} onClick={() => api(`/tutor/${saved.id}`).then(history => { setSession(saved.id); setTurns(history); }).catch(message)}>{saved.question}</button>)}</div></details>}{!turns.length && <div className="tutor-prompts">{['Explain the grammar in my translation.', 'Suggest a more natural alternative.', 'Give me a short practice exercise.'].map(q => <button key={q} onClick={() => setQuestion(q)}>{q}<ArrowRight size={16}/></button>)}</div>}<div className="conversation" aria-live="polite">{turns.map((turn, i) => <div key={i}><div className="user-turn">{turn.question}</div><div className="tutor-turn"><span className="mini-eyebrow">FLUENTFLOW TUTOR</span><p>{turn.answer}</p>{[['Other ways to say it', turn.alternatives], ['Try it yourself', turn.exercises], ['Your next step', turn.recommendations]].map(([label, values]) => values?.length ? <div key={label}><strong>{label}</strong><ul>{values.map((v, n) => <li key={n}>{v}</li>)}</ul></div> : null)}{turn.sources?.map(s => <a key={s.id} href={s.url} target="_blank" rel="noreferrer">{s.title} ↗</a>)}</div></div>)}</div><form className="tutor-form" onSubmit={ask}><label className="sr-only" htmlFor="question">Ask your tutor</label><input id="question" value={question} onChange={e => setQuestion(e.target.value)} maxLength={2000} placeholder="What would you like to understand?"/><button className="primary" disabled={busy || !question.trim()} aria-label="Send tutor question"><Send size={18}/></button></form><label className="rag-toggle"><input type="checkbox" checked={useRag} disabled={!caps?.rag} onChange={e => setUseRag(e.target.checked)}/> Ground answers in the grammar library {caps?.rag ? '' : '(not enabled)'}</label><p className="muted text-xs">AI explanations can be inaccurate. Check important language decisions with a qualified speaker.</p></section>}
        {['history', 'vocabulary'].includes(page) && <section className="panel list-panel">{!user ? <Empty title="A space for your progress" text="Sign in to keep translations and vocabulary in your private account." action={() => setAuth('login')} label="Sign in"/> : <>{page === 'vocabulary' && <form className="vocab-form" onSubmit={async e => { e.preventDefault(); const form = e.currentTarget; const values = Object.fromEntries(new FormData(form)); try { const item = await api('/vocabulary', { method: 'POST', body: JSON.stringify({ ...values, language: target }) }); setItems(old => [item, ...old]); form.reset(); } catch (err) { message(err); } }}><input aria-label="Word or phrase" name="word" placeholder="Word or phrase" required maxLength={200}/><input aria-label="Meaning" name="meaning" placeholder="Meaning or a useful note" required maxLength={1000}/><button className="primary"><Plus size={16}/> Save</button></form>}{!items.length ? <Empty title={page === 'history' ? 'Your story starts with a translation' : 'Collect your first word'} text="Your saved progress will appear here."/> : items.map(item => <article className="saved-item" key={item.id}><div><span className="mini-eyebrow">{languages[item.target_lang || item.language] || item.language} {item.tone && ` · ${item.tone}`}</span><h3>{item.text || item.word}</h3><p dir="auto">{item.translated_text || item.meaning}</p>{item.created_at && <small>{new Date(item.created_at).toLocaleString()}</small>}</div><button className="icon-button" aria-label={`Delete ${page === 'history' ? 'translation' : 'word'}`} onClick={async () => { try { await api(`/${page}/${item.id}`, { method: 'DELETE' }); setItems(old => old.filter(x => x.id !== item.id)); } catch (e) { message(e); } }}><Trash2 size={17}/></button></article>)}</>}</section>}
        {page === 'evaluation' && <><section className="metrics-grid">{[['Requests', metrics?.requests], ['Median latency', metrics?.p50_ms == null ? null : `${Math.round(metrics.p50_ms)} ms`], ['P95 latency', metrics?.p95_ms == null ? null : `${Math.round(metrics.p95_ms)} ms`], ['Estimated inference cost', metrics?.estimated_cost_usd == null ? null : `$${metrics.estimated_cost_usd.toFixed(5)}`]].map(([label, value]) => <div className="panel metric" key={label}><span>{label}</span><strong>{value ?? '—'}</strong><small>{value == null ? 'No measurements available' : 'From your recorded usage'}</small></div>)}</section><section className="panel evaluation-panel"><h2>Evidence before claims.</h2><p>Translation quality needs reference translations. BLEU, chrF, optional COMET, speech WER, and OCR CER are available in the offline evaluation pipeline. No quality benchmark has been measured yet.</p><div className="evaluation-bars">{['BLEU', 'chrF', 'COMET', 'Speech WER', 'OCR CER'].map(label => <div key={label}><span>{label}</span><div/><small>Not measured</small></div>)}</div><p className="muted">{browserOnly ? 'Usage covers the latest 100 translations saved on this device.' : 'Usage covers up to your latest 1,000 text/image/speech translation requests.'} {!browserOnly && 'It excludes tutor and document jobs. Cost remains unknown until provider prices are configured.'} {metrics?.fallback_rate != null && `Fallback rate: ${(metrics.fallback_rate * 100).toFixed(1)}%. Failure rate: ${(metrics.failure_rate * 100).toFixed(1)}%.`}</p></section></>}
        {page === 'settings' && <section className="panel settings-panel"><h2>Your preferences</h2><p>Small details that make this workspace yours.</p><label>Appearance<select value={theme} onChange={e => setTheme(e.target.value)}><option value="light">Light</option><option value="dark">Dark</option></select></label><label>Preferred target language<select value={target} onChange={invalidate(setTarget)}>{Object.entries(languages).map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></label><button className="primary" onClick={async () => { if (!requireUser()) return; try { await api('/me/preferences', { method: 'PATCH', body: JSON.stringify({ theme, target_lang: target }) }); setNotice('Preferences saved.'); } catch (e) { message(e); } }}><Check size={16}/> Save preferences</button><hr/><h3>{browserOnly ? 'Device storage & privacy' : 'Account & privacy'}</h3><p>{browserOnly ? 'Up to 100 translations and 100 vocabulary entries are saved in this browser. They are not synced or protected by an account.' : user ? `${user.name} · ${user.email}` : 'Sign in to save progress across learning sessions.'}</p>{browserOnly && <button className="danger-button" onClick={() => { if (window.confirm('Delete all translations, vocabulary and preferences saved on this device?')) { clearDeviceData(); setItems([]); setResult(null); setNotice('Device data cleared.'); } }}>Clear saved device data</button>}{!browserOnly && <p className="muted">Sessions stay in browser memory. Signing out or reloading requires a new login. Translation and learning records follow the server retention policy.</p>}{!browserOnly && user && <><button className="secondary" onClick={() => api('/me/purge-expired', { method: 'POST' }).then(r => setNotice(`${r.deleted} expired records removed.`)).catch(message)}>Remove expired records</button><button className="danger-button" onClick={async () => { if (!window.confirm('Permanently delete your account and all saved records?')) return; try { await api('/me', { method: 'DELETE' }); logout(); setNotice('Account deleted.'); } catch (e) { message(e); } }}>Delete account and data</button></>}</section>}
        <footer><span className="footer-brand"><AudioLines size={16}/> FluentFlow AI</span><span>Made for a world that speaks many languages.</span><span>Translate. Understand. Connect.</span></footer>
      </main>
    </div>
    {notice && <div className="toast" role="alert"><span>{notice}</span><button className="icon-button" aria-label="Dismiss notification" onClick={() => setNotice('')}><X size={17}/></button></div>}
    {auth && <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget) setAuth(null); }}><section className="auth-modal" role="dialog" aria-modal="true" aria-labelledby="auth-title" onKeyDown={e => { if (e.key === 'Escape') setAuth(null); if (e.key === 'Tab') { const nodes = [...e.currentTarget.querySelectorAll('button:not(:disabled),input,a[href]')]; if (e.shiftKey && document.activeElement === nodes[0]) { e.preventDefault(); nodes.at(-1).focus(); } else if (!e.shiftKey && document.activeElement === nodes.at(-1)) { e.preventDefault(); nodes[0].focus(); } } }}><button className="icon-button modal-close" aria-label="Close sign in" onClick={() => setAuth(null)}><X size={20}/></button><span className="brand-icon"><AudioLines size={26}/></span><h2 id="auth-title">{auth === 'signup' ? 'A world of words awaits.' : 'Welcome back.'}</h2><p>Your translations. Your learning. Your space.</p><form onSubmit={authenticate}>{auth === 'signup' && <label>Your name<input autoFocus name="name" required maxLength={80} autoComplete="name"/></label>}<label>Email address<input autoFocus={auth === 'login'} name="email" type="email" required autoComplete="email"/></label><label>Password<input name="password" type="password" minLength={10} maxLength={128} required autoComplete={auth === 'signup' ? 'new-password' : 'current-password'}/><small>At least 10 characters</small></label><button className="primary" disabled={busy}>{busy ? 'Please wait…' : auth === 'signup' ? 'Create your account' : 'Sign in'}<ArrowRight size={16}/></button></form><button className="text-button auth-switch" onClick={() => setAuth(auth === 'signup' ? 'login' : 'signup')}>{auth === 'signup' ? 'Already have an account? Sign in' : 'New here? Create an account'}</button></section></div>}
  </div>;
}

function Empty({ title, text, action, label }) { return <div className="empty-state"><BookOpen size={34}/><h2>{title}</h2><p>{text}</p>{action && <button className="primary" onClick={action}>{label}<ArrowRight size={16}/></button>}</div>; }
