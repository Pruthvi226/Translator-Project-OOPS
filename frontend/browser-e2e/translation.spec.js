import { test, expect } from '@playwright/test';
async function navigate(page, name) {
  const menu = page.getByRole('button', { name: 'Open navigation', exact: true });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole('button', { name, exact: true }).click();
}
test('static production build translates without auth and persists device records', async ({ page }) => {
  await page.route('https://api.mymemory.translated.net/get?**', route => route.fulfill({ json: { responseStatus: 200, responseData: { translatedText: 'नमस्ते' } } }));
  await page.goto('./');
  await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toHaveCount(0);
  await page.getByLabel('Text to translate').fill('Hello');
  await page.getByRole('button', { name: 'Translate', exact: true }).click();
  await expect(page.locator('.translated-content')).toHaveText('नमस्ते');
  await page.reload(); await navigate(page, 'Your translations');
  await expect(page.locator('.saved-item')).toContainText('नमस्ते');
  await navigate(page, 'Vocabulary');
  await page.getByLabel('Word or phrase').fill('hola'); await page.getByLabel('Meaning', { exact: true }).fill('hello');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.locator('.saved-item')).toContainText('hola');
  await page.getByRole('button', { name: 'Delete word' }).click();
  await expect(page.locator('.saved-item')).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
test('quota failure allows a retry and document text stays on-device', async ({ page }) => {
  let fail = true;
  await page.route('https://api.mymemory.translated.net/get?**', route => route.fulfill({ json: fail ? { responseStatus: 403, quotaFinished: true } : { responseStatus: 200, responseData: { translatedText: 'नमस्ते' } } }));
  await page.goto('./');
  await page.getByRole('tab', { name: 'Document', exact: true }).click();
  await page.getByLabel('Upload document').setInputFiles({ name: 'greeting.txt', mimeType: 'text/plain', buffer: Buffer.from('Hello') });
  await page.getByRole('button', { name: 'Translate', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('quota');
  await expect(page.locator('.translated-content')).toHaveCount(0);
  fail = false;
  await page.getByRole('button', { name: 'Translate', exact: true }).click();
  await expect(page.locator('.translated-content')).toHaveText('नमस्ते');
  await expect(page.locator('.extracted')).toContainText('Hello');
});
