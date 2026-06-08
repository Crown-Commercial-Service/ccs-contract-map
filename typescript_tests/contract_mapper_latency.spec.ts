import { test, expect } from '@playwright/test';
import { postDescription } from './apiHelper';

// Non Functional
test("Latency check: Response should not take longer than 5 seconds @latency", async({request}) =>{
    const start_time = Date.now();

    const response = await postDescription(request, "Test latency");

    const end_time = Date.now();
    const duration = end_time - start_time;
    console.log(`⏱️ Request took ${duration}ms`);
    expect(response.ok()).toBeTruthy();

    expect(duration).toBeLessThan(5000);
});