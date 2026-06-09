import { defineConfig } from '@playwright/test';
import dotenv from 'dotenv';

// 1. Force load your local environment variables
dotenv.config();

export default defineConfig({
  testDir: './typescript_tests',
  workers: process.env.CI ? 2 : '50%',
  fullyParallel: false,
  timeout: 30000,
  expect: { timeout: 30000 },

  projects: [
//     {
//       name: 'Accuracy-Phase',
//       testMatch: /.*accuracy\.spec\.ts/,
//       timeout: 120000,
//       retries: 1,
//     },
    {
      name: 'Latency-Phase',
      testMatch: /.*latency\.spec\.ts/,
      timeout: 10000,
    },
  {
      name: 'Parallel-Phase',
      testMatch: /.*parallel\.spec\.ts/,
      timeout: 120000,
      retries: 1,
    },
//     {
//       name: 'Load-Phase',
//       testMatch: /.*stress\.spec\.ts/,
//       timeout: 120000,
//       dependencies: ['Accuracy-Phase'],
//       retries: 1,
//     },
  ],

  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],

// Add the local process manager this basically boots up fastapi from current codebase rather than APIM to see if changes work
  webServer: {
    command: 'uvicorn src.api.v3_endpoint:app --workers 4 --host 0.0.0.0 --port 5000', // Launches FastAPI with 4 concurrent workers
    url: 'http://127.0.0.1:5000/docs',                // Playwright pings this URL until it's awake and healthy
    reuseExistingServer: !process.env.CI,              // Locally it won't keep restarting; in CI it boots completely fresh
    timeout: 60000,                                    // Gives Python up to 30 seconds to boot up smoothly
  },
});

