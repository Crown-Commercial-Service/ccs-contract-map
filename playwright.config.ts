import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './typescript_tests',
  workers: 1,
  fullyParallel: false,
  timeout: 30000,
  expect: { timeout: 5000 },

  projects: [
    {
      name: 'Accuracy-Phase',
      testMatch: /.*accuracy\.spec\.ts/,
      timeout: 30000,
    },
    {
      name: 'Latency-Phase',
      testMatch: /.*latency\.spec\.ts/,
      timeout: 10000,
    },
    {
      name: 'Load-Phase',
      testMatch: /.*stress\.spec\.ts/,
      timeout: 120000,
      dependencies: ['Accuracy-Phase'],
      retries: 1,
    },
    {
      name: 'ErrorScenarios-Phase',
      testMatch: /.*error_scenarios\.spec\.ts/,
      timeout: 30000,
    },
  ],

  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
});

