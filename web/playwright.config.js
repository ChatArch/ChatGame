import { defineConfig, devices } from '@playwright/test'

const port = Number(process.env.CHATGAME_E2E_PORT || 8134)
const baseURL = `http://127.0.0.1:${port}`

export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: `cd .. && PYTHONPATH=src CHATGAME_WEB_ASSETS_DIR=src/chatgame/web_static python -m uvicorn chatgame.api:app --host 127.0.0.1 --port ${port} --log-level info`,
    url: `${baseURL}/api/health`,
    reuseExistingServer: false,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
