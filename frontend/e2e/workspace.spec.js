import { test, expect } from '@playwright/test';
test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/**', async route => {
    const url = route.request().url();
    const body = url.endsWith('/capabilities') ? {languages:{en:'English',hi:'Hindi'},providers:[{id:'gemini',tone:true}],speech:false,rag:false} : url.endsWith('/auth/signup') ? {access_token:'test-token'} : url.endsWith('/me') ? {name:'Test Learner',email:'test@example.com',preferences:{}} : url.endsWith('/translate') ? {id:'translation-1',translated_text:'नमस्ते',detected_language:'en',providers:['gemini'],warnings:[]} : {};
    await route.fulfill({json:body});
  });
});
test('sign up and translate through the workspace', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', {name:'Translation studio.'})).toBeVisible();
  await page.screenshot({path:`test-results/workspace-${test.info().project.name}.png`,fullPage:true});
  await page.getByLabel('Text to translate').fill('Hello');
  await page.getByRole('button', {name:'Translate',exact:true}).click();
  await page.getByLabel('Your name').fill('Test Learner');
  await page.getByLabel('Email address').fill('test@example.com');
  await page.getByLabel('Password').fill('strong-password-123');
  await page.getByRole('button',{name:'Create your account'}).click();
  await expect(page.getByRole('dialog')).toBeHidden();
  await page.getByRole('button',{name:'Translate',exact:true}).click();
  await expect(page.getByText('नमस्ते',{exact:true})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});
test('renders untrusted model output as text', async ({ page }) => {
  await page.route('**/api/v1/translate', route => route.fulfill({json:{id:'unsafe',translated_text:'<img src=x onerror=alert(1)>',detected_language:'en',providers:['gemini'],warnings:[]}}));
  await page.goto('/');
  await page.getByLabel('Text to translate').fill('Hello');
  await page.getByRole('button',{name:'Translate',exact:true}).click();
  await page.getByLabel('Your name').fill('Test Learner');
  await page.getByLabel('Email address').fill('test@example.com');
  await page.getByLabel('Password').fill('strong-password-123');
  await page.getByRole('button',{name:'Create your account'}).click();
  await expect(page.getByRole('dialog')).toBeHidden();
  await page.getByRole('button',{name:'Translate',exact:true}).click();
  await expect(page.locator('.translated-content')).toHaveText('<img src=x onerror=alert(1)>');
  await expect(page.locator('img[src="x"]')).toHaveCount(0);
});
