import { test, expect } from '@playwright/test';
import { classificationCases } from './fixtures/testData';
import { postDescription } from './apiHelper';

// Functional tests
// using forEach so that a failure of one test doesn't block the others
classificationCases.forEach(({ description, expected }, index) => {
    test(`checking if model produces expected output for case ${index + 1}: ${expected} @accuracy`, async ({ request }) => {
        const response = await postDescription(request, description);
        expect(response.ok()).toBeTruthy();
        expect(response.status()).toBe(200);

        const body = await response.json();
        const actual = body.AI_label;
        console.log(`Description: ${description} => AI Label: ${actual}`, 'Status code: ', response.status());
        expect(body.AI_label, "The AI labels should match the expected categories and be correct").toBe(expected);
    });
});