import { test, expect } from '@playwright/test';
import dotenv from 'dotenv';

dotenv.config();
// Non Functional
test("Latency check: Response should not take longer than 5 seconds", async({request}) =>{
    const url = process.env.APIM_URL;
    const key = process.env.APIM_SUBSCRIPTION_KEY;

    const start_time = Date.now();

    const response = await request.post(
        url, {
            headers: { 'Ocp-Apim-Subscription-Key': key },
            data: { description: "Laptops need updating" }
            });


    const end_time = Date.now();
    const duration = end_time - start_time;
    console.log(`⏱️ Request took ${duration}ms`);
    expect(response.ok()).toBeTruthy();

    expect(duration).toBeLessThan(5000);



    });