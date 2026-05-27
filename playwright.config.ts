import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './typescript_tests',
  workers: 1,           // Essential for sequential order
  fullyParallel: false,

  projects: [
    {
      name: 'Accuracy-Phase',
      testMatch: /.*accuracy\.spec\.ts/,
    },
    {
      name: 'Latency-Phase',
      testMatch: /.*latency\.spec\.ts/,
    },
    {
      name: 'Load-Phase',
      testMatch: /.*stress\.spec\.ts/,
      // Now Stress waits for Accuracy to finish
      dependencies: ['Accuracy-Phase'],
    },
  ],
});

// npx playwright test --workers=1

