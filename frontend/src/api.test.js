import { afterEach, expect, test, vi } from 'vitest';

afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); vi.resetModules(); });

test('static hosting without a backend never sends account data', async () => {
  vi.stubEnv('VITE_STATIC_ONLY', 'true');
  vi.stubEnv('VITE_API_BASE_URL', '');
  vi.resetModules();
  const fetch = vi.fn();
  vi.stubGlobal('fetch', fetch);
  const { api, apiAvailable } = await import('./api');
  expect(apiAvailable).toBe(false);
  await expect(api('/auth/login', { method: 'POST', body: JSON.stringify({ password: 'test-only' }) })).rejects.toThrow('unavailable in browser-only mode');
  expect(fetch).not.toHaveBeenCalled();
});

test('a configured backend receives authenticated API requests', async () => {
  vi.stubEnv('VITE_STATIC_ONLY', 'true');
  vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.com/');
  vi.resetModules();
  const fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ status: 'ok' }) });
  vi.stubGlobal('fetch', fetch);
  const { api, setToken, apiAvailable } = await import('./api');
  setToken('test-only-token');
  expect(apiAvailable).toBe(true);
  await api('/me');
  expect(fetch).toHaveBeenCalledWith('https://api.example.com/api/v1/me', expect.objectContaining({
    headers: expect.objectContaining({ Authorization: 'Bearer test-only-token' })
  }));
});

test('normal builds retain same-origin API routing', async () => {
  vi.stubEnv('VITE_STATIC_ONLY', '');
  vi.stubEnv('VITE_API_BASE_URL', '');
  vi.resetModules();
  const fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
  vi.stubGlobal('fetch', fetch);
  const { api } = await import('./api');
  await api('/capabilities');
  expect(fetch.mock.calls[0][0]).toBe('/api/v1/capabilities');
});
