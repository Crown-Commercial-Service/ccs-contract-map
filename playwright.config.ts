import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './typescript_tests',
  workers: 1,           // Essential for sequential order
  fullyParallel: false,

  projects: [
    {
      name: 'Accuracy-Phase',
      testMatch: /.*accuracy\.spec\.ts/,
      timeout: 120000,
      retries: 1,

    },
    {
      name: 'Latency-Phase',
      testMatch: /.*latency\.spec\.ts/,
      timeout: 120000,
      retries: 1,

    },
    {
      name: 'Parallel-Phase',
      testMatch: /.*parallel\.spec\.ts/,
      // Now Stress waits for Accuracy to finish
      timeout: 120000,
      dependencies: ['Accuracy-Phase'],
      retries: 1,
    },
  ],
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
});

// npx playwright test --workers=1

