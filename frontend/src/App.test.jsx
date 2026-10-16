import React from 'react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ languages: { en: 'English', hi: 'Hindi' }, providers: [], rag: false, speech: false }) }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
test('translation workspace validates input and shows engine setup honestly', async () => {
  render(<App/>);
  expect(screen.getByRole('button', { name: 'Translate' })).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Text to translate'), { target: { value: 'Hello' } });
  expect(screen.getByRole('button', { name: 'Translate' })).toBeEnabled();
  await waitFor(() => expect(screen.getByText('Provider setup needed')).toBeVisible());
  fireEvent.click(screen.getByRole('button', { name: 'Translate' }));
  expect(screen.getByRole('dialog')).toBeVisible();
});
test('switches modalities and preserves accessible labels', async () => {
  render(<App/>);
  fireEvent.click(screen.getByRole('tab', { name: 'Image' }));
  expect(screen.getByLabelText('Upload image')).toHaveAttribute('accept', '.png,.jpg,.jpeg,.webp');
  fireEvent.click(screen.getByRole('tab', { name: 'Document' }));
  expect(screen.getByLabelText('Upload document')).toHaveAttribute('accept', '.pdf,.docx,.txt');
  await waitFor(() => expect(screen.getByText('Provider setup needed')).toBeVisible());
});
test('evaluation never invents quality metrics', async () => {
  render(<App/>);
  fireEvent.click(screen.getByRole('button', { name: 'Usage & evaluation' }));
  expect(screen.getAllByText('Not measured')).toHaveLength(5);
  expect(screen.getByText(/No quality benchmark has been measured yet/)).toBeVisible();
  await waitFor(() => expect(screen.getByText('Provider setup needed')).toBeVisible());
});

test('an unavailable service is reported instead of staying in a connecting state', async () => {
  globalThis.fetch.mockRejectedValue(new Error('offline'));
  render(<App/>);
  await waitFor(() => expect(screen.getByText('Translation service offline')).toBeVisible());
  expect(screen.getByRole('status')).toHaveTextContent('Translation service is not connected');
  fireEvent.change(screen.getByLabelText('Text to translate'), { target: { value: 'Hello' } });
  fireEvent.click(screen.getByRole('button', { name: 'Translate' }));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});
