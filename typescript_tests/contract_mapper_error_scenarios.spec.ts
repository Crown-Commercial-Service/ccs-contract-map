import { test, expect } from '@playwright/test';
import { classificationCases } from './fixtures/testData';
import { postDescription } from './apiHelper';

// Negative and error handling tests 
test.skip("this test is currently broken: verify endpoint behaviour when empty description is provided @errorcases", async ({ request }) => {
    const emptyDescription = "";
    const response = await postDescription(request, emptyDescription);
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const body = await response.json();
    console.log(`Response for empty description: `, body, 'Status code: ', response.status());
    expect(body.AI_label, "The AI label for empty description should be as expected").toBe("Outside New Taxonomy");    
});

test.skip("this test is currently hold until all Live RM Numbers are in training data: verify endpoint behaviour when description refers Expired RM Number @errorcases", async ({ request }) => {
    const expiredRMDescription = "Agreement ID RM6111"; // Description referring to an expired RM number
    const response = await postDescription(request, expiredRMDescription);
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const body = await response.json();
    console.log(`Response for expired RM number description: `, body, 'Status code: ', response.status());
    expect(body.AI_label, "The AI label for expired RM number description should be as expected").toBe("Outside New Taxonomy");    
});

test("verify endpoint behaviour when invalid credentials are provided @errorcases", async ({ request }) => {  
    // Simulate invalid credentials by temporarily changing the subscription key
    const response = await request.post(`${process.env.APIM_URL}`, {
        headers: {
            'Ocp-Apim-Subscription-Key': `invalid_key`,
            'Content-Type': 'application/json'
        },
        data: { description: "Test description with invalid credentials" },
    });
    expect(response.ok()).toBeFalsy();

    const body = await response.json();
    console.log(`Response for invalid credentials: `, body, 'Status code: ', response.status());

    expect(response.status(), "The status code for invalid credentials should be 401").toBe(401);
});

test("verify endpoint behaviour when malformed input is provided @errorcases", async ({ request }) => {
    // Simulate malformed input by changing jsonbody structure
    const malformedInput = { invalid: "This is a string" };
    const response = await request.post(`${process.env.APIM_URL}`, {
        headers: {
            'Ocp-Apim-Subscription-Key': `${process.env.APIM_SUBSCRIPTION_KEY}`,
            'Content-Type': 'application/json'
        },
        data: malformedInput,
    });
    expect(response.ok()).toBeFalsy();

    const body = await response.json();
    console.log(`Response for malformed input: `, body, 'Status code: ', response.status());
    expect(response.status(), "The status code for malformed input should be 422").toBe(422);
    expect(body.detail[0].msg, "The response body for malformed input should indicate the error").toContain("Field required");
});

test("verify endpoint behaviour when submitting binary data @errorcases", async ({ request }) => {
    const response = await request.post(`${process.env.APIM_URL}`, {
        headers: {
            'Ocp-Apim-Subscription-Key': `${process.env.APIM_SUBSCRIPTION_KEY}`,
            'Content-Type': 'application/json'
        },
        data: { description: Buffer.from([0x00, 0x01, 0x02]) }, // Binary data instead of string
    });
    expect(response.ok()).toBeFalsy();

    console.log("Buffer.from([0x00, 0x01, 0x02]): ", Buffer.from([0x00, 0x01, 0x02]));
    const body = await response.json();
    console.log(`Response for binary data input: `, body, 'Status code: ', response.status());
    expect(response.status(), "The status code for binary data input should be 422").toBe(422);
    expect(body.detail[0].msg, "The response body for binary data input should indicate the error").toContain("Input should be a valid string");
});

test("verify endpoint behaviour when description has punctuation marks & special characters @errorcases", async ({ request }) => {
    const punctuations = "! # $ % + & ' * - / = ? ^ _ ` . { | } ~";
    const specialChars = "© ® ™ € £ ¥";
    const response = await postDescription(request, classificationCases[0].description + punctuations + specialChars);
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const body = await response.json();
    console.log(`Response for description with punctuation marks: `, body, 'Status code: ', response.status());
    expect(body.AI_label, "The AI label for description with punctuation marks should be as expected").toBe(classificationCases[0].expected);    
});

test.skip("This test is broken: verify endpoint behaviour when description has mutilingual characters @errorcases", async ({ request }) => {
    const multilingualDescription = "Replacement CCTV şèřvèř";
    const response = await postDescription(request, multilingualDescription);
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const body = await response.json();
    console.log(`Response for description with multilingual characters: `, body, 'Status code: ', response.status());
    expect(body.AI_label, "The AI label for description with multilingual characters should be as expected").toBe("Hardware");    
});

    