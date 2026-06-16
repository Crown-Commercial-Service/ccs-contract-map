import { test, expect } from '@playwright/test';
import { classificationCases } from './fixtures/testData';
import { postDescription } from './apiHelper';

// Functional tests
test("checking if model produces expected output @accuracy", async ({ request }) => {
    for (const { description, expected } of classificationCases) {
        const response = await postDescription(request, description);
        expect(response.ok()).toBeTruthy();
        expect(response.status()).toBe(200);

        const body = await response.json();
        const actual = body.AI_label;
        console.log(`Description: ${description} => AI Label: ${actual}`, 'Status code: ', response.status());
        expect(body.AI_label, "The AI labels should match the expected categories in order and be correct").toBe(expected);
    }
});