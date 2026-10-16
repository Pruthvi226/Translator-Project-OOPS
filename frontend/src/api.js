let token = '';
const apiOrigin = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
export const apiAvailable = !(import.meta.env.VITE_STATIC_ONLY === 'true' && !apiOrigin);
export const setToken = (value) => { token = value; };
export async function api(path, options = {}) {
  if (!apiAvailable) throw new Error('Translation service is not connected yet.');
  const { raw = false, ...init } = options;
  const form = init.body instanceof FormData;
  const response = await fetch(`${apiOrigin}/api/v1${path}`, {
    ...init,
    headers: { ...(form ? {} : { 'Content-Type': 'application/json' }), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers },
    signal: init.signal || AbortSignal.timeout(180000)
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const message = typeof data.detail === 'string' ? data.detail : data.detail?.map(x => x.msg).join('; ');
    const error = new Error(message || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  if (response.status === 204) return null;
  return raw ? response.blob() : response.json();
}
export function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
