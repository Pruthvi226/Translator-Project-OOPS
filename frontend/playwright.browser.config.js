import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './browser-e2e',
  use: { baseURL: 'http://127.0.0.1:4174/Translator-Project-OOPS/' },
  webServer: {
    command: 'npm run build && npx vite preview --host 127.0.0.1 --port 4174',
    url: 'http://127.0.0.1:4174/Translator-Project-OOPS/',
    env: { VITE_STATIC_ONLY: 'true', VITE_API_BASE_URL: '', VITE_BASE_PATH: '/Translator-Project-OOPS/' },
    timeout: 120000
  },
  projects: [{ name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } }, { name: 'mobile', use: { viewport: { width: 390, height: 844 } } }]
});
