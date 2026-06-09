import { test, expect } from '@playwright/test';
import { classificationCases } from './fixtures/testData';
import { postDescription } from './apiHelper';

// Negative and error handling tests
test("checking if model produces expected output when empty description is provided @errorcodes", async ({ request }) => {
    const emptyDescription = ""; // Empty description to trigger error handling
    const response = await postDescription(request, emptyDescription);
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const body = await response.json();
    console.log(`Response for empty description: `, body, 'Status code: ', response.status());
    expect(body.AI_label, "The AI label for empty description should be as expected").toBe("Outside New Taxonomy");    
});

test("checking if model produces expected output when description refers Expired RM Number @errorcodes", async ({ request }) => {
    const expiredRMDescription = "Agreement ID RM6111"; // Description referring to an expired RM number
    const response = await postDescription(request, expiredRMDescription);
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const body = await response.json();
    console.log(`Response for expired RM number description: `, body, 'Status code: ', response.status());
    expect(body.AI_label, "The AI label for expired RM number description should be as expected").toBe("Outside New Taxonomy");    
});

test("checking if model returns unauthorized error for invalid credentials @errorcodes", async ({ request }) => {  
    // Simulate invalid credentials by temporarily changing the subscription key
    const originalKey = process.env.APIM_SUBSCRIPTION_KEY;
    process.env.APIM_SUBSCRIPTION_KEY = "invalid_key";

    const response = await postDescription(request, classificationCases[0].description);
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    console.log(`Response for invalid credentials: `, body, 'Status code: ', response.status());

    expect(response.status(), "The status code for invalid credentials should be 401").toBe(401);

    // Restore the original subscription key
    process.env.APIM_SUBSCRIPTION_KEY = originalKey;
});

test("checking if model returns bad request error for malformed input @errorcodes", async ({ request }) => {
    // Simulate malformed input by sending a non-string description
    const malformedInput = { invalid: "This is a string" }; // Malformed input
    const response = await request.post(`${process.env.APIM_URL}`, {
        headers: {
            'Ocp-Apim-Subscription-Key': `${process.env.APIM_SUBSCRIPTION_KEY}`,
            'Content-Type': 'application/json'
        },
        data: malformedInput,
    });
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    console.log(`Response for malformed input: `, body, 'Status code: ', response.status());
    expect(response.status(), "The status code for malformed input should be 422").toBe(422);
    expect(body.details.msg, "The response body for malformed input should indicate the error").toContain("JSON decode error");
});
    