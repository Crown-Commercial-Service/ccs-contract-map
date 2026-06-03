import { test, expect } from '@playwright/test';
import dotenv from 'dotenv';

// Load the .env file
dotenv.config();

// Non-Functional test
test('stress test @load', async ({ request }) => {
    test.setTimeout(120000);//allow for more time for the test
    const url = process.env.APIM_URL;
    const key = process.env.APIM_SUBSCRIPTION_KEY;
    const total_requests = 501;

    if (!url || !key){
         throw new Error("You need to input values in your .env file")
        }
    console.log(" Sending ${total_requests} to APIM");

    const tasks = Array.from({ length: total_requests }).map(async (_, i) => {
            return request.post(url, {
                headers: {
                    'Content-Type': 'application/json',
                    'Ocp-Apim-Subscription-Key': key
                },
                data: {
                    description: `Stress test call #${i}`,
//                     timestamp: new Date().toISOString()
                }
            });
        });
    // fire all requests all at the same time
    const responses = await Promise.all(tasks);

    //collect status code
    const statuses = responses.map(res => res.status());

    // 4. Count the results
    const successCount = statuses.filter(s => s === 200).length;
    const rateLimitedCount = statuses.filter(s => s === 429).length;
    const otherStatuses = statuses.filter(s => s !== 200 && s !== 429);
    const uniqueOtherCodes = [...new Set(otherStatuses)];

    console.log("------------------------------------");
    console.log(`✅ Success (200): ${successCount}`);
    console.log(`❌ Rate Limited (429): ${rateLimitedCount}`);
    if (otherStatuses.length > 0) console.log(`⚠️ Other Statuses: ${otherStatuses.length} , statuses: ${uniqueOtherCodes}`);
    console.log("------------------------------------");

    expect(rateLimitedCount, 'Rate limit must triggered').toBeGreaterThan(0);

    // run this code:  npx playwright test contract_mapper_functional.spec.ts --reporter=list



});
