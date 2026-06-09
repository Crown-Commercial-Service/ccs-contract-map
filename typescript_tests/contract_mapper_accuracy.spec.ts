import { test, expect } from '@playwright/test';
import { classificationCases } from './fixtures/testData';
import { postDescription } from './apiHelper';

// Functional tests
test("checking if model produces expected output @accuracy", async ({ request }) => {
    for (const { description, expected } of classificationCases) {
        const response = await postDescription(request, description);

        // 🚀 CRITICAL FOR GIT CI: Gather information before any 'expect' throws an error
        const isOk = response.ok();
        const statusCode = response.status();

        // Safely extract the raw body string (even if it's a Python error traceback)
        const rawBodyText = await response.text().catch(() => "Unable to read response body text");

        // 💥 BYPASS PLAYWRIGHT BUFFER: Force terminal to print instantly to Git logs
        process.stderr.write(`\n======================================================================\n`);
        process.stderr.write(`📝 TESTING CASE: "${description.substring(0, 70)}..."\n`);
        process.stderr.write(`📊 HTTP STATUS : ${statusCode} (Expected 200 | OK: ${isOk})\n`);
        process.stderr.write(`🎯 TARGET LABEL: "${expected}"\n`);

        if (!isOk) {
            process.stderr.write(`❌ RAW ERROR RESPONSE FROM SERVER:\n${rawBodyText}\n`);
        } else {
            try {
                const body = JSON.parse(rawBodyText);
                process.stderr.write(`🧠 ACTUAL AI LABEL RETURNED: "${body.AI_label}"\n`);
            } catch (e) {
                process.stderr.write(`❌ SUCCESS STATUS BUT FAILED TO PARSE JSON BODY.\n`);
            }
        }
        process.stderr.write(`======================================================================\n\n`);

        // 🛠️ Playwright strict assertions (these will halt execution on failure)
        expect(isOk, `API request failed with status code ${statusCode}`).toBeTruthy();
        expect(statusCode).toBe(200);

        // Verify data matching logic if the request layer succeeded
        const body = JSON.parse(rawBodyText);
        expect(body.AI_label, "The AI labels should match the expected categories").toBe(expected);
    }
});
// import { test, expect } from '@playwright/test';
// import { classificationCases } from './fixtures/testData';
// import { postDescription } from './apiHelper';
//
// // Functional tests
// test("checking if model produces expected output @accuracy", async ({ request }) => {
//     for (const { description, expected } of classificationCases) {
//         const response = await postDescription(request, description);
//         expect(response.ok()).toBeTruthy();
//         expect(response.status()).toBe(200);
//
//         const body = await response.json();
//         const actual = body.AI_label;
//         console.log(`Description: ${description} => AI Label: ${actual}`, 'Status code: ', response.status());
//         expect(body.AI_label, "The AI labels should match the expected categories in order and be correct").toBe(expected);
//     }
// });