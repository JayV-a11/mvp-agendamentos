import { defineConfig } from '@playwright/test';

// O servidor e o banco são criados pelo Pytest. Impede apontar estes testes para produção.
const origin = process.env['E2E_BASE_URL'];
if (process.env['E2E_ISOLATED'] !== '1' || !origin || new URL(origin).hostname !== '127.0.0.1') {
  throw new Error('Execute pelo Pytest com --frontend-e2e para usar PostgreSQL isolado.');
}
export default defineConfig({
  testDir: 'e2e',
  workers: 1,
  retries: 0,
  timeout: 120_000,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  expect: { timeout: 15_000 },
  use: {
    baseURL: origin,
    channel: process.env['E2E_BROWSER'] ?? 'msedge',
    headless: true,
    actionTimeout: 15_000,
    viewport: { width: 390, height: 844 },
    locale: 'pt-BR',
    timezoneId: 'Asia/Tokyo',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
});
