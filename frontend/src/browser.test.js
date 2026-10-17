import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { browserApi, clearDeviceData, splitText, translateInBrowser } from './browser';
beforeEach(() => { localStorage.clear(); });
afterEach(() => vi.unstubAllGlobals());
const request = (text = 'Hello world', src_lang = 'en', target_lang = 'hi') => ({ text, src_lang, target_lang });
test('splits Unicode into API-safe byte lengths without losing content', () => {
  const text = 'नमस्ते 🙂\n'.repeat(140); const chunks = splitText(text);
  expect(chunks.join('')).toBe(text);
  expect(chunks.every(chunk => new TextEncoder().encode(chunk).length <= 480)).toBe(true);
});
test('translates with an explicit pair and saves history locally', async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ responseStatus: 200, responseData: { translatedText: 'नमस्ते दुनिया' } }) });
  vi.stubGlobal('fetch', fetch);
  const result = await translateInBrowser(request());
  expect(result.translated_text).toBe('नमस्ते दुनिया');
  const url = fetch.mock.calls[0][0];
  expect(url.searchParams.get('langpair')).toBe('en|hi');
  expect(url.searchParams.get('q')).toBe('Hello world');
  expect(await browserApi('/history?limit=100')).toEqual([result]);
});
test('quota errors are not displayed or saved as translations', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ responseStatus: 403, quotaFinished: true, responseData: { translatedText: 'QUOTA LIMIT' } }) }));
  await expect(translateInBrowser(request())).rejects.toThrow('quota');
  expect(await browserApi('/history')).toEqual([]);
});
test('network failures are actionable and do not leave a partial saved result', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network')));
  await expect(translateInBrowser(request())).rejects.toThrow('internet connection');
  expect(await browserApi('/history')).toEqual([]);
});
test('requires a real source language and bounds input before sending', async () => {
  const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
  await expect(translateInBrowser(request('Hello', 'auto'))).rejects.toThrow('source');
  await expect(translateInBrowser(request('a'.repeat(5001)))).rejects.toThrow('5,000');
  expect(fetch).not.toHaveBeenCalled();
});
test('same-language input avoids wasting the provider quota', async () => {
  const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
  expect((await translateInBrowser(request('Hello', 'en', 'en'))).translated_text).toBe('Hello');
  expect(fetch).not.toHaveBeenCalled();
});
test('vocabulary can be saved, deleted, and cleared without an account', async () => {
  const saved = await browserApi('/vocabulary', { method: 'POST', body: JSON.stringify({ word: 'hola', meaning: 'hello', language: 'es' }) });
  expect(await browserApi('/vocabulary')).toEqual([saved]);
  await browserApi(`/vocabulary/${saved.id}`, { method: 'DELETE' });
  expect(await browserApi('/vocabulary')).toEqual([]);
  await translateInBrowser(request('hello', 'en', 'en'));
  clearDeviceData();
  expect(await browserApi('/history')).toEqual([]);
});
