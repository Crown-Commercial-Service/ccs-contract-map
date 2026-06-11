import { test, expect } from "@playwright/test";
import { postDescription } from "./apiHelper";

// Non-Functional test
test("stress test @load", async ({ request }) => {
  const total_requests = 501;
  console.log(`Sending ${total_requests} to APIM`);

  const tasks = Array.from({ length: total_requests }).map(async (_, i) => {
    return postDescription(request, `Test load ${i}`);
  });
  // fire all requests all at the same time
  const responses = await Promise.all(tasks);

  // collect status code
  const statuses = responses.map((res) => res.status());

  // Count the results
  const successCount = statuses.filter((s) => s === 200).length;
  const rateLimitedCount = statuses.filter((s) => s === 429).length;
  const otherStatuses = statuses.filter((s) => s !== 200 && s !== 429);
  const uniqueOtherCodes = [...new Set(otherStatuses)];

  console.log("------------------------------------");
  console.log(`✅ Success (200): ${successCount}`);
  console.log(`❌ Rate Limited (429): ${rateLimitedCount}`);
  if (otherStatuses.length > 0)
    console.log(
      `⚠️ Other Statuses: ${otherStatuses.length} , statuses: ${uniqueOtherCodes}`,
    );
  console.log("------------------------------------");

  expect(rateLimitedCount, "Rate limit must triggered").toBeGreaterThan(0);
});
