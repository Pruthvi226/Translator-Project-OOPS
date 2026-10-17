// Static hosting: documents stay on-device; only extracted text goes to MyMemory.
export const browserLanguages = { en: 'English', hi: 'Hindi', kn: 'Kannada', ta: 'Tamil', te: 'Telugu', mr: 'Marathi', bn: 'Bengali', es: 'Spanish', fr: 'French', de: 'German', ja: 'Japanese', ar: 'Arabic', it: 'Italian', pt: 'Portuguese', ru: 'Russian', ko: 'Korean', gu: 'Gujarati', ml: 'Malayalam', pa: 'Punjabi', ur: 'Urdu' };
export const deviceUser = { name: 'This device', preferences: {} };
const key = 'fluentflow-device-v1';
function read() { try { return JSON.parse(localStorage.getItem(key)) || {}; } catch { return {}; } }
function write(data) {
  try { localStorage.setItem(key, JSON.stringify(data)); }
  catch { throw new Error('Device storage is full or blocked. Clear saved records in Settings or allow site storage.'); }
}
export function clearDeviceData() { localStorage.removeItem(key); localStorage.removeItem('fluentflow-theme'); }
export function splitText(text, maxBytes = 480) {
  // Keep whitespace intact, including newlines, and never split a Unicode code point.
  const encoder = new TextEncoder(); const parts = []; let chunk = '';
  for (const char of text) {
    if (encoder.encode(chunk + char).length > maxBytes) { parts.push(chunk); chunk = ''; }
    chunk += char;
  }
  if (chunk) parts.push(chunk);
  return parts;
}
function decodeEntities(text) {
  const area = document.createElement('textarea'); area.innerHTML = text;
  return area.value;
}
export async function translateInBrowser({ text, src_lang, target_lang }) {
  if (!text?.trim()) throw new Error('Enter some text first.');
  if (text.length > 5000) throw new Error('Translate up to 5,000 characters at a time in browser mode.');
  if (!browserLanguages[src_lang] || !browserLanguages[target_lang]) throw new Error('Choose the source and target languages. Automatic detection is unavailable in browser mode.');
  const start = performance.now(); const translated = [];
  if (src_lang === target_lang) translated.push(text);
  if (src_lang !== target_lang) {
    // Prefer word boundaries, but safely split long unbroken input too.
    const chunks = []; let current = '';
    for (const piece of text.split(/(\s+)/)) {
      if (new TextEncoder().encode(current + piece).length <= 480) current += piece;
      else { if (current) chunks.push(current); const parts = splitText(piece); chunks.push(...parts.slice(0, -1)); current = parts.at(-1) || ''; }
    }
    if (current) chunks.push(current);
    for (const chunk of chunks) {
      if (!chunk.trim()) { translated.push(chunk); continue; }
      const leading = chunk.match(/^\s*/)[0], trailing = chunk.match(/\s*$/)[0];
      const url = new URL('https://api.mymemory.translated.net/get');
      url.searchParams.set('q', chunk.trim()); url.searchParams.set('langpair', `${src_lang}|${target_lang}`);
      let response;
      try { response = await fetch(url, { signal: AbortSignal.timeout(30000), credentials: 'omit', referrerPolicy: 'no-referrer' }); }
      catch { throw new Error('Translation could not connect. Check your internet connection and try again.'); }
      if (!response.ok) throw new Error(`Translation service is unavailable (${response.status}). Try again later.`);
      const data = await response.json();
      if (data.quotaFinished || Number(data.responseStatus) === 429) throw new Error('The free translation quota has been reached. Try again tomorrow.');
      if (Number(data.responseStatus) !== 200 || typeof data.responseData?.translatedText !== 'string' || !data.responseData.translatedText.trim()) throw new Error(data.responseDetails || 'This language pair is unavailable. Choose another pair and try again.');
      const machine = data.matches?.find(match => match['created-by'] === 'MT!' && match.segment === chunk.trim());
      translated.push(leading + decodeEntities(machine?.translation || data.responseData.translatedText) + trailing);
    }
  }
  const result = { id: crypto.randomUUID(), text, translated_text: translated.join(''), src_lang, target_lang, providers: [src_lang === target_lang ? 'Same language' : 'MyMemory'], created_at: new Date().toISOString(), latency_ms: performance.now() - start };
  const state = read(); state.history = [result, ...(state.history || [])].slice(0, 100);
  try { write(state); } catch (error) { result.warnings = [error.message + ' Translation was not saved.']; }
  return result;
}
export async function extractOnDevice(file, mode, language = 'eng') {
  if (!file) throw new Error('Choose a file first.');
  if (file.size > 10 * 1024 * 1024) throw new Error('Choose a file smaller than 10 MB.');
  if (mode === 'image') {
    const bitmap = await createImageBitmap(file);
    const pixels = bitmap.width * bitmap.height; bitmap.close();
    if (pixels > 20000000) throw new Error('Use an image with fewer than 20 million pixels.');
    const { createWorker } = await import('tesseract.js');
    const worker = await createWorker(language);
    try { return (await worker.recognize(file)).data.text; } finally { await worker.terminate(); }
  }
  const ext = file.name.split('.').at(-1).toLowerCase();
  if (ext === 'txt') return file.text();
  if (ext === 'docx') {
    const mammoth = await import('mammoth/mammoth.browser.js');
    return (await (mammoth.default || mammoth).extractRawText({ arrayBuffer: await file.arrayBuffer() })).value;
  }
  if (ext === 'pdf') {
    const pdfjs = await import('pdfjs-dist');
    const { default: workerUrl } = await import('pdfjs-dist/build/pdf.worker.min.mjs?url');
    pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
    const task = pdfjs.getDocument({ data: await file.arrayBuffer(), isEvalSupported: false });
    try {
      const pdf = await task.promise;
      if (pdf.numPages > 50) throw new Error('Choose a PDF with no more than 50 pages.');
      const pages = [];
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i); const content = await page.getTextContent();
        pages.push(content.items.map(item => item.str + (item.hasEOL ? '\n' : ' ')).join(''));
        page.cleanup();
      }
      return pages.join('\n\n');
    } finally { await task.destroy(); }
  }
  throw new Error('Choose a TXT, DOCX, or text-based PDF document.');
}
export async function browserApi(path, options = {}) {
  const state = read(); const body = options.body ? JSON.parse(options.body) : {};
  if (path === '/capabilities') return { languages: browserLanguages, providers: [{ id: 'MyMemory' }], speech: false, rag: false, upload_limit_mb: 10 };
  if (path === '/translate') return translateInBrowser(body);
  if (path.startsWith('/history') || path.startsWith('/vocabulary')) {
    const collection = path.startsWith('/history') ? 'history' : 'vocabulary';
    if (options.method === 'DELETE') { state[collection] = (state[collection] || []).filter(item => item.id !== path.split('/')[2]); write(state); return null; }
    if (options.method === 'POST') { const item = { ...body, id: crypto.randomUUID(), created_at: new Date().toISOString() }; state[collection] = [item, ...(state[collection] || [])].slice(0, 100); write(state); return item; }
    return state[collection] || [];
  }
  if (path === '/metrics') {
    const times = (state.history || []).map(item => item.latency_ms).sort((a, b) => a - b);
    return { requests: times.length, p50_ms: times.length ? times[Math.floor((times.length - 1) * .5)] : null, p95_ms: times.length ? times[Math.ceil((times.length - 1) * .95)] : null, estimated_cost_usd: null };
  }
  if (path === '/me/preferences') { state.preferences = body; write(state); return body; }
  if (path === '/tutor-sessions') return [];
  throw new Error('This feature requires a hosted AI backend and is unavailable in browser-only mode.');
}
export function devicePreferences() { return read().preferences || {}; }
